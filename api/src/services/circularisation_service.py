"""
Circularisation, sous-lot a (docs/PLAN_circularisation.md) : population des
tiers, sélection MANUELLE avec motif, mode de confirmation, mémo de sélection
et son circuit de revue. Maquettes 2_Selection_tiers et 3_Memo_selection.

Les specs CAC-CIR-01, CAC-SEUILS-01 et ECH-01 ne sont pas dans le dépôt :
aucune règle de sélection automatique ici (sous-lot d). Choix provisoires
signalés par TODO(spec) / TODO(décision).

Collections : `CirSelection` (une version par (mission, type de tiers), la
population y est photographiée), `CirMemo` (versions figées du mémo),
`CirJournal` (toutes les actions, en ajout seul, lu par le Journal d'audit).
Rien n'est supprimé. Chaque document porte `mission_id`.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId

from src.utils.database import get_database
from src.services import fichiers_complementaires_service as fc_service
from src.services import rapprochement_ipe_service as rapprochement
from src.services import verrou_ipe_service
from src.services.revue_ipe_service import LIBELLES_FICHIERS

COLLECTION_SELECTION = "CirSelection"
COLLECTION_MEMO = "CirMemo"
COLLECTION_JOURNAL = "CirJournal"

MODULE_JOURNAL = "Sélection des tiers"
LONGUEUR_MIN_MOTIF = 15  # convention des commentaires du circuit IPE (CLAUDE.md)

# Types de tiers de la maquette 2_Selection_tiers. Seuls Clients et
# Fournisseurs ont une population (balances auxiliaires actives).
# TODO(spec: CAC-CIR-01) : liste définitive ; population des Avocats, des
# Bailleurs (saisie ? comptes de la balance générale ?) et des Banques (52x ?
# relevés ?).
TYPES_TIERS = (
    {"cle": "clients", "libelle": "Clients", "type_fichier": "auxiliaire_client", "module_ipe": "ipe_1_clients"},
    {"cle": "fournisseurs", "libelle": "Fournisseurs", "type_fichier": "auxiliaire_fournisseur",
     "module_ipe": "ipe_2_fournisseurs"},
    {"cle": "avocats", "libelle": "Avocats", "etiquette": "à saisir",
     "indisponible": "Population à saisir · source à confirmer par CAC-CIR-01"},
    {"cle": "bailleurs", "libelle": "Bailleurs", "etiquette": "à saisir",
     "indisponible": "Population à saisir · source à confirmer par CAC-CIR-01"},
    {"cle": "banques", "libelle": "Banques", "etiquette": "relevés",
     "indisponible": "Relevés bancaires · source à confirmer par CAC-CIR-01"},
)
_TYPES = {t["cle"]: t for t in TYPES_TIERS}

MODES = ("positif", "negatif")
STATUTS_MODIFIABLES = ("en_cours", "en_attente_correction")

# Libellés des seuils de l'étape 5, tels que l'écran V1 les affiche. La
# correspondance avec SS / SP / TS de la maquette n'est PAS établie.
# TODO(spec: CAC-SEUILS-01) : équivalence SS / SP / TS.
SEUILS_ETAPE_5 = (
    ("materiality", "Materiality Threshold"),
    ("performance_materiality", "Performance Materiality"),
    ("trivial_misstatements", "Clearly Trivial Threshold"),
)


def _maintenant() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db():
    return get_database()


def _type(type_tiers: str) -> Dict[str, Any]:
    if type_tiers not in _TYPES:
        raise ValueError(f"Type de tiers inconnu : {type_tiers}.")
    return _TYPES[type_tiers]


def _exiger_utilisateur(utilisateur_id: Optional[str], action: str) -> str:
    if not (utilisateur_id or "").strip():
        raise ValueError(f"{action} : utilisateur non identifié. Reconnectez-vous puis réessayez.")
    return utilisateur_id.strip()


def _exiger_motif(motif: Optional[str], quoi: str = "Le motif") -> str:
    motif = (motif or "").strip()
    if len(motif) < LONGUEUR_MIN_MOTIF:
        raise ValueError(f"{quoi} est obligatoire et doit contenir au moins {LONGUEUR_MIN_MOTIF} caractères.")
    return motif


def _journaliser(mission_id: str, utilisateur_id: Optional[str], action: str, detail: str, **reference) -> None:
    _db()[COLLECTION_JOURNAL].insert_one({
        "mission_id": mission_id,
        "horodatage": _maintenant(),
        "utilisateur_id": utilisateur_id,
        "module": MODULE_JOURNAL,
        "action": action,
        "detail": detail,
        "reference": reference,
    })


# --- Population (fonctions pures) ----------------------------------------------

def lignes_population(lignes_fichier: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Tiers d'une balance auxiliaire : numéro, libellé, solde (débit − crédit,
    même convention que le rapprochement IPE). Aucun tiers n'est écarté.
    TODO(spec: CAC-CIR-01) : soldes nuls, soldes de sens inverse.
    """
    cle = rapprochement._cle_identifiante(lignes_fichier)
    population = []
    for ligne in lignes_fichier:
        numero = str((ligne.get(cle) if cle else None) or "").strip()
        if not numero:
            continue
        solde = rapprochement._solde_ligne_auxiliaire(ligne)
        population.append({
            "numero": numero,
            "libelle": str(ligne.get("libelle_compte") or ligne.get("libelle") or "").strip(),
            "solde": solde if solde is not None else 0,
        })
    return population


