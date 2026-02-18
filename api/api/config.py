"""
Configuration centralisée pour l'application CAC Perform
Gère les paramètres d'environnement, la base de données et autres configurations
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Config:
    """Configuration de base"""
    
    # Configuration Flask
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Configuration MongoDB
    MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
    MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'cac_perform')
    MONGO_USERNAME = os.getenv('MONGO_USERNAME')
    MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
    MONGO_AUTH_SOURCE = os.getenv('MONGO_AUTH_SOURCE', 'admin')
    MONGO_CONNECT_TIMEOUT_MS = int(os.getenv('MONGO_CONNECT_TIMEOUT_MS', 5000))
    MONGO_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv('MONGO_SERVER_SELECTION_TIMEOUT_MS', 5000))
    
    # Configuration de l'application
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    
    # Configuration CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
    
    @property
    def MONGO_URI(self):
        """Construit l'URI MongoDB selon la configuration"""
        if self.MONGO_USERNAME and self.MONGO_PASSWORD:
            return f"mongodb://{self.MONGO_USERNAME}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DB_NAME}?authSource={self.MONGO_AUTH_SOURCE}"
        else:
            return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DB_NAME}"
    
    @classmethod
    def init_app(cls, app):
        """Initialise la configuration de l'application"""
        pass


class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    
    DEBUG = True
    ENV = 'development'
    
    # Configuration MongoDB pour le développement
    MONGO_HOST = "localhost"
    MONGO_PORT = 27017
    MONGO_DB_NAME = "cac_perform"
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        logger.info("🔧 Configuration de développement chargée")


class ProductionConfig(Config):
    """Configuration pour la production"""
    
    ENV = 'production'
    DEBUG = False
    
    # Configuration MongoDB pour la production (depuis les variables d'environnement)
    SECRET_KEY = os.getenv('SECRET_KEY')
    MONGO_HOST = os.getenv('MONGO_HOST')
    MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')
    MONGO_USERNAME = os.getenv('MONGO_USERNAME')
    MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Vérifier que les variables critiques sont définies
        required_vars = ['SECRET_KEY', 'MONGO_HOST', 'MONGO_DB_NAME']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
        
        logger.info("🚀 Configuration de production chargée")


class TestingConfig(Config):
    """Configuration pour les tests"""
    
    TESTING = True
    DEBUG = True
    ENV = 'testing'
    
    # Base de données de test séparée
    MONGO_DB_NAME = "cac_perform_test"
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        logger.info("🧪 Configuration de test chargée")


# Dictionnaire des configurations disponibles
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


