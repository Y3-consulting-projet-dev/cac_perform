#!/usr/bin/env python3
"""
Script de test pour la nouvelle architecture CAC Perform
Teste les endpoints, la configuration et la base de données
"""

import requests
import json
import sys
from pprint import pprint

# Configuration
BASE_URL = "http://localhost:5000"
TIMEOUT = 10

def test_endpoint(method, endpoint, data=None, expected_status=200):
    """
    Teste un endpoint spécifique
    
    Args:
        method: Méthode HTTP (GET, POST, PUT, DELETE)
        endpoint: URL de l'endpoint
        data: Données à envoyer (pour POST/PUT)
        expected_status: Code de statut attendu
        
    Returns:
        dict: Résultat du test
    """
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=TIMEOUT)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=TIMEOUT)
        elif method == "DELETE":
            response = requests.delete(url, timeout=TIMEOUT)
        else:
            return {"success": False, "error": f"Méthode {method} non supportée"}
        
        success = response.status_code == expected_status
        
        try:
            response_data = response.json()
        except:
            response_data = response.text
        
        return {
            "success": success,
            "status_code": response.status_code,
            "expected_status": expected_status,
            "data": response_data,
            "url": url
        }
        
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Connexion refusée - Le serveur est-il démarré?",
            "url": url
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Timeout - Le serveur met trop de temps à répondre",
            "url": url
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "url": url
        }

def run_tests():
    """
    Lance tous les tests
    """
    print("🧪 TEST DE LA NOUVELLE ARCHITECTURE CAC PERFORM")
    print("=" * 60)
    
    tests = [
        # Tests système
        {
            "name": "Health Check",
            "method": "GET",
            "endpoint": "/health",
            "expected_status": 200
        },
        {
            "name": "API Info",
            "method": "GET", 
            "endpoint": "/api/info",
            "expected_status": 200
        },
        
        # Tests API moderne
        {
            "name": "Liste clients (API moderne)",
            "method": "GET",
            "endpoint": "/api/v1/clients/",
            "expected_status": 200
        },
        {
            "name": "Référentiels disponibles",
            "method": "GET",
            "endpoint": "/api/v1/clients/referentiels",
            "expected_status": 200
        },
        
        # Tests API legacy (compatibilité)
        {
            "name": "Liste clients (API legacy)",
            "method": "GET",
            "endpoint": "/cors/client/afficher_clients/",
            "expected_status": 200
        },
        
        # Test de création de client
        {
            "name": "Création client (API moderne)",
            "method": "POST",
            "endpoint": "/api/v1/clients/",
            "data": {
                "nom": "Test Client API",
                "activite": "Test d'API",
                "referentiel": "syscohada",
                "forme_juridique": "SARL",
                "capital": 1000000.0,
                "siege_social": "123 Rue Test, Abidjan",
                "adresse": "123 Rue Test, Abidjan, Côte d'Ivoire"
            },
            "expected_status": 200
        }
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"\n🔍 Test: {test['name']}")
        print(f"   {test['method']} {test['endpoint']}")
        
        result = test_endpoint(
            test['method'],
            test['endpoint'],
            test.get('data'),
            test['expected_status']
        )
        
        if result['success']:
            print(f"   ✅ SUCCÈS (Status: {result['status_code']})")
            passed += 1
        else:
            print(f"   ❌ ÉCHEC")
            if 'error' in result:
                print(f"      Erreur: {result['error']}")
            else:
                print(f"      Status attendu: {result['expected_status']}")
                print(f"      Status reçu: {result['status_code']}")
                if isinstance(result.get('data'), dict) and 'error' in result['data']:
                    print(f"      Message: {result['data']['error']}")
            failed += 1
        
        results.append({**test, **result})
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    print(f"✅ Tests réussis: {passed}")
    print(f"❌ Tests échoués: {failed}")
    print(f"📊 Total: {len(tests)}")
    
    if failed == 0:
        print("\n🎉 Tous les tests sont passés! L'architecture fonctionne correctement.")
    else:
        print(f"\n⚠️  {failed} test(s) ont échoué. Vérifiez la configuration.")
    
    # Détails des échecs
    if failed > 0:
        print("\n🔍 DÉTAILS DES ÉCHECS:")
        for result in results:
            if not result['success']:
                print(f"\n❌ {result['name']}")
                print(f"   URL: {result['url']}")
                if 'error' in result:
                    print(f"   Erreur: {result['error']}")
                else:
                    print(f"   Status: {result['status_code']} (attendu: {result['expected_status']})")
    
    return failed == 0

def test_database_connection():
    """
    Teste spécifiquement la connexion à la base de données
    """
    print("\n🗄️  TEST DE CONNEXION BASE DE DONNÉES")
    print("-" * 40)
    
    try:
        from src.utils.database import check_connection, get_database_stats
        
        if check_connection():
            print("✅ Connexion à la base de données: OK")
            
            stats = get_database_stats()
            if stats and 'collections' in stats:
                print(f"📊 Collections: {stats['collections']}")
                if 'details' in stats:
                    for collection, count in stats['details'].items():
                        print(f"   - {collection}: {count} documents")
            else:
                print("⚠️  Impossible de récupérer les statistiques")
            
            return True
        else:
            print("❌ Connexion à la base de données: ÉCHEC")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test de base de données: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Démarrage des tests...")
    
    # Test de la base de données d'abord
    db_ok = test_database_connection()
    
    # Tests des endpoints
    api_ok = run_tests()
    
    # Résultat final
    print("\n" + "=" * 60)
    if db_ok and api_ok:
        print("🎉 TOUS LES TESTS SONT PASSÉS!")
        print("✅ L'architecture CAC Perform est opérationnelle")
        sys.exit(0)
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        if not db_ok:
            print("   - Problème de base de données")
        if not api_ok:
            print("   - Problème d'API")
        print("🔧 Vérifiez la configuration et les logs")
        sys.exit(1)
