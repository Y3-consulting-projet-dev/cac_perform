"""
Circuit de revue du contrôle IPE (Module 1, CAC-IPE-01) — voir
docs/PLAN_verrou_IPE.md. Nouveau périmètre V2, service dédié (CLAUDE.md :
rien dans api/src/model.py ni dans les routes /cors/mission).

Statuts du circuit (Mission1.ipe.statut_circuit) :
  "en_cours" -> "soumis_pour_revue" -> "valide"
                        ^                 |
                        |                 | (invalider : n'importe quel état -> "en_cours")
                "en_attente_correction" <-+  (demande de correction manager)

ipe_fiabilite_validee et statut_circuit sont toujours tenus cohérents
("valide" <=> True) — écrit uniquement par rapprochement_ipe_service.
valider_fiabilite pour la transition finale ; ce module écrit les
transitions intermédiaires (soumission, demande de correction), les
qualifications d'écart, les justifications des modules non évaluables et
les remarques, qui ne touchent jamais ipe_fiabilite_validee.

TODO(décision) : aucun contrôle de rôle n'existe sur les missions
aujourd'hui (CLAUDE.md, point de sécurité connu) — qui a le droit de
soumettre pour revue, de demander une correction, ou de valider n'est pas
vérifié ici. Ne pas inventer de règle : décision à faire remonter.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from bson import ObjectId

from src.utils.database import get_database
from src.services import verrou_ipe_service

COLLECTION_MISSION = "Mission1"

STATUTS_CIRCUIT = ("en_cours", "soumis_pour_revue", "en_attente_correction", "valide")

# Depuis quels statuts chaque action est autorisée — transitions explicites,
# jamais implicites (docs/PLAN_verrou_IPE.md).
STATUTS_SOURCE_AUTORISES_SOUMISSION = ("en_cours", "en_attente_correction")
STATUT_SOURCE_AUTORISE_DEMANDE_CORRECTION = "soumis_pour_revue"
# La qualification des écarts et la justification des modules non évaluables
# sont le travail de l'auditeur : figées une fois le contrôle soumis ou validé.
STATUTS_EDITION_AUDITEUR = ("en_cours", "en_attente_correction")

# Causes possibles d'un écart, liste PROVISOIRE et paramétrable issue du
# cahier des charges §2.3.4. TODO(spec: CAC-IPE-01) — liste définitive non
# confirmée : la modifier ici seulement (elle est renvoyée au frontend avec
# l'état IPE, aucune copie ailleurs).
CAUSES_ECART = (
    "Cut-off",
    "Erreur d'imputation",
    "En cours de justification",
    "Partie liée",
)

TYPES_REMARQUE = ("information", "demande_correction")

LONGUEUR_MIN_COMMENTAIRE = 15


def _collection():
    return get_database()[COLLECTION_MISSION]


def _maintenant() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cle_ecart(module: Optional[str], numero_compte: Optional[str]) -> str:
    return f"{module}:{numero_compte}"


# ---------------------------------------------------------------------------
# Règles pures (testées sans base)
# ---------------------------------------------------------------------------

def qualification_est_complete(qualification: Optional[Dict[str, Any]]) -> bool:
    """Une qualification compte si elle a une cause de la liste ET un commentaire non vide."""
    if not qualification:
        return False
    return (
        qualification.get("cause") in CAUSES_ECART
        and bool((qualification.get("commentaire") or "").strip())
    )


def ecarts_non_qualifies(
    modules: Optional[Dict[str, Any]],
    qualifications: Optional[List[Dict[str, Any]]],
) -> List[str]:
    """
    Fonction pure : identifiants "module:numero_compte" des collectifs en
    écart réel (c["ok"] est False, dans un module au statut "ecart" — jamais
    "non_evaluable") sans qualification complète (cause de CAUSES_ECART +
    commentaire). Une simple remarque ne qualifie pas un écart.
    """
    qualifiees = {
        _cle_ecart(q.get("module"), q.get("numero_compte"))
        for q in (qualifications or [])
        if qualification_est_complete(q)
    }

    manquants: List[str] = []
    for cle_module, module in (modules or {}).items():
        if module.get("statut") != "ecart":
            continue
        collectifs = (module.get("derniere_evaluation") or {}).get("detail_collectifs") or []
        for collectif in collectifs:
            if collectif.get("ok"):
                continue
            cle = _cle_ecart(cle_module, collectif.get("numero_compte"))
            if cle not in qualifiees:
                manquants.append(cle)
    return manquants


def demandes_correction_non_traitees(remarques: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Fonction pure : remarques de type "demande_correction" pas encore marquées traitées."""
    return [
        r for r in (remarques or [])
        if r.get("type") == "demande_correction" and not r.get("traitee")
    ]


