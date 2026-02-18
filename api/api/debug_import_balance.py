#!/usr/bin/env python3
"""
Script de diagnostic pour l'import des balances Excel
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId
from src.model import Mission
import traceback

def test_import_balance():
    """Test l'import d'une balance Excel"""
    
    print("🔍 Diagnostic de l'import des balances...")
    
    # Connexion MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['cac_perform']
    
    # Récupérer la dernière mission
    missions = list(db.Mission1.find({}, {'_id': 1, 'nom': 1}).sort('_id', -1).limit(1))
    
    if not missions:
        print("❌ Aucune mission trouvée")
        return
    
    mission_id = str(missions[0]['_id'])
    mission = db.Mission1.find_one({'_id': ObjectId(mission_id)})
    balances = mission.get('balances', [])
    
    print(f"📋 Mission: {mission_id}")
    print(f"📊 Balances liées: {len(balances)}")
    
    if len(balances) >= 2:
        balance_2024_id = balances[0]
        balance_2023_id = balances[1]
        
        balance_2024 = db.Balance.find_one({'_id': ObjectId(balance_2024_id)})
        balance_2023 = db.Balance.find_one({'_id': ObjectId(balance_2023_id)})
        
        print(f"\n📈 Balance 2024 (ID: {balance_2024_id})")
        print(f"   Nom: {balance_2024.get('nom', 'Sans nom')}")
        print(f"   Année: {balance_2024.get('annee', 'N/A')}")
        print(f"   Lignes: {len(balance_2024.get('balance', []))}")
        
        print(f"\n📈 Balance 2023 (ID: {balance_2023_id})")
        print(f"   Nom: {balance_2023.get('nom', 'Sans nom')}")
        print(f"   Année: {balance_2023.get('annee', 'N/A')}")
        print(f"   Lignes: {len(balance_2023.get('balance', []))}")
        
        # Afficher quelques exemples si des données existent
        if balance_2024.get('balance'):
            print(f"\n🔍 Exemples Balance 2024:")
            for i, ligne in enumerate(balance_2024.get('balance', [])[:3]):
                print(f"   {i+1}. Compte: {ligne.get('numero_compte', 'N/A')}")
                print(f"      Libellé: {ligne.get('libelle', 'N/A')[:50]}")
                print(f"      DI: {ligne.get('debit_initial', 0)}")
                print(f"      CI: {ligne.get('credit_initial', 0)}")
        
        if balance_2023.get('balance'):
            print(f"\n🔍 Exemples Balance 2023:")
            for i, ligne in enumerate(balance_2023.get('balance', [])[:3]):
                print(f"   {i+1}. Compte: {ligne.get('numero_compte', 'N/A')}")
                print(f"      Libellé: {ligne.get('libelle', 'N/A')[:50]}")
                print(f"      DF: {ligne.get('debit_fin', 0)}")
                print(f"      CF: {ligne.get('credit_fin', 0)}")
    
    # Test de création d'une balance avec un fichier Excel
    print(f"\n🧪 Test de création de balance...")
    
    # Chercher des fichiers Excel dans le dossier docs
    docs_folder = os.path.join(os.path.dirname(__file__), '..', 'docs')
    excel_files = []
    
    if os.path.exists(docs_folder):
        for file in os.listdir(docs_folder):
            if file.endswith(('.xlsx', '.xls')):
                excel_files.append(os.path.join(docs_folder, file))
    
    if excel_files:
        print(f"📁 Fichiers Excel trouvés: {len(excel_files)}")
        for file in excel_files:
            print(f"   - {os.path.basename(file)}")
        
        # Tester l'import du premier fichier
        test_file = excel_files[0]
        print(f"\n🔬 Test d'import avec: {os.path.basename(test_file)}")
        
        try:
            mission_obj = Mission()
            
            # Simuler un fichier uploadé
            class MockFile:
                def __init__(self, filepath):
                    self.filename = os.path.basename(filepath)
                    self.filepath = filepath
                
                def read(self):
                    with open(self.filepath, 'rb') as f:
                        return f.read()
            
            mock_file = MockFile(test_file)
            result = mission_obj.creation_balance(mock_file, 2024, "test_client")
            
            print(f"✅ Import réussi!")
            print(f"   Balance ID: {result[0]}")
            print(f"   Lignes créées: {len(result[1])}")
            
            if result[1]:
                print(f"   Premier compte: {result[1][0].get('numero_compte', 'N/A')}")
                print(f"   Premier libellé: {result[1][0].get('libelle', 'N/A')[:50]}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'import: {str(e)}")
            traceback.print_exc()
    else:
        print(f"❌ Aucun fichier Excel trouvé dans {docs_folder}")

if __name__ == "__main__":
    test_import_balance()

