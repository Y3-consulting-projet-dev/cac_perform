#!/usr/bin/env python3
"""
Script interactif pour accéder à la base de données MongoDB
Permet de lister, rechercher et modifier les données
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

# Configuration MongoDB (développement par défaut)
MONGO_HOST = "localhost"
MONGO_PORT = 27017
DB_NAME = "cac_perform"

def connect_db():
    """Établit une connexion à MongoDB"""
    try:
        client = MongoClient(f'mongodb://{MONGO_HOST}:{MONGO_PORT}/', serverSelectionTimeoutMS=5000)
        client.server_info()  # Test de connexion
        db = client[DB_NAME]
        print(f"✅ Connexion réussie à MongoDB")
        print(f"   Host: {MONGO_HOST}:{MONGO_PORT}")
        print(f"   Base de données: {DB_NAME}")
        return client, db
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print(f"   Vérifiez que MongoDB est bien démarré")
        return None, None

def afficher_statistiques(db):
    """Affiche des statistiques sur la base de données"""
    print("\n" + "=" * 80)
    print("📊 STATISTIQUES DE LA BASE DE DONNÉES")
    print("=" * 80)
    
    collections = db.list_collection_names()
    print(f"\n📋 Collections disponibles ({len(collections)}):")
    for col in collections:
        count = db[col].count_documents({})
        print(f"   - {col}: {count} document(s)")

def lister_clients(db):
    """Liste tous les clients"""
    print("\n" + "=" * 80)
    print("👤 LISTE DES CLIENTS")
    print("=" * 80)
    
    clients = list(db.Client.find({}).sort("_id", -1))
    
    if not clients:
        print("   Aucun client trouvé")
        return
    
    for idx, client in enumerate(clients, 1):
        client_id = str(client['_id'])
        nom = client.get('nom', 'Sans nom')
        activite = client.get('activite', 'N/A')
        
        # Compter les missions
        missions_count = db.Mission1.count_documents({"id_client": client_id})
        
        print(f"\n{idx}. {nom}")
        print(f"   ID: {client_id}")
        print(f"   Activité: {activite}")
        print(f"   Missions: {missions_count}")

def lister_missions(db, client_id=None):
    """Liste les missions"""
    print("\n" + "=" * 80)
    print("📋 LISTE DES MISSIONS")
    print("=" * 80)
    
    query = {"id_client": client_id} if client_id else {}
    missions = list(db.Mission1.find(query).sort("_id", -1))
    
    if not missions:
        print(f"   Aucune mission trouvée" + (f" pour le client {client_id}" if client_id else ""))
        return
    
    for idx, mission in enumerate(missions, 1):
        mission_id = str(mission['_id'])
        id_client = mission.get('id_client', 'N/A')
        annee = mission.get('annee_auditee', 'N/A')
        date_debut = mission.get('date_debut', 'N/A')
        date_fin = mission.get('date_fin', 'N/A')
        balances = mission.get('balances', [])
        
        print(f"\n{idx}. Mission ID: {mission_id}")
        print(f"   Client ID: {id_client}")
        print(f"   Année: {annee}")
        print(f"   Période: {date_debut} → {date_fin}")
        print(f"   Balances: {len(balances)}")

def lister_balances(db):
    """Liste toutes les balances"""
    print("\n" + "=" * 80)
    print("💰 LISTE DES BALANCES")
    print("=" * 80)
    
    balances = list(db.Balance.find({}).sort("_id", -1).limit(20))
    
    if not balances:
        print("   Aucune balance trouvée")
        return
    
    for idx, balance in enumerate(balances, 1):
        balance_id = str(balance['_id'])
        id_client = balance.get('id_client', 'N/A')
        annee = balance.get('annee_balance', balance.get('periode', 'N/A'))
        balance_data = balance.get('balance', [])
        
        print(f"\n{idx}. Balance ID: {balance_id}")
        print(f"   Client ID: {id_client}")
        print(f"   Année: {annee}")
        print(f"   Nombre de lignes: {len(balance_data)}")

def menu_principal():
    """Affiche le menu principal"""
    print("\n" + "=" * 80)
    print("📚 MENU PRINCIPAL - ACCÈS BASE DE DONNÉES")
    print("=" * 80)
    print("1. Afficher les statistiques")
    print("2. Lister tous les clients")
    print("3. Lister toutes les missions")
    print("4. Lister les missions d'un client")
    print("5. Lister les balances")
    print("6. Rechercher une mission par ID")
    print("7. Rechercher un client par ID")
    print("8. Quitter")
    print("=" * 80)

def rechercher_mission(db, mission_id):
    """Recherche une mission par ID"""
    print("\n" + "=" * 80)
    print(f"🔍 RECHERCHE MISSION: {mission_id}")
    print("=" * 80)
    
    try:
        mission = db.Mission1.find_one({"_id": ObjectId(mission_id)})
        
        if not mission:
            print("❌ Mission non trouvée")
            return
        
        print(f"✅ Mission trouvée:")
        print(f"   ID: {mission_id}")
        print(f"   Client ID: {mission.get('id_client', 'N/A')}")
        print(f"   Année: {mission.get('annee_auditee', 'N/A')}")
        print(f"   Date début: {mission.get('date_debut', 'N/A')}")
        print(f"   Date fin: {mission.get('date_fin', 'N/A')}")
        print(f"   Balances: {len(mission.get('balances', []))}")
        print(f"   Contrôle intangibilité: {'Oui' if mission.get('controle_intangibilite') else 'Non'}")
        print(f"   Matérialité: {'Oui' if mission.get('materiality') else 'Non'}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def rechercher_client(db, client_id):
    """Recherche un client par ID"""
    print("\n" + "=" * 80)
    print(f"🔍 RECHERCHE CLIENT: {client_id}")
    print("=" * 80)
    
    try:
        client = db.Client.find_one({"_id": ObjectId(client_id)})
        
        if not client:
            print("❌ Client non trouvé")
            return
        
        print(f"✅ Client trouvé:")
        print(f"   ID: {client_id}")
        print(f"   Nom: {client.get('nom', 'N/A')}")
        print(f"   Activité: {client.get('activite', 'N/A')}")
        print(f"   Adresse: {client.get('adresse', 'N/A')}")
        print(f"   Forme juridique: {client.get('forme_juridique', 'N/A')}")
        
        # Lister les missions du client
        missions = list(db.Mission1.find({"id_client": client_id}))
        print(f"\n   Missions associées: {len(missions)}")
        for mission in missions:
            print(f"      - {mission.get('annee_auditee', 'N/A')} ({str(mission['_id'])})")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    """Fonction principale"""
    print("🔌 Connexion à MongoDB...")
    client, db = connect_db()
    
    if client is None or db is None:
        return
    
    while True:
        menu_principal()
        choix = input("\nVotre choix: ").strip()
        
        if choix == "1":
            afficher_statistiques(db)
        elif choix == "2":
            lister_clients(db)
        elif choix == "3":
            lister_missions(db)
        elif choix == "4":
            client_id = input("ID du client: ").strip()
            lister_missions(db, client_id)
        elif choix == "5":
            lister_balances(db)
        elif choix == "6":
            mission_id = input("ID de la mission: ").strip()
            rechercher_mission(db, mission_id)
        elif choix == "7":
            client_id = input("ID du client: ").strip()
            rechercher_client(db, client_id)
        elif choix == "8":
            print("\n👋 Au revoir!")
            break
        else:
            print("❌ Choix invalide")
        
        input("\nAppuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interruption - Au revoir!")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