def modules_non_evaluables_sans_justification(
    modules: Optional[Dict[str, Any]],
    justifications: Optional[Dict[str, Any]],
) -> List[str]:
    """
    Fonction pure : modules au statut "non_evaluable" sans justification
    écrite. Leur traitement métier reste TODO(spec: CAC-IPE-01) ; la
    justification rend seulement visible et traçable le choix de valider
    malgré tout.
    """
    manquants = []
    for cle_module, module in (modules or {}).items():
        if module.get("statut") != "non_evaluable":
            continue
        justification = (justifications or {}).get(cle_module) or {}
        if not (justification.get("commentaire") or "").strip():
            manquants.append(cle_module)
    return manquants


def refus_marquage_remarque(
    remarque: Dict[str, Any],
    utilisateur_id: Optional[str],
    traitee: bool,
) -> Optional[str]:
    """
    Fonction pure : message de refus, ou None si le (dé)marquage est permis.
    - Le demandeur doit être identifié, et être l'auteur enregistré de la
      remarque. TODO(décision) : en attendant les rôles, la vérification
      porte sur l'utilisateur enregistré côté frontend — pas un contrôle
      d'accès. Une remarque d'auteur non identifié ne peut donc être
      (dé)marquée par personne ; seules les remarques informatives peuvent
      être dans ce cas (une demande de correction exige un auteur
      identifié, voir ajouter_remarque/demander_correction) et elles ne
      bloquent rien.
    - Une remarque ne peut être marquée traitée qu'après la réponse de
      l'auditeur.
    """
    if not utilisateur_id:
        return "Utilisateur non identifié : impossible de marquer une remarque traitée ou de la rouvrir."
    if remarque.get("utilisateur_id") != utilisateur_id:
        return "Seul l'auteur de la remarque peut la marquer traitée ou la rouvrir."
    if traitee and not remarque.get("reponse"):
        return "La remarque ne peut être marquée traitée qu'après la réponse de l'auditeur."
    return None


def refus_soumission(etat: Dict[str, Any]) -> Optional[str]:
    """
    Fonction pure : message de refus de « Soumettre pour revue », ou None.
    Exige chaque écart qualifié et chaque module non évaluable justifié
    (le statut source est contrôlé à part par soumettre_pour_revue).
    """
    manquants = ecarts_non_qualifies(etat.get("modules"), etat.get("qualifications_ecarts"))
    if manquants:
        return "Soumission refusée : écart(s) non qualifié(s) (cause + commentaire) : " + ", ".join(manquants) + "."

    sans_justification = modules_non_evaluables_sans_justification(
        etat.get("modules"), etat.get("justifications_non_evaluables")
    )
    if sans_justification:
        return (
            "Soumission refusée : module(s) non évaluable(s) sans justification écrite : "
            + ", ".join(sans_justification) + "."
        )
    return None


def refus_demande_correction_sans_auteur(utilisateur_id: Optional[str]) -> Optional[str]:
    """Fonction pure : une demande de correction exige un utilisateur identifié (elle doit pouvoir être marquée traitée par son auteur)."""
    if not utilisateur_id:
        return "Utilisateur non identifié : impossible de créer une demande de correction."
    return None


