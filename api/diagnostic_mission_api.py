"""
Script de diagnostic complet pour l'API de création de mission
"""

import requests
import sys

BASE_URL = "http://localhost:5000"

def test_server():
    """Teste si le serveur est en cours d'exécution"""
    print("="*60)
    print("🧪 TEST 1: Serveur Flask")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Serveur Flask est en cours d'exécution")
            return True
        else:
            print(f"⚠️  Serveur répond avec le statut: {response.status_code}")
            return True
    except requests.exceptions.ConnectionError:
        print("❌ Serveur Flask n'est pas en cours d'exécution")
        print("   → Démarrez le serveur avec: python app.py")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_endpoint_exists():
    """Teste si l'endpoint moderne existe"""
    print("\n" + "="*60)
    print("🧪 TEST 2: Endpoint Moderne /api/v1/missions/")
    print("="*60)
    
    try:
        # Test OPTIONS (preflight CORS)
        response = requests.options(f"{BASE_URL}/api/v1/missions/", timeout=2)
        print(f"   OPTIONS Status: {response.status_code}")
        
        # Test POST sans données (devrait retourner erreur 400)
        response = requests.post(f"{BASE_URL}/api/v1/missions/", timeout=2)
        print(f"   POST Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
        if response.status_code == 404:
            print("\n❌ ERREUR: Endpoint /api/v1/missions/ non trouvé (404)")
            return False
        elif response.status_code in [400, 422]:
            print("\n✅ SUCCÈS: L'endpoint existe et répond !")
            print("   → L'erreur 400 est normale (données manquantes)")
            return True
        else:
            print(f"\n⚠️  Statut inattendu: {response.status_code}")
            return True
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERREUR: Impossible de se connecter au serveur")
        return False
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        return False

def test_legacy_endpoint():
    """Teste si l'endpoint legacy existe toujours"""
    print("\n" + "="*60)
    print("🧪 TEST 3: Endpoint Legacy /cors/mission/nouvelle_mission")
    print("="*60)
    
    try:
        response = requests.post(f"{BASE_URL}/cors/mission/nouvelle_mission", timeout=2)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 404:
            print("   ⚠️  Endpoint legacy non trouvé")
            return False
        elif response.status_code in [400, 422]:
            print("   ✅ Endpoint legacy existe et répond")
            return True
        else:
            print(f"   ⚠️  Statut: {response.status_code}")
            return True
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_routes_info():
    """Teste l'endpoint /api/info pour voir les routes"""
    print("\n" + "="*60)
    print("🧪 TEST 4: Routes enregistrées")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/info", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint /api/info accessible")
            print(f"📋 Informations: {data}")
            return True
        else:
            print(f"⚠️  /api/info retourne: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Erreur: {e}")
        return False

def check_all_routes():
    """Liste toutes les routes disponibles"""
    print("\n" + "="*60)
    print("🧪 TEST 5: Liste de toutes les routes")
    print("="*60)
    
    endpoints_to_test = [
        "GET /health",
        "GET /api/info",
        "OPTIONS /api/v1/missions/",
        "POST /api/v1/missions/",
        "OPTIONS /cors/mission/nouvelle_mission",
        "POST /cors/mission/nouvelle_mission",
        "GET /api/v1/clients/",
    ]
    
    for endpoint in endpoints_to_test:
        method, path = endpoint.split(' ', 1)
        try:
            url = f"{BASE_URL}{path}"
            if method == "GET":
                response = requests.get(url, timeout=2)
            elif method == "POST":
                response = requests.post(url, timeout=2)
            elif method == "OPTIONS":
                response = requests.options(url, timeout=2)
            else:
                continue
            
            status_icon = "✅" if response.status_code != 404 else "❌"
            print(f"   {status_icon} {endpoint}: {response.status_code}")
            
        except Exception as e:
            print(f"   ❌ {endpoint}: Erreur - {str(e)[:50]}")

def main():
    print("="*60)
    print("🔍 DIAGNOSTIC COMPLET - API MISSION")
    print("="*60)
    
    # Test 1: Serveur
    if not test_server():
        print("\n" + "="*60)
        print("❌ ARRÊT: Le serveur Flask n'est pas démarré")
        print("="*60)
        sys.exit(1)
    
    # Test 2: Endpoint moderne
    endpoint_modern_exists = test_endpoint_exists()
    
    # Test 3: Endpoint legacy
    endpoint_legacy_exists = test_legacy_endpoint()
    
    # Test 4: Routes info
    test_routes_info()
    
    # Test 5: Liste toutes les routes
    check_all_routes()
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ")
    print("="*60)
    
    if endpoint_modern_exists:
        print("✅ Endpoint moderne /api/v1/missions/ : OK")
    else:
        print("❌ Endpoint moderne /api/v1/missions/ : NON TROUVÉ")
        print("   → Vérifiez que les routes sont bien enregistrées")
        print("   → Vérifiez les logs du serveur au démarrage")
    
    if endpoint_legacy_exists:
        print("✅ Endpoint legacy /cors/mission/nouvelle_mission : OK")
    else:
        print("⚠️  Endpoint legacy /cors/mission/nouvelle_mission : NON TROUVÉ")
    
    print("\n" + "="*60)
    print("💡 SOLUTIONS")
    print("="*60)
    
    if not endpoint_modern_exists:
        print("1. Vérifiez que le blueprint mission est enregistré dans src/routes/__init__.py")
        print("2. Vérifiez les logs du serveur Flask au démarrage")
        print("3. Cherchez '📋 Missions modernes: /api/v1/missions/' dans les logs")
        print("4. Redémarrez le serveur Flask")
    else:
        print("✅ L'endpoint moderne existe. Le problème peut venir :")
        print("   1. Des données envoyées (format, validation)")
        print("   2. De l'instance axios dans le frontend")
        print("   3. Des fichiers manquants ou invalides")

if __name__ == "__main__":
    main()








