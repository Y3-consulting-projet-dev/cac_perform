"""
Gestionnaires d'erreurs centralisés pour l'application CAC Perform
"""

from flask import jsonify, current_app
from marshmallow import ValidationError
from pymongo.errors import PyMongoError
from bson.errors import InvalidId
import traceback
import logging

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """
    Enregistre tous les gestionnaires d'erreurs pour l'application
    
    Args:
        app: Instance de l'application Flask
    """
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Gère les erreurs de validation Marshmallow"""
        logger.warning(f"Erreur de validation: {error.messages}")
        
        return jsonify({
            "error": "Erreurs de validation",
            "message": "Les données fournies ne sont pas valides",
            "details": error.messages
        }), 400
    
    
    @app.errorhandler(PyMongoError)
    def handle_mongo_error(error):
        """Gère les erreurs MongoDB"""
        logger.error(f"Erreur MongoDB: {str(error)}")
        
        return jsonify({
            "error": "Erreur de base de données",
            "message": "Une erreur s'est produite lors de l'accès à la base de données",
            "details": str(error) if current_app.debug else "Erreur interne"
        }), 500
    
    
    @app.errorhandler(InvalidId)
    def handle_invalid_id_error(error):
        """Gère les erreurs d'ID MongoDB invalides"""
        logger.warning(f"ID MongoDB invalide: {str(error)}")
        
        return jsonify({
            "error": "ID invalide",
            "message": "L'identifiant fourni n'est pas valide",
            "details": str(error)
        }), 400
    
    
    @app.errorhandler(ValueError)
    def handle_value_error(error):
        """Gère les erreurs de valeur"""
        logger.warning(f"Erreur de valeur: {str(error)}")
        
        return jsonify({
            "error": "Valeur invalide",
            "message": str(error)
        }), 400
    
    
    @app.errorhandler(KeyError)
    def handle_key_error(error):
        """Gère les erreurs de clé manquante"""
        logger.warning(f"Clé manquante: {str(error)}")
        
        return jsonify({
            "error": "Paramètre manquant",
            "message": f"Le paramètre {str(error)} est requis"
        }), 400
    
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Gère les erreurs 404"""
        return jsonify({
            "error": "Ressource non trouvée",
            "message": "La ressource demandée n'existe pas"
        }), 404
    
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Gère les erreurs 405"""
        return jsonify({
            "error": "Méthode non autorisée",
            "message": "La méthode HTTP utilisée n'est pas autorisée pour cette ressource"
        }), 405
    
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Gère les erreurs internes du serveur"""
        logger.error(f"Erreur interne: {str(error)}")
        
        if current_app.debug:
            traceback.print_exc()
        
        return jsonify({
            "error": "Erreur interne du serveur",
            "message": "Une erreur inattendue s'est produite",
            "details": str(error) if current_app.debug else "Erreur interne"
        }), 500
    
    
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """Gestionnaire d'erreur générique pour toutes les autres exceptions"""
        logger.error(f"Erreur non gérée: {type(error).__name__}: {str(error)}")
        
        if current_app.debug:
            print(f"\n{'='*60}")
            print(f"❌ ERREUR NON GÉRÉE")
            print(f"{'='*60}")
            print(f"Type: {type(error).__name__}")
            print(f"Message: {str(error)}")
            traceback.print_exc()
            print(f"{'='*60}\n")
        
        return jsonify({
            "error": "Erreur inattendue",
            "message": "Une erreur inattendue s'est produite",
            "type": type(error).__name__,
            "details": str(error) if current_app.debug else "Erreur interne"
        }), 500
    
    
    # Gestionnaire pour les requêtes OPTIONS (CORS preflight)
    @app.before_request
    def handle_preflight():
        """Gère les requêtes OPTIONS pour CORS"""
        from flask import request
        
        if request.method == "OPTIONS":
            response = jsonify({"message": "OK"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "*")
            response.headers.add('Access-Control-Allow-Methods', "*")
            return response
    
    
    logger.info("✅ Gestionnaires d'erreurs enregistrés")
