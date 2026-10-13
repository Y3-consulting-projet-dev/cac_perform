"""
Verrou IPE (Module 1, CAC-IPE-01) — mécanisme de blocage IPE-GLOBAL-01.
Nouveau périmètre V2 — voir docs/PLAN_verrou_IPE.md.

Ne modifie ni api/src/model.py ni api/src/mission/routes.py : le blocage est
un hook Blueprint.before_request enregistré depuis api/src/routes/__init__.py
(le seul point d'enregistrement touché, conformément à CLAUDE.md).

⚠️ IPE_VERROU_ACTIF reste à "false" par défaut (voir env.template) : tant
qu'il n'est pas activé, verifier_verrou_ipe() est un no-op total — aucune
régression sur les 9 étapes existantes. Ne jamais l'activer en production
avant que les droits (qui valide ?) et CAC-IPE-01 (rattachement, tolérance,
orphelins, conditions de TRUE) soient intégrés (voir CLAUDE.md).
"""
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from flask import jsonify, make_response, request

from src.utils.database import get_database
from src.services import fichiers_complementaires_service as fc_service

COLLECTION_MISSION = "Mission1"

# Décision métier à confirmer (docs/PLAN_verrou_IPE.md §3) : liste des
# endpoints Flask du blueprint "mission" concernés par IPE-GLOBAL-01, déduite
# du séquencement de CLAUDE.md ("après ouverture des cycles"), pas une règle
# actée par CAC-IPE-01. Unique paramètre à modifier ici — jamais de condition
# dispersée ailleurs dans le code.
ENDPOINTS_VERROUILLABLES = {
    # matérialité (étape 5)
    "mission.materialite_route", "mission.get_benchmarks", "mission.save_materiality",
    "mission.validate_materiality", "mission.get_materiality",
    # analyse quantitative (étape 6)
    "mission.analyse_quantitative_route", "mission.save_quantitative_threshold_mode",
    "mission.save_quantitative_threshold_mode_alias", "mission.make_quantitative_analysis",
    "mission.download_analyse_quantitative",
    # analyse qualitative (étape 7)
    "mission.analyse_qualitative_route", "mission.init_qualitative_responses_route",
    "mission.save_qualitative_responses_route", "mission.make_qualitative_analysis",
    "mission.download_analyse_qualitative",
    # décision finale des comptes à tester (étape 8)
    "mission.presentation_comptes_significatifs_route",
    # grouping / préparation des leads (étape 9)
    "mission.get_grouping_with_qualitative", "mission.make_final", "mission.download_grouping",
    # états financiers préliminaires (étape 10)
    "mission.etats_financiers_preliminaires_route", "mission.classement_bilan_route",
    # revue analytique finale (étape 11)
    "mission.revue_analytique_route", "mission.update_commentaire_route",
    "mission.revue_analytique_finale_route", "mission.save_revue_analytique_route",
    "mission.download_revue_analytique",
}


def verrou_actif() -> bool:
    """Flag global, désactivé par défaut (voir env.template : IPE_VERROU_ACTIF)."""
    return os.getenv("IPE_VERROU_ACTIF", "false").strip().lower() in ("1", "true", "yes", "on")


def _collection():
    return get_database()[COLLECTION_MISSION]


def _etat_par_defaut() -> Dict[str, Any]:
    return {
        "verrou_applicable": False,
        "verrou_actif": False,
        "ipe_fiabilite_validee": None,
        "statut_circuit": "en_cours",
        "modules": {},
        "historique": [],
        "fichiers_references": {},
        "remarques": [],
        "qualifications_ecarts": [],
        "justifications_non_evaluables": {},
    }


def lire_etat_ipe(mission_id: str) -> Dict[str, Any]:
    """
    État IPE brut d'une mission (Mission1.ipe), ou valeurs par défaut
    "non évalué / antérieure au verrou" si le sous-document est absent —
    additif et rétrocompatible : une mission sans historique IPE n'est
    jamais traitée comme une erreur (docs/PLAN_verrou_IPE.md §1).
    """
    try:
        object_id = ObjectId(mission_id)
    except InvalidId:
        return _etat_par_defaut()

    doc = _collection().find_one({"_id": object_id}, {"ipe": 1})
    if not doc:
        return _etat_par_defaut()

    ipe = doc.get("ipe") or {}
    etat = _etat_par_defaut()
    etat.update({
        "verrou_applicable": ipe.get("verrou_applicable", False),
        "verrou_actif": ipe.get("verrou_actif", False),
        "ipe_fiabilite_validee": ipe.get("ipe_fiabilite_validee"),
        "statut_circuit": ipe.get("statut_circuit") or "en_cours",
        "modules": ipe.get("modules", {}),
        "historique": ipe.get("historique", []),
        "fichiers_references": ipe.get("fichiers_references", {}),
        "remarques": ipe.get("remarques", []),
        "qualifications_ecarts": ipe.get("qualifications_ecarts", []),
        "justifications_non_evaluables": ipe.get("justifications_non_evaluables", {}),
    })
    return etat


