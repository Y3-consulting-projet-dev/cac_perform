#!/usr/bin/env python3
"""
Script pour vérifier que les données sont bien sauvegardées dans MongoDB
et visibles dans MongoDB Compass
"""

from pymongo import MongoClient
from bson import ObjectId
import sys

def verifier_donnees():
    """Vérifie les données dans la base MongoDB"""
    
    print("=" * 70)
    print("🔍 VÉRIFICATION DES DONNÉES DANS MONGODB")
    print("=" * 70)
    
    try:
        # Connexion directe à MongoDB (même configuration que l'app)
        client = MongoClient('mongodb://localhost:27017/')
        db_name = 'cac_perform'
        db = client[db_name]
        
        print(f"\n📊 Base de données utilisée: {db_name}")
        print(f"📍 Connexion: mongodb://localhost:27017/")
        
        # Lister toutes les bases de données
        print(f"\n📋 Bases de données disponibles:")
        for db_name_available in client.list_database_names():
            print(f"   - {db_name_available}")
        
        # Vérifier les collections dans cac_perform
        print(f"\n📁 Collections dans '{db_name}':")
        collections = db.list_collection_names()
        for coll_name in collections:
            count = db[coll_name].count_documents({})
            print(f"   - {coll_name}: {count} document(s)")
        
        # Vérifier les clients
        print(f"\n👥 CLIENTS:")
        clients = list(db.Client.find({}).limit(10))
        print(f"   Total: {db.Client.count_documents({})} client(s)")
        if clients:
            print(f"   Derniers clients créés:")
            for i, client in enumerate(clients[:5], 1):
                print(f"   {i}. ID: {client['_id']}")
                print(f"      Nom: {client.get('nom', 'N/A')}")
                print(f"      Activité: {client.get('activite', 'N/A')}")
        else:
            print(f"   ⚠️  Aucun client trouvé!")
        
        # Vérifier les missions
        print(f"\n📋 MISSIONS:")
        missions = list(db.Mission1.find({}).sort('_id', -1).limit(10))
        print(f"   Total: {db.Mission1.count_documents({})} mission(s)")
        if missions:
            print(f"   Dernières missions créées:")
            for i, mission in enumerate(missions[:5], 1):
                print(f"   {i}. ID: {mission['_id']}")
                print(f"      ID Client: {mission.get('id_client', 'N/A')}")
                print(f"      Année auditée: {mission.get('annee_auditee', 'N/A')}")
                print(f"      Balances: {len(mission.get('balances', []))}")
        else:
            print(f"   ⚠️  Aucune mission trouvée!")
        
        # Vérifier les balances
        print(f"\n💰 BALANCES:")
        balances = list(db.Balance.find({}).sort('_id', -1).limit(10))
        print(f"   Total: {db.Balance.count_documents({})} balance(s)")
        if balances:
            print(f"   Dernières balances créées:")
            for i, balance in enumerate(balances[:5], 1):
                print(f"   {i}. ID: {balance['_id']}")
                print(f"      Année: {balance.get('annee_balance', balance.get('periode', 'N/A'))}")
                print(f"      Lignes: {len(balance.get('balance', []))}")
        else:
            print(f"   ⚠️  Aucune balance trouvée!")
        
        print(f"\n" + "=" * 70)
        print("💡 POUR VÉRIFIER DANS MONGODB COMPASS:")
        print("=" * 70)
        print(f"1. Connectez-vous à: mongodb://localhost:27017/")
        print(f"2. Sélectionnez la base de données: {db_name}")
        print(f"3. Vérifiez les collections: Client, Mission1, Balance")
        print(f"4. Si vous ne voyez pas les données, vérifiez:")
        print(f"   - Que vous êtes connecté à la même instance MongoDB")
        print(f"   - Que vous regardez la bonne base de données ({db_name})")
        print(f"   - Que MongoDB Compass est à jour (rafraîchir avec F5)")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    verifier_donnees()

