#!/usr/bin/env python3
"""
Diagnostic complet pour un client spécifique
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId

def diagnostic_client(client_id):
    """Diagnostic complet pour un client"""
    
    print("=" * 80)
    print(f"🔍 DIAGNOSTIC COMPLET - CLIENT ID: {client_id}")
    print("=" * 80)
    
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['cac_perform']
        
        # 1. Vérifier le client
        print(f"\n1️⃣  VÉRIFICATION DU CLIENT")
        print("-" * 80)
        client_doc = db.Client.find_one({"_id": ObjectId(client_id)})
        
        if not client_doc:
            print(f"❌ Client non trouvé")
            return
        
        print(f"✅ Client trouvé: {client_doc.get('nom', 'Sans nom')}")
        
        # 2. Chercher les missions
        print(f"\n2️⃣  RECHERCHE DES MISSIONS")
        print("-" * 80)
        
        # Essayer avec string
        missions_string = list(db.Mission1.find({"id_client": client_id}))
        print(f"📊 Missions trouvées (recherche avec string): {len(missions_string)}")
        
        # Essayer avec ObjectId
        try:
            missions_objectid = list(db.Mission1.find({"id_client": ObjectId(client_id)}))
            print(f"📊 Missions trouvées (recherche avec ObjectId): {len(missions_objectid)}")
        except:
            missions_objectid = []
        
        missions = missions_string if missions_string else missions_objectid
        
        if len(missions) == 0:
            print(f"\n❌ AUCUNE MISSION TROUVÉE pour ce client")
            print(f"\n💡 Vérifiez que des missions ont bien été créées pour ce client")
            
            # Vérifier toutes les missions
            toutes_missions = list(db.Mission1.find({}).limit(5))
            if toutes_missions:
                print(f"\n📋 Exemples d'id_client dans d'autres missions:")
                for m in toutes_missions:
                    m_id_client = m.get('id_client', 'N/A')
                    print(f"   - Mission {m['_id']}: id_client='{m_id_client}' (type: {type(m_id_client)})")
            return
        
        print(f"\n✅ {len(missions)} mission(s) trouvée(s):\n")
        
        # 3. Analyser chaque mission
        for idx, mission in enumerate(missions, 1):
            mission_id = str(mission['_id'])
            annee = mission.get('annee_auditee', 'N/A')
            
            print(f"{'='*80}")
            print(f"Mission {idx}: {mission_id}")
            print(f"{'='*80}")
            print(f"   Année: {annee}")
            print(f"   Dates: {mission.get('date_debut', 'N/A')} → {mission.get('date_fin', 'N/A')}")
            
            # Vérifier les balances
            balances_ids = mission.get('balances', [])
            print(f"\n   💰 Balances: {len(balances_ids)}")
            
            if len(balances_ids) < 2:
                print(f"      ⚠️  Pas assez de balances (minimum 2 requis: N et N-1)")
            
            total_comptes = 0
            for bal_idx, bal_id in enumerate(balances_ids):
                balance = db.Balance.find_one({"_id": ObjectId(bal_id)})
                if balance:
                    balance_data = balance.get('balance', [])
                    print(f"      Balance {bal_idx + 1}: {len(balance_data)} lignes")
                    
                    # Compter les comptes valides
                    comptes_valides = 0
                    for ligne in balance_data:
                        num = ligne.get('numero_compte')
                        if num and str(num).strip() and str(num).strip() != "None":
                            comptes_valides += 1
                    
                    print(f"         Comptes valides: {comptes_valides}")
                    total_comptes += comptes_valides
                    
                    if comptes_valides == 0 and len(balance_data) > 0:
                        print(f"         ❌ PROBLÈME: {len(balance_data)} lignes mais 0 comptes valides!")
                        print(f"         → Les numéros de compte sont None ou vides")
                else:
                    print(f"      Balance {bal_idx + 1}: ❌ Non trouvée")
            
            # Vérifier le rapport d'intangibilité
            rapport = mission.get('controle_intangibilite')
            if rapport:
                total_comptes_rapport = rapport.get('total_comptes', 0)
                print(f"\n   🔍 Contrôle intangibilité:")
                print(f"      Comptes trouvés: {total_comptes_rapport}")
                print(f"      Écarts: {rapport.get('ecarts_count', 0)}")
                
                if total_comptes_rapport == 0:
                    print(f"      ❌ PROBLÈME: 0 comptes trouvés!")
                    print(f"      → Ceci correspond au problème que vous rencontrez")
                    print(f"      → Total comptes valides dans les balances: {total_comptes}")
                    
                    if total_comptes == 0:
                        print(f"      💡 SOLUTION: Les balances doivent être réimportées")
                        print(f"         avec des fichiers Excel contenant des numéros de compte valides")
                    else:
                        print(f"      💡 SOLUTION: Il y a un problème dans la fonction d'indexation")
                        print(f"         Vérifiez les logs du serveur lors de l'exécution du contrôle")
            else:
                print(f"\n   🔍 Contrôle intangibilité: Non exécuté")
            
            print()
        
        # Résumé
        print("=" * 80)
        print("📊 RÉSUMÉ")
        print("=" * 80)
        print(f"Client: {client_doc.get('nom', 'Sans nom')}")
        print(f"Missions: {len(missions)}")
        print(f"\n💡 Pour diagnostiquer une mission spécifique:")
        print(f"   python diagnostic_rapide_intangibilite.py <MISSION_ID>")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnostic_client_complet.py <client_id>")
        print("\nExemple:")
        print("  python diagnostic_client_complet.py 690103f3013b374b6f390573")
        sys.exit(1)
    
    diagnostic_client(sys.argv[1])