def mission_est_bloquee(etat_ipe: Dict[str, Any]) -> bool:
    """
    Décision IPE-GLOBAL-01 (docs/PLAN_verrou_IPE.md §3, résolution des
    anciennes décisions 1/6 du §8) :
    - verrou_applicable=False (mission antérieure au verrou, ou sous-document
      absent) -> jamais bloquée ;
    - verrou_applicable=True -> bloquée sauf si ipe_fiabilite_validee est
      explicitement True (absent/None/False = bloquant par défaut, prudence).
    """
    if not etat_ipe.get("verrou_applicable"):
        return False
    return etat_ipe.get("ipe_fiabilite_validee") is not True


def statut_affiche(etat_ipe: Dict[str, Any]) -> str:
    """
    Statut destiné à l'indicateur « Fiabilité IPE » de la barre latérale et
    à l'écran dédié (docs/PLAN_verrou_IPE.md §6, circuit de revue) :
    "anterieure_au_verrou" | "non_commence" | "en_cours" |
    "soumis_pour_revue" | "en_attente_correction" | "valide". Dérivé de
    statut_circuit (jamais de ipe_fiabilite_validee directement) : les deux
    sont maintenus en cohérence à chaque écriture (valider_fiabilite,
    invalidation automatique) — "valide" <=> ipe_fiabilite_validee is True.
    """
    if not etat_ipe.get("verrou_applicable"):
        return "anterieure_au_verrou"

    statut_circuit = etat_ipe.get("statut_circuit") or "en_cours"
    if statut_circuit in ("valide", "soumis_pour_revue", "en_attente_correction"):
        return statut_circuit

    # "en_cours" : distingue "jamais évalué" de "évalué mais pas encore soumis".
    if not etat_ipe.get("modules"):
        return "non_commence"
    return "en_cours"


def capturer_verrou_applicable_a_la_creation(mission_id: str) -> None:
    """
    Fige Mission1.ipe.verrou_applicable à la création de la mission, à
    l'état courant du flag global IPE_VERROU_ACTIF (docs/PLAN_verrou_IPE.md
    §2 bis). Idempotent : n'écrase jamais une valeur déjà figée (filtre sur
    "ipe.verrou_applicable" absent).
    """
    try:
        object_id = ObjectId(mission_id)
    except InvalidId:
        return

    actif = verrou_actif()
    _collection().update_one(
        {"_id": object_id, "ipe.verrou_applicable": {"$exists": False}},
        {"$set": {
            "ipe.verrou_applicable": actif,
            "ipe.verrou_actif": actif,
            "ipe.ipe_fiabilite_validee": None,
            "ipe.statut_circuit": "en_cours",
            "ipe.modules": {},
            "ipe.historique": [],
            "ipe.remarques": [],
            "ipe.qualifications_ecarts": [],
            "ipe.justifications_non_evaluables": {},
        }},
    )


def endpoint_est_verrouillable(endpoint: Optional[str]) -> bool:
    return bool(endpoint) and endpoint in ENDPOINTS_VERROUILLABLES


def verifier_verrou_ipe():
    """
    Hook Blueprint.before_request du blueprint "mission" (enregistré depuis
    api/src/routes/__init__.py, jamais depuis api/src/mission/). No-op tant
    que IPE_VERROU_ACTIF est désactivé (défaut) : aucune régression possible
    sur les 9 étapes existantes.
    """
    if not verrou_actif():
        return None

    if not endpoint_est_verrouillable(request.endpoint):
        return None

    mission_id = (request.view_args or {}).get("id_mission")
    if not mission_id:
        # Route verrouillable sans mission_id dans l'URL : non gatable par ce
        # mécanisme (docs/PLAN_verrou_IPE.md §3, limite connue : generate_efi
        # notamment). On ne bloque jamais une route qu'on ne peut pas
        # rattacher à une mission précise.
        return None

    # verifier_coherence_fichiers (pas lire_etat_ipe) : détecte, à la lecture,
    # un remplacement de fichier survenu sans invalidation à l'écriture
    # (notamment la balance générale, importée par le flux V1 — voir plus bas).
    etat = verifier_coherence_fichiers(mission_id)
    if mission_est_bloquee(etat):
        return make_response(jsonify({
            "success": False,
            "error": "Cycle verrouillé : fiabilité IPE non validée (IPE-GLOBAL-01).",
            "code": "IPE_VERROU",
        }), 403)
    return None


