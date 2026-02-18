#!/usr/bin/env python3
"""
Script pour identifier et nettoyer les balances vides (0 lignes)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId

def nettoyer_balances_vides(dry_run=True):
    """Nettoie les balances vides de la base de données"""
    
    print("=" * 80)
    print(f"🧹 NETTOYAGE DES BALANCES VIDES")
    print("=" * 80)
    
    if dry_run:
        print("\n⚠️  MODE DRY-RUN (simulation uniquement, aucune suppression)")
    else:
        print("\n⚠️  MODE RÉEL (les balances vides seront supprimées)")
        reponse = input("Êtes-vous sûr de vouloir continuer? (oui/non): ").strip().lower()
        if reponse != 'oui':
            print("❌ Opération annulée")
            return
    
    try:
        # Connexion
        client = MongoClient('mongodb://localhost:27017/')
        db = client['cac_perform']
        
        # Trouver toutes les balances vides
        balances_vides = list(db.Balance.find({
            "$or": [
                {"balance": {"$size": 0}},
                {"balance": {"$exists": False}},
                {"balance": []}
            ]
        }))
        
        print(f"\n📊 Résultat de la recherche:")
        print(f"   Balances vides trouvées: {len(balances_vides)}")
        
        if len(balances_vides) == 0:
            print("\n✅ Aucune balance vide trouvée!")
            return
        
        print(f"\n📋 Détails des balances vides:")
        for balance in balances_vides:
            balance_id = str(balance['_id'])
            client_id = balance.get('id_client', 'N/A')
            annee = balance.get('annee_balance', balance.get('periode', 'N/A'))
            
            print(f"\n   - Balance ID: {balance_id}")
            print(f"     Client ID: {client_id}")
            print(f"     Année: {annee}")
            
            # Vérifier si elle est utilisée dans une mission
            missions = list(db.Mission1.find({
                "balances": {"$in": [balance_id]}
            }))
            
            if missions:
                print(f"     ⚠️  UTILISÉE dans {len(missions)} mission(s):")
                for mission in missions:
                    print(f"        - Mission {mission['_id']} (Année: {mission.get('annee_auditee', 'N/A')})")
                    if not dry_run:
                        print(f"          ⚠️  Cette mission devra être supprimée ou mise à jour!")
            else:
                print(f"     ✅ Non utilisée (peut être supprimée sans risque)")
        
        if not dry_run:
            print(f"\n🗑️  Suppression des balances vides...")
            supprimees = 0
            
            for balance in balances_vides:
                balance_id = str(balance['_id'])
                
                # Vérifier si elle est dans une mission
                missions = list(db.Mission1.find({
                    "balances": {"$in": [balance_id]}
                }))
                
                if len(missions) > 0:
                    print(f"   ⚠️  Balance {balance_id} non supprimée (utilisée dans {len(missions)} mission(s))")
                else:
                    result = db.Balance.delete_one({"_id": ObjectId(balance_id)})
                    if result.deleted_count > 0:
                        supprimees += 1
                        print(f"   ✅ Balance {balance_id} supprimée")
            
            print(f"\n✅ {supprimees} balance(s) vide(s) supprimée(s)")
            print(f"⚠️  {len(balances_vides) - supprimees} balance(s) conservée(s) (utilisées dans des missions)")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Par défaut, mode dry-run pour sécurité
    dry_run = True
    
    if len(sys.argv) > 1 and sys.argv[1] == "--exec":
        dry_run = False
    
    nettoyer_balances_vides(dry_run)
    
    if dry_run:
        print("\n💡 Pour vraiment supprimer, utilisez:")
        print("   python nettoyer_balances_vides.py --exec")









