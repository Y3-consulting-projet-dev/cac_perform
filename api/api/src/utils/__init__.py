"""
Utilitaires pour l'application CAC Perform
"""

from .database import (
    get_database,
    get_mongo_collection,
    check_connection,
    get_database_stats,
    ensure_connection,
    get_client_collection,
    get_mission_collection,
    get_balance_collection,
    get_manager_collection,
    get_collaborateur_collection,
    get_db_legacy
)

__all__ = [
    'get_database',
    'get_mongo_collection',
    'check_connection',
    'get_database_stats',
    'ensure_connection',
    'get_client_collection',
    'get_mission_collection',
    'get_balance_collection',
    'get_manager_collection',
    'get_collaborateur_collection',
    'get_db_legacy'
]