def decisions_courantes(decisions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Dernière décision par tiers (l'historique complet reste dans `decisions`)."""
    courantes = {}
    for d in decisions or []:
        courantes[d["numero"]] = d
    return courantes


def indicateurs(population: List[Dict[str, Any]], decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Indicateurs de la maquette. Valeurs en valeur absolue des soldes —
    TODO(spec: CAC-CIR-01) : convention provisoire (soldes de sens inverse).
    """
    courantes = decisions_courantes(decisions)
    retenus = [t for t in population if courantes.get(t["numero"], {}).get("retenu")]
    valeur_population = sum(abs(t["solde"]) for t in population)
    valeur_couverte = sum(abs(t["solde"]) for t in retenus)
    return {
        "nb_tiers": len(population),
        "nb_retenus": len(retenus),
        "taux_selection": (len(retenus) / len(population) * 100) if population else None,
        "valeur_population": valeur_population,
        "valeur_couverte": valeur_couverte,
        "taux_couverture": (valeur_couverte / valeur_population * 100) if valeur_population else None,
        "solde_moyen_retenu": (valeur_couverte / len(retenus)) if retenus else None,
    }


def tiers_affiches(population: List[Dict[str, Any]], decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Lignes du tableau : tiers + décision courante (origine « Ajout manuel » / « Exclusion manuelle »)."""
    courantes = decisions_courantes(decisions)
    lignes = []
    for t in population:
        d = courantes.get(t["numero"])
        lignes.append({
            **t,
            "retenu": bool(d and d["retenu"]),
            "origine": None if not d else ("ajout_manuel" if d["retenu"] else "exclusion_manuelle"),
            "motif": d["motif"] if d else None,
            "utilisateur_id": d["utilisateur_id"] if d else None,
            "horodatage": d["horodatage"] if d else None,
        })
    return lignes


# --- Lectures --------------------------------------------------------------------

def _mission(mission_id: str) -> Dict[str, Any]:
    try:
        oid = ObjectId(mission_id)
    except (InvalidId, TypeError):
        raise ValueError("Identifiant de mission invalide.")
    mission = _db()["Mission1"].find_one({"_id": oid}, {"id_client": 1, "annee_auditee": 1, "materiality": 1})
    if not mission:
        raise ValueError("Mission introuvable.")
    return mission


def seuils_etape_5(mission: Dict[str, Any]) -> Dict[str, Any]:
    """Seuils du benchmark retenu à l'étape 5 (Mission1.materiality, choice). Lecture seule, rien n'est recalculé."""
    retenu = next((m for m in mission.get("materiality") or [] if m.get("choice") is True), None)
    return {
        "disponible": retenu is not None,
        "benchmark": retenu.get("benchmark") if retenu else None,
        "valeurs": [{"cle": cle, "libelle": libelle, "valeur": retenu.get(cle) if retenu else None}
                    for cle, libelle in SEUILS_ETAPE_5],
        "correspondance": "Correspondance avec SS / SP / TS à confirmer par CAC-SEUILS-01",
    }


def _etat_ipe(mission_id: str) -> Dict[str, Any]:
    etat = verrou_ipe_service.lire_etat_ipe(mission_id)
    return {
        "statut_affiche": verrou_ipe_service.statut_affiche(etat),
        "ipe_fiabilite_validee": etat.get("ipe_fiabilite_validee"),
        "statut_circuit": etat.get("statut_circuit"),
        "modules": {m: (etat.get("modules") or {}).get(m, {}).get("statut") for m in ("ipe_1_clients", "ipe_2_fournisseurs")},
    }


def _fichier_actif(mission_id: str, type_fichier: str) -> Optional[Dict[str, Any]]:
    actifs = fc_service.lister_fichiers_complementaires(mission_id).get(type_fichier) or []
    return actifs[0] if actifs else None


def _selection_active(mission_id: str, type_tiers: str) -> Optional[Dict[str, Any]]:
    return _db()[COLLECTION_SELECTION].find_one({"mission_id": mission_id, "type_tiers": type_tiers, "actif": True})


def raison_a_refaire(selection: Dict[str, Any], fichier_actif: Optional[Dict[str, Any]]) -> Optional[str]:
    """Fichier source remplacé ou retiré depuis la photographie de la population : sélection à refaire."""
    source = selection["population"]["source"]
    if not fichier_actif:
        return f"Le fichier « {source['nom_fichier']} » a été retiré depuis la constitution de la population."
    if str(fichier_actif.get("_id")) != source["fichier_id"]:
        return (f"Le fichier « {source['nom_fichier']} » a été remplacé depuis la constitution de la population "
                f"(version {fichier_actif.get('version')} active) : constituez à nouveau la population.")
    return None


def _memo_courant(selection_id: str) -> Optional[Dict[str, Any]]:
    return _db()[COLLECTION_MEMO].find_one({"selection_id": selection_id}, sort=[("version", -1)])


def _serialiser(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if doc is None:
        return None
    return {**doc, "_id": str(doc["_id"])}


def etat_type(mission_id: str, type_tiers: str) -> Dict[str, Any]:
    config = _type(type_tiers)
    etat = {"cle": config["cle"], "libelle": config["libelle"], "indisponible": config.get("indisponible"),
            "etiquette": config.get("etiquette")}
    if config.get("indisponible"):
        return etat
    fichier = _fichier_actif(mission_id, config["type_fichier"])
    etat["fichier_actif"] = None if not fichier else {
        "_id": str(fichier.get("_id")), "nom_fichier": fichier.get("nom_fichier"),
        "version": fichier.get("version"), "nb_lignes": fichier.get("nb_lignes"),
    }
    selection = _selection_active(mission_id, type_tiers)
    if selection:
        population = selection["population"]["lignes"]
        etat["selection"] = {
            **{k: v for k, v in _serialiser(selection).items() if k not in ("population", "decisions")},
            "population": {k: v for k, v in selection["population"].items() if k != "lignes"},
            "tiers": tiers_affiches(population, selection["decisions"]),
            "indicateurs": indicateurs(population, selection["decisions"]),
            "a_refaire": raison_a_refaire(selection, fichier),
            "memo": _serialiser(_memo_courant(str(selection["_id"]))),
        }
    else:
        etat["selection"] = None
    return etat


def lire_circularisation(mission_id: str) -> Dict[str, Any]:
    """État de la sélection pour les cinq types de tiers, seuils de l'étape 5, état IPE."""
    mission = _mission(mission_id)
    return {
        "mission": _entite_et_exercice(mission),
        "seuils": seuils_etape_5(mission),
        "ipe": _etat_ipe(mission_id),
        "types": [etat_type(mission_id, t["cle"]) for t in TYPES_TIERS],
        "longueur_min_motif": LONGUEUR_MIN_MOTIF,
    }


# --- Actions ---------------------------------------------------------------------

def _selection_modifiable(mission_id: str, type_tiers: str) -> Dict[str, Any]:
    selection = _selection_active(mission_id, type_tiers)
    if not selection:
        raise ValueError("Constituez d'abord la population.")
    if selection["statut"] not in STATUTS_MODIFIABLES:
        raise ValueError("Sélection figée : le mémo a été soumis pour revue ou validé.")
    return selection


def constituer_population(mission_id: str, type_tiers: str, utilisateur_id: Optional[str]) -> Dict[str, Any]:
    """
    Photographie la population depuis le fichier actif et ouvre une nouvelle
    version de sélection (la précédente est archivée, jamais supprimée). L'état
    de la fiabilité IPE est enregistré avec la population.
    TODO(décision) : sélection permise avant la validation de la fiabilité IPE
    (bandeau + trace) ; blocage par le verrou non décidé.
    """
    _mission(mission_id)
    config = _type(type_tiers)
    if config.get("indisponible"):
        raise ValueError(f"{config['libelle']} : {config['indisponible']}.")
    utilisateur_id = _exiger_utilisateur(utilisateur_id, "Constitution de la population")
    precedente = _selection_active(mission_id, type_tiers)
    if precedente and precedente["statut"] == "soumis_pour_revue":
        raise ValueError("Le mémo est soumis pour revue : attendez la validation ou une demande de correction.")
    fichier = _fichier_actif(mission_id, config["type_fichier"])
    if not fichier:
        raise ValueError(f"Aucune {LIBELLES_FICHIERS[config['type_fichier']]} active : "
                         "importez-la dans Fichiers complémentaires.")
    doc_fichier = _db()["Balance"].find_one({"_id": ObjectId(str(fichier["_id"])), "mission_id": mission_id})
    population = lignes_population(doc_fichier.get("balance") or [])

    db = _db()
    version = 1
    if precedente:
        version = precedente["version"] + 1
        db[COLLECTION_SELECTION].update_one({"_id": precedente["_id"]}, {"$set": {"actif": False}})
    horodatage = _maintenant()
    selection = {
        "mission_id": mission_id,
        "type_tiers": type_tiers,
        "version": version,
        "actif": True,
        "cree_le": horodatage,
        "cree_par": utilisateur_id,
        "methode": "manuelle",
        "population": {
            "source": {"fichier_id": str(doc_fichier["_id"]), "type_fichier": config["type_fichier"],
                       "nom_fichier": doc_fichier.get("nom_fichier"), "version": doc_fichier.get("version"),
                       "date_import": doc_fichier.get("date_import")},
            "ipe": _etat_ipe(mission_id),
            "lignes": population,
        },
        "mode": {"valeur": "positif", "motif": None, "utilisateur_id": None, "horodatage": None},
        "decisions": [],
        "statut": "en_cours",
    }
    selection_id = str(db[COLLECTION_SELECTION].insert_one(selection).inserted_id)
    _journaliser(mission_id, utilisateur_id, "Population constituée",
                 f"{config['libelle']} · {doc_fichier.get('nom_fichier')} · v{doc_fichier.get('version')} · "
                 f"{len(population)} tiers · sélection version {version}",
                 type_tiers=type_tiers, selection_id=selection_id)
    return etat_type(mission_id, type_tiers)


def decider_tiers(mission_id: str, type_tiers: str, numero: str, retenu: bool,
                  motif: Optional[str], utilisateur_id: Optional[str]) -> Dict[str, Any]:
    """Retenir ou exclure un tiers : motif obligatoire, auteur identifié, décision ajoutée à l'historique."""
    config = _type(type_tiers)
    utilisateur_id = _exiger_utilisateur(utilisateur_id, "Décision sur un tiers")
    motif = _exiger_motif(motif)
    selection = _selection_modifiable(mission_id, type_tiers)
    tiers = next((t for t in selection["population"]["lignes"] if t["numero"] == numero), None)
    if not tiers:
        raise ValueError(f"Tiers {numero} absent de la population.")
    courante = decisions_courantes(selection["decisions"]).get(numero)
    if bool(courante and courante["retenu"]) == bool(retenu):
        raise ValueError(f"Le tiers {numero} est déjà {'retenu' if retenu else 'non retenu'}.")
    decision = {"numero": numero, "retenu": bool(retenu), "motif": motif,
                "utilisateur_id": utilisateur_id, "horodatage": _maintenant()}
    _db()[COLLECTION_SELECTION].update_one({"_id": selection["_id"]}, {"$push": {"decisions": decision}})
    _journaliser(mission_id, utilisateur_id, "Tiers retenu" if retenu else "Tiers exclu",
                 f"{config['libelle']} · {numero} · {tiers['libelle']} · « {motif} »",
                 type_tiers=type_tiers, selection_id=str(selection["_id"]))
    return etat_type(mission_id, type_tiers)


def definir_mode(mission_id: str, type_tiers: str, mode: str, motif: Optional[str],
                 utilisateur_id: Optional[str]) -> Dict[str, Any]:
    """
    Mode de confirmation : positif par défaut ; négatif avec motif obligatoire.
    TODO(décision) : « décision du Manager » (maquette) enregistrée sans
    contrôle de rôle, faute d'authentification. TODO(spec: CAC-CIR-01) :
    conditions d'emploi de la confirmation négative.
    """
    config = _type(type_tiers)
    if mode not in MODES:
        raise ValueError("Mode de confirmation inconnu.")
    utilisateur_id = _exiger_utilisateur(utilisateur_id, "Mode de confirmation")
    motif = _exiger_motif(motif, "Le motif de la confirmation négative") if mode == "negatif" else None
    selection = _selection_modifiable(mission_id, type_tiers)
    if selection["mode"]["valeur"] == mode:
        raise ValueError(f"Le mode est déjà « {mode} ».")
    nouveau = {"valeur": mode, "motif": motif, "utilisateur_id": utilisateur_id, "horodatage": _maintenant()}
    _db()[COLLECTION_SELECTION].update_one({"_id": selection["_id"]}, {"$set": {"mode": nouveau}})
    _journaliser(mission_id, utilisateur_id, "Mode de confirmation modifié",
                 f"{config['libelle']} · {'négatif' if mode == 'negatif' else 'positif'}"
                 + (f" · « {motif} »" if motif else ""),
                 type_tiers=type_tiers, selection_id=str(selection["_id"]))
    return etat_type(mission_id, type_tiers)


# --- Mémo de sélection -----------------------------------------------------------

def _entite_et_exercice(mission: Dict[str, Any]) -> Dict[str, Any]:
    client = None
    try:
        client = _db()["Client_db"].find_one({"_id": ObjectId(str(mission.get("id_client")))}, {"company_name": 1})
    except (InvalidId, TypeError):
        pass
    annee = mission.get("annee_auditee")
    if isinstance(annee, list):
        annee = annee[0] if annee else None
    return {"entite": (client or {}).get("company_name"), "exercice": annee}


def contenu_memo(mission: Dict[str, Any], selection: Dict[str, Any]) -> Dict[str, Any]:
    """Contenu du mémo (maquette 3_Memo_selection), calculé sur la sélection : figé à la soumission."""
    config = _type(selection["type_tiers"])
    population = selection["population"]["lignes"]
    par_numero = {t["numero"]: t for t in population}
    return {
        **_entite_et_exercice(mission),
        "type_tiers": config["libelle"],
        "selection_version": selection["version"],
        "norme": "ISA 505, confirmations externes",
        "mode": selection["mode"],
        "population": {**selection["population"]["source"], "nb_tiers": len(population),
                       "libelle_fichier": LIBELLES_FICHIERS.get(selection["population"]["source"]["type_fichier"])},
        "ipe": selection["population"]["ipe"],
        "methode": "Sélection manuelle",  # sous-lot d : seuils et MUS
        "resultat": indicateurs(population, selection["decisions"]),
        "decisions": [
            {**d, "libelle": par_numero.get(d["numero"], {}).get("libelle")} for d in selection["decisions"]
        ],
    }


def lire_memo(mission_id: str, type_tiers: str) -> Dict[str, Any]:
    """Aperçu : contenu figé du mémo soumis, sinon contenu courant (brouillon)."""
    _type(type_tiers)
    mission = _mission(mission_id)
    selection = _selection_active(mission_id, type_tiers)
    if not selection:
        raise ValueError("Constituez d'abord la population.")
    memo = _memo_courant(str(selection["_id"]))
    if memo and memo["statut"] in ("soumis", "valide"):
        return {"statut": memo["statut"], "memo": _serialiser(memo), "contenu": memo["contenu"]}
    return {"statut": "brouillon", "memo": _serialiser(memo), "contenu": contenu_memo(mission, selection)}


def soumettre_memo(mission_id: str, type_tiers: str, utilisateur_id: Optional[str]) -> Dict[str, Any]:
    """Fige le mémo (nouvelle version) et la sélection. Refusé si le fichier source a changé depuis."""
    config = _type(type_tiers)
    utilisateur_id = _exiger_utilisateur(utilisateur_id, "Soumission du mémo")
    mission = _mission(mission_id)
    selection = _selection_modifiable(mission_id, type_tiers)
    raison = raison_a_refaire(selection, _fichier_actif(mission_id, config["type_fichier"]))
    if raison:
        raise ValueError(raison)
    precedent = _memo_courant(str(selection["_id"]))
    version = (precedent["version"] + 1) if precedent else 1
    horodatage = _maintenant()
    db = _db()
    db[COLLECTION_MEMO].insert_one({
        "mission_id": mission_id,
        "selection_id": str(selection["_id"]),
        "type_tiers": type_tiers,
        "version": version,
        "statut": "soumis",
        "contenu": contenu_memo(mission, selection),
        "soumis_par": utilisateur_id,
        "soumis_le": horodatage,
        "decision": None,
    })
    db[COLLECTION_SELECTION].update_one({"_id": selection["_id"]}, {"$set": {"statut": "soumis_pour_revue"}})
    _journaliser(mission_id, utilisateur_id, "Mémo soumis pour revue",
                 f"{config['libelle']} · mémo version {version}", type_tiers=type_tiers,
                 selection_id=str(selection["_id"]))
    return etat_type(mission_id, type_tiers)


def _decider_memo(mission_id: str, type_tiers: str, valide: bool, commentaire: Optional[str],
                  utilisateur_id: Optional[str]) -> Dict[str, Any]:
    """
    Validation ou demande de correction du mémo soumis.
    TODO(décision) : qui peut valider (Manager) — pas de contrôle de rôle,
    faute d'authentification ; utilisateur identifié exigé.
    """
    config = _type(type_tiers)
    action = "Validation du mémo" if valide else "Demande de correction du mémo"
    utilisateur_id = _exiger_utilisateur(utilisateur_id, action)
    commentaire = _exiger_motif(commentaire, "Le commentaire")
    selection = _selection_active(mission_id, type_tiers)
    memo = _memo_courant(str(selection["_id"])) if selection else None
    if not memo or memo["statut"] != "soumis":
        raise ValueError(f"{action} impossible : aucun mémo soumis pour revue.")
    horodatage = _maintenant()
    db = _db()
    db[COLLECTION_MEMO].update_one({"_id": memo["_id"]}, {"$set": {
        "statut": "valide" if valide else "correction_demandee",
        "decision": {"valide": valide, "utilisateur_id": utilisateur_id, "horodatage": horodatage,
                     "commentaire": commentaire},
    }})
    db[COLLECTION_SELECTION].update_one({"_id": selection["_id"]},
                                        {"$set": {"statut": "valide" if valide else "en_attente_correction"}})
    _journaliser(mission_id, utilisateur_id, "Mémo validé" if valide else "Correction du mémo demandée",
                 f"{config['libelle']} · mémo version {memo['version']} · « {commentaire} »",
                 type_tiers=type_tiers, selection_id=str(selection["_id"]))
    return etat_type(mission_id, type_tiers)


def valider_memo(mission_id, type_tiers, commentaire, utilisateur_id):
    return _decider_memo(mission_id, type_tiers, True, commentaire, utilisateur_id)


def demander_correction_memo(mission_id, type_tiers, commentaire, utilisateur_id):
    return _decider_memo(mission_id, type_tiers, False, commentaire, utilisateur_id)
