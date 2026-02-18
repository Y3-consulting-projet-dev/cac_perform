"""
Script de test pour l'API de création de mission
"""

import requests
import json
from datetime import datetime
import os

# Configuration
BASE_URL = "http://localhost:5000"
API_ENDPOINT = f"{BASE_URL}/cors/mission/nouvelle_mission"

# Exemple de données de test
EXAMPLE_DATA = {
    "annee_auditee": "2024",
    "date_debut": "2024-01-01",
    "date_fin": "2024-12-31",
    # "id": "65a1b2c3d4e5f6789abcdef0"  # À remplacer par un ID client valide
}


def test_create_mission(client_id, balance_files, use_example_files=False):
    """
    Teste la création d'une mission
    
    Args:
        client_id: ID du client (ObjectId MongoDB)
        balance_files: Liste des chemins vers les fichiers Excel
        use_example_files: Si True, utilise les fichiers d'exemple du dossier docs/
    """
    
    if use_example_files:
        # Utiliser les fichiers d'exemple s'ils existent
        docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
        balance_files = [
            os.path.join(docs_dir, "Balance Générale - 2023.xlsx"),
            os.path.join(docs_dir, "Balance Générale - AF VF - 2024 (1).xlsx")
        ]
        # Filtrer les fichiers qui n'existent pas
        balance_files = [f for f in balance_files if os.path.exists(f)]
    
    print(f"\n{'='*60}")
    print(f"🧪 TEST - Création Mission")
    print(f"{'='*60}")
    print(f"📡 Endpoint: {API_ENDPOINT}")
    print(f"👤 ID Client: {client_id}")
    print(f"📅 Année auditée: {EXAMPLE_DATA['annee_auditee']}")
    print(f"📆 Période: {EXAMPLE_DATA['date_debut']} → {EXAMPLE_DATA['date_fin']}")
    print(f"📁 Fichiers:")
    
    # Vérifier que les fichiers existent
    valid_files = []
    for file_path in balance_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / 1024  # Taille en KB
            print(f"   ✅ {os.path.basename(file_path)} ({file_size:.2f} KB)")
            valid_files.append(file_path)
        else:
            print(f"   ❌ {file_path} (NON TROUVÉ)")
    
    if len(valid_files) < 2:
        print(f"\n❌ ERREUR - Au moins 2 fichiers sont requis")
        print(f"   Fichiers fournis: {len(valid_files)}")
        return False
    
    print(f"{'-'*60}")
    
    try:
        # Préparer les données multipart/form-data
        files = []
        for file_path in valid_files:
            files.append(
                ('files[]', (
                    os.path.basename(file_path),
                    open(file_path, 'rb'),
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ))
            )
        
        data = {
            'annee_auditee': EXAMPLE_DATA['annee_auditee'],
            'id': client_id,
            'date_debut': EXAMPLE_DATA['date_debut'],
            'date_fin': EXAMPLE_DATA['date_fin']
        }
        
        # Envoyer la requête
        print("📤 Envoi de la requête...")
        response = requests.post(
            API_ENDPOINT,
            files=files,
            data=data,
            timeout=60  # Timeout plus long car l'upload peut prendre du temps
        )
        
        # Fermer les fichiers
        for _, file_tuple in files:
            file_tuple[1].close()
        
        # Afficher les résultats
        print(f"📊 Statut HTTP: {response.status_code}")
        print(f"📄 Réponse:")
        
        try:
            response_data = response.json()
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        except:
            print(response.text)
        
        # Vérifier le résultat
        if response.status_code == 200:
            if response_data.get("success"):
                print(f"\n✅ SUCCÈS - Mission créée avec succès!")
                mission_id = response_data.get("data", {}).get("_id", "N/A")
                print(f"🆔 ID de la mission: {mission_id}")
                return True
            else:
                print(f"\n❌ ÉCHEC - {response_data.get('error', 'Erreur inconnue')}")
                return False
        else:
            print(f"\n❌ ÉCHEC - Statut HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERREUR - Impossible de se connecter au serveur")
        print(f"   Vérifiez que le serveur Flask est démarré sur {BASE_URL}")
        return False
    except FileNotFoundError as e:
        print(f"\n❌ ERREUR - Fichier non trouvé: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERREUR - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_errors():
    """Teste les erreurs de validation"""
    print(f"\n{'='*60}")
    print(f"🧪 TEST - Erreurs de Validation")
    print(f"{'='*60}")
    
    # Test 1: Pas de fichiers
    print("\n📝 Test 1: Pas de fichiers")
    try:
        response = requests.post(
            API_ENDPOINT,
            data={
                'annee_auditee': '2024',
                'id': '65a1b2c3d4e5f6789abcdef0',
                'date_debut': '2024-01-01',
                'date_fin': '2024-12-31'
            },
            timeout=10
        )
        print(f"   Statut: {response.status_code}")
        print(f"   Réponse: {response.json()}")
    except Exception as e:
        print(f"   Erreur: {e}")
    
    # Test 2: Champs manquants
    print("\n📝 Test 2: Champs manquants")
    try:
        response = requests.post(
            API_ENDPOINT,
            files=[('files[]', ('test.xlsx', b'fake content', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))],
            data={
                'annee_auditee': '2024',
                # Manque id, date_debut, date_fin
            },
            timeout=10
        )
        print(f"   Statut: {response.status_code}")
        print(f"   Réponse: {response.json()}")
    except Exception as e:
        print(f"   Erreur: {e}")


def get_clients():
    """Récupère la liste des clients pour faciliter les tests"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/clients/", timeout=10)
        if response.status_code == 200:
            clients = response.json().get("response", [])
            if clients:
                print("\n📋 Clients disponibles:")
                for i, client in enumerate(clients[:5], 1):  # Afficher les 5 premiers
                    print(f"   {i}. {client.get('nom', 'N/A')} (ID: {client.get('_id', 'N/A')})")
                return clients[0].get('_id') if clients else None
            else:
                print("\n⚠️  Aucun client trouvé. Créez d'abord un client.")
                return None
        else:
            print(f"\n⚠️  Erreur lors de la récupération des clients: {response.status_code}")
            return None
    except Exception as e:
        print(f"\n⚠️  Erreur lors de la récupération des clients: {e}")
        return None


def main():
    """Fonction principale"""
    print("="*60)
    print("🚀 TEST API - CRÉATION DE MISSION")
    print("="*60)
    
    # Demander l'ID du client ou le récupérer automatiquement
    print("\n📋 Récupération de la liste des clients...")
    client_id = get_clients()
    
    if not client_id:
        print("\n❌ Aucun client disponible. Veuillez créer un client d'abord.")
        print("   Utilisez: POST /api/v1/clients/")
        return
    
    # Demander les fichiers
    print("\n" + "="*60)
    print("📍 INSTRUCTIONS")
    print("="*60)
    print("Pour tester, vous devez fournir les chemins vers 2 fichiers Excel:")
    print("  1. Balance N (ex: Balance_2024.xlsx)")
    print("  2. Balance N-1 (ex: Balance_2023.xlsx)")
    print("\nOu utilisez les fichiers d'exemple dans le dossier docs/")
    
    use_example = input("\nUtiliser les fichiers d'exemple? (o/n): ").lower().strip() == 'o'
    
    if use_example:
        # Test avec les fichiers d'exemple
        print(f"\n📍 TEST avec fichiers d'exemple")
        test_create_mission(client_id, [], use_example_files=True)
    else:
        # Demander les chemins des fichiers
        file1 = input("\nChemin vers Balance N: ").strip().strip('"')
        file2 = input("Chemin vers Balance N-1: ").strip().strip('"')
        
        balance_files = [file1, file2]
        
        # Test avec les fichiers fournis
        print(f"\n📍 TEST avec fichiers fournis")
        test_create_mission(client_id, balance_files, use_example_files=False)
    
    # Tests d'erreurs de validation (optionnel)
    # test_validation_errors()
    
    print("\n" + "="*60)
    print("✅ TESTS TERMINÉS")
    print("="*60)


if __name__ == "__main__":
    main()








