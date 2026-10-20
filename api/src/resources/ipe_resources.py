"""
Contrôleurs HTTP pour le verrou IPE (Module 1, CAC-IPE-01) et son circuit de
revue. Nouveau périmètre V2 — voir docs/PLAN_verrou_IPE.md §3, §4, §5. Ne
touche pas aux ressources mission/client existantes.
"""
from flask import request, jsonify, make_response
from marshmallow import ValidationError

from src.services import verrou_ipe_service
from src.services import rapprochement_ipe_service
from src.services import revue_ipe_service
from src.schemas.ipe_schemas import (
    ValidationFiabiliteSchema,
    SoumissionRevueSchema,
    DemandeCorrectionSchema,
    RemarqueCreationSchema,
    ReponseRemarqueSchema,
    TraiterRemarqueSchema,
    QualificationEcartSchema,
    JustificationNonEvaluableSchema,
    validate_ipe_data,
)


def _reponse(etat, code=200):
    """
    Réponse commune : état IPE + statut affiché + liste des causes d'écart
    (source unique : revue_ipe_service.CAUSES_ECART, jamais recopiée côté
    frontend) + fraîcheur du rapprochement (raison du refus de soumission
    s'il n'est pas lancé ou porte sur des fichiers remplacés depuis).
    """
    etat["statut_affiche"] = verrou_ipe_service.statut_affiche(etat)
    etat["causes_ecart"] = list(revue_ipe_service.CAUSES_ECART)
    mission_id = (request.view_args or {}).get("mission_id")
    if mission_id:
        raison = revue_ipe_service.refus_rapprochement(etat, verrou_ipe_service.references_fichiers_actuelles(mission_id))
        etat["rapprochement_a_jour"] = {"ok": raison is None, "raison": raison}
    return make_response(jsonify({"success": True, "data": etat}), code)


def _executer(action, schema=None, code=200):
    """Valide le corps (si schéma), exécute l'action, mappe les erreurs : schéma/règle -> 400, reste -> 500."""
    try:
        data = validate_ipe_data(request.get_json() or {}, schema) if schema else {}
        return _reponse(action(data), code)
    except ValidationError as e:
        return make_response(jsonify({"success": False, "error": "Erreurs de validation", "errors": e.messages}), 400)
    except ValueError as e:
        return make_response(jsonify({"success": False, "error": str(e)}), 400)
    except Exception as e:
        return make_response(jsonify({"success": False, "error": f"Erreur serveur: {str(e)}"}), 500)


