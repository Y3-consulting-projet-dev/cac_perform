"""
Test de la connexion depuis le frontend
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_frontend_login():
    """Test de la connexion avec les paramètres du frontend"""
    
    print("🧪 Test de connexion Frontend")
    print("=" * 40)
    
    # Format utilisé par le frontend après correction
    login_data = {
        "email": "test@example.com",
        "password": "TestPass123!"
    }
    
    print("📤 Données envoyées par le frontend:")
    print(json.dumps(login_data, indent=2))
    print(f"📍 URL: {BASE_URL}/api/v1/users/login")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/users/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Connexion réussie!")
            print(f"🔑 Token reçu: {result.get('token', 'N/A')[:50]}...")
            print(f"👤 Utilisateur: {result.get('user', {}).get('email', 'N/A')}")
            return True
        else:
            print("❌ Connexion échouée")
            print(f"📝 Réponse: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
        print("   Vérifiez que le serveur Flask est démarré")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_cors_headers():
    """Test des en-têtes CORS"""
    
    print("\n🌐 Test des en-têtes CORS")
    print("=" * 30)
    
    try:
        # Test OPTIONS (preflight)
        response = requests.options(
            f"{BASE_URL}/api/v1/users/login",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        print(f"📊 OPTIONS Status: {response.status_code}")
        print(f"🔗 CORS Headers:")
        cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
        for header, value in cors_headers.items():
            print(f"   {header}: {value}")
            
        if response.status_code == 200:
            print("✅ CORS configuré correctement")
        else:
            print("❌ Problème CORS")
            
    except Exception as e:
        print(f"❌ Erreur CORS: {e}")

if __name__ == "__main__":
    print("🚀 Test de connexion Frontend - CAC Perform")
    print("=" * 50)
    
    success = test_frontend_login()
    test_cors_headers()
    
    if success:
        print("\n🎉 Le frontend devrait maintenant pouvoir se connecter!")
    else:
        print("\n❌ Il y a encore un problème à résoudre.")








