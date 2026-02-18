#!/usr/bin/env python3
"""
Test d'import avec FileStorage
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId
from src.model import Mission
from werkzeug.datastructures import FileStorage

def test_import_with_filestorage():
    print('🔍 Test d import avec FileStorage...')

    # Créer un objet FileStorage simulé
    file_path = '../docs/Balance UM  2023 VF(N-1).xlsx'

    if os.path.exists(file_path):
        print(f'📁 Fichier trouvé: {file_path}')
        
        try:
            # Créer un FileStorage
            with open(file_path, 'rb') as f:
                file_storage = FileStorage(
                    stream=f,
                    filename='Balance UM  2023 VF(N-1).xlsx',
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                
                # Tester l'import
                mission_obj = Mission()
                result = mission_obj.creation_balance(file_storage, 2023, 'test_client')
                
                print(f'✅ Import réussi!')
                print(f'   Balance ID: {result[0]}')
                print(f'   Lignes créées: {len(result[1])}')
                
                if result[1]:
                    print(f'\n🔍 Premières lignes importées:')
                    for i, ligne in enumerate(result[1][:3]):
                        compte = ligne.get('numero_compte', 'N/A')
                        libelle = ligne.get('libelle', 'N/A')[:50]
                        di = ligne.get('debit_initial', 0)
                        ci = ligne.get('credit_initial', 0)
                        df = ligne.get('debit_fin', 0)
                        cf = ligne.get('credit_fin', 0)
                        
                        print(f'   {i+1}. Compte: {compte}')
                        print(f'      Libellé: {libelle}')
                        print(f'      DI: {di}')
                        print(f'      CI: {ci}')
                        print(f'      DF: {df}')
                        print(f'      CF: {cf}')
                        print()
                
        except Exception as e:
            print(f'❌ Erreur: {str(e)}')
            import traceback
            traceback.print_exc()
    else:
        print(f'❌ Fichier non trouvé: {file_path}')

if __name__ == "__main__":
    test_import_with_filestorage()

