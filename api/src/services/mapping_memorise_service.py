"""
Service de mapping mémorisé par client et logiciel comptable.
Nouveau périmètre V2 — voir docs/PLAN_import_refonte.md §2.

Collection dédiée `MappingImport` (distincte de Client_db et Balance). Un
mapping est identifié par (id_client, logiciel_comptable) et VERSIONNÉ :
chaque sauvegarde crée une nouvelle version plutôt que d'écraser la
précédente, pour la traçabilité. `recuperer_mapping` renvoie toujours la
dernière version.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.utils.database import get_database


def _collection():
    db = get_database()
    return db["MappingImport"]


def enregistrer_mapping(id_client: str, logiciel_comptable: str, mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Crée une nouvelle version du mapping pour (id_client, logiciel_comptable)."""
    collection = _collection()

    derniere_version = collection.find_one(
        {"id_client": id_client, "logiciel_comptable": logiciel_comptable},
        sort=[("version", -1)],
    )
    nouvelle_version = (derniere_version["version"] + 1) if derniere_version else 1

    document = {
        "id_client": id_client,
        "logiciel_comptable": logiciel_comptable,
        "mapping": mapping,
        "version": nouvelle_version,
        "created_at": datetime.utcnow().isoformat(),
    }
    result = collection.insert_one(document)
    document["_id"] = str(result.inserted_id)
    return document


def recuperer_mapping(id_client: str, logiciel_comptable: str) -> Optional[Dict[str, Any]]:
    """Retourne la dernière version mémorisée pour ce couple, ou None si aucune n'existe."""
    collection = _collection()
    document = collection.find_one(
        {"id_client": id_client, "logiciel_comptable": logiciel_comptable},
        sort=[("version", -1)],
    )
    if document:
        document["_id"] = str(document["_id"])
    return document


def lister_historique_mapping(id_client: str, logiciel_comptable: str) -> List[Dict[str, Any]]:
    """Retourne toutes les versions mémorisées pour ce couple, de la plus récente à la plus ancienne."""
    collection = _collection()
    documents = list(
        collection.find({"id_client": id_client, "logiciel_comptable": logiciel_comptable}).sort("version", -1)
    )
    for doc in documents:
        doc["_id"] = str(doc["_id"])
    return documents
