from flask import Flask
import os
from flask_cors import CORS
from config import config, db_manager

def create_app():
    # Instancier l'app Flask
    app = Flask(__name__)

    # Déterminer le mode depuis l'environnement
    config_name = os.getenv('FLASK_ENV', 'development')
    if config_name not in config:
        config_name = 'development'
    
    # Charger la configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Configuration CORS
    CORS(app, resources={
        r"/*": {
            "origins": app.config.get('CORS_ORIGINS', ["http://localhost:5173"]),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Authorization", "Content-Type", "X-Requested-With"]
        }
    })

    # Initialiser la base de données
    db_manager.init_app(app)
    
   # importation et enregistrement des blueprint
    from src.collaborateur import collab
    from src.mission import mission
    from src.manager import manager
    from src.customer import client

    app.register_blueprint(collab)
    app.register_blueprint(mission)
    app.register_blueprint(client)
    app.register_blueprint(manager)

    # config telechargement facture
    # BALANCES_FOLDER = 'Balance'
    # app.config['BALANCES_FOLDER'] = BALANCES_FOLDER

    # if not os.path.exists(BALANCES_FOLDER):
    #     os.makedirs(BALANCES_FOLDER)

    return app, model