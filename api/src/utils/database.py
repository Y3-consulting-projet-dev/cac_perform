"""
Utilitaires pour la base de données
Module centralisé pour l'accès à MongoDB
"""

from config import db_manager, get_db, get_collection
from pymongo.errors import PyMongoError
import logging

logger = logging.getLogger(__name__)


def get_database():
    """
    Retourne l'instance de la base de données MongoDB
    Tente de reconnecter automatiquement si la connexion est perdue
    
    Returns:
        Database: Instance de la base de données MongoDB
        
    Raises:
        RuntimeError: Si la base de données n'est pas connectée et ne peut pas être reconnectée
    """
    try:
        db = get_db()
        
        # Sécurité supplémentaire : certaines exécutions legacy renvoyaient None
        # au lieu de lever une exception, ce qui provoquait ensuite un
        # "'NoneType' object has no attribute 'Mission1'" lors de l'accès.
        if db is None:
            logger.warning("⚠️ get_db() a renvoyé None, tentative de reconnexion...")
            ensure_connection()
            db = get_db()
            if db is None:
                raise RuntimeError("Base de données non connectée (get_db a renvoyé None)")
        
        return db
    except RuntimeError as e:
        logger.warning(f"⚠️ Connexion perdue, tentative de reconnexion automatique...")
        # Essayer de reconnecter via ensure_connection
        try:
            ensure_connection()
            return get_db()
        except Exception as reconnect_error:
            logger.error(f"❌ Erreur d'accès à la base de données: {e}")
            logger.error(f"❌ Échec de la reconnexion: {reconnect_error}")
            raise RuntimeError(f"Base de données non connectée: {e}") from reconnect_error


def get_mongo_collection(collection_name: str):
    """
    Retourne une collection MongoDB spécifique
    
    Args:
        collection_name: Nom de la collection
        
    Returns:
        Collection: Instance de la collection MongoDB
    """
    try:
        return get_collection(collection_name)
    except Exception as e:
        logger.error(f"Erreur d'accès à la collection {collection_name}: {e}")
        raise


def check_connection():
    """
    Vérifie si la connexion à la base de données est active
    
    Returns:
        bool: True si connecté, False sinon
    """
    return db_manager.is_connected()


def get_database_stats():
    """
    Retourne des statistiques sur la base de données
    
    Returns:
        dict: Statistiques de la base de données
    """
    return db_manager.get_stats()


def ensure_connection():
    """
    S'assure que la connexion à la base de données est active
    Reconnecte si nécessaire
    
    Raises:
        ConnectionError: Si impossible de se connecter
    """
    if not check_connection():
        try:
            db_manager.connect()
            logger.info("Reconnexion à la base de données réussie")
        except Exception as e:
            logger.error(f"Impossible de se reconnecter à la base de données: {e}")
            raise ConnectionError(f"Connexion à la base de données échouée: {e}")


# Alias pour la compatibilité avec l'ancien code
def get_client_collection():
    """Retourne la collection Client"""
    return get_mongo_collection('Client')


def get_mission_collection():
    """Retourne la collection Mission1"""
    return get_mongo_collection('Mission1')


def get_balance_collection():
    """Retourne la collection Balance"""
    return get_mongo_collection('Balance')


def get_manager_collection():
    """Retourne la collection Manager"""
    return get_mongo_collection('Manager')


def get_collaborateur_collection():
    """Retourne la collection Collaborateur"""
    return get_mongo_collection('Collaborateur')


# Fonction de compatibilité pour l'ancien code
def get_db_legacy():
    """
    Fonction de compatibilité pour l'ancien code qui utilisait directement 'db'
    
    Returns:
        Database: Instance de la base de données
    """
    return get_database()
