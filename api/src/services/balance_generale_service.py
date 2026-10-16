"""
Import V2 de la balance générale (exercice N) d'une mission EXISTANTE —
remplacement depuis l'écran Fichiers complémentaires. La création de
mission reste sur l'import V1 (api/src/model.py, non modifié).

Même mécanisme que les fichiers complémentaires : détection de la ligne
d'en-tête et correspondance des colonnes (mapping_apercu_service, mapping
mémorisé par client + logiciel), contrôles préliminaires, versions.

Le document produit a la MÊME FORME qu'un document Balance de l'import V1
(numero_compte, libelle, debit/credit initial/mvt/fin, solde_reel, solde,
sign_solde ; id_client, annee_balance) pour que les étapes V1 continuent de
le lire sans changement. Il remplace l'_id de la balance N à la MÊME
POSITION dans Mission1.balances (la V1 lit N en [0] et N-1 en [1]).

Lignes de sous-total (règle validée, docs/PLAN_verrou_IPE.md) : une ligne
est écartée si son numéro est le préfixe d'autres comptes du fichier ET si
ses montants égalent la somme de ces comptes. Le libellé n'est jamais lu.
Les lignes écartées sont tracées dans les contrôles préliminaires.

Limite assumée, signalée à l'écran : les données que la V1 a dérivées des
balances à la création de la mission (Mission1.balance_variation, grouping,
efi) ne sont PAS recalculées ici. TODO(décision) : faut-il les recalculer
au remplacement (au risque d'écraser le travail déjà fait sur les étapes) ?
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId
from bson.errors import InvalidId

from src.utils.database import get_database
from src.services import mapping_apercu_service as apercu_service
from src.services import mapping_memorise_service
from src.services import controle_preliminaire_service as cp_service
from src.services import verrou_ipe_service

TYPE_FICHIER = "balance_generale"

# Montants comparés par la règle des sous-totaux (forme V1).
CHAMPS_MONTANTS = ["debit_initial", "credit_initial", "debit_mvt", "credit_mvt", "debit_fin", "credit_fin"]
TOLERANCE_SOUS_TOTAL = 0.01  # arrondi Excel, même seuil que controler_bouclage_total


# --------------------------------------------------------------------------
# Fonctions pures
# --------------------------------------------------------------------------

def detecter_sous_totaux(lignes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Sépare les comptes des lignes de sous-total (forme V1). Fonction pure.

    Une ligne est un sous-total si son numéro est le préfixe d'au moins un
    autre compte du fichier ET si chacun de ses montants égale la somme de
    ces comptes. Traitement des numéros les plus longs d'abord : un
    sous-total imbriqué (« 284 ») est écarté avant son parent (« 28 »), qui
    est alors comparé aux seuls comptes restants — jamais compté deux fois.

    Renvoie (comptes, sous_totaux) ; chaque sous-total porte
    `nb_comptes_detail` (nombre de comptes qu'il résume).
    """
    def numero(ligne):
        return str(ligne.get("numero_compte") or "").strip()

    ordre = sorted(range(len(lignes)), key=lambda i: -len(numero(lignes[i])))
    ecartes = set()
    detail: Dict[int, int] = {}
    for i in ordre:
        n = numero(lignes[i])
        if not n:
            continue
        enfants = [
            j for j in range(len(lignes))
            if j != i and j not in ecartes
            and len(numero(lignes[j])) > len(n) and numero(lignes[j]).startswith(n)
        ]
        if not enfants:
            continue
        egal = all(
            abs((lignes[i].get(champ) or 0) - sum((lignes[j].get(champ) or 0) for j in enfants)) <= TOLERANCE_SOUS_TOTAL
            for champ in CHAMPS_MONTANTS
        )
        if egal:
            ecartes.add(i)
            detail[i] = len(enfants)

    comptes = [l for i, l in enumerate(lignes) if i not in ecartes]
    sous_totaux = [{**lignes[i], "nb_comptes_detail": detail[i]} for i in sorted(ecartes)]
    return comptes, sous_totaux


