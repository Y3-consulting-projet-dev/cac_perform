"""
Encodeur JSON personnalisé pour les types MongoDB et autres objets spéciaux
"""

import json
from bson import ObjectId
from bson.timestamp import Timestamp
from datetime import datetime, date
import decimal


class MongoJSONEncoder(json.JSONEncoder):
    """
    Encodeur JSON personnalisé qui gère les types MongoDB et autres objets Python
    """
    
    def default(self, obj):
        """
        Convertit les objets Python en types JSON sérialisables
        
        Args:
            obj: Objet à sérialiser
            
        Returns:
            Représentation JSON sérialisable de l'objet
        """
        
        # ObjectId MongoDB
        if isinstance(obj, ObjectId):
            return str(obj)
        
        # Timestamp MongoDB
        elif isinstance(obj, Timestamp):
            return obj.time
        
        # DateTime Python
        elif isinstance(obj, datetime):
            return obj.isoformat()
        
        # Date Python
        elif isinstance(obj, date):
            return obj.isoformat()
        
        # Decimal Python
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        
        # Set Python
        elif isinstance(obj, set):
            return list(obj)
        
        # Bytes Python
        elif isinstance(obj, bytes):
            try:
                return obj.decode('utf-8')
            except UnicodeDecodeError:
                return obj.hex()
        
        # Fallback vers l'encodeur parent
        return super().default(obj)