def capturer_verrou_apres_creation_mission(response):
    """
    Hook Blueprint.after_request du blueprint "mission" (enregistré depuis
    api/src/routes/__init__.py, jamais depuis api/src/mission/). Capture
    verrou_applicable juste après une création de mission réussie
    (endpoint mission.new_assign), sans modifier new_assign() ni model.py
    (docs/PLAN_verrou_IPE.md §2 bis).
    """
    if request.endpoint != "mission.new_assign" or response.status_code != 200:
        return response

    payload = response.get_json(silent=True) or {}
    mission_id = (payload.get("data") or {}).get("_id")
    if mission_id:
        capturer_verrou_applicable_a_la_creation(mission_id)
    return response


# Type de fichier complémentaire -> module IPE qu'il alimente (docs/PLAN_verrou_IPE.md §4).
TYPE_VERS_MODULE = {
    "auxiliaire_client": "ipe_1_clients",
    "auxiliaire_fournisseur": "ipe_2_fournisseurs",
    "immobilisations": "ipe_3_immobilisations",
}


def decider_invalidation(
    etat_ipe: Dict[str, Any],
    type_fichier: str,
    nouveau_fichier_id: Optional[str],
) -> Optional[Dict[str, Any]]:
    """
    Fonction pure : décide si le remplacement de `type_fichier` (nouvel _id
    `nouveau_fichier_id`) doit invalider automatiquement une validation
    existante — uniquement si ce type de fichier avait servi à la dernière
    validation positive (fichiers_references, capturé par
    rapprochement_ipe_service.valider_fiabilite) ET que le fichier a
    effectivement changé. Ne décide rien côté Mongo : voir
    invalider_si_fichier_remplace pour l'écriture.

    `nouveau_fichier_id` à None : le fichier a été retiré sans remplacement
    (action « Retirer » de l'écran Fichiers complémentaires).

    Renvoie None si rien à invalider, sinon {"updates": {...}, "action": ...,
    "resultat": {...}, "commentaire": ...} à transformer en entrée
    d'historique par l'appelant.
    """
    reference = (etat_ipe.get("fichiers_references") or {}).get(type_fichier)
    if not reference:
        return None  # jamais utilisé par une validation positive : rien à invalider
    if reference.get("_id") == nouveau_fichier_id:
        return None  # même document (ne devrait pas arriver, un import crée toujours un nouvel _id)

    module = TYPE_VERS_MODULE.get(type_fichier)
    # statut_circuit repasse à "en_cours" avec ipe_fiabilite_validee (les
    # deux doivent toujours rester cohérents — docs/PLAN_verrou_IPE.md).
    updates: Dict[str, Any] = {"ipe.ipe_fiabilite_validee": False, "ipe.statut_circuit": "en_cours"}
    if module:
        updates[f"ipe.modules.{module}.statut"] = "non_evalue"

    return {
        "updates": updates,
        "action": "invalidation_automatique",
        "resultat": {"type_fichier": type_fichier, "module": module},
        "commentaire": (
            f"Fichier '{type_fichier}' {'retiré' if nouveau_fichier_id is None else 'remplacé'} après validation : "
            "fiabilité IPE invalidée automatiquement."
        ),
    }


def invalider_si_fichier_remplace(mission_id: str, type_fichier: str, nouveau_fichier_id: Optional[str]) -> None:
    """
    Invalidation automatique après remplacement d'un fichier utilisé par une
    validation IPE positive (docs/PLAN_verrou_IPE.md). Appelée depuis les
    services d'import (balance_auxiliaire_service, immobilisation_service)
    juste après l'insertion réussie d'une nouvelle version active — jamais
    depuis model.py/mission routes.

    Limite connue : la balance générale (legacy, api/src/model.py) n'a
    aujourd'hui aucune route de remplacement pour une mission existante —
    cette fonction n'est donc appelée que pour les 3 types de fichiers
    complémentaires. Si un tel remplacement est ajouté un jour, il devra
    appeler cette même fonction avec type_fichier="balance_generale".
    """
    etat = lire_etat_ipe(mission_id)
    decision = decider_invalidation(etat, type_fichier, nouveau_fichier_id)
    if decision is None:
        return

    horodatage = datetime.now(timezone.utc).isoformat()
    historique_entree = {
        "horodatage": horodatage,
        "utilisateur_id": None,
        "action": decision["action"],
        "resultat": decision["resultat"],
        "commentaire": decision["commentaire"],
    }

    _collection().update_one(
        {"_id": ObjectId(mission_id)},
        {
            "$set": decision["updates"],
            "$push": {"ipe.historique": historique_entree},
        },
    )


