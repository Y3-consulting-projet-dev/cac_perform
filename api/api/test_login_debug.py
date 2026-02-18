"""
Script de debug pour l'API de connexion
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_login_debug():
    """Test de debug pour la connexion"""
    
    print("🔍 Debug de l'API de connexion")
    print("=" * 50)
    
    # Test 1: Vérifier les métadonnées
    print("\n1️⃣ Test des métadonnées...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/users/metadata")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Métadonnées OK")
        else:
            print(f"   ❌ Erreur métadonnées: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 2: Créer un utilisateur de test
    print("\n2️⃣ Création d'un utilisateur de test...")
    test_user = {
        "firstname": "Test",
        "lastname": "User",
        "email": "test@example.com",
        "password": "TestPass123!",
        "role": "Auditeur",
        "grade": "Junior",
        "departement": "Audit"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/users/register", json=test_user)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            print("   ✅ Utilisateur créé")
        elif response.status_code == 400 and "existe déjà" in response.text:
            print("   ℹ️  Utilisateur existe déjà")
        else:
            print(f"   ❌ Erreur création: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 3: Connexion avec le nouveau format
    print("\n3️⃣ Test connexion (nouveau format)...")
    login_data = {
        "email": "test@example.com",
        "password": "TestPass123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/users/login", json=login_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Connexion réussie!")
            print(f"   Token: {result.get('token', 'N/A')[:50]}...")
            return result.get('token')
        else:
            print("   ❌ Connexion échouée")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 4: Connexion avec l'ancien format (compatibilité)
    print("\n4️⃣ Test connexion (ancien format)...")
    old_login_data = {
        "mail": "test@example.com",
        "pwd": "TestPass123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/cors/manager/connexion/", json=old_login_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Connexion compatibilité OK!")
        else:
            print("   ❌ Connexion compatibilité échouée")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 5: Vérifier la santé de l'API
    print("\n5️⃣ Test de santé de l'API...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            health = response.json()
            print(f"   Database: {health.get('database', {}).get('connected', 'Unknown')}")
        else:
            print(f"   ❌ Santé: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    test_login_debug()
