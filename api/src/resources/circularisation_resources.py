"""
Contrôleurs HTTP de la circularisation, sous-lot a (docs/PLAN_circularisation.md) :
population, sélection manuelle, mode de confirmation, mémo de sélection.
"""
from flask import request, jsonify, make_response
from marshmallow import ValidationError

from src.services import circularisation_service as cir
from src.schemas.circularisation_schemas import (
    PopulationSchema, DecisionTiersSchema, ModeSchema, DecisionMemoSchema,
)


def _executer(action, schema=None, code=200):
    """Même convention que ipe_resources : schéma/règle -> 400, reste -> 500."""
    try:
        corps = request.get_json(silent=True)
        if corps is None and request.get_data():
            raise ValueError("Corps de la requête illisible : JSON UTF-8 attendu.")
        data = schema().load(corps or {}) if schema else {}
        return make_response(jsonify({"success": True, "data": action(data)}), code)
    except ValidationError as e:
        return make_response(jsonify({"success": False, "error": "Erreurs de validation", "errors": e.messages}), 400)
    except ValueError as e:
        return make_response(jsonify({"success": False, "error": str(e)}), 400)
    except Exception as e:
        return make_response(jsonify({"success": False, "error": f"Erreur serveur: {str(e)}"}), 500)


class CircularisationResource:
    """Contrôleur pour /api/v1/missions/<id>/circularisation[...]"""

    @staticmethod
    def lire(mission_id):
        return _executer(lambda _: cir.lire_circularisation(mission_id))

    @staticmethod
    def constituer_population(mission_id, type_tiers):
        return _executer(lambda d: cir.constituer_population(mission_id, type_tiers, d["utilisateur_id"]), PopulationSchema)

    @staticmethod
    def decider_tiers(mission_id, type_tiers):
        return _executer(lambda d: cir.decider_tiers(
            mission_id, type_tiers, d["numero"], d["retenu"], d["motif"], d["utilisateur_id"]), DecisionTiersSchema)

    @staticmethod
    def definir_mode(mission_id, type_tiers):
        return _executer(lambda d: cir.definir_mode(mission_id, type_tiers, d["mode"], d["motif"], d["utilisateur_id"]),
                         ModeSchema)

    @staticmethod
    def lire_memo(mission_id, type_tiers):
        return _executer(lambda _: cir.lire_memo(mission_id, type_tiers))

    @staticmethod
    def soumettre_memo(mission_id, type_tiers):
        return _executer(lambda d: cir.soumettre_memo(mission_id, type_tiers, d["utilisateur_id"]), PopulationSchema)

    @staticmethod
    def valider_memo(mission_id, type_tiers):
        return _executer(lambda d: cir.valider_memo(mission_id, type_tiers, d["commentaire"], d["utilisateur_id"]),
                         DecisionMemoSchema)

    @staticmethod
    def demander_correction_memo(mission_id, type_tiers):
        return _executer(lambda d: cir.demander_correction_memo(
            mission_id, type_tiers, d["commentaire"], d["utilisateur_id"]), DecisionMemoSchema)
