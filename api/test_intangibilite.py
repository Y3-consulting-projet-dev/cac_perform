#!/usr/bin/env python3
"""
Script de test pour diagnostiquer le contrôle d'intangibilité
"""

from src.models import clit
from bson import ObjectId
import json

def test_intangibilite():
    """Teste le contrôle d'intangibilité pour toutes les missions"""
    
    # Connexion à la base
    db = clit.get_database('cac_perform')
    
    print("🔍 Diagnostic du Contrôle d'Intangibilité")
    print("=" * 60)
    
    # Lister toutes les missions
    missions = list(db.Mission1.find({}, {'_id': 1, 'nom': 1, 'balances': 1}))
    
    if not missions:
        print("❌ Aucune mission trouvée")
        return
    
    print(f"📋 {len(missions)} mission(s) trouvée(s)")
    print()
    
    for i, mission in enumerate(missions):
        mission_id = mission['_id']
        mission_name = mission.get('nom', 'Sans nom')
        balances = mission.get('balances', [])
        
        print(f"🔍 Mission {i+1}: {mission_name}")
        print(f"   ID: {mission_id}")
        print(f"   Balances: {len(balances)}")
        
        if len(balances) < 2:
            print("   ⚠️  Moins de 2 balances (N et N-1 requis)")
            continue
        
        # Charger les balances
        try:
            balance_n = db.Balance.find_one({"_id": ObjectId(balances[0])}, {"balance": 1})
            balance_n1 = db.Balance.find_one({"_id": ObjectId(balances[1])}, {"balance": 1})
            
            if not balance_n or not balance_n1:
                print("   ❌ Balances introuvables")
                continue
            
            # Analyser les comptes de bilan
            comptes_bilan_n = []
            comptes_bilan_n1 = []
            
            for ligne in balance_n.get("balance", []):
                num = str(ligne.get("numero_compte", ""))
                if num.startswith(("1", "2", "3", "4", "5")):
                    di = int(ligne.get("debit_initial", 0) or 0)
                    ci = int(ligne.get("credit_initial", 0) or 0)
                    solde = di - ci
                    comptes_bilan_n.append({
                        "numero": num,
                        "solde": solde,
                        "ligne": ligne
                    })
            
            for ligne in balance_n1.get("balance", []):
                num = str(ligne.get("numero_compte", ""))
                if num.startswith(("1", "2", "3", "4", "5")):
                    df = int(ligne.get("debit_fin", 0) or 0)
                    cf = int(ligne.get("credit_fin", 0) or 0)
                    solde = df - cf
                    comptes_bilan_n1.append({
                        "numero": num,
                        "solde": solde,
                        "ligne": ligne
                    })
            
            print(f"   📊 Comptes de bilan N: {len(comptes_bilan_n)}")
            print(f"   📊 Comptes de bilan N-1: {len(comptes_bilan_n1)}")
            
            # Détecter les écarts
            erreurs = []
            for compte_n in comptes_bilan_n:
                num = compte_n["numero"]
                solde_n = compte_n["solde"]
                
                # Chercher le même compte en N-1
                compte_n1 = next((c for c in comptes_bilan_n1 if c["numero"] == num), None)
                
                if compte_n1:
                    solde_n1 = compte_n1["solde"]
                    if solde_n != solde_n1:
                        ecart = solde_n - solde_n1
                        erreurs.append({
                            "numero": num,
                            "solde_n": solde_n,
                            "solde_n1": solde_n1,
                            "ecart": ecart
                        })
                else:
                    # Compte nouveau
                    erreurs.append({
                        "numero": num,
                        "solde_n": solde_n,
                        "solde_n1": None,
                        "ecart": None
                    })
            
            print(f"   🔍 Écarts détectés: {len(erreurs)}")
            
            if erreurs:
                print("   📋 Détail des écarts:")
                for erreur in erreurs[:5]:  # Afficher les 5 premiers
                    if erreur["ecart"] is not None:
                        print(f"      - {erreur['numero']}: {erreur['solde_n']} vs {erreur['solde_n1']} (écart: {erreur['ecart']})")
                    else:
                        print(f"      - {erreur['numero']}: {erreur['solde_n']} (nouveau compte)")
            else:
                print("   ✅ Aucun écart détecté - Continuité parfaite")
            
            # Vérifier le rapport stocké
            rapport_stocke = mission.get('controle_intangibilite')
            if rapport_stocke:
                print(f"   📄 Rapport stocké: {rapport_stocke.get('ok', 'N/A')}")
                print(f"   📄 Écarts stockés: {len(rapport_stocke.get('ecarts', []))}")
            else:
                print("   ⚠️  Aucun rapport d'intangibilité stocké")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        print()

if __name__ == "__main__":
    test_intangibilite()



