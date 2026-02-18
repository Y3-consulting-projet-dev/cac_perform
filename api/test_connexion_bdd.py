#!/usr/bin/env python3
"""
Script simple pour tester la connexion à MongoDB et afficher des informations de base
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient

# Configuration
MONGO_HOST = "localhost"
MONGO_PORT = 27017
DB_NAME = "cac_perform"

def test_connexion():
    """Teste la connexion à MongoDB"""
    print("🔌 Test de connexion à MongoDB...")
    print(f"   Host: {MONGO_HOST}:{MONGO_PORT}")
    print(f"   Base: {DB_NAME}")
    print("-" * 60)
    
    try:
        # Connexion
        client = MongoClient(
            f'mongodb://{MONGO_HOST}:{MONGO_PORT}/',
            serverSelectionTimeoutMS=5000
        )
        
        # Test de connexion
        client.server_info()
        print("✅ Connexion réussie!")
        
        # Accès à la base
        db = client[DB_NAME]
        
        # Lister les collections (vérifier que la base existe)
        if db is None:
            print("❌ Impossible d'accéder à la base de données")
            return False
        
        collections = db.list_collection_names()
        print(f"\n📚 Collections disponibles ({len(collections)}):")
        for col in collections:
            count = db[col].count_documents({})
            print(f"   - {col}: {count} document(s)")
        
        # Afficher quelques statistiques
        print("\n📊 Statistiques rapides:")
        print(f"   Clients: {db.Client.count_documents({})}")
        print(f"   Missions: {db.Mission1.count_documents({})}")
        print(f"   Balances: {db.Balance.count_documents({})}")
        
        client.close()
        print("\n✅ Test terminé avec succès!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur de connexion: {e}")
        print("\n💡 Vérifications:")
        print("   1. MongoDB est-il démarré?")
        print("   2. Le port 27017 est-il accessible?")
        print("   3. La configuration est-elle correcte?")
        return False

if __name__ == "__main__":
    test_connexion()

