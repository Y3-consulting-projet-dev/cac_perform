#!/usr/bin/env python3
"""
Script de diagnostic détaillé pour le contrôle d'intangibilité
Permet de vérifier pourquoi aucun compte n'est trouvé
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId
from src.config.db import MyMongo

def diagnostic_intangibilite(mission_id):
    """Diagnostique pourquoi le contrôle d'intangibilité ne trouve aucun compte"""
    
    print("=" * 80)
    print("🔍 DIAGNOSTIC CONTRÔLE D'INTANGIBILITÉ")
    print("=" * 80)
    
    try:
        # Connexion à MongoDB
        client = MongoClient('mongodb://localhost:27017')
        db = client['cac_perform']
        
        # Récupérer la mission
        print(f"\n📋 Recherche de la mission: {mission_id}")
        mission = db.Mission1.find_one({"_id": ObjectId(mission_id)})
        
        if not mission:
            print(f"❌ Mission {mission_id} non trouvée")
            return
        
        print(f"✅ Mission trouvée: {mission.get('annee_auditee', 'N/A')}")
        
        # Vérifier les balances
        balances_ids = mission.get("balances", [])
        print(f"\n📊 Balances associées: {len(balances_ids)}")
        
        if len(balances_ids) < 2:
            print(f"❌ Il faut au moins 2 balances (N et N-1), mais seulement {len(balances_ids)} trouvée(s)")
            return
        
        # Analyser chaque balance
        for idx, bal_id in enumerate(balances_ids):
            print(f"\n{'='*80}")
            print(f"🔍 Analyse Balance {idx + 1} (ID: {bal_id})")
            print(f"{'='*80}")
            
            balance = db.Balance.find_one({"_id": ObjectId(bal_id)})
            
            if not balance:
                print(f"❌ Balance {bal_id} introuvable")
                continue
            
            balance_data = balance.get("balance", [])
            annee = balance.get("annee_balance", balance.get("periode", "N/A"))
            
            print(f"📅 Année: {annee}")
            print(f"📊 Nombre de lignes: {len(balance_data)}")
            
            if len(balance_data) == 0:
                print("❌ Balance vide - aucune ligne de données")
                continue
            
            # Analyser les premières lignes
            print(f"\n📋 Analyse des premières lignes:")
            comptes_valides = 0
            comptes_invalides = 0
            comptes_none = 0
            comptes_vides = 0
            
            for i, ligne in enumerate(balance_data[:10]):  # Analyser les 10 premières lignes
                if not ligne:
                    print(f"  ⚠️  Ligne {i}: ligne None ou vide")
                    continue
                
                num_compte = ligne.get("numero_compte")
                
                if num_compte is None:
                    comptes_none += 1
                    print(f"  ❌ Ligne {i}: numero_compte = None")
                    print(f"     Clés disponibles: {list(ligne.keys())}")
                elif str(num_compte).strip() == "":
                    comptes_vides += 1
                    print(f"  ❌ Ligne {i}: numero_compte = '' (vide)")
                else:
                    num_str = str(num_compte).strip()
                    if num_str:
                        comptes_valides += 1
                        if i < 3:  # Afficher les 3 premiers comptes valides
                            print(f"  ✅ Ligne {i}: numero_compte = '{num_str}' (type: {type(num_compte)})")
                            print(f"     Libellé: {ligne.get('libelle', 'N/A')[:50]}")
                    else:
                        comptes_invalides += 1
                        print(f"  ⚠️  Ligne {i}: numero_compte = '{num_compte}' (devient vide après strip)")
            
            # Statistiques globales
            print(f"\n📊 Statistiques globales (sur toutes les lignes):")
            
            for ligne in balance_data:
                num_compte = ligne.get("numero_compte")
                if num_compte is None:
                    comptes_none += 1
                elif str(num_compte).strip() == "":
                    comptes_vides += 1
                else:
                    num_str = str(num_compte).strip()
                    if num_str:
                        comptes_valides += 1
                    else:
                        comptes_invalides += 1
            
            print(f"  ✅ Comptes valides: {comptes_valides}")
            print(f"  ❌ Comptes None: {comptes_none}")
            print(f"  ❌ Comptes vides: {comptes_vides}")
            print(f"  ⚠️  Comptes invalides: {comptes_invalides}")
            print(f"  📊 Total lignes: {len(balance_data)}")
            
            # Vérifier les champs disponibles
            if len(balance_data) > 0:
                premiere_ligne = balance_data[0]
                print(f"\n📋 Structure de la première ligne:")
                print(f"  Clés disponibles: {list(premiere_ligne.keys())}")
                print(f"  Exemple de valeurs:")
                for key, value in list(premiere_ligne.items())[:5]:
                    print(f"    - {key}: {value} (type: {type(value)})")
            
            # Recommandations
            if comptes_valides == 0:
                print(f"\n❌ PROBLÈME DÉTECTÉ:")
                if comptes_none > 0:
                    print(f"   - Le champ 'numero_compte' est None dans {comptes_none} lignes")
                    print(f"   - Vérifiez que l'import Excel a bien créé ce champ")
                if comptes_vides > 0:
                    print(f"   - Le champ 'numero_compte' est vide dans {comptes_vides} lignes")
                    print(f"   - Vérifiez que votre fichier Excel a bien des numéros de compte dans la première colonne")
                print(f"\n💡 SOLUTION:")
                print(f"   - Réimporter les balances avec un fichier Excel valide")
                print(f"   - Vérifier que la première colonne contient bien les numéros de compte (non vides)")
        
        # Vérifier le rapport d'intangibilité stocké
        print(f"\n{'='*80}")
        print(f"📋 Vérification du rapport d'intangibilité stocké")
        print(f"{'='*80}")
        
        rapport = mission.get("controle_intangibilite")
        if rapport:
            print(f"✅ Rapport d'intangibilité trouvé")
            print(f"   - Total comptes: {rapport.get('total_comptes', 0)}")
            print(f"   - Écarts: {rapport.get('ecarts_count', 0)}")
            print(f"   - OK: {rapport.get('ok', False)}")
            if rapport.get('message'):
                print(f"   - Message: {rapport.get('message')}")
        else:
            print(f"⚠️  Aucun rapport d'intangibilité stocké")
        
    except Exception as e:
        print(f"❌ Erreur lors du diagnostic: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnostic_intangibilite_detaille.py <mission_id>")
        print("\nExemple:")
        print("  python diagnostic_intangibilite_detaille.py 507f1f77bcf86cd799439011")
        sys.exit(1)
    
    mission_id = sys.argv[1]
    diagnostic_intangibilite(mission_id)