def _references_actuelles(mission_id: str) -> Dict[str, Optional[str]]:
    """
    Recalcule les références (_id) actuellement résolvables pour chaque type
    de fichier utilisé par le rapprochement IPE. None quand un type n'est
    plus résolvable (balance générale introuvable/ambiguë après un
    remplacement, ou plus aucun fichier actif pour un type complémentaire) —
    un None est bien un changement si une référence existait auparavant.

    Import différé de rapprochement_ipe_service : évite le cycle (ce module
    importe verrou_ipe_service pour lire_etat_ipe).
    """
    from src.services import rapprochement_ipe_service

    actuelles: Dict[str, Optional[str]] = {}

    try:
        balance_generale = rapprochement_ipe_service.resoudre_balance_generale(mission_id)
        actuelles["balance_generale"] = str(balance_generale["_id"])
    except ValueError:
        actuelles["balance_generale"] = None

    fichiers = fc_service.lister_fichiers_complementaires(mission_id)
    for type_fichier, docs in fichiers.items():
        actuelles[type_fichier] = docs[0]["_id"] if docs else None

    return actuelles


def detecter_fichiers_modifies(
    fichiers_references: Dict[str, Any],
    references_actuelles: Dict[str, Optional[str]],
) -> List[Dict[str, Any]]:
    """
    Fonction pure : compare les références figées à la dernière validation
    positive (Mission1.ipe.fichiers_references) aux références actuellement
    résolvables. Renvoie la liste des types dont le fichier a changé (ou a
    disparu) depuis — [] si tout est inchangé.
    """
    changements = []
    for type_fichier, reference in (fichiers_references or {}).items():
        id_reference = reference.get("_id") if isinstance(reference, dict) else None
        id_actuel = references_actuelles.get(type_fichier)
        if id_actuel != id_reference:
            changements.append({
                "type_fichier": type_fichier,
                "id_reference": id_reference,
                "id_actuel": id_actuel,
            })
    return changements


def verifier_coherence_fichiers(mission_id: str) -> Dict[str, Any]:
    """
    « Lecture avec vérification » de l'état IPE (docs/PLAN_verrou_IPE.md) :
    si la dernière validation positive référence des fichiers et que l'un
    d'eux a changé depuis — notamment la balance générale, importée par le
    flux V1 (api/src/model.py) qui ne déclenche AUCUNE invalidation à
    l'écriture (voir invalider_si_fichier_remplace, limité aux fichiers
    complémentaires) — la fiabilité est considérée comme non validée et
    l'incohérence est journalisée (jamais une invalidation silencieuse).

    Appelée partout où l'état IPE sert à une décision ou à un affichage
    (hook de blocage verifier_verrou_ipe, GET /ipe) — jamais lors d'une
    évaluation/validation elle-même, qui travaille sur lire_etat_ipe (lecture
    brute, sans effet de bord caché derrière une simple lecture).
    """
    etat = lire_etat_ipe(mission_id)
    if etat.get("ipe_fiabilite_validee") is not True or not etat.get("fichiers_references"):
        return etat  # rien à vérifier : jamais validé, ou sans référence figée

    references_actuelles = _references_actuelles(mission_id)
    changements = detecter_fichiers_modifies(etat["fichiers_references"], references_actuelles)
    if not changements:
        return etat

    horodatage = datetime.now(timezone.utc).isoformat()
    historique_entree = {
        "horodatage": horodatage,
        "utilisateur_id": None,
        "action": "invalidation_detectee_a_la_lecture",
        "resultat": {"changements": changements},
        "commentaire": (
            "Fiabilité IPE invalidée : un ou plusieurs fichiers référencés "
            "ont changé depuis la dernière validation (détecté à la lecture, "
            "ex. balance générale remplacée via le flux V1)."
        ),
    }

    _collection().update_one(
        {"_id": ObjectId(mission_id)},
        {
            # statut_circuit repasse à "en_cours" avec ipe_fiabilite_validee
            # (toujours cohérents — docs/PLAN_verrou_IPE.md).
            "$set": {"ipe.ipe_fiabilite_validee": False, "ipe.statut_circuit": "en_cours"},
            "$push": {"ipe.historique": historique_entree},
        },
    )

    etat["ipe_fiabilite_validee"] = False
    etat["statut_circuit"] = "en_cours"
    etat["historique"] = etat.get("historique", []) + [historique_entree]
    return etat
