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
transitions intermédiaires (soumission, demande de correction) et les
remarques, qui ne touchent jamais ipe_fiabilite_validee.

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


def _collection():
    return get_database()[COLLECTION_MISSION]


def ecarts_non_qualifies(
    modules: Optional[Dict[str, Any]],
    remarques: Optional[List[Dict[str, Any]]],
) -> List[str]:
    """
    Fonction pure : identifiants "module:numero_compte" des collectifs en
    écart réel (c["ok"] est False, dans un module au statut "ecart" — jamais
    "non_evaluable") sans aucune remarque de niveau écart attachée. C'est le
    mécanisme de qualification de ce circuit : TODO(spec: CAC-IPE-01) — les
    valeurs possibles de qualification.etiquette restent, elles, non
    confirmées ; on ne tranche ici que CE mécanisme (au moins une remarque
    par collectif en écart), pas une classification métier inventée.
    """
    collectifs_commentes = {
        (r.get("module"), r.get("numero_compte"))
        for r in (remarques or [])
        if r.get("module") and r.get("numero_compte")
    }

    manquants: List[str] = []
    for cle_module, module in (modules or {}).items():
        if module.get("statut") != "ecart":
            continue
        collectifs = (module.get("derniere_evaluation") or {}).get("detail_collectifs") or []
        for collectif in collectifs:
            if collectif.get("ok"):
                continue
            numero = collectif.get("numero_compte")
            if (cle_module, numero) not in collectifs_commentes:
                manquants.append(f"{cle_module}:{numero}")
    return manquants


def soumettre_pour_revue(
    mission_id: str,
    utilisateur_id: Optional[str] = None,
    commentaire: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Action auditeur : "en_cours" ou "en_attente_correction" -> "soumis_pour_revue".
    Refusée (ValueError, rien écrit) si le statut actuel ne le permet pas,
    ou si un écart réel n'a aucune remarque attachée (ecarts_non_qualifies).
    TODO(décision) : qui a le droit de soumettre n'est pas vérifié.
    """
    etat = verrou_ipe_service.lire_etat_ipe(mission_id)
    statut_actuel = etat.get("statut_circuit") or "en_cours"

    if statut_actuel not in STATUTS_SOURCE_AUTORISES_SOUMISSION:
        raise ValueError(
            "Soumission refusée : possible uniquement depuis « En cours » ou « En attente de "
            f"correction » (statut actuel : {statut_actuel})."
        )

    manquants = ecarts_non_qualifies(etat.get("modules"), etat.get("remarques"))
    if manquants:
        raise ValueError(
            "Soumission refusée : écart(s) non qualifié(s) (aucune remarque attachée) : "
            + ", ".join(manquants) + "."
        )

    horodatage = datetime.now(timezone.utc).isoformat()
    historique_entree = {
        "horodatage": horodatage,
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
    valide ni n'invalide ipe_fiabilite_validee (reste tel quel — on n'a
    jamais validé à ce stade). Commentaire obligatoire (contrôlé par
    DemandeCorrectionSchema, même règle que valider_fiabilite).
    TODO(décision) : qui a le droit de demander une correction n'est pas
    vérifié.
    """
    etat = verrou_ipe_service.lire_etat_ipe(mission_id)
    statut_actuel = etat.get("statut_circuit") or "en_cours"

    if statut_actuel != STATUT_SOURCE_AUTORISE_DEMANDE_CORRECTION:
        raise ValueError(
            "Demande de correction refusée : possible uniquement depuis « Soumis pour revue » "
            f"(statut actuel : {statut_actuel})."
        )

    horodatage = datetime.now(timezone.utc).isoformat()
    historique_entree = {
        "horodatage": horodatage,
        "utilisateur_id": utilisateur_id,
        "action": "demande_correction",
        "resultat": {"statut_circuit": "en_attente_correction"},
        "commentaire": commentaire,
    }
    _collection().update_one(
        {"_id": ObjectId(mission_id)},
        {
            "$set": {"ipe.statut_circuit": "en_attente_correction"},
            "$push": {"ipe.historique": historique_entree},
        },
    )
    return verrou_ipe_service.lire_etat_ipe(mission_id)


def ajouter_remarque(
    mission_id: str,
    commentaire: str,
    utilisateur_id: Optional[str] = None,
    module: Optional[str] = None,
    numero_compte: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ajoute une remarque à deux niveaux (docs/PLAN_verrou_IPE.md) : générale
    sur le contrôle (module/numero_compte absents) ou sur un écart précis,
    par compte collectif (module + numero_compte renseignés). Une remarque
    sur un écart précis compte comme qualification pour ecarts_non_qualifies.
    """
    horodatage = datetime.now(timezone.utc).isoformat()
    remarque = {
        "_id": str(uuid4()),
        "horodatage": horodatage,
        "utilisateur_id": utilisateur_id,
        "commentaire": commentaire,
        "module": module,
        "numero_compte": numero_compte,
        "reponse": None,
        "traitee": False,
    }
    historique_entree = {
        "horodatage": horodatage,
        "utilisateur_id": utilisateur_id,
        "action": "remarque_ajoutee",
        "resultat": {"module": module, "numero_compte": numero_compte},
        "commentaire": commentaire,
    }
    _collection().update_one(
        {"_id": ObjectId(mission_id)},
        {"$push": {"ipe.remarques": remarque, "ipe.historique": historique_entree}},
    )
    return verrou_ipe_service.lire_etat_ipe(mission_id)


def repondre_remarque(
    mission_id: str,
    remarque_id: str,
    commentaire: str,
    utilisateur_id: Optional[str] = None,
) -> Dict[str, Any]:
    """L'auditeur répond à une remarque existante (identifiée par son _id)."""
    horodatage = datetime.now(timezone.utc).isoformat()
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
    """Marque (ou démarque) une remarque comme traitée."""
    horodatage = datetime.now(timezone.utc).isoformat()
    historique_entree = {
        "horodatage": horodatage,
        "utilisateur_id": utilisateur_id,
        "action": "remarque_traitee" if traitee else "remarque_rouverte",
        "resultat": {"remarque_id": remarque_id},
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
