"""
Contrôleurs HTTP des courriers de circularisation, sous-lot b
(docs/PLAN_circularisation.md) : annuaire des coordonnées, bibliothèque de
modèles Word. Génération et envoi : pas encore de route.
"""
from io import BytesIO

from flask import request, jsonify, make_response, send_file

from src.services import courriers_service


def _executer(action, code=200):
    """Même convention que circularisation_resources : règle -> 400, reste -> 500."""
    try:
        return make_response(jsonify({"success": True, "data": action()}), code)
    except ValueError as e:
        return make_response(jsonify({"success": False, "error": str(e)}), 400)
    except Exception as e:
        return make_response(jsonify({"success": False, "error": f"Erreur serveur: {str(e)}"}), 500)


class CourriersResource:
    """Contrôleur pour /api/v1/missions/<id>/courriers[...]"""

    @staticmethod
    def lire(mission_id):
        return _executer(lambda: courriers_service.lire_courriers(mission_id))

    @staticmethod
    def enregistrer_coordonnees(mission_id):
        def action():
            corps = request.get_json(silent=True)
            if not isinstance(corps, dict):
                raise ValueError("Corps de la requête illisible : JSON UTF-8 attendu.")
            return courriers_service.enregistrer_coordonnees(
                mission_id, str(corps.get("type_tiers") or ""), str(corps.get("numero") or ""), corps,
                corps.get("utilisateur_id"))
        return _executer(action)

    @staticmethod
    def importer_modele(mission_id):
        def action():
            fichier = request.files.get("fichier")
            if not fichier:
                raise ValueError("Aucun fichier reçu.")
            return courriers_service.importer_modele(
                mission_id, request.form.get("code", ""), fichier.filename, fichier.read(),
                request.form.get("utilisateur_id"))
        return _executer(action, 201)

    @staticmethod
    def telecharger_modele(mission_id, modele_id):
        try:
            fichier = courriers_service.lire_fichier_modele(modele_id)
        except ValueError as e:
            return make_response(jsonify({"success": False, "error": str(e)}), 404)
        return send_file(BytesIO(fichier["contenu"]), as_attachment=True, download_name=fichier["nom_fichier"],
                         mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