class DatabaseManager:
    """Gestionnaire centralisé de la base de données MongoDB"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.config = None
        self._is_connected = False
    
    def init_app(self, app):
        """Initialise la connexion à la base de données avec l'application Flask"""
        self.config = app.config
        self.connect()
        
        # Ajouter le gestionnaire de base de données à l'application
        app.db_manager = self
        
        # Hook pour fermer la connexion à l'arrêt de l'application
        @app.teardown_appcontext
        def close_db(error):
            if error:
                logger.error(f"Erreur dans l'application: {error}")
    
    def connect(self):
        """Établit la connexion à MongoDB"""
        try:
            # Configuration de la connexion
            connection_params = {
                'host': self.config['MONGO_HOST'],
                'port': self.config['MONGO_PORT'],
                'connectTimeoutMS': self.config.get('MONGO_CONNECT_TIMEOUT_MS', 5000),
                'serverSelectionTimeoutMS': self.config.get('MONGO_SERVER_SELECTION_TIMEOUT_MS', 5000),
            }
            
            # Ajouter l'authentification si configurée
            if self.config.get('MONGO_USERNAME') and self.config.get('MONGO_PASSWORD'):
                connection_params.update({
                    'username': self.config['MONGO_USERNAME'],
                    'password': self.config['MONGO_PASSWORD'],
                    'authSource': self.config.get('MONGO_AUTH_SOURCE', 'admin')
                })
            
            # Créer la connexion
            self.client = MongoClient(**connection_params)
            
            # Tester la connexion
            self.client.server_info()
            
            # Sélectionner la base de données
            self.db = self.client[self.config['MONGO_DB_NAME']]
            
            self._is_connected = True
            logger.info(f"✅ Connexion MongoDB établie: {self.config['MONGO_HOST']}:{self.config['MONGO_PORT']}/{self.config['MONGO_DB_NAME']}")
            
            # Initialiser les collections si nécessaire
            self._init_collections()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ Erreur de connexion MongoDB: {e}")
            self._is_connected = False
            raise
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors de la connexion: {e}")
            self._is_connected = False
            raise
    
    def _init_collections(self):
        """Initialise les collections si elles n'existent pas"""
        try:
            collections_info = {
                'Client': 'docs/client_test.json',
                'Mission1': 'docs/mission_test.json',
                'Balance': 'docs/balance_test.json',
                'Manager': None,
                'Collaborateur': None
            }
            
            existing_collections = self.db.list_collection_names()
            
            if not existing_collections:
                logger.info("🔧 Initialisation des collections...")
                
                for collection_name, json_file in collections_info.items():
                    if collection_name not in existing_collections:
                        collection = self.db[collection_name]
                        
                        if json_file:
                            # Charger les données depuis le fichier JSON si disponible
                            self._load_collection_from_json(collection, json_file)
                        else:
                            # Créer une collection vide
                            collection.insert_one({"_init": True})
                            collection.delete_one({"_init": True})
                            logger.info(f"📁 Collection '{collection_name}' créée (vide)")
                
                logger.info("✅ Collections initialisées")
            else:
                logger.info(f"📚 Collections existantes: {existing_collections}")
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de l'initialisation des collections: {e}")
    
    def _load_collection_from_json(self, collection, json_file):
        """Charge une collection depuis un fichier JSON"""
        try:
            import json
            from bson import ObjectId
            
            json_path = os.path.join(os.path.dirname(__file__), json_file)
            
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if isinstance(data, dict):
                        data = [data]
                    
                    # Convertir les ObjectId si nécessaire
                    for doc in data:
                        if "_id" in doc and isinstance(doc["_id"], dict) and "$oid" in doc["_id"]:
                            doc["_id"] = ObjectId(doc["_id"]["$oid"])
                    
                    if data:
                        collection.insert_many(data)
                        logger.info(f"📁 Collection '{collection.name}' créée avec {len(data)} document(s)")
            else:
                logger.warning(f"⚠️ Fichier JSON non trouvé: {json_path}")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement de {json_file}: {e}")
    
    def get_db(self):
        """Retourne l'instance de la base de données"""
        # Vérifier si la connexion est active
        if not self._is_connected or self.db is None:
            # Essayer de reconnecter si la configuration est disponible
            if self.config is not None:
                try:
                    logger.warning("⚠️ Connexion perdue, tentative de reconnexion...")
                    self.connect()
                    logger.info("✅ Reconnexion réussie")
                except Exception as e:
                    logger.error(f"❌ Échec de la reconnexion: {e}")
                    raise RuntimeError("Base de données non connectée. Appelez connect() d'abord.")
            else:
                raise RuntimeError("Base de données non connectée. Appelez connect() d'abord.")
        return self.db
    
    def get_collection(self, name):
        """Retourne une collection spécifique"""
        return self.get_db()[name]
    
    def is_connected(self):
        """Vérifie si la connexion est active"""
        try:
            if self.client and self._is_connected:
                self.client.server_info()
                return True
        except:
            self._is_connected = False
        return False
    
    def close(self):
        """Ferme la connexion à la base de données"""
        if self.client:
            self.client.close()
            self._is_connected = False
            logger.info("🔌 Connexion MongoDB fermée")
    
    def get_stats(self):
        """Retourne des statistiques sur la base de données"""
        if not self.is_connected():
            return {"error": "Base de données non connectée"}
        
        try:
            db = self.get_db()
            collections = db.list_collection_names()
            
            stats = {
                "database": self.config['MONGO_DB_NAME'],
                "collections": len(collections),
                "details": {}
            }
            
            for collection_name in collections:
                count = db[collection_name].count_documents({})
                stats["details"][collection_name] = count
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return {"error": str(e)}


# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()


def get_db():
    """Fonction utilitaire pour obtenir la base de données"""
    return db_manager.get_db()


def get_collection(name):
    """Fonction utilitaire pour obtenir une collection"""
    return db_manager.get_collection(name)