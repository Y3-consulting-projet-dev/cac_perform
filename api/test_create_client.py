"""
Script de test pour l'API de création de client
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
API_ENDPOINT = f"{BASE_URL}/api/v1/clients/"
LEGACY_ENDPOINT = f"{BASE_URL}/cors/client/nouveau_client/"

# Exemples de données de test
EXAMPLES = [
    {
        "nom": "Entreprise ABC SARL",
        "activite": "Conseil en audit et expertise comptable",
        "referentiel": "syscohada",
        "forme_juridique": "SARL",
        "capital": 1000000.0,
        "siege_social": "Abidjan, Cocody Angré 7ème Tranche",
        "adresse": "123 Boulevard de la République, Cocody, Abidjan, Côte d'Ivoire",
        "n_cc": "CC123456789"
    },
    {
        "nom": f"Société Test {datetime.now().strftime('%Y%m%d%H%M%S')}",
        "activite": "Commerce général",
        "referentiel": "ifrs",
        "forme_juridique": "SA",
        "capital": 5000000.0,
        "siege_social": "Abidjan, Plateau",
        "adresse": "456 Avenue Franchet d'Esperey, Plateau, Abidjan"
    },
    {
        "nom": "Boutique Moderne Test",
        "activite": "Vente de produits cosmétiques",
        "referentiel": "pcg",
        "forme_juridique": "SARL",
        "capital": 500000.0,
        "siege_social": "Yopougon, Sicogi",
        "adresse": "789 Rue du Commerce, Yopougon, Abidjan",
        "n_cc": "CC987654321"
    }
]


def test_create_client(client_data, use_legacy=False):
    """
    Teste la création d'un client
    
    Args:
        client_data: Données du client à créer
        use_legacy: Si True, utilise l'endpoint legacy
    """
    endpoint = LEGACY_ENDPOINT if use_legacy else API_ENDPOINT
    endpoint_name = "Legacy" if use_legacy else "Moderne"
    
    print(f"\n{'='*60}")
    print(f"🧪 TEST - Création Client (API {endpoint_name})")
    print(f"{'='*60}")
    print(f"📡 Endpoint: {endpoint}")
    print(f"📦 Données:")
    print(json.dumps(client_data, indent=2, ensure_ascii=False))
    print(f"{'-'*60}")
    
    try:
        # Envoyer la requête
        response = requests.post(
            endpoint,
            json=client_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Afficher les résultats
        print(f"📊 Statut HTTP: {response.status_code}")
        print(f"📄 Réponse:")
        
        try:
            response_data = response.json()
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        except:
            print(response.text)
        
        # Vérifier le résultat
        if response.status_code in [200, 201]:
            print(f"\n✅ SUCCÈS - Client créé avec succès!")
            if isinstance(response_data, dict) and "data" in response_data:
                client_id = response_data.get("data", {}).get("_id", "N/A")
                print(f"🆔 ID du client: {client_id}")
            return True
        else:
            print(f"\n❌ ÉCHEC - Erreur lors de la création")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERREUR - Impossible de se connecter au serveur")
        print(f"   Vérifiez que le serveur Flask est démarré sur {BASE_URL}")
        return False
    except Exception as e:
        print(f"\n❌ ERREUR - {str(e)}")
        return False


def test_validation_errors():
    """Teste les erreurs de validation"""
    print(f"\n{'='*60}")
    print(f"🧪 TEST - Erreurs de Validation")
    print(f"{'='*60}")
    
    # Test 1: Champs manquants
    invalid_data_1 = {
        "nom": "Test",
        # Manque les autres champs requis
    }
    print("\n📝 Test 1: Champs manquants")
    test_create_client(invalid_data_1)
    
    # Test 2: Référentiel invalide
    invalid_data_2 = {
        "nom": "Test Client",
        "activite": "Test",
        "referentiel": "INVALIDE",  # Référentiel invalide
        "forme_juridique": "SARL",
        "capital": 1000.0,
        "siege_social": "Abidjan",
        "adresse": "123 Rue Test"
    }
    print("\n📝 Test 2: Référentiel invalide")
    test_create_client(invalid_data_2)


def main():
    """Fonction principale"""
    print("="*60)
    print("🚀 TEST API - CRÉATION DE CLIENT")
    print("="*60)
    
    # Test 1: Création avec API moderne
    print("\n" + "="*60)
    print("📍 TEST 1: API MODERNE (/api/v1/clients/)")
    print("="*60)
    
    for i, example in enumerate(EXAMPLES, 1):
        print(f"\n--- Exemple {i} ---")
        test_create_client(example, use_legacy=False)
    
    # Test 2: Création avec API legacy
    print("\n" + "="*60)
    print("📍 TEST 2: API LEGACY (/cors/client/nouveau_client/)")
    print("="*60)
    
    test_create_client(EXAMPLES[0], use_legacy=True)
    
    # Test 3: Erreurs de validation
    # test_validation_errors()  # Décommenter pour tester les erreurs
    
    print("\n" + "="*60)
    print("✅ TESTS TERMINÉS")
    print("="*60)


if __name__ == "__main__":
    main()