def refus_validation(etat: Dict[str, Any]) -> Optional[str]:
    """
    Fonction pure : message de refus d'une validation positive, ou None.
    Appelée par rapprochement_ipe_service.valider_fiabilite en plus du
    contrôle de statut ("soumis_pour_revue").
    """
    manquants = ecarts_non_qualifies(etat.get("modules"), etat.get("qualifications_ecarts"))
    if manquants:
        return "Validation refusée : écart(s) non qualifié(s) (cause + commentaire) : " + ", ".join(manquants) + "."

    demandes = demandes_correction_non_traitees(etat.get("remarques"))
    if demandes:
        return (
            f"Validation refusée : {len(demandes)} demande(s) de correction non traitée(s). "
            "L'auteur de chaque demande doit la marquer traitée après la réponse de l'auditeur."
        )

    sans_justification = modules_non_evaluables_sans_justification(
        etat.get("modules"), etat.get("justifications_non_evaluables")
    )
    if sans_justification:
        return (
            "Validation refusée : module(s) non évaluable(s) sans justification écrite : "
            + ", ".join(sans_justification) + "."
        )
    return None


# ---------------------------------------------------------------------------
# Actions (écriture Mongo)
# ---------------------------------------------------------------------------

def _verifier_edition_auditeur(etat: Dict[str, Any], action: str) -> None:
    statut_actuel = etat.get("statut_circuit") or "en_cours"
    if statut_actuel not in STATUTS_EDITION_AUDITEUR:
        raise ValueError(
            f"{action} impossible : le contrôle est au statut « {statut_actuel} ». "
            "Possible uniquement depuis « En cours » ou « En attente de correction »."
        )


