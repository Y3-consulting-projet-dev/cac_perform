#!/usr/bin/env python3
"""
Script simple pour lister toutes les missions avec leurs IDs
Utile pour trouver rapidement l'ID d'une mission
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId

def lister_missions():
    """Liste toutes les missions avec leurs informations principales"""
    
    print("=" * 80)
    print("📋 LISTE DE TOUTES LES MISSIONS")
    print("=" * 80)
    
    try:
        # Connexion
        client = MongoClient('mongodb://localhost:27017/')
        db = client['cac_perform']
        
        # Récupérer toutes les missions
        missions = list(db.Mission1.find({}).sort("_id", -1))
        
        if not missions:
            print("\n❌ Aucune mission trouvée dans la base de données")
            return
        
        print(f"\n✅ {len(missions)} mission(s) trouvée(s):\n")
        
        for idx, mission in enumerate(missions, 1):
            mission_id = str(mission['_id'])
            id_client = mission.get('id_client', 'N/A')
            annee = mission.get('annee_auditee', 'N/A')
            date_debut = mission.get('date_debut', 'N/A')
            date_fin = mission.get('date_fin', 'N/A')
            
            # Récupérer le nom du client si possible
            client_nom = 'N/A'
            if id_client != 'N/A':
                try:
                    client_doc = db.Client.find_one({"_id": ObjectId(id_client)})
                    if client_doc:
                        client_nom = client_doc.get('nom', 'Sans nom')
                    else:
                        # Essayer avec string
                        client_doc = db.Client.find_one({"_id": ObjectId(id_client)})
                        if not client_doc:
                            client_doc = db.Client.find_one({"_id": id_client})
                        if client_doc:
                            client_nom = client_doc.get('nom', 'Sans nom')
                except:
                    pass
            
            # Vérifier les balances
            balances = mission.get('balances', [])
            balances_info = []
            for bal_id in balances:
                balance = db.Balance.find_one({"_id": ObjectId(bal_id)})
                if balance:
                    balance_data = balance.get('balance', [])
                    balances_info.append(f"{len(balance_data)} lignes")
            
            print(f"{idx}. Mission ID: {mission_id}")
            print(f"   📅 Année: {annee}")
            print(f"   👤 Client: {client_nom} (ID: {id_client})")
            print(f"   📆 Période: {date_debut} → {date_fin}")
            print(f"   💰 Balances: {len(balances)} ({', '.join(balances_info) if balances_info else 'N/A'})")
            
            # Afficher le rapport d'intangibilité s'il existe
            rapport = mission.get('controle_intangibilite')
            if rapport:
                total_comptes = rapport.get('total_comptes', 0)
                ecarts = rapport.get('ecarts_count', 0)
                print(f"   🔍 Contrôle intangibilité: {total_comptes} compte(s), {ecarts} écart(s)")
            else:
                print(f"   🔍 Contrôle intangibilité: Non exécuté")
            
            print()
        
        print("=" * 80)
        print("💡 Pour diagnostiquer une mission, copiez son ID et utilisez:")
        print("   python diagnostic_controle_intangibilite_complet.py <MISSION_ID>")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Import nécessaire
    from bson import ObjectId
    lister_missions()