def _nombre(valeur) -> float:
    return float(valeur) if isinstance(valeur, (int, float)) else 0.0


def convertir_en_forme_v1(ligne: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fonction pure : ligne lue selon le mapping (noms de la balance générale
    « numero/debit_initial… » ou du format Y3 « numero_compte/solde_ouverture_debit… »)
    -> ligne au format exact de l'import V1. Mêmes calculs que model.py :
    solde_reel = debit_fin - credit_fin, solde = |solde_reel|,
    sign_solde = D si debit_fin >= credit_fin.

    Solde final absent du fichier : déduit de ouverture + mouvements
    (arithmétique, pas une convention). Format à montant unique : positif
    = débit, négatif = crédit (même convention que les fichiers
    complémentaires, TODO(spec: CAC-IPE-01)).
    """
    def lire(*cles):
        for cle in cles:
            if ligne.get(cle) is not None:
                return ligne.get(cle)
        return None

    debit_initial = _nombre(lire("debit_initial", "solde_ouverture_debit"))
    credit_initial = _nombre(lire("credit_initial", "solde_ouverture_credit"))
    debit_mvt = _nombre(lire("debit_mvt", "mouvement_debit"))
    credit_mvt = _nombre(lire("credit_mvt", "mouvement_credit"))
    debit_fin_brut = lire("debit_fin", "solde_final_debit")
    credit_fin_brut = lire("credit_fin", "solde_final_credit")

    if "montant" in ligne and debit_fin_brut is None and credit_fin_brut is None:
        montant = _nombre(ligne.get("montant"))
        debit_fin, credit_fin = max(montant, 0.0), max(-montant, 0.0)
    elif debit_fin_brut is None and credit_fin_brut is None:
        net = (debit_initial - credit_initial) + (debit_mvt - credit_mvt)
        debit_fin, credit_fin = max(net, 0.0), max(-net, 0.0)
    else:
        debit_fin, credit_fin = _nombre(debit_fin_brut), _nombre(credit_fin_brut)

    solde_reel = debit_fin - credit_fin
    return {
        "numero_compte": str(lire("numero_compte", "numero") or "").strip(),
        "libelle": str(lire("libelle", "libelle_compte") or "").strip(),
        "debit_initial": debit_initial,
        "credit_initial": credit_initial,
        "debit_mvt": debit_mvt,
        "credit_mvt": credit_mvt,
        "debit_fin": debit_fin,
        "credit_fin": credit_fin,
        "solde_reel": solde_reel,
        "solde": abs(solde_reel),
        "sign_solde": "D" if debit_fin >= credit_fin else "C",
    }


def _vers_noms_bouclage(ligne_v1: Dict[str, Any]) -> Dict[str, Any]:
    """Noms attendus par controle_preliminaire_service.controler_bouclage_ligne."""
    return {
        "_ligne_excel": ligne_v1.get("_ligne_excel"),
        "numero_compte": ligne_v1["numero_compte"],
        "libelle_compte": ligne_v1["libelle"],
        "solde_ouverture_debit": ligne_v1["debit_initial"],
        "solde_ouverture_credit": ligne_v1["credit_initial"],
        "mouvement_debit": ligne_v1["debit_mvt"],
        "mouvement_credit": ligne_v1["credit_mvt"],
        "solde_final_debit": ligne_v1["debit_fin"],
        "solde_final_credit": ligne_v1["credit_fin"],
    }


# --------------------------------------------------------------------------
# Accès Mongo
# --------------------------------------------------------------------------

def _mission(mission_id: str) -> Dict[str, Any]:
    try:
        object_id = ObjectId(mission_id)
    except InvalidId:
        raise ValueError(f"mission_id invalide : '{mission_id}'")
    mission = get_database()["Mission1"].find_one({"_id": object_id}, {"balances": 1, "annee_auditee": 1, "id_client": 1})
    if not mission:
        raise ValueError("Mission non trouvée")
    return mission


def _position_balance_n(mission: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Position et document de la balance N dans Mission1.balances (choisie par année, comme le rapprochement IPE)."""
    annee_n = str(mission.get("annee_auditee"))
    db = get_database()
    for index, balance_id in enumerate(mission.get("balances") or []):
        try:
            doc = db["Balance"].find_one({"_id": ObjectId(balance_id)})
        except InvalidId:
            continue
        if doc and str(doc.get("annee_balance")) == annee_n:
            return index, doc
    raise ValueError(f"Aucune balance générale de l'exercice {annee_n} n'est rattachée à la mission.")


def _resoudre_mapping(fichier, id_client: str, logiciel_comptable: Optional[str],
                      mapping_force: Optional[Dict[str, str]]) -> Dict[str, Any]:
    """Même priorité que les fichiers complémentaires : explicite > mémorisé > aperçu automatique."""
    apercu = apercu_service.generer_apercu_mapping(fichier)
    if mapping_force:
        return {"mapping": mapping_force, "apercu": apercu}
    if logiciel_comptable:
        memorise = mapping_memorise_service.recuperer_mapping(id_client, logiciel_comptable)
        if memorise and memorise.get("mapping"):
            return {"mapping": memorise["mapping"], "apercu": apercu}
    return {"mapping": apercu["mapping_propose"], "apercu": apercu}


def resume_balance(doc: Dict[str, Any], actif: bool) -> Dict[str, Any]:
    """Résumé affiché sur la carte « Balance générale » (V1 ou V2)."""
    return {
        "_id": str(doc["_id"]),
        "type": TYPE_FICHIER,
        "origine": "import_v2" if doc.get("type") == TYPE_FICHIER else "import_v1",
        "nom_fichier": doc.get("nom_fichier"),
        "date_import": doc.get("date_import"),
        "version": doc.get("version", 1),
        "actif": actif,
        "annee_balance": doc.get("annee_balance"),
        "nb_lignes": len(doc.get("balance") or []),
        "utilisateur_id": doc.get("utilisateur_id"),
    }


def lire_balance_generale(mission_id: str) -> Dict[str, Any]:
    """Balance N en vigueur + versions précédentes (chaîne `remplace_balance_id`)."""
    mission = _mission(mission_id)
    _, actuelle = _position_balance_n(mission)
    historique = []
    db = get_database()
    precedente_id = actuelle.get("remplace_balance_id")
    while precedente_id:
        doc = db["Balance"].find_one({"_id": ObjectId(precedente_id)})
        if not doc:
            break
        historique.append(resume_balance(doc, actif=False))
        precedente_id = doc.get("remplace_balance_id")
    return {"active": resume_balance(actuelle, actif=True), "historique": historique}


def lire_detail(mission_id: str, balance_id: str) -> Optional[Dict[str, Any]]:
    """
    Détail d'une balance générale de la mission (en vigueur ou précédente),
    même forme que fichiers_complementaires_service.lire_detail_fichier.
    Cloisonnement : None si la balance n'appartient pas à la mission.
    """
    from src.services import fichiers_complementaires_service as fc_service  # import différé : évite un cycle

    etat = lire_balance_generale(mission_id)
    ids_mission = {etat["active"]["_id"], *(h["_id"] for h in etat["historique"])}
    if balance_id not in ids_mission:
        return None
    doc = get_database()["Balance"].find_one({"_id": ObjectId(balance_id)})
    lignes = doc.get("balance") or []
    return {
        **resume_balance(doc, actif=balance_id == etat["active"]["_id"]),
        "mapping_utilise": doc.get("mapping_utilise"),
        "controles_preliminaires": doc.get("controles_preliminaires"),
        "lignes": lignes,
        "totaux": fc_service._calculer_totaux(lignes),
    }


def importer_balance_generale(
    fichier,
    mission_id: str,
    utilisateur_id: Optional[str] = None,
    logiciel_comptable: Optional[str] = None,
    mapping: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Remplace la balance générale N de la mission. Ne supprime rien :
    l'ancien document reste en base, référencé par `remplace_balance_id`
    (et archivé `actif=False` s'il venait déjà de cet import V2).
    """
    mission = _mission(mission_id)
    position, ancienne = _position_balance_n(mission)
    id_client = str(mission.get("id_client"))

    integrite = cp_service.controler_integrite(fichier)
    if not integrite["ok"]:
        raise ValueError("; ".join(integrite["erreurs"]) or "Fichier invalide")

    resolu = _resoudre_mapping(fichier, id_client, logiciel_comptable, mapping)
    lignes_brutes = apercu_service.lire_lignes_selon_mapping(fichier, resolu["mapping"])
    if not lignes_brutes:
        raise ValueError("Aucune ligne exploitable trouvée dans le fichier (vérifiez la correspondance des colonnes)")

    lignes_v1 = [{**convertir_en_forme_v1(l), "_ligne_excel": l.get("_ligne_excel")} for l in lignes_brutes]
    avec_numero, sans_numero = cp_service.separer_lignes_sans_identifiant(
        [{**l, "numero_compte": l["numero_compte"] or None} for l in lignes_v1], "numero_compte",
    )
    if not avec_numero:
        raise ValueError("Aucune ligne avec un numéro de compte trouvée dans le fichier")

    comptes, sous_totaux = detecter_sous_totaux(avec_numero)

    lignes_ecartees = sans_numero + [
        {"ligne_excel": s.get("_ligne_excel"), "motif": "sous_total",
         "contenu": {k: v for k, v in s.items() if k != "_ligne_excel"}}
        for s in sous_totaux
    ]
    controles = {
        "integrite": integrite,
        "doublons": cp_service.controler_doublons(comptes, cle="numero_compte"),
        "lignes_ecartees": {"nb": len(lignes_ecartees), "lignes": lignes_ecartees},
        "sous_totaux": {
            "nb": len(sous_totaux),
            "lignes": [{"ligne_excel": s.get("_ligne_excel"), "numero_compte": s["numero_compte"],
                        "libelle": s["libelle"], "nb_comptes_detail": s["nb_comptes_detail"]} for s in sous_totaux],
        },
        "bouclage_total": cp_service.controler_bouclage_total(comptes, sans_numero, "numero_compte"),
        "bouclage_ligne": cp_service.controler_bouclage_ligne([_vers_noms_bouclage(c) for c in comptes]),
    }

    db = get_database()
    precedente_v2 = ancienne.get("type") == TYPE_FICHIER
    version = (ancienne.get("version", 1) + 1) if precedente_v2 else 2  # la V1 compte comme version 1
    nouveau = {
        # Forme V1 (lue par model.py) :
        "id_client": ancienne.get("id_client", id_client),
        "annee_balance": ancienne.get("annee_balance"),
        "balance": [{k: v for k, v in c.items() if k != "_ligne_excel"} for c in comptes],
        # Traçabilité V2 :
        "mission_id": mission_id,
        "type": TYPE_FICHIER,
        "actif": True,
        "version": version,
        "nom_fichier": getattr(fichier, "filename", None),
        "date_import": datetime.utcnow().isoformat(),
        "utilisateur_id": utilisateur_id,
        "remplace_balance_id": str(ancienne["_id"]),
        "mapping_utilise": resolu["mapping"],
        "format_detecte": resolu["apercu"].get("format_propose"),
        "controles_preliminaires": controles,
    }
    nouvel_id = str(db["Balance"].insert_one(nouveau).inserted_id)

    if precedente_v2:
        db["Balance"].update_one({"_id": ancienne["_id"]}, {"$set": {"actif": False}})
    # Même position que l'ancienne balance N : la V1 lit N en [0], N-1 en [1].
    db["Mission1"].update_one({"_id": mission["_id"]}, {"$set": {f"balances.{position}": nouvel_id}})

    verrou_ipe_service.invalider_si_fichier_remplace(mission_id, TYPE_FICHIER, nouvel_id)

    return {
        "_id": nouvel_id,
        "type": TYPE_FICHIER,
        "version": version,
        "nb_lignes": len(comptes),
        "nb_sous_totaux_ecartes": len(sous_totaux),
        "nb_lignes_sans_numero_ecartees": len(sans_numero),
        "format_detecte": nouveau["format_detecte"],
        "donnees_v1_derivees_recalculees": False,
    }
