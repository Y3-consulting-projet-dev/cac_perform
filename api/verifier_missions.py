#!/usr/bin/env python3
"""
Script pour vérifier que les missions sont bien sauvegardées et récupérées depuis MongoDB
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId

def verifier_missions():
    """Vérifie toutes les missions dans la base de données"""
    
    print("=" * 80)
    print("🔍 VÉRIFICATION DES MISSIONS DANS LA BASE DE DONNÉES")
    print("=" * 80)
    
    try:
        # Connexion à MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['cac_perform']
        
        # Compter toutes les missions
        total_missions = db.Mission1.count_documents({})
        print(f"\n📊 Total de missions dans la base: {total_missions}")
        
        if total_missions == 0:
            print("\n❌ Aucune mission trouvée dans la base de données")
            print("   Vérifiez que:")
            print("   - MongoDB est bien en cours d'exécution")
            print("   - Vous avez bien créé des missions via l'interface")
            print("   - Les missions ont bien été sauvegardées")
            return
        
        # Récupérer toutes les missions
        print(f"\n📋 Liste de toutes les missions:")
        print("-" * 80)
        
        missions = list(db.Mission1.find({}).sort("_id", -1))
        
        for idx, mission in enumerate(missions, 1):
            mission_id = str(mission['_id'])
            id_client = mission.get('id_client', 'NON DÉFINI')
            annee = mission.get('annee_auditee', 'N/A')
            date_debut = mission.get('date_debut', 'N/A')
            date_fin = mission.get('date_fin', 'N/A')
            balances = mission.get('balances', [])
            
            print(f"\n{idx}. Mission ID: {mission_id}")
            print(f"   - ID Client: {id_client}")
            print(f"   - Année auditée: {annee}")
            print(f"   - Date début: {date_debut}")
            print(f"   - Date fin: {date_fin}")
            print(f"   - Nombre de balances: {len(balances)}")
            
            # Vérifier que id_client existe
            if id_client == 'NON DÉFINI' or not id_client:
                print(f"   ⚠️  ATTENTION: id_client manquant ou invalide")
        
        # Vérifier les missions par client
        print(f"\n" + "=" * 80)
        print(f"📊 MISSIONS PAR CLIENT")
        print("=" * 80)
        
        # Récupérer tous les clients
        clients = list(db.Client.find({}))
        print(f"\n📋 Nombre de clients: {len(clients)}")
        
        for client in clients:
            client_id = str(client['_id'])
            client_nom = client.get('nom', 'Sans nom')
            
            # Chercher les missions de ce client
            missions_client = list(db.Mission1.find({"id_client": client_id}))
            
            print(f"\n👤 Client: {client_nom} (ID: {client_id})")
            print(f"   Missions trouvées: {len(missions_client)}")
            
            if len(missions_client) == 0:
                print(f"   ⚠️  Aucune mission trouvée pour ce client")
            else:
                for mission in missions_client:
                    mission_id = str(mission['_id'])
                    annee = mission.get('annee_auditee', 'N/A')
                    print(f"      - Mission {mission_id}: Année {annee}")
        
        # Vérifier les missions sans id_client
        print(f"\n" + "=" * 80)
        print(f"⚠️  MISSIONS SANS ID_CLIENT (PROBLÈME POTENTIEL)")
        print("=" * 80)
        
        missions_sans_client = list(db.Mission1.find({"id_client": {"$exists": False}}))
        missions_client_vide = list(db.Mission1.find({"id_client": ""}))
        missions_client_null = list(db.Mission1.find({"id_client": None}))
        
        total_problematiques = len(missions_sans_client) + len(missions_client_vide) + len(missions_client_null)
        
        if total_problematiques > 0:
            print(f"\n❌ {total_problematiques} mission(s) avec un id_client invalide:")
            print(f"   - Missions sans champ id_client: {len(missions_sans_client)}")
            print(f"   - Missions avec id_client vide: {len(missions_client_vide)}")
            print(f"   - Missions avec id_client None: {len(missions_client_null)}")
            print(f"\n   Ces missions ne seront PAS visibles dans l'interface client!")
            
            for mission in missions_sans_client + missions_client_vide + missions_client_null:
                mission_id = str(mission['_id'])
                print(f"   - Mission {mission_id}: id_client = {repr(mission.get('id_client'))}")
        else:
            print(f"\n✅ Toutes les missions ont un id_client valide")
        
        print(f"\n" + "=" * 80)
        print(f"✅ Vérification terminée")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la vérification: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verifier_missions()

