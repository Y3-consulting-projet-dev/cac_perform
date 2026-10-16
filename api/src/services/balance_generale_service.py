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
import hashlib
import json
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

# Paires comparées (forme V1) : (libellé, champ débit, champ crédit).
PAIRES = [
    ("ouverture", "debit_initial", "credit_initial"),
    ("mouvements", "debit_mvt", "credit_mvt"),
    ("solde_final", "debit_fin", "credit_fin"),
]
CHAMPS_MONTANTS = [champ for _, d, c in PAIRES for champ in (d, c)]
TOLERANCE = 0.01  # arrondi Excel, même seuil que controler_bouclage_total
DECISIONS_POSSIBLES = ("ecarter", "garder")


# --------------------------------------------------------------------------
# Fonctions pures
# --------------------------------------------------------------------------

def _paire_correspond(ligne: Dict[str, Any], enfants: List[Dict[str, Any]], champ_d: str, champ_c: str) -> bool:
    """Brut (débit = somme des débits ET crédit = somme des crédits) OU net (débit − crédit = somme des nets)."""
    d, c = ligne.get(champ_d) or 0, ligne.get(champ_c) or 0
    somme_d = sum((e.get(champ_d) or 0) for e in enfants)
    somme_c = sum((e.get(champ_c) or 0) for e in enfants)
    brut = abs(d - somme_d) <= TOLERANCE and abs(c - somme_c) <= TOLERANCE
    net = abs((d - c) - (somme_d - somme_c)) <= TOLERANCE
    return brut or net