def soumettre_pour_revue(
    mission_id: str,
    utilisateur_id: Optional[str] = None,
    commentaire: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Action auditeur : "en_cours" ou "en_attente_correction" -> "soumis_pour_revue".
    Refusée (ValueError, rien écrit) si le statut actuel ne le permet pas,
    si un écart réel n'est pas qualifié (cause + commentaire), ou si un
    module non évaluable n'a pas de justification écrite (refus_soumission).
    TODO(décision) : qui a le droit de soumettre n'est pas vérifié.
    """
    etat = verrou_ipe_service.lire_etat_ipe(mission_id)
    statut_actuel = etat.get("statut_circuit") or "en_cours"

    if statut_actuel not in STATUTS_SOURCE_AUTORISES_SOUMISSION:
        raise ValueError(
            "Soumission refusée : possible uniquement depuis « En cours » ou « En attente de "
            f"correction » (statut actuel : {statut_actuel})."
        )

    refus = refus_soumission(etat)
    if refus:
        raise ValueError(refus)

    historique_entree = {
        "horodatage": _maintenant(),
        "utilisateur_id": utilisateur_id,
        "action": "soumission_revue",
        "resultat": {"statut_circuit": "soumis_pour_revue"},
        "commentaire": commentaire,
    }
    _collection().update_one(
        {"_id": ObjectId(mission_id)},
        {
            "$set": {"ipe.statut_circuit": "soumis_pour_revue"},
            "$push": {"ipe.historique": historique_entree},
        },
    )
    return verrou_ipe_service.lire_etat_ipe(mission_id)


def demander_correction(
    mission_id: str,
    commentaire: str,
    utilisateur_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Action manager : "soumis_pour_revue" -> "en_attente_correction". Ne
    valide ni n'invalide ipe_fiabilite_validee. Le commentaire devient une
    remarque générale de type "demande_correction" (auteur = demandeur) :
    elle bloque la validation tant que son auteur ne l'a pas marquée
    traitée après la réponse de l'auditeur.
    Refusée sans utilisateur identifié (sinon la demande ne pourrait jamais
    être marquée traitée par son auteur).
    TODO(décision) : qui a le droit de demander une correction n'est pas
    vérifié.
    """
    refus = refus_demande_correction_sans_auteur(utilisateur_id)
    if refus:
        raise ValueError(refus)

    etat = verrou_ipe_service.lire_etat_ipe(mission_id)
    statut_actuel = etat.get("statut_circuit") or "en_cours"

    if statut_actuel != STATUT_SOURCE_AUTORISE_DEMANDE_CORRECTION:
        raise ValueError(
            "Demande de correction refusée : possible uniquement depuis « Soumis pour revue » "
            f"(statut actuel : {statut_actuel})."
        )

    horodatage = _maintenant()
    remarque = _nouvelle_remarque(horodatage, commentaire, utilisateur_id, None, None, "demande_correction")
    historique_entree = {
        "horodatage": horodatage,
        "utilisateur_id": utilisateur_id,
        "action": "demande_correction",
        "resultat": {"statut_circuit": "en_attente_correction", "remarque_id": remarque["_id"]},
        "commentaire": commentaire,
    }
    _collection().update_one(
        {"_id": ObjectId(mission_id)},
        {
            "$set": {"ipe.statut_circuit": "en_attente_correction"},
            "$push": {"ipe.remarques": remarque, "ipe.historique": historique_entree},
        },
    )
    return verrou_ipe_service.lire_etat_ipe(mission_id)


def qualifier_ecart(
    mission_id: str,
    module: str,
    numero_compte: str,
    cause: str,
    commentaire: str,
    utilisateur_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Qualifie un écart précis (module + compte collectif) : cause choisie
    dans CAUSES_ECART + commentaire. Remplace une qualification existante
    du même écart. Refusée si le contrôle est soumis ou validé.
    """
    if cause not in CAUSES_ECART:
        raise ValueError(
            f"Cause inconnue : « {cause} ». Causes possibles : " + ", ".join(CAUSES_ECART) + "."
        )

    etat = verrou_ipe_service.lire_etat_ipe(mission_id)
    _verifier_edition_auditeur(etat, "Qualification")

    module_doc = (etat.get("modules") or {}).get(module) or {}
    collectifs_en_ecart = {
        c.get("numero_compte")
        for c in (module_doc.get("derniere_evaluation") or {}).get("detail_collectifs") or []
        if not c.get("ok")
    }
    if module_doc.get("statut") != "ecart" or numero_compte not in collectifs_en_ecart:
        raise ValueError(
            f"Aucun écart à qualifier pour {module} / compte collectif {numero_compte} "
            "dans la dernière évaluation."
        )

    horodatage = _maintenant()
    qualification = {
        "module": module,
        "numero_compte": numero_compte,
        "cause": cause,
        "commentaire": commentaire,
        "utilisateur_id": utilisateur_id,
        "horodatage": horodatage,
    }
    autres = [
        q for q in (etat.get("qualifications_ecarts") or [])
        if not (q.get("module") == module and q.get("numero_compte") == numero_compte)
    ]
    historique_entree = {
        "horodatage": horodatage,
        "utilisateur_id": utilisateur_id,
        "action": "qualification_ecart",
        "resultat": {"module": module, "numero_compte": numero_compte, "cause": cause},
        "commentaire": commentaire,
    }
    _collection().update_one(
        {"_id": ObjectId(mission_id)},
        {
            "$set": {"ipe.qualifications_ecarts": autres + [qualification]},
            "$push": {"ipe.historique": historique_entree},
        },
    )
    return verrou_ipe_service.lire_etat_ipe(mission_id)


def justifier_module_non_evaluable(
    mission_id: str,
    module: str,
    commentaire: str,
    utilisateur_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Justification écrite d'un module "non_evaluable", exigée pour soumettre
    pour revue et pour valider.
    Refusée si le module n'est pas non évaluable ou si le contrôle est
    soumis ou validé.
    """
    etat = verrou_ipe_service.lire_etat_ipe(mission_id)
    _verifier_edition_auditeur(etat, "Justification")

    module_doc = (etat.get("modules") or {}).get(module) or {}
    if module_doc.get("statut") != "non_evaluable":
        raise ValueError(f"Le module {module} n'est pas « non évaluable » : aucune justification à saisir.")

    horodatage = _maintenant()
    justification = {"commentaire": commentaire, "utilisateur_id": utilisateur_id, "horodatage": horodatage}
    historique_entree = {
        "horodatage": horodatage,
        "utilisateur_id": utilisateur_id,
        "action": "justification_non_evaluable",
        "resultat": {"module": module},
        "commentaire": commentaire,
    }
    _collection().update_one(
        {"_id": ObjectId(mission_id)},
        {
            "$set": {f"ipe.justifications_non_evaluables.{module}": justification},
            "$push": {"ipe.historique": historique_entree},
        },
    )
    return verrou_ipe_service.lire_etat_ipe(mission_id)


def _nouvelle_remarque(
    horodatage: str,
    commentaire: str,
    utilisateur_id: Optional[str],
    module: Optional[str],
    numero_compte: Optional[str],
    type_remarque: str,
) -> Dict[str, Any]:
    return {
        "_id": str(uuid4()),
        "horodatage": horodatage,
        "utilisateur_id": utilisateur_id,
        "commentaire": commentaire,
        "module": module,
        "numero_compte": numero_compte,
        "type": type_remarque,
        "reponse": None,
        "traitee": False,
    }


def ajouter_remarque(
    mission_id: str,
    commentaire: str,
    utilisateur_id: Optional[str] = None,
    module: Optional[str] = None,
    numero_compte: Optional[str] = None,
    type_remarque: str = "information",
) -> Dict[str, Any]:
    """
    Ajoute une remarque à deux niveaux (générale ou sur un écart précis),
    de type "information" ou "demande_correction". Une demande de
    correction non traitée bloque la validation.
    """
    if type_remarque not in TYPES_REMARQUE:
        raise ValueError(f"Type de remarque inconnu : « {type_remarque} ».")
    if type_remarque == "demande_correction":
        refus = refus_demande_correction_sans_auteur(utilisateur_id)
        if refus:
            raise ValueError(refus)

    horodatage = _maintenant()
    remarque = _nouvelle_remarque(horodatage, commentaire, utilisateur_id, module, numero_compte, type_remarque)
    historique_entree = {
        "horodatage": horodatage,
        "utilisateur_id": utilisateur_id,
        "action": "remarque_ajoutee",
        "resultat": {"module": module, "numero_compte": numero_compte, "type": type_remarque},
        "commentaire": commentaire,
    }
    _collection().update_one(
        {"_id": ObjectId(mission_id)},
        {"$push": {"ipe.remarques": remarque, "ipe.historique": historique_entree}},
    )
    return verrou_ipe_service.lire_etat_ipe(mission_id)


def _trouver_remarque(etat: Dict[str, Any], remarque_id: str) -> Dict[str, Any]:
    remarque = next((r for r in etat.get("remarques") or [] if r.get("_id") == remarque_id), None)
    if remarque is None:
        raise ValueError("Remarque introuvable pour cette mission.")
    return remarque


def repondre_remarque(
    mission_id: str,
    remarque_id: str,
    commentaire: str,
    utilisateur_id: Optional[str] = None,
) -> Dict[str, Any]:
    """L'auditeur répond à une remarque existante (identifiée par son _id)."""
    etat = verrou_ipe_service.lire_etat_ipe(mission_id)
    _trouver_remarque(etat, remarque_id)

    horodatage = _maintenant()
    reponse = {"horodatage": horodatage, "utilisateur_id": utilisateur_id, "commentaire": commentaire}
    historique_entree = {
        "horodatage": horodatage,
        "utilisateur_id": utilisateur_id,
        "action": "remarque_repondue",
        "resultat": {"remarque_id": remarque_id},
        "commentaire": commentaire,
    }
    _collection().update_one(
        {"_id": ObjectId(mission_id), "ipe.remarques._id": remarque_id},
        {
            "$set": {"ipe.remarques.$.reponse": reponse},
            "$push": {"ipe.historique": historique_entree},
        },
    )
    return verrou_ipe_service.lire_etat_ipe(mission_id)


def marquer_remarque_traitee(
    mission_id: str,
    remarque_id: str,
    traitee: bool = True,
    utilisateur_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Marque (ou démarque) une remarque comme traitée — réservé à son auteur,
    et seulement après la réponse de l'auditeur (refus_marquage_remarque).
    """
    etat = verrou_ipe_service.lire_etat_ipe(mission_id)
    remarque = _trouver_remarque(etat, remarque_id)
    refus = refus_marquage_remarque(remarque, utilisateur_id, traitee)
    if refus:
        raise ValueError(refus)

    historique_entree = {
        "horodatage": _maintenant(),
        "utilisateur_id": utilisateur_id,
        "action": "remarque_traitee" if traitee else "remarque_rouverte",
        "resultat": {"remarque_id": remarque_id, "type": remarque.get("type")},
        "commentaire": None,
    }
    _collection().update_one(
        {"_id": ObjectId(mission_id), "ipe.remarques._id": remarque_id},
        {
            "$set": {"ipe.remarques.$.traitee": traitee},
            "$push": {"ipe.historique": historique_entree},
        },
    )
    return verrou_ipe_service.lire_etat_ipe(mission_id)
