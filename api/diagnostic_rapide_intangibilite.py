#!/usr/bin/env python3
"""
Diagnostic rapide pour comprendre pourquoi le contrôle d'intangibilité trouve 0 comptes
alors que les balances contiennent des données
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId

def diagnostic_rapide(mission_id):
    """Diagnostic rapide de l'indexation des comptes"""
    
    print("=" * 80)
    print(f"🔍 DIAGNOSTIC RAPIDE - INDEXATION DES COMPTES")
    print(f"Mission ID: {mission_id}")
    print("=" * 80)
    
    try:
        # Connexion
        client = MongoClient('mongodb://localhost:27017/')
        db = client['cac_perform']
        
        # Récupérer la mission
        mission = db.Mission1.find_one({"_id": ObjectId(mission_id)})
        if not mission:
            print(f"❌ Mission non trouvée")
            return
        
        balances_ids = mission.get('balances', [])
        print(f"\n📊 Balances de la mission: {len(balances_ids)}")
        
        # Analyser chaque balance
        for idx, bal_id in enumerate(balances_ids):
            print(f"\n{'='*80}")
            print(f"Balance {idx + 1} (ID: {bal_id})")
            print(f"{'='*80}")
            
            balance = db.Balance.find_one({"_id": ObjectId(bal_id)})
            if not balance:
                print(f"❌ Balance non trouvée")
                continue
            
            balance_data = balance.get('balance', [])
            print(f"📊 Lignes brutes: {len(balance_data)}")
            
            if len(balance_data) == 0:
                print(f"❌ Balance vide!")
                continue
            
            # Simuler exactement la fonction _index_by_compte
            print(f"\n🔍 Indexation des comptes (comme dans le code)...")
            
            index = {}
            lignes_ignorees = 0
            lignes_ignorees_none = 0
            lignes_ignorees_vide = 0
            lignes_ignorees_invalid = 0
            
            for ligne_idx, ligne in enumerate(balance_data):
                if not ligne:
                    lignes_ignorees += 1
                    continue
                
                num_compte = ligne.get("numero_compte")
                
                # Debug pour les 5 premières lignes
                if ligne_idx < 5:
                    print(f"   Ligne {ligne_idx}: numero_compte = {repr(num_compte)} (type: {type(num_compte)})")
                
                # Vérifier None
                if num_compte is None:
                    lignes_ignorees_none += 1
                    if ligne_idx < 5:
                        print(f"      ❌ Ignorée (None)")
                    continue
                
                # Convertir en string
                num_str = str(num_compte).strip()
                
                # Vérifier chaîne vide
                if not num_str or num_str == "None" or num_str.lower() == "nan":
                    lignes_ignorees_vide += 1
                    if ligne_idx < 5:
                        print(f"      ❌ Ignorée (vide après conversion)")
                    continue
                
                # Ajouter au index
                index[num_str] = ligne
                if ligne_idx < 5:
                    print(f"      ✅ Indexée comme '{num_str}'")
            
            # Résultats
            print(f"\n📊 RÉSULTATS DE L'INDEXATION:")
            print(f"   ✅ Comptes indexés: {len(index)}")
            print(f"   ❌ Lignes None ignorées: {lignes_ignorees_none}")
            print(f"   ❌ Lignes vides ignorées: {lignes_ignorees_vide}")
            print(f"   ❌ Lignes invalides: {lignes_ignorees_invalid}")
            print(f"   ⚠️  Lignes None (objet): {lignes_ignorees}")
            
            if len(index) > 0:
                print(f"\n✅ Exemples de comptes indexés:")
                for i, (num, ligne) in enumerate(list(index.items())[:5]):
                    libelle = ligne.get('libelle', 'N/A')[:40]
                    debit_init = ligne.get('debit_initial', 0)
                    credit_init = ligne.get('credit_initial', 0)
                    print(f"   {i+1}. {num}: {libelle} (DI={debit_init}, CI={credit_init})")
            else:
                print(f"\n❌ PROBLÈME: AUCUN COMPTE INDEXÉ!")
                print(f"\n💡 ANALYSE:")
                if lignes_ignorees_none > 0:
                    print(f"   - {lignes_ignorees_none} lignes ont numero_compte = None")
                    print(f"   → Vérifiez que l'import Excel a bien créé le champ 'numero_compte'")
                if lignes_ignorees_vide > 0:
                    print(f"   - {lignes_ignorees_vide} lignes ont numero_compte vide")
                    print(f"   → Vérifiez que la première colonne de votre Excel contient des numéros de compte")
                
                # Analyser les premières lignes en détail
                print(f"\n📋 ANALYSE DÉTAILLÉE DES 10 PREMIÈRES LIGNES:")
                for ligne_idx, ligne in enumerate(balance_data[:10]):
                    print(f"   Ligne {ligne_idx}:")
                    print(f"      Clés disponibles: {list(ligne.keys())}")
                    print(f"      numero_compte: {repr(ligne.get('numero_compte'))}")
                    if 'numero_compte' not in ligne:
                        print(f"      ⚠️  Le champ 'numero_compte' n'existe pas dans cette ligne!")
        
        # Résumé final
        print(f"\n" + "=" * 80)
        print(f"💡 RECOMMANDATION")
        print("=" * 80)
        
        total_indexed = 0
        for bal_id in balances_ids:
            balance = db.Balance.find_one({"_id": ObjectId(bal_id)})
            if balance:
                balance_data = balance.get('balance', [])
                index = {}
                for ligne in balance_data:
                    num_compte = ligne.get("numero_compte")
                    if num_compte is None:
                        continue
                    num_str = str(num_compte).strip()
                    if num_str and num_str != "None" and num_str.lower() != "nan":
                        index[num_str] = ligne
                total_indexed += len(index)
        
        if total_indexed == 0:
            print(f"\n❌ PROBLÈME IDENTIFIÉ:")
            print(f"   Aucun compte n'a pu être indexé dans aucune balance")
            print(f"\n🔧 SOLUTION:")
            print(f"   1. Les balances doivent être réimportées")
            print(f"   2. Vérifiez que vos fichiers Excel ont bien des numéros de compte dans la première colonne")
            print(f"   3. Vérifiez que l'import a bien créé le champ 'numero_compte'")
            print(f"   4. Les logs du serveur lors de l'import devraient montrer combien de lignes ont été traitées")
        else:
            print(f"\n✅ {total_indexed} compte(s) indexé(s) au total")
            print(f"   Le contrôle d'intangibilité devrait fonctionner normalement")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnostic_rapide_intangibilite.py <mission_id>")
        print("\nExemple:")
        print("  python diagnostic_rapide_intangibilite.py 69022cb9df502e7375ead1a9")
        sys.exit(1)
    
    mission_id = sys.argv[1]
    diagnostic_rapide(mission_id)









