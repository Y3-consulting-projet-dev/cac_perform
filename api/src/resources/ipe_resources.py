"""
Contrôleurs HTTP pour le verrou IPE (Module 1, CAC-IPE-01). Nouveau périmètre
V2 — voir docs/PLAN_verrou_IPE.md §3, §4, §5. Ne touche pas aux ressources
mission/client existantes.
"""
from flask import request, jsonify, make_response
from marshmallow import ValidationError

from src.services import verrou_ipe_service
from src.services import rapprochement_ipe_service
from src.schemas.ipe_schemas import ValidationFiabiliteSchema, validate_ipe_data


class IpeResource:
    """Contrôleur pour /api/v1/missions/<id>/ipe[...]"""

    @staticmethod
    def obtenir_etat(mission_id: str):
        """GET /api/v1/missions/<id>/ipe — état IPE courant (+ statut affiché pour la barre latérale)."""
        try:
            etat = verrou_ipe_service.lire_etat_ipe(mission_id)
            etat["statut_affiche"] = verrou_ipe_service.statut_affiche(etat)
            return make_response(jsonify({"success": True, "data": etat}), 200)
        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)

    @staticmethod
    def evaluer(mission_id: str):
        """
        POST /api/v1/missions/<id>/ipe/evaluer — lance le rapprochement IPE-1/2/3.
        Échec explicite (400) si la balance générale de l'exercice audité est
        introuvable ou ambiguë (docs/PLAN_verrou_IPE.md §4) : rien n'est
        enregistré dans ce cas.
        """
        try:
            etat = rapprochement_ipe_service.evaluer_ipe(mission_id)
            etat["statut_affiche"] = verrou_ipe_service.statut_affiche(etat)
            return make_response(jsonify({"success": True, "data": etat}), 200)
        except ValueError as e:
            return make_response(jsonify({"success": False, "error": str(e)}), 400)
        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)

    @staticmethod
    def valider(mission_id: str):
        """
        POST /api/v1/missions/<id>/ipe/validation — validation manager de la
        fiabilité IPE. Une validation positive fige les références des
        fichiers utilisés ; échoue en 400 (sans rien valider) si la balance
        générale de l'exercice audité est introuvable/ambiguë.
        """
        try:
            data = validate_ipe_data(request.get_json() or {}, ValidationFiabiliteSchema)
            etat = rapprochement_ipe_service.valider_fiabilite(
                mission_id,
                validee=data["validee"],
                utilisateur_id=data.get("utilisateur_id"),
                commentaire=data.get("commentaire"),
            )
            etat["statut_affiche"] = verrou_ipe_service.statut_affiche(etat)
            return make_response(jsonify({"success": True, "data": etat}), 200)
        except ValidationError as e:
            return make_response(jsonify({
                "success": False,
                "error": "Erreurs de validation",
                "errors": e.messages,
            }), 400)
        except ValueError as e:
            return make_response(jsonify({"success": False, "error": str(e)}), 400)
        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)
