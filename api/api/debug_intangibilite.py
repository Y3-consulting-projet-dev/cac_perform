#!/usr/bin/env python3
"""
Script simple pour déboguer l'intangibilité
"""

from pymongo import MongoClient
from bson import ObjectId

# Connexion directe
client = MongoClient('mongodb://localhost:27017/')
db = client['cac_perform']

print("🔍 Diagnostic Intangibilité")
print("=" * 40)

# Lister les missions
missions = list(db.Mission1.find({}, {'_id': 1, 'nom': 1, 'balances': 1, 'controle_intangibilite': 1}))

print(f"📋 {len(missions)} mission(s) trouvée(s)")

for i, mission in enumerate(missions):
    print(f"\n🔍 Mission {i+1}: {mission.get('nom', 'Sans nom')}")
    print(f"   ID: {mission['_id']}")
    
    balances = mission.get('balances', [])
    print(f"   Balances: {len(balances)}")
    
    # Vérifier le rapport d'intangibilité
    rapport = mission.get('controle_intangibilite')
    if rapport:
        print(f"   📄 Rapport stocké:")
        print(f"      - OK: {rapport.get('ok')}")
        print(f"      - Nombre d'écarts: {len(rapport.get('ecarts', []))}")
        
        ecarts = rapport.get('ecarts', [])
        if ecarts:
            print(f"   📊 Détail des écarts:")
            for j, ecart in enumerate(ecarts[:3]):  # Afficher les 3 premiers
                print(f"      {j+1}. Compte: {ecart.get('numero_compte')}")
                print(f"         Ouverture N: {ecart.get('ouverture_n')}")
                print(f"         Clôture N-1: {ecart.get('cloture_n1')}")
                print(f"         Écart: {ecart.get('ecart')}")
                print(f"         Message: {ecart.get('message')}")
        else:
            print("   ✅ Aucun écart détecté")
    else:
        print("   ⚠️  Aucun rapport d'intangibilité stocké")
        
        # Si pas de rapport, analyser les balances
        if len(balances) >= 2:
            print("   🔍 Analyse des balances...")
            try:
                balance_n = db.Balance.find_one({"_id": ObjectId(balances[0])}, {"balance": 1})
                balance_n1 = db.Balance.find_one({"_id": ObjectId(balances[1])}, {"balance": 1})
                
                if balance_n and balance_n1:
                    # Compter les comptes de bilan
                    comptes_n = [l for l in balance_n.get("balance", []) 
                               if str(l.get("numero_compte", "")).startswith(("1", "2", "3", "4", "5"))]
                    comptes_n1 = [l for l in balance_n1.get("balance", []) 
                                if str(l.get("numero_compte", "")).startswith(("1", "2", "3", "4", "5"))]
                    
                    print(f"      - Comptes de bilan N: {len(comptes_n)}")
                    print(f"      - Comptes de bilan N-1: {len(comptes_n1)}")
                    
                    # Détecter les comptes nouveaux
                    nums_n = {str(l.get("numero_compte")) for l in comptes_n}
                    nums_n1 = {str(l.get("numero_compte")) for l in comptes_n1}
                    nouveaux = nums_n - nums_n1
                    
                    print(f"      - Comptes nouveaux: {len(nouveaux)}")
                    if nouveaux:
                        print(f"      - Exemples: {list(nouveaux)[:3]}")
                else:
                    print("      ❌ Balances introuvables")
            except Exception as e:
                print(f"      ❌ Erreur: {e}")

print("\n" + "=" * 40)
print("✅ Diagnostic terminé")



