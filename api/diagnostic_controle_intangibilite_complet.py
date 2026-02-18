#!/usr/bin/env python3
"""
Diagnostic complet du contrôle d'intangibilité pour comprendre pourquoi 0 comptes sont trouvés
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId

def diagnostic_complet(mission_id):
    """Diagnostic complet de pourquoi le contrôle d'intangibilité trouve 0 comptes"""
    
    print("=" * 80)
    print(f"🔍 DIAGNOSTIC COMPLET - CONTRÔLE D'INTANGIBILITÉ")
    print(f"Mission ID: {mission_id}")
    print("=" * 80)
    
    try:
        # Connexion
        client = MongoClient('mongodb://localhost:27017/')
        db = client['cac_perform']
        
        # 1. Vérifier la mission
        print(f"\n1️⃣  VÉRIFICATION DE LA MISSION")
        print("-" * 80)
        mission = db.Mission1.find_one({"_id": ObjectId(mission_id)})
        
        if not mission:
            print(f"❌ Mission {mission_id} non trouvée")
            return
        
        print(f"✅ Mission trouvée")
        print(f"   Année: {mission.get('annee_auditee', 'N/A')}")
        print(f"   Client: {mission.get('id_client', 'N/A')}")
        
        # 2. Vérifier les balances
        print(f"\n2️⃣  VÉRIFICATION DES BALANCES")
        print("-" * 80)
        balances_ids = mission.get('balances', [])
        print(f"   IDs des balances: {len(balances_ids)}")
        
        if len(balances_ids) < 2:
            print(f"   ❌ PAS ASSEZ DE BALANCES: {len(balances_ids)} (minimum 2 requis: N et N-1)")
            return
        
        for idx, bal_id in enumerate(balances_ids):
            print(f"\n   📊 Balance {idx + 1} (ID: {bal_id}):")
            balance = db.Balance.find_one({"_id": ObjectId(bal_id)})
            
            if not balance:
                print(f"      ❌ Balance non trouvée en base")
                continue
            
            balance_data = balance.get('balance', [])
            annee = balance.get('annee_balance', balance.get('periode', 'N/A'))
            
            print(f"      Année: {annee}")
            print(f"      Nombre de lignes: {len(balance_data)}")
            
            if len(balance_data) == 0:
                print(f"      ⚠️  PROBLÈME: Balance VIDE (0 lignes)")
                print(f"      💡 Cette balance doit être réimportée")
            else:
                print(f"      ✅ Balance contient des données")
                
                # Analyser les comptes
                comptes_valides = 0
                comptes_none = 0
                comptes_vides = 0
                
                for ligne in balance_data:
                    num_compte = ligne.get('numero_compte')
                    if num_compte is None:
                        comptes_none += 1
                    elif str(num_compte).strip() == "":
                        comptes_vides += 1
                    else:
                        comptes_valides += 1
                
                print(f"      📋 Analyse des comptes:")
                print(f"         ✅ Comptes valides: {comptes_valides}")
                print(f"         ❌ Comptes None: {comptes_none}")
                print(f"         ❌ Comptes vides: {comptes_vides}")
                
                # Afficher les 5 premiers comptes
                if comptes_valides > 0:
                    print(f"      📋 Exemples de comptes valides:")
                    for ligne in balance_data[:5]:
                        num = ligne.get('numero_compte')
                        if num and str(num).strip():
                            print(f"         - {num}: {ligne.get('libelle', 'N/A')[:40]}")
                    if len(balance_data) > 5:
                        print(f"         ... et {len(balance_data) - 5} autres lignes")
                else:
                    print(f"      ❌ AUCUN COMPTE VALIDE dans cette balance!")
                    print(f"      💡 Causes possibles:")
                    print(f"         - Les numéros de compte sont tous None ou vides")
                    print(f"         - Le format Excel n'a pas été correctement importé")
        
        # 3. Vérifier le rapport d'intangibilité stocké
        print(f"\n3️⃣  VÉRIFICATION DU RAPPORT D'INTANGIBILITÉ")
        print("-" * 80)
        rapport = mission.get('controle_intangibilite')
        
        if rapport:
            print(f"✅ Rapport d'intangibilité trouvé")
            print(f"   OK: {rapport.get('ok', False)}")
            print(f"   Total comptes: {rapport.get('total_comptes', 0)}")
            print(f"   Écarts: {rapport.get('ecarts_count', 0)}")
            
            if rapport.get('message'):
                print(f"   Message: {rapport.get('message')}")
            
            if rapport.get('total_comptes', 0) == 0:
                print(f"\n   ⚠️  PROBLÈME: 0 comptes trouvés")
        else:
            print(f"⚠️  Aucun rapport d'intangibilité stocké")
            print(f"   Le contrôle n'a peut-être pas encore été exécuté")
        
        # 4. Test de la fonction _index_by_compte
        print(f"\n4️⃣  TEST DE L'INDEXATION DES COMPTES")
        print("-" * 80)
        
        for idx, bal_id in enumerate(balances_ids):
            balance = db.Balance.find_one({"_id": ObjectId(bal_id)})
            if not balance:
                continue
            
            balance_data = balance.get('balance', [])
            if len(balance_data) == 0:
                print(f"   Balance {idx + 1}: Skip (vide)")
                continue
            
            # Simuler la fonction _index_by_compte
            index = {}
            lignes_ignorees = 0
            
            for ligne in balance_data:
                num_compte = ligne.get("numero_compte")
                if num_compte is None:
                    lignes_ignorees += 1
                    continue
                
                num_str = str(num_compte).strip()
                if not num_str or num_str == "None" or num_str.lower() == "nan":
                    lignes_ignorees += 1
                    continue
                
                index[num_str] = ligne
            
            print(f"   Balance {idx + 1}:")
            print(f"      Lignes brutes: {len(balance_data)}")
            print(f"      Comptes indexés: {len(index)}")
            print(f"      Lignes ignorées: {lignes_ignorees}")
            
            if len(index) > 0:
                print(f"      ✅ Exemples de comptes indexés:")
                for i, (num, ligne) in enumerate(list(index.items())[:3]):
                    print(f"         - {num}: {ligne.get('libelle', 'N/A')[:40]}")
            else:
                print(f"      ❌ AUCUN COMPTE INDEXÉ!")
                print(f"      💡 Tous les numéros de compte sont invalides")
        
        # 5. Recommandations
        print(f"\n" + "=" * 80)
        print(f"💡 RECOMMANDATIONS")
        print("=" * 80)
        
        has_balance_vide = False
        has_no_valid_accounts = False
        
        for bal_id in balances_ids:
            balance = db.Balance.find_one({"_id": ObjectId(bal_id)})
            if balance:
                balance_data = balance.get('balance', [])
                if len(balance_data) == 0:
                    has_balance_vide = True
                else:
                    # Vérifier comptes valides
                    comptes_valides = sum(1 for ligne in balance_data 
                                        if ligne.get('numero_compte') and str(ligne.get('numero_compte')).strip())
                    if comptes_valides == 0:
                        has_no_valid_accounts = True
        
        if has_balance_vide:
            print(f"\n1. ⚠️  Des balances sont VIDES")
            print(f"   → Réimportez ces balances avec des fichiers Excel valides")
            print(f"   → Utilisez le script: python reparer_mission_balance_vide.py --mission {mission_id}")
        
        if has_no_valid_accounts:
            print(f"\n2. ⚠️  Des balances n'ont aucun compte valide")
            print(f"   → Vérifiez que les numéros de compte ne sont pas vides dans Excel")
            print(f"   → Réimportez avec un format correct")
        
        print(f"\n3. ✅ Vérifiez les logs du serveur lors de l'exécution du contrôle")
        print(f"   → Cherchez les messages: '📊 Comptes indexés dans N:', '📊 Comptes indexés dans N-1:'")
        
        print(f"\n4. ✅ Réexécutez le contrôle d'intangibilité depuis l'interface")
        print(f"   → Le contrôle devrait maintenant afficher des statistiques détaillées")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnostic_controle_intangibilite_complet.py <mission_id>")
        print("\nExemple:")
        print("  python diagnostic_controle_intangibilite_complet.py 6901f0bf070f53bf0b2b8214")
        sys.exit(1)
    
    mission_id = sys.argv[1]
    diagnostic_complet(mission_id)









