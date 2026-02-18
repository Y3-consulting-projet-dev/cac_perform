"""
Application principale CAC Perform
Architecture moderne avec gestion centralisée des routes, configuration et erreurs
"""

from flask import Flask
import os
import json
from pprint import pprint
import logging

# Configuration et extensions
from config import config
from extensions import init_extensions

# Utilitaires
from src.utils.json_encoder import MongoJSONEncoder
from src.utils.error_handlers import register_error_handlers
from src.routes import register_routes


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """
    Factory pour créer l'application Flask
    
    Args:
        config_name: Nom de la configuration à utiliser ('development', 'production', 'testing')
        
    Returns:
        tuple: (app, config_name) - Instance Flask et nom de configuration utilisée
    """
    
    # Créer l'instance Flask
    app = Flask(__name__)
    
    # Déterminer la configuration à utiliser
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    if config_name not in config:
        logger.warning(f"Configuration '{config_name}' non trouvée, utilisation de 'development'")
        config_name = 'development'
    
    # Charger la configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Configurer l'encodeur JSON personnalisé
    # Configuration de l'encodeur JSON pour Flask moderne
    from flask.json.provider import DefaultJSONProvider
    
    class MongoJSONProvider(DefaultJSONProvider):
        def dumps(self, obj, **kwargs):
            return json.dumps(obj, cls=MongoJSONEncoder, **kwargs)
        
        def loads(self, s):
            return json.loads(s)
    
    app.json = MongoJSONProvider(app)
    
    # Afficher les informations de configuration
    print_config_info(app, config_name)
    
    # Initialiser les extensions (CORS, base de données, etc.)
    init_extensions(app)
    
    # Enregistrer les gestionnaires d'erreurs
    register_error_handlers(app)
    
    # Enregistrer toutes les routes
    register_routes(app)
    
    # Afficher les routes disponibles en mode debug
    if app.debug:
        print_routes_info(app)
    
    logger.info(f"✅ Application CAC Perform créée avec la configuration '{config_name}'")
    
    return app, config_name


def print_config_info(app, config_name):
    """
    Affiche les informations de configuration au démarrage
    
    Args:
        app: Instance Flask
        config_name: Nom de la configuration
    """
    print("=" * 70)
    print("🚀 CAC PERFORM API - DÉMARRAGE")
    print("=" * 70)
    print(f"📋 Configuration: {config_name.upper()}")
    print(f"🐛 Debug: {'✅ Activé' if app.debug else '❌ Désactivé'}")
    print(f"🌍 Environnement: {app.config.get('ENV', 'unknown')}")
    
    # Configuration base de données
    print("\n📊 Configuration Base de Données:")
    print(f"   Host: {app.config.get('MONGO_HOST', 'Non configuré')}")
    print(f"   Port: {app.config.get('MONGO_PORT', 'Non configuré')}")
    print(f"   Base: {app.config.get('MONGO_DB_NAME', 'Non configuré')}")
    print(f"   Auth: {'✅ Configurée' if app.config.get('MONGO_USERNAME') else '❌ Aucune'}")
    
    # Configuration CORS
    print("\n🌐 Configuration CORS:")
    origins = app.config.get('CORS_ORIGINS', [])
    if isinstance(origins, str):
        origins = origins.split(',')
    for origin in origins:
        print(f"   - {origin.strip()}")
    
    # Configuration sécurité
    print("\n🔐 Configuration Sécurité:")
    print(f"   Secret Key: {'✅ Configurée' if app.config.get('SECRET_KEY') else '❌ Manquante'}")
    
    print("=" * 70)


def print_routes_info(app):
    """
    Affiche toutes les routes disponibles en mode debug
    
    Args:
        app: Instance Flask
    """
    print("\n📍 ROUTES DISPONIBLES:")
    print("-" * 50)
    
    routes = []
    for rule in app.url_map.iter_rules():
        methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        routes.append((rule.rule, methods, rule.endpoint))
    
    # Trier par URL
    routes.sort(key=lambda x: x[0])
    
    # Grouper par préfixe
    current_prefix = ""
    for route, methods, endpoint in routes:
        # Déterminer le préfixe
        parts = route.split('/')
        if len(parts) > 2:
            prefix = '/' + parts[1]
            if parts[2]:
                prefix += '/' + parts[2]
        else:
            prefix = "/"
        
        # Afficher le groupe si nouveau préfixe
        if prefix != current_prefix:
            current_prefix = prefix
            print(f"\n📁 {prefix}")
        
        # Afficher la route
        print(f"   {methods:<20} {route}")
    
    print("-" * 50)
    print(f"📊 Total: {len(routes)} routes enregistrées\n")


def run_app():
    """
    Lance l'application Flask
    """
    # Créer l'application
    app, config_name = create_app()
    
    # Configuration du serveur
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = config_name == 'development'
    
    print(f"🌐 Serveur démarré sur http://{host}:{port}")
    print(f"🔧 Mode: {'Développement' if debug else 'Production'}")
    
    if debug:
        print("💡 Conseils de développement:")
        print("   - API moderne: http://localhost:5000/api/v1/clients/")
        print("   - API legacy: http://localhost:5000/cors/client/afficher_clients/")
        print("   - Santé: http://localhost:5000/health")
        print("   - Info: http://localhost:5000/api/info")
    
    print("=" * 70)
    
    try:
        # Lancer le serveur
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Arrêt du serveur CAC Perform")
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
        raise


if __name__ == '__main__':
    run_app()