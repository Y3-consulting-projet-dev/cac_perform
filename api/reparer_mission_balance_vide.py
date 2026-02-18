#!/usr/bin/env python3
"""
Script pour réparer une mission qui contient une balance vide
Peut supprimer la mission ou supprimer uniquement la balance vide
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId

def reparer_mission_balance_vide(mission_id=None, balance_id=None):
    """Répare une mission avec balance vide"""
    
    print("=" * 80)
    print("🔧 RÉPARATION MISSION AVEC BALANCE VIDE")
    print("=" * 80)
    
    try:
        # Connexion
        client = MongoClient('mongodb://localhost:27017/')
        db = client['cac_perform']
        
        if mission_id:
            # Mode 1: Réparer une mission spécifique
            print(f"\n📋 Recherche de la mission: {mission_id}")
            mission = db.Mission1.find_one({"_id": ObjectId(mission_id)})
            
            if not mission:
                print(f"❌ Mission {mission_id} non trouvée")
                return
            
            print(f"✅ Mission trouvée")
            print(f"   Année: {mission.get('annee_auditee', 'N/A')}")
            print(f"   Client: {mission.get('id_client', 'N/A')}")
            
            balances_ids = mission.get('balances', [])
            print(f"\n📊 Analyse des {len(balances_ids)} balance(s):")
            
            balances_vides = []
            balances_valides = []
            
            for bal_id in balances_ids:
                balance = db.Balance.find_one({"_id": ObjectId(bal_id)})
                if balance:
                    balance_data = balance.get('balance', [])
                    if len(balance_data) == 0:
                        balances_vides.append(bal_id)
                        print(f"   ❌ Balance {bal_id}: VIDE (0 lignes)")
                    else:
                        balances_valides.append(bal_id)
                        print(f"   ✅ Balance {bal_id}: {len(balance_data)} lignes")
            
            if len(balances_vides) == 0:
                print(f"\n✅ Aucune balance vide dans cette mission")
                return
            
            print(f"\n⚠️  PROBLÈME DÉTECTÉ:")
            print(f"   - {len(balances_vides)} balance(s) vide(s)")
            print(f"   - {len(balances_valides)} balance(s) valide(s)")
            
            if len(balances_valides) == 0:
                print(f"\n❌ Cette mission n'a AUCUNE balance valide!")
                print(f"   Action recommandée: Supprimer la mission et en créer une nouvelle")
                
                choix = input("\nVoulez-vous supprimer cette mission? (oui/non): ").strip().lower()
                if choix == 'oui':
                    # Supprimer aussi les balances associées
                    for bal_id in balances_vides:
                        db.Balance.delete_one({"_id": ObjectId(bal_id)})
                        print(f"   ✅ Balance {bal_id} supprimée")
                    
                    db.Mission1.delete_one({"_id": ObjectId(mission_id)})
                    print(f"   ✅ Mission {mission_id} supprimée")
                    print(f"\n✅ Mission supprimée. Vous pouvez maintenant en créer une nouvelle avec des balances valides.")
                else:
                    print(f"   Opération annulée")
            else:
                print(f"\n💡 SOLUTION: Retirer les balances vides de la mission")
                
                choix = input("\nVoulez-vous retirer les balances vides de la mission? (oui/non): ").strip().lower()
                if choix == 'oui':
                    # Mettre à jour la mission pour ne garder que les balances valides
                    db.Mission1.update_one(
                        {"_id": ObjectId(mission_id)},
                        {"$set": {"balances": balances_valides}}
                    )
                    print(f"   ✅ Mission mise à jour: {len(balances_valides)} balance(s) conservée(s)")
                    
                    # Supprimer les balances vides
                    for bal_id in balances_vides:
                        db.Balance.delete_one({"_id": ObjectId(bal_id)})
                        print(f"   ✅ Balance vide {bal_id} supprimée")
                    
                    print(f"\n⚠️  ATTENTION: Cette mission n'a maintenant que {len(balances_valides)} balance(s)")
                    print(f"   Pour un contrôle complet, il faut 2 balances (N et N-1)")
                    print(f"   Recommandation: Ajouter la balance manquante ou créer une nouvelle mission")
                else:
                    print(f"   Opération annulée")
        
        elif balance_id:
            # Mode 2: Analyser une balance spécifique
            print(f"\n📋 Analyse de la balance: {balance_id}")
            
            balance = db.Balance.find_one({"_id": ObjectId(balance_id)})
            if not balance:
                print(f"❌ Balance non trouvée")
                return
            
            balance_data = balance.get('balance', [])
            print(f"   Nombre de lignes: {len(balance_data)}")
            
            if len(balance_data) == 0:
                # Trouver les missions utilisant cette balance
                missions = list(db.Mission1.find({
                    "balances": {"$in": [balance_id]}
                }))
                
                print(f"\n   Cette balance est utilisée dans {len(missions)} mission(s):")
                for mission in missions:
                    print(f"      - Mission {mission['_id']} (Année: {mission.get('annee_auditee', 'N/A')})")
                
                if len(missions) > 0:
                    print(f"\n💡 Pour réparer, utilisez:")
                    print(f"   python reparer_mission_balance_vide.py --mission {missions[0]['_id']}")
            else:
                print(f"   ✅ Cette balance contient des données")
        
        else:
            print(f"\n❌ Usage incorrect")
            print(f"\nUsage:")
            print(f"  python reparer_mission_balance_vide.py --mission <MISSION_ID>")
            print(f"  python reparer_mission_balance_vide.py --balance <BALANCE_ID>")
            print(f"\nExemple:")
            print(f"  python reparer_mission_balance_vide.py --mission 6901f0bf070f53bf0b2b8214")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    mission_id = None
    balance_id = None
    
    # Parser les arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--mission" and len(sys.argv) > 2:
            mission_id = sys.argv[2]
        elif sys.argv[1] == "--balance" and len(sys.argv) > 2:
            balance_id = sys.argv[2]
        else:
            print("Usage incorrect")
            print("\nUsage:")
            print("  python reparer_mission_balance_vide.py --mission <MISSION_ID>")
            print("  python reparer_mission_balance_vide.py --balance <BALANCE_ID>")
            sys.exit(1)
    
    reparer_mission_balance_vide(mission_id, balance_id)









