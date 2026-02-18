"""
Script de test et debug pour l'API de création de mission
Teste l'endpoint POST /api/v1/missions/ avec des fichiers réels
"""

import requests
import os
from pathlib import Path

def test_mission_creation():
    """Teste la création d'une mission avec des fichiers"""
    
    # URL de l'API
    url = "http://localhost:5000/api/v1/missions/"
    
    # Chercher des fichiers Excel dans le dossier docs
    docs_dir = Path(__file__).parent.parent / "docs"
    
    # Chercher des fichiers Excel
    excel_files = list(docs_dir.glob("*.xlsx"))
    
    if len(excel_files) < 2:
        print("❌ ERREUR: Moins de 2 fichiers Excel trouvés dans le dossier docs/")
        print(f"   Fichiers trouvés: {[f.name for f in excel_files]}")
        print("   Veuillez ajouter au moins 2 fichiers Excel dans le dossier docs/")
        return
    
    # Prendre les 2 premiers fichiers
    file1 = excel_files[0]
    file2 = excel_files[1]
    
    print("=" * 70)
    print("🧪 TEST API CRÉATION MISSION")
    print("=" * 70)
    print(f"📁 Fichier 1: {file1.name}")
    print(f"📁 Fichier 2: {file2.name}")
    print(f"🌐 URL: {url}")
    print()
    
    # Préparer les données
    files = [
        ('files[]', (file1.name, open(file1, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')),
        ('files[]', (file2.name, open(file2, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
    ]
    
    data = {
        'annee_auditee': '2024',
        'id_client': '65a1b2c3d4e5f6789abcdef0',  # Remplacez par un ID client valide
        'date_debut': '2024-01-01',
        'date_fin': '2024-12-31'
    }
    
    print("📦 Données envoyées:")
    print(f"   - annee_auditee: {data['annee_auditee']}")
    print(f"   - id_client: {data['id_client']}")
    print(f"   - date_debut: {data['date_debut']}")
    print(f"   - date_fin: {data['date_fin']}")
    print(f"   - fichiers: {len(files)} fichiers")
    print()
    
    try:
        print("🚀 Envoi de la requête...")
        response = requests.post(url, files=files, data=data)
        
        print(f"📊 Statut HTTP: {response.status_code}")
        print(f"📋 Réponse: {response.text[:500]}")  # Limiter à 500 caractères
        
        if response.status_code == 201:
            print("✅ SUCCÈS: Mission créée avec succès!")
            result = response.json()
            if result.get('success'):
                print(f"   Mission ID: {result.get('data', {}).get('_id', 'N/A')}")
        else:
            print("❌ ERREUR: La requête a échoué")
            try:
                error_data = response.json()
                print(f"   Message d'erreur: {error_data.get('error', 'Erreur inconnue')}")
            except:
                print(f"   Réponse brute: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print("❌ ERREUR: Impossible de se connecter au serveur")
        print("   Assurez-vous que le serveur Flask est démarré (python app.py)")
    except Exception as e:
        print(f"❌ ERREUR: {type(e).__name__}: {str(e)}")
    finally:
        # Fermer les fichiers
        for _, file_tuple in files:
            if len(file_tuple) > 1 and hasattr(file_tuple[1], 'close'):
                file_tuple[1].close()
    
    print("=" * 70)


def test_with_real_client_id():
    """Teste avec un ID client réel depuis la base de données"""
    from src.utils.database import get_database
    
    print("\n" + "=" * 70)
    print("🔍 RECHERCHE D'UN CLIENT EXISTANT")
    print("=" * 70)
    
    try:
        db = get_database()
        client = db.Client.find_one()
        
        if client:
            client_id = str(client['_id'])
            print(f"✅ Client trouvé: {client.get('nom', 'N/A')}")
            print(f"   ID: {client_id}")
            print()
            
            # Relancer le test avec cet ID
            url = "http://localhost:5000/api/v1/missions/"
            docs_dir = Path(__file__).parent.parent / "docs"
            excel_files = list(docs_dir.glob("*.xlsx"))
            
            if len(excel_files) < 2:
                print("❌ Moins de 2 fichiers Excel trouvés")
                return
            
            file1 = excel_files[0]
            file2 = excel_files[1]
            
            files = [
                ('files[]', (file1.name, open(file1, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')),
                ('files[]', (file2.name, open(file2, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
            ]
            
            data = {
                'annee_auditee': '2024',
                'id_client': client_id,
                'date_debut': '2024-01-01',
                'date_fin': '2024-12-31'
            }
            
            print("🚀 Envoi de la requête avec l'ID client réel...")
            response = requests.post(url, files=files, data=data)
            
            print(f"📊 Statut HTTP: {response.status_code}")
            print(f"📋 Réponse: {response.text}")
            
            if response.status_code == 201:
                print("✅ SUCCÈS!")
            else:
                print("❌ ÉCHEC")
                try:
                    error_data = response.json()
                    print(f"   Erreur: {error_data.get('error', 'N/A')}")
                except:
                    pass
            
            # Fermer les fichiers
            for _, file_tuple in files:
                if len(file_tuple) > 1 and hasattr(file_tuple[1], 'close'):
                    file_tuple[1].close()
        else:
            print("❌ Aucun client trouvé dans la base de données")
            print("   Créez d'abord un client via l'API /api/v1/clients/")
            
    except Exception as e:
        print(f"❌ ERREUR: {type(e).__name__}: {str(e)}")


if __name__ == '__main__':
    # Test 1: Avec un ID client fictif
    test_mission_creation()
    
    # Test 2: Avec un ID client réel
    test_with_real_client_id()





