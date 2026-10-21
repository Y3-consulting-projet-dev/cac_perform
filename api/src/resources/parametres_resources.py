"""
Contrôleur HTTP des paramètres communs (page C, maquette
docs/maquettes/7_Parametres.html). CONSULTATION SEULE : une route GET,
aucune route d'écriture tant qu'il n'y a pas d'authentification.
"""
from flask import jsonify, make_response

from src.services import parametres_service


class ParametresResource:
    """Contrôleur pour /api/v1/parametres"""

    @staticmethod
    def lire():
        """GET /api/v1/parametres — réglages utilisés par le code, avec leur source."""
        try:
            return make_response(jsonify({"success": True, "data": parametres_service.lire_parametres()}), 200)
        except Exception as e:
            return make_response(jsonify({"success": False, "error": f"Erreur serveur: {e}"}), 500)
