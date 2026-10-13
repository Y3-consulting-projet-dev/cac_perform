"""
Vérifications AVANT l'enregistrement d'un fichier complémentaire (balance
auxiliaire clients/fournisseurs, fichier des immobilisations) :

1. cohérence du type : les comptes du fichier correspondent-ils à la carte
   choisie (41x clients, 40x fournisseurs, 2x immobilisations) ?
2. cohérence de l'exercice : l'année lue dans le nom du fichier ou ses
   lignes de titre correspond-elle à l'exercice audité de la mission ?

Ces contrôles produisent des ALERTES, jamais un refus : l'utilisateur voit
l'alerte et choisit d'annuler ou d'importer quand même (écran Fichiers
complémentaires). Rien n'est écrit en base ici.
"""
import io
import re
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional

import openpyxl
from bson import ObjectId
from bson.errors import InvalidId

from src.services import mapping_apercu_service as apercu_service
from src.utils.database import get_database

# Famille de comptes attendue par type de fichier (racine SYSCOHADA).
FAMILLES_COMPTES = {
    "auxiliaire_client": {"racine": "41", "libelle": "comptes clients (41x)", "court": "client (41x)",
                          "fichier": "une balance auxiliaire clients"},
    "auxiliaire_fournisseur": {"racine": "40", "libelle": "comptes fournisseurs (40x)", "court": "fournisseur (40x)",
                               "fichier": "une balance auxiliaire fournisseurs"},
    "immobilisations": {"racine": "2", "libelle": "comptes d'immobilisations (2x)", "court": "d'immobilisation (2x)",
                        "fichier": "un fichier des immobilisations"},
}

# TODO(décision) : seuil à partir duquel la carte choisie est jugée
# incohérente. Hypothèse de travail : alerte si moins de la moitié des
# comptes reconnus appartiennent à la famille attendue.
PART_MINIMALE_FAMILLE_ATTENDUE = 0.5

MOTIF_ANNEE = re.compile(r"(?<!\d)(20\d{2})(?!\d)")


def famille_du_compte(numero: Any) -> Optional[str]:
    """Type de fichier dont relève un numéro de compte, ou None s'il n'est pas reconnu."""
    texte = str(numero or "").strip()
    if not texte or not texte[0].isdigit():
        return None  # code tiers alphanumérique (ex. « FRS001 ») : non concluant
    # Racines les plus longues d'abord : « 40 »/« 41 » avant « 2 ».
    for type_fichier, famille in sorted(FAMILLES_COMPTES.items(), key=lambda kv: -len(kv[1]["racine"])):
        if texte.startswith(famille["racine"]):
            return type_fichier
    return "autres"


def controler_type(type_fichier: str, numeros: Iterable[Any]) -> Dict[str, Any]:
    """
    Fonction pure. Répartit les comptes par famille et renvoie une alerte si
    la famille attendue pour `type_fichier` est minoritaire. Aucun compte
    reconnu -> pas d'alerte, une information « non vérifiable ».
    """
    repartition: Dict[str, int] = {}
    for numero in numeros:
        famille = famille_du_compte(numero)
        if famille:
            repartition[famille] = repartition.get(famille, 0) + 1

    total = sum(repartition.values())
    attendue = FAMILLES_COMPTES[type_fichier]
    resultat: Dict[str, Any] = {"repartition_comptes": repartition, "alerte": None, "information": None}

    if total == 0:
        resultat["information"] = (
            "Type du fichier non vérifiable : aucun numéro de compte reconnu."
        )
        return resultat

    part_attendue = repartition.get(type_fichier, 0) / total
    if part_attendue >= PART_MINIMALE_FAMILLE_ATTENDUE:
        return resultat

    dominante = max(repartition, key=repartition.get)
    if dominante in FAMILLES_COMPTES:
        contenu = f"des {FAMILLES_COMPTES[dominante]['libelle']}"
    else:
        contenu = "surtout des comptes hors des familles 40x, 41x et 2x"
    resultat["alerte"] = {
        "code": "type_incoherent",
        "message": (
            f"Ce fichier contient {contenu} : il ne semble pas être "
            f"{attendue['fichier']} ({repartition.get(type_fichier, 0)} compte {attendue['court']} "
            f"sur {total} comptes reconnus)."
        ),
    }
    return resultat