class IpeResource:
    """Contrôleur pour /api/v1/missions/<id>/ipe[...]"""

    @staticmethod
    def obtenir_etat(mission_id: str):
        """
        GET /api/v1/missions/<id>/ipe — état IPE courant. Passe par
        verifier_coherence_fichiers : si un fichier référencé par la dernière
        validation a changé depuis, l'état renvoyé reflète l'invalidation.
        """
        return _executer(lambda _: verrou_ipe_service.verifier_coherence_fichiers(mission_id))

    @staticmethod
    def evaluer(mission_id: str):
        """
        POST /api/v1/missions/<id>/ipe/evaluer — lance le rapprochement IPE-1/2/3.
        Échec explicite (400) si la balance générale de l'exercice audité est
        introuvable ou ambiguë : rien n'est enregistré dans ce cas.
        """
        return _executer(lambda _: rapprochement_ipe_service.evaluer_ipe(mission_id))

    @staticmethod
    def valider(mission_id: str):
        """
        POST /api/v1/missions/<id>/ipe/validation — validation (ou
        invalidation) de la fiabilité IPE. Validation refusée (400) hors
        « Soumis pour revue », avec un écart non qualifié, une demande de
        correction non traitée ou un module non évaluable non justifié.
        TODO(décision) : qui a le droit de valider n'est pas vérifié.
        """
        return _executer(
            lambda d: rapprochement_ipe_service.valider_fiabilite(
                mission_id,
                validee=d["validee"],
                utilisateur_id=d.get("utilisateur_id"),
                commentaire=d.get("commentaire"),
            ),
            ValidationFiabiliteSchema,
        )

    @staticmethod
    def soumettre(mission_id: str):
        """
        POST /api/v1/missions/<id>/ipe/soumettre — action auditeur. Refusée
        (400) si un écart n'est pas qualifié (cause + commentaire) ou si le
        statut ne le permet pas. TODO(décision) : qui a le droit de soumettre.
        """
        return _executer(
            lambda d: revue_ipe_service.soumettre_pour_revue(
                mission_id,
                utilisateur_id=d.get("utilisateur_id"),
                commentaire=d.get("commentaire"),
            ),
            SoumissionRevueSchema,
        )

    @staticmethod
    def demander_correction(mission_id: str):
        """
        POST /api/v1/missions/<id>/ipe/demander-correction — action manager,
        commentaire obligatoire. Ne valide ni n'invalide. TODO(décision) :
        qui a le droit de demander une correction.
        """
        return _executer(
            lambda d: revue_ipe_service.demander_correction(
                mission_id,
                commentaire=d["commentaire"],
                utilisateur_id=d.get("utilisateur_id"),
            ),
            DemandeCorrectionSchema,
        )

    @staticmethod
    def qualifier_ecart(mission_id: str):
        """PUT /api/v1/missions/<id>/ipe/qualifications — cause + commentaire pour un écart (par compte collectif)."""
        return _executer(
            lambda d: revue_ipe_service.qualifier_ecart(
                mission_id,
                module=d["module"],
                numero_compte=d["numero_compte"],
                cause=d["cause"],
                commentaire=d["commentaire"],
                utilisateur_id=d.get("utilisateur_id"),
            ),
            QualificationEcartSchema,
        )

    @staticmethod
    def justifier_non_evaluable(mission_id: str):
        """PUT /api/v1/missions/<id>/ipe/justifications-non-evaluables — justification écrite d'un module non évaluable."""
        return _executer(
            lambda d: revue_ipe_service.justifier_module_non_evaluable(
                mission_id,
                module=d["module"],
                commentaire=d["commentaire"],
                utilisateur_id=d.get("utilisateur_id"),
            ),
            JustificationNonEvaluableSchema,
        )

    @staticmethod
    def ajouter_remarque(mission_id: str):
        """POST /api/v1/missions/<id>/ipe/remarques — remarque générale ou sur un écart, informative ou demande de correction."""
        return _executer(
            lambda d: revue_ipe_service.ajouter_remarque(
                mission_id,
                commentaire=d["commentaire"],
                utilisateur_id=d.get("utilisateur_id"),
                module=d.get("module"),
                numero_compte=d.get("numero_compte"),
                type_remarque=d.get("type") or "information",
            ),
            RemarqueCreationSchema,
            code=201,
        )

    @staticmethod
    def repondre_remarque(mission_id: str, remarque_id: str):
        """PUT /api/v1/missions/<id>/ipe/remarques/<remarque_id>/reponse — réponse de l'auditeur."""
        return _executer(
            lambda d: revue_ipe_service.repondre_remarque(
                mission_id,
                remarque_id,
                commentaire=d["commentaire"],
                utilisateur_id=d.get("utilisateur_id"),
            ),
            ReponseRemarqueSchema,
        )

    @staticmethod
    def marquer_remarque_traitee(mission_id: str, remarque_id: str):
        """
        PUT /api/v1/missions/<id>/ipe/remarques/<remarque_id>/traitee — réservé
        à l'auteur de la remarque, après la réponse de l'auditeur (400 sinon).
        """
        return _executer(
            lambda d: revue_ipe_service.marquer_remarque_traitee(
                mission_id,
                remarque_id,
                traitee=d["traitee"],
                utilisateur_id=d.get("utilisateur_id"),
            ),
            TraiterRemarqueSchema,
        )
