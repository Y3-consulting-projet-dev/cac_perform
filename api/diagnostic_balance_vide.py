#!/usr/bin/env python3
"""
Script pour diagnostiquer pourquoi une balance est vide (0 lignes)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId

def diagnostic_balance(balance_id):
    """Diagnostique une balance spécifique"""
    
    print("=" * 80)
    print(f"🔍 DIAGNOSTIC BALANCE: {balance_id}")
    print("=" * 80)
    
    try:
        # Connexion
        client = MongoClient('mongodb://localhost:27017/')
        db = client['cac_perform']
        
        # Récupérer la balance
        balance = db.Balance.find_one({"_id": ObjectId(balance_id)})
        
        if not balance:
            print(f"❌ Balance {balance_id} non trouvée")
            return
        
        print(f"\n✅ Balance trouvée")
        print(f"   ID: {balance_id}")
        print(f"   Client ID: {balance.get('id_client', 'N/A')}")
        print(f"   Année: {balance.get('annee_balance', balance.get('periode', 'N/A'))}")
        
        balance_data = balance.get('balance', [])
        print(f"   Nombre de lignes: {len(balance_data)}")
        
        if len(balance_data) == 0:
            print(f"\n⚠️  PROBLÈME: La balance est VIDE (0 lignes)")
            
            # Vérifier si c'est une balance récemment créée
            print(f"\n📋 Informations sur la balance:")
            print(f"   - Toutes les clés: {list(balance.keys())}")
            print(f"   - Balance data type: {type(balance_data)}")
            print(f"   - Balance data value: {balance_data}")
            
            # Vérifier la mission associée
            print(f"\n🔍 Recherche des missions utilisant cette balance...")
            missions = list(db.Mission1.find({
                "balances": {"$in": [balance_id]}
            }))
            
            if missions:
                print(f"   ✅ Trouvée dans {len(missions)} mission(s):")
                for mission in missions:
                    print(f"      - Mission {mission['_id']} (Année: {mission.get('annee_auditee', 'N/A')})")
            else:
                print(f"   ⚠️  Cette balance n'est utilisée dans aucune mission")
            
            print(f"\n💡 CAUSES POSSIBLES:")
            print(f"   1. L'import Excel a échoué silencieusement")
            print(f"   2. Le format Excel n'a pas été reconnu")
            print(f"   3. Toutes les lignes ont été ignorées lors de l'import:")
            print(f"      - Numéros de compte vides ou None")
            print(f"      - Format incorrect (nombre de colonnes)")
            print(f"      - Feuille Excel non trouvée")
            print(f"   4. L'import a été fait avant les améliorations récentes")
            
            print(f"\n🔧 SOLUTIONS:")
            print(f"   1. Vérifiez les logs du serveur lors de l'import")
            print(f"   2. Réimportez la balance avec un fichier Excel valide")
            print(f"   3. Vérifiez que le fichier Excel contient bien des données")
            print(f"   4. Supprimez cette balance vide et réimportez")
            
        else:
            print(f"\n✅ La balance contient {len(balance_data)} lignes")
            print(f"\n📋 Premières lignes:")
            for idx, ligne in enumerate(balance_data[:5], 1):
                print(f"   {idx}. Compte: {ligne.get('numero_compte', 'N/A')}, Libellé: {ligne.get('libelle', 'N/A')[:30]}")
            
            if len(balance_data) > 5:
                print(f"   ... et {len(balance_data) - 5} autres lignes")
        
        # Vérifier les métadonnées
        print(f"\n📊 Métadonnées de la balance:")
        for key, value in balance.items():
            if key != 'balance':  # On a déjà affiché balance
                if isinstance(value, list):
                    print(f"   - {key}: [{len(value)} élément(s)]")
                elif isinstance(value, dict):
                    print(f"   - {key}: [dictionnaire]")
                else:
                    print(f"   - {key}: {value}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnostic_balance_vide.py <balance_id>")
        print("\nExemple:")
        print("  python diagnostic_balance_vide.py 6901f0bf070f53bf0b2b8213")
        sys.exit(1)
    
    balance_id = sys.argv[1]
    diagnostic_balance(balance_id)