def annees_detectees(nom_fichier: Optional[str], lignes_titre: Iterable[Iterable[Any]]) -> List[int]:
    """Fonction pure : années (20xx) lues dans le nom du fichier et les cellules des lignes de titre."""
    annees = set()
    for match in MOTIF_ANNEE.findall(nom_fichier or ""):
        annees.add(int(match))
    for ligne in lignes_titre:
        for cellule in ligne:
            if isinstance(cellule, (datetime, date)):
                annees.add(cellule.year)
            elif cellule is not None:
                annees.update(int(m) for m in MOTIF_ANNEE.findall(str(cellule)))
    return sorted(annees)


def controler_exercice(annee_auditee: Optional[str], annees: List[int]) -> Dict[str, Any]:
    """
    Fonction pure. Alerte si des années ont été lues dans le fichier et
    qu'aucune n'est l'exercice audité.

    TODO(spec) : règle de tolérance exacte non définie (exercice décalé à
    cheval sur deux années, fichier N-1 fourni volontairement, etc.).
    Hypothèse de travail : pas d'alerte dès que l'exercice audité figure
    parmi les années lues.
    """
    resultat: Dict[str, Any] = {"annees_detectees": annees, "alerte": None, "information": None}
    if not annee_auditee:
        resultat["information"] = "Exercice audité de la mission inconnu : année non vérifiée."
        return resultat
    if not annees:
        resultat["information"] = "Aucune année trouvée dans le nom ni dans l'en-tête du fichier : exercice non vérifié."
        return resultat
    if int(annee_auditee) in annees:
        return resultat
    resultat["alerte"] = {
        "code": "exercice_incoherent",
        "message": (
            f"Le fichier semble porter sur {', '.join(str(a) for a in annees)}, "
            f"alors que l'exercice audité de la mission est {annee_auditee}."
        ),
    }
    return resultat


def annee_auditee_de_la_mission(mission_id: str) -> Optional[str]:
    """Mission1.annee_auditee sous forme « AAAA », None si absente ou illisible."""
    try:
        object_id = ObjectId(mission_id)
    except InvalidId:
        raise ValueError(f"mission_id invalide : '{mission_id}'")
    mission = get_database()["Mission1"].find_one({"_id": object_id}, {"annee_auditee": 1})
    if not mission:
        raise ValueError("Mission non trouvée")
    brute = mission.get("annee_auditee")
    if isinstance(brute, list):  # certaines missions historiques stockent une liste
        brute = brute[0] if brute else None
    try:
        return str(int(brute))
    except (TypeError, ValueError):
        return None


def _lignes_titre(contenu: bytes) -> List[List[Any]]:
    """Lignes situées avant la ligne d'en-tête (titre, entité, période...)."""
    workbook = openpyxl.load_workbook(io.BytesIO(contenu), data_only=True, read_only=True)
    sheet = apercu_service._choisir_feuille(workbook)
    ligne_entete = apercu_service._trouver_ligne_entete(sheet)
    lignes = [list(r) for r in sheet.iter_rows(min_row=1, max_row=max(ligne_entete - 1, 0), values_only=True)] \
        if ligne_entete > 1 else []
    workbook.close()
    return lignes


def verifier_fichier(fichier, type_fichier: str, annee_auditee: Optional[str]) -> Dict[str, Any]:
    """
    Lit le fichier (même mapping automatique que l'import) et renvoie
    {alertes: [...], informations: [...], repartition_comptes, annees_detectees}.
    """
    if type_fichier not in FAMILLES_COMPTES:
        raise ValueError(f"Type de fichier inconnu : '{type_fichier}'")

    contenu = fichier.read()
    apercu = apercu_service.generer_apercu_mapping(io.BytesIO(contenu))
    lignes = apercu_service.lire_lignes_selon_mapping(io.BytesIO(contenu), apercu["mapping_propose"])
    numeros = [l.get("numero_compte") or l.get("numero") or l.get("categorie") for l in lignes]

    type_ok = controler_type(type_fichier, numeros)
    exercice = controler_exercice(
        annee_auditee,
        annees_detectees(getattr(fichier, "filename", None), _lignes_titre(contenu)),
    )

    return {
        "alertes": [r["alerte"] for r in (type_ok, exercice) if r["alerte"]],
        "informations": [r["information"] for r in (type_ok, exercice) if r["information"]],
        "repartition_comptes": type_ok["repartition_comptes"],
        "annees_detectees": exercice["annees_detectees"],
        "annee_auditee": annee_auditee,
    }
