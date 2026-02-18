"""
Extensions Flask pour l'application CAC Perform
Centralise l'initialisation de toutes les extensions
"""

from flask_cors import CORS
from config import db_manager

# Instance globale de CORS
cors = CORS()

# Instance globale du gestionnaire de base de données (déjà définie dans config.py)
# db_manager est importé depuis config.py

def init_extensions(app):
    """
    Initialise toutes les extensions Flask
    
    Args:
        app: Instance de l'application Flask
    """
    
    # Configuration CORS complète
    cors.init_app(app, 
        resources={
            r"/*": {
                "origins": app.config.get('CORS_ORIGINS', ["http://localhost:5173"]),
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": [
                    "Content-Type", 
                    "Authorization", 
                    "Accept",
                    "X-Requested-With",
                    "Cache-Control"
                ],
                "expose_headers": [
                    "Content-Disposition", 
                    "Content-Type",
                    "X-Total-Count"
                ],
                "supports_credentials": True,
                "max_age": 3600
            }
        }
    )
    
    # Initialiser le gestionnaire de base de données
    db_manager.init_app(app)
    
    print("✅ Extensions initialisées avec succès")