def _ecarts(ligne: Dict[str, Any], enfants: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Par paire : montants de la ligne, somme de ses comptes, écart net — pour l'alerte à l'auditeur."""
    resultat = {}
    for paire, champ_d, champ_c in PAIRES:
        d, c = ligne.get(champ_d) or 0, ligne.get(champ_c) or 0
        somme_d = sum((e.get(champ_d) or 0) for e in enfants)
        somme_c = sum((e.get(champ_c) or 0) for e in enfants)
        resultat[paire] = {
            "ligne_debit": d, "ligne_credit": c,
            "somme_debit": somme_d, "somme_credit": somme_c,
            "ecart_net": (d - c) - (somme_d - somme_c),
            "correspond": _paire_correspond(ligne, enfants, champ_d, champ_c),
        }
    return resultat


def detecter_sous_totaux(
    lignes: List[Dict[str, Any]],
    decisions: Optional[Dict[str, str]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Sépare les comptes des lignes de sous-total (forme V1). Fonction pure.

    Règle validée : une ligne est un sous-total si son numéro est le préfixe
    d'au moins un autre compte du fichier ET si, pour chacune des trois
    paires (ouverture, mouvements, solde final), ses montants égalent la
    somme de ces comptes, en brut ou en net (débit − crédit). Le libellé
    n'est jamais lu. Numéros les plus longs d'abord : un sous-total imbriqué
    (« 284 ») est traité avant son parent (« 28 »), qui n'est comparé
    qu'aux comptes restants — jamais de double comptage.

    Ligne « ambiguë » : numéro préfixe d'autres comptes, mais montants qui ne
    correspondent pas. Ni gardée ni écartée en silence : l'auditeur décide
    (`decisions` = {numero_compte: "ecarter" | "garder"}). Sans décision,
    elle est gardée PROVISOIREMENT pour évaluer ses parents (elle reste
    signalée, et l'import refuse de l'enregistrer sans décision).

    Renvoie (comptes, sous_totaux, ambigus).
    """
    decisions = decisions or {}

    def numero(ligne):
        return str(ligne.get("numero_compte") or "").strip()

    ordre = sorted(range(len(lignes)), key=lambda i: -len(numero(lignes[i])))
    ecartes: Dict[int, Dict[str, Any]] = {}
    ambigus: List[Dict[str, Any]] = []
    for i in ordre:
        n = numero(lignes[i])
        if not n:
            continue
        enfants = [
            lignes[j] for j in range(len(lignes))
            if j != i and j not in ecartes
            and len(numero(lignes[j])) > len(n) and numero(lignes[j]).startswith(n)
        ]
        if not enfants:
            continue
        if all(_paire_correspond(lignes[i], enfants, d, c) for _, d, c in PAIRES):
            ecartes[i] = {"nb_comptes_detail": len(enfants), "motif": "sous_total"}
            continue
        decision = decisions.get(n)
        ambigus.append({
            "ligne_excel": lignes[i].get("_ligne_excel"),
            "numero_compte": n,
            "libelle": lignes[i].get("libelle"),
            "nb_comptes_detail": len(enfants),
            "ecarts": _ecarts(lignes[i], enfants),
            "decision": decision if decision in DECISIONS_POSSIBLES else None,
        })
        if decision == "ecarter":
            ecartes[i] = {"nb_comptes_detail": len(enfants), "motif": "sous_total_ecarte_par_l_auditeur"}

    comptes = [l for i, l in enumerate(lignes) if i not in ecartes]
    sous_totaux = [{**lignes[i], **ecartes[i]} for i in sorted(ecartes)]
    ambigus.sort(key=lambda a: (a["ligne_excel"] is None, a["ligne_excel"] or 0, a["numero_compte"]))
    return comptes, sous_totaux, ambigus


def controler_equilibre(comptes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Après retrait des sous-totaux : total débit = total crédit, pour chaque paire. Fonction pure."""
    paires = {}
    for paire, champ_d, champ_c in PAIRES:
        total_d = sum((l.get(champ_d) or 0) for l in comptes)
        total_c = sum((l.get(champ_c) or 0) for l in comptes)
        paires[paire] = {"total_debit": total_d, "total_credit": total_c, "ecart": total_d - total_c,
                         "ok": abs(total_d - total_c) <= TOLERANCE}
    return {"ok": all(p["ok"] for p in paires.values()), "paires": paires}


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


def id_client_de_la_mission(mission_id: str) -> str:
    return str(_mission(mission_id).get("id_client"))


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
    remplacements = get_database()["Mission1"].find_one(
        {"_id": mission["_id"]}, {"balance_generale_remplacements": 1},
    ).get("balance_generale_remplacements") or []
    return {
        "active": resume_balance(actuelle, actif=True),
        "historique": historique,
        "remplacements": [{k: v for k, v in r.items() if k != "empreintes"} for r in remplacements],
    }


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


def analyser_fichier(
    fichier,
    id_client: str,
    logiciel_comptable: Optional[str] = None,
    mapping: Optional[Dict[str, str]] = None,
    decisions: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Lit et contrôle le fichier SANS RIEN ÉCRIRE : sert à la vérification
    avant enregistrement (lignes ambiguës, équilibre) et à l'import.
    """
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

    comptes, sous_totaux, ambigus = detecter_sous_totaux(avec_numero, decisions)

    lignes_ecartees = sans_numero + [
        {"ligne_excel": s.get("_ligne_excel"), "motif": s["motif"],
         "contenu": {k: v for k, v in s.items() if k not in ("_ligne_excel", "motif")}}
        for s in sous_totaux
    ]
    controles = {
        "integrite": integrite,
        "doublons": cp_service.controler_doublons(comptes, cle="numero_compte"),
        "lignes_ecartees": {"nb": len(lignes_ecartees), "lignes": lignes_ecartees},
        "sous_totaux": {
            "nb": len(sous_totaux),
            "lignes": [{"ligne_excel": s.get("_ligne_excel"), "numero_compte": s["numero_compte"], "libelle": s["libelle"],
                        "nb_comptes_detail": s["nb_comptes_detail"], "motif": s["motif"]} for s in sous_totaux],
        },
        "sous_totaux_ambigus": {"nb": len(ambigus), "lignes": ambigus},
        "equilibre": controler_equilibre(comptes),
        "bouclage_total": cp_service.controler_bouclage_total(comptes, sans_numero, "numero_compte"),
        "bouclage_ligne": cp_service.controler_bouclage_ligne([_vers_noms_bouclage(c) for c in comptes]),
    }
    return {"comptes": comptes, "sous_totaux": sous_totaux, "sans_numero": sans_numero,
            "ambigus": ambigus, "controles": controles, "resolu": resolu}


def resume_analyse(analyse: Dict[str, Any]) -> Dict[str, Any]:
    """Ce que la vérification renvoie à l'écran (sans les lignes)."""
    return {
        "nb_comptes": len(analyse["comptes"]),
        "sous_totaux": analyse["controles"]["sous_totaux"],
        "sous_totaux_ambigus": analyse["controles"]["sous_totaux_ambigus"],
        "equilibre": analyse["controles"]["equilibre"],
        "format_detecte": analyse["resolu"]["apercu"].get("format_propose"),
    }


# Données que la V1 calcule à partir des balances et enregistre dans
# Mission1 (relevé dans api/src/model.py, dernière définition de chaque
# méthode) :
# - balance_variation : calculée à la création, RECALCULÉE et enregistrée par
#   l'étape 9 (make_final_sm), qui régénère et enregistre aussi grouping ;
# - grouping : calculé à la création, régénéré par l'étape 9 uniquement
#   (les étapes 6/7 l'enregistrent sans recalculer ses montants) ;
# - efi : calculé à la création, jamais recalculé ni réenregistré ensuite.
DONNEES_V1_DERIVEES = ("balance_variation", "grouping", "efi")

# Étape (clé de GroupingAnalyse.vue) -> données enregistrées qu'elle utilise.
# Les étapes 3 (cohérence), 4 (intangibilité) et le classement du bilan
# relisent les balances elles-mêmes, et l'étape 9 recalcule : toujours à jour.
DONNEES_PAR_ETAPE = {
    "materialite": ("efi",),
    "quantitatif": ("grouping",),
    "qualitatif": ("grouping",),
    "presentation": ("grouping",),
    "efi": ("balance_variation",),
    "revue": ("balance_variation", "efi", "grouping"),
}
# Ce qui rend une donnée de nouveau à jour : grouping est régénéré en même
# temps que balance_variation (étape 9), donc suit son empreinte.
EMPREINTE_DE_REFERENCE = {"balance_variation": "balance_variation", "grouping": "balance_variation", "efi": "efi"}


def _empreinte(valeur: Any) -> str:
    return hashlib.sha256(json.dumps(valeur, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def fraicheur_par_etape(mission: Dict[str, Any]) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Fonction pure. Pour chaque étape V1 qui utilise des données enregistrées
    dans la mission : None si ces données sont à jour, sinon la version de
    la balance générale sur laquelle elles ont été calculées et la date de
    son remplacement.

    Principe : à chaque remplacement, l'empreinte de chaque donnée dérivée
    est relevée. Si l'empreinte actuelle a changé depuis le dernier
    remplacement, la V1 l'a recalculée depuis (à partir des balances) : elle
    est à jour. Sinon elle date d'avant le remplacement le plus ancien dont
    l'empreinte est identique à l'actuelle (aucun recalcul depuis).
    TODO(décision) : recalcul des données V1 après remplacement.
    """
    remplacements = mission.get("balance_generale_remplacements") or []
    resultat: Dict[str, Optional[Dict[str, Any]]] = {}
    for etape, donnees in DONNEES_PAR_ETAPE.items():
        perimee = None
        for donnee in donnees:
            reference = EMPREINTE_DE_REFERENCE[donnee]
            actuelle = _empreinte(mission.get(reference))
            if not remplacements or remplacements[-1]["empreintes"].get(reference) != actuelle:
                continue  # aucun remplacement, ou recalculée depuis le dernier
            premier = next(r for r in remplacements if r["empreintes"].get(reference) == actuelle)
            candidat = {"version": premier["version_remplacee"], "remplacee_le": premier["horodatage"]}
            if perimee is None or candidat["version"] < perimee["version"]:
                perimee = candidat
        resultat[etape] = perimee
    return resultat


def lire_fraicheur(mission_id: str) -> Dict[str, Optional[Dict[str, Any]]]:
    try:
        object_id = ObjectId(mission_id)
    except InvalidId:
        raise ValueError(f"mission_id invalide : '{mission_id}'")
    projection = {"balance_generale_remplacements": 1, **{d: 1 for d in DONNEES_V1_DERIVEES}}
    mission = get_database()["Mission1"].find_one({"_id": object_id}, projection)
    if not mission:
        raise ValueError("Mission non trouvée")
    return fraicheur_par_etape(mission)


def importer_balance_generale(
    fichier,
    mission_id: str,
    utilisateur_id: Optional[str] = None,
    logiciel_comptable: Optional[str] = None,
    mapping: Optional[Dict[str, str]] = None,
    decisions: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Remplace la balance générale N de la mission. Ne supprime rien :
    l'ancien document reste en base, référencé par `remplace_balance_id`
    (et archivé `actif=False` s'il venait déjà de cet import V2).

    Refuse d'enregistrer tant qu'une ligne ambiguë (forme de sous-total,
    montants qui ne correspondent pas) n'a pas reçu de décision.
    """
    mission = _mission(mission_id)
    position, ancienne = _position_balance_n(mission)
    id_client = str(mission.get("id_client"))

    analyse = analyser_fichier(fichier, id_client, logiciel_comptable, mapping, decisions)
    sans_decision = [a["numero_compte"] for a in analyse["ambigus"] if not a["decision"]]
    if sans_decision:
        raise ValueError(
            "Décision requise (« Écarter » ou « Garder ») pour les lignes qui ont la forme d'un sous-total "
            f"sans correspondre à leurs comptes : {', '.join(sans_decision)}."
        )

    horodatage = datetime.utcnow().isoformat()
    # Traçabilité des choix de l'auditeur sur les lignes ambiguës.
    for ligne in analyse["controles"]["sous_totaux_ambigus"]["lignes"]:
        ligne["utilisateur_id"] = utilisateur_id
        ligne["horodatage"] = horodatage

    comptes = analyse["comptes"]
    db = get_database()
    precedente_v2 = ancienne.get("type") == TYPE_FICHIER
    version_remplacee = ancienne.get("version", 1) if precedente_v2 else 1  # l'import V1 compte comme version 1
    version = version_remplacee + 1
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
        "date_import": horodatage,
        "utilisateur_id": utilisateur_id,
        "remplace_balance_id": str(ancienne["_id"]),
        "mapping_utilise": analyse["resolu"]["mapping"],
        "format_detecte": analyse["resolu"]["apercu"].get("format_propose"),
        "controles_preliminaires": analyse["controles"],
    }
    nouvel_id = str(db["Balance"].insert_one(nouveau).inserted_id)

    if precedente_v2:
        db["Balance"].update_one({"_id": ancienne["_id"]}, {"$set": {"actif": False}})

    mission_complete = db["Mission1"].find_one({"_id": mission["_id"]}, {d: 1 for d in DONNEES_V1_DERIVEES})
    historique = {
        "horodatage": horodatage,
        "utilisateur_id": utilisateur_id,
        "version_remplacee": version_remplacee,
        "nouvelle_version": version,
        "ancienne_balance_id": str(ancienne["_id"]),
        "nouvelle_balance_id": nouvel_id,
        "nom_fichier": nouveau["nom_fichier"],
        "decisions_sous_totaux": [
            {"numero_compte": a["numero_compte"], "libelle": a["libelle"], "decision": a["decision"]}
            for a in analyse["ambigus"]
        ],
        # Empreintes des données V1 dérivées au moment du remplacement :
        # voir fraicheur_par_etape.
        "empreintes": {d: _empreinte(mission_complete.get(d)) for d in DONNEES_V1_DERIVEES},
    }
    # Même position que l'ancienne balance N : la V1 lit N en [0], N-1 en [1].
    db["Mission1"].update_one(
        {"_id": mission["_id"]},
        {"$set": {f"balances.{position}": nouvel_id}, "$push": {"balance_generale_remplacements": historique}},
    )

    verrou_ipe_service.invalider_si_fichier_remplace(mission_id, TYPE_FICHIER, nouvel_id)

    return {
        "_id": nouvel_id,
        "type": TYPE_FICHIER,
        "version": version,
        "nb_lignes": len(comptes),
        "nb_sous_totaux_ecartes": len(analyse["sous_totaux"]),
        "nb_lignes_sans_numero_ecartees": len(analyse["sans_numero"]),
        "equilibre": analyse["controles"]["equilibre"],
        "format_detecte": nouveau["format_detecte"],
        "donnees_v1_derivees_recalculees": False,
    }


def _fcfa(montant: float) -> str:
    return f"{montant:,.0f}".replace(",", " ")


LIBELLES_PAIRES = {"ouverture": "ouverture", "mouvements": "mouvements", "solde_final": "solde final"}


def alertes_analyse(analyse: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Alertes affichées avant l'enregistrement : lignes ambiguës sans décision, balance déséquilibrée."""
    alertes = []
    for ligne in analyse["ambigus"]:
        if ligne["decision"]:
            continue
        ecarts = "; ".join(
            f"{LIBELLES_PAIRES[paire]} : écart net {_fcfa(e['ecart_net'])}"
            for paire, e in ligne["ecarts"].items() if not e["correspond"]
        )
        alertes.append({
            "code": "sous_total_ambigu",
            "numero_compte": ligne["numero_compte"],
            "message": (
                f"La ligne {ligne['numero_compte']} « {ligne['libelle'] or 'sans libellé'} » a la forme d'un sous-total "
                f"({ligne['nb_comptes_detail']} comptes dessous) mais ne correspond pas à leur somme ({ecarts}). "
                "Choisissez « Écarter » (c'est un sous-total) ou « Garder » (c'est un compte)."
            ),
        })
    equilibre = analyse["controles"]["equilibre"]
    if not equilibre["ok"]:
        detail = "; ".join(
            f"{LIBELLES_PAIRES[paire]} : débit {_fcfa(p['total_debit'])}, crédit {_fcfa(p['total_credit'])}, écart {_fcfa(p['ecart'])}"
            for paire, p in equilibre["paires"].items() if not p["ok"]
        )
        alertes.append({
            "code": "desequilibre",
            "message": f"La balance n'est pas équilibrée après retrait des sous-totaux ({detail}). Vérifiez que l'export est complet.",
        })
    return alertes
