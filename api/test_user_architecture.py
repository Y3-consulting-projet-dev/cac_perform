"""
Script de test pour la nouvelle architecture de gestion des utilisateurs
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_user_metadata():
    """Test: Récupération des métadonnées"""
    print("\n--- Test: User Metadata ---")
    response = requests.get(f"{BASE_URL}/api/v1/users/metadata")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert "roles" in response.json()
    assert "grades" in response.json()
    assert "departements" in response.json()

def test_user_registration():
    """Test: Inscription d'un utilisateur"""
    print("\n--- Test: User Registration ---")
    user_data = {
        "firstname": "Jean",
        "lastname": "Dupont",
        "email": "jean.dupont@test.com",
        "password": "MotDePasse123!",
        "role": "Auditeur",
        "grade": "Senior",
        "departement": "Audit"
    }
    response = requests.post(f"{BASE_URL}/api/v1/users/register", json=user_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 201
    assert response.json()["email"] == "jean.dupont@test.com"
    return response.json()["user_id"]

def test_user_login(email="jean.dupont@test.com", password="MotDePasse123!"):
    """Test: Connexion d'un utilisateur"""
    print(f"\n--- Test: User Login ({email}) ---")
    login_data = {
        "email": email,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/api/v1/users/login", json=login_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert "token" in response.json()
    return response.json()["token"]

def test_user_profile(token):
    """Test: Récupération du profil utilisateur"""
    print("\n--- Test: User Profile ---")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/users/profile", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()["email"] == "jean.dupont@test.com"

def test_update_profile(token):
    """Test: Mise à jour du profil"""
    print("\n--- Test: Update Profile ---")
    headers = {"Authorization": f"Bearer {token}"}
    update_data = {
        "grade": "Expert",
        "departement": "Conseil"
    }
    response = requests.put(f"{BASE_URL}/api/v1/users/profile", json=update_data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()["grade"] == "Expert"

def test_change_password(token):
    """Test: Changement de mot de passe"""
    print("\n--- Test: Change Password ---")
    headers = {"Authorization": f"Bearer {token}"}
    password_data = {
        "current_password": "MotDePasse123!",
        "new_password": "NouveauMotDePasse456!"
    }
    response = requests.put(f"{BASE_URL}/api/v1/users/password", json=password_data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200

def test_logout(token):
    """Test: Déconnexion"""
    print("\n--- Test: User Logout ---")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/v1/users/logout", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200

def test_legacy_login():
    """Test: Connexion avec l'ancien format"""
    print("\n--- Test: Legacy Login ---")
    login_data = {
        "mail": "jean.dupont@test.com",
        "pwd": "NouveauMotDePasse456!"
    }
    response = requests.post(f"{BASE_URL}/cors/manager/connexion/", json=login_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert "token" in response.json()

def test_admin_features():
    """Test: Fonctionnalités administrateur"""
    print("\n--- Test: Admin Features ---")
    
    # Créer un admin
    admin_data = {
        "firstname": "Admin",
        "lastname": "System",
        "email": "admin@test.com",
        "password": "AdminPass123!",
        "role": "Administrateur",
        "grade": "Directeur",
        "departement": "Administration"
    }
    
    # Inscription admin
    response = requests.post(f"{BASE_URL}/api/v1/users/register", json=admin_data)
    print(f"Admin Registration Status: {response.status_code}")
    
    # Connexion admin
    admin_token = test_user_login("admin@test.com", "AdminPass123!")
    
    # Liste des utilisateurs
    print("\n--- Test: List Users (Admin) ---")
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/api/v1/users/", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    
    # Statistiques
    print("\n--- Test: User Stats (Admin) ---")
    response = requests.get(f"{BASE_URL}/api/v1/users/stats", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200

def test_validation_errors():
    """Test: Erreurs de validation"""
    print("\n--- Test: Validation Errors ---")
    
    # Email invalide
    invalid_user = {
        "firstname": "Test",
        "lastname": "User",
        "email": "invalid-email",
        "password": "weak",
        "role": "InvalidRole",
        "grade": "Junior",
        "departement": "Audit"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/users/register", json=invalid_user)
    print(f"Invalid Registration Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 400

if __name__ == "__main__":
    print("🚀 Démarrage des tests de la nouvelle architecture utilisateur...")
    print("=" * 70)
    
    try:
        # Tests de base
        test_user_metadata()
        user_id = test_user_registration()
        token = test_user_login()
        test_user_profile(token)
        test_update_profile(token)
        test_change_password(token)
        test_logout(token)
        
        # Test de compatibilité
        test_legacy_login()
        
        # Tests admin
        test_admin_features()
        
        # Tests d'erreurs
        test_validation_errors()
        
        print("\n" + "=" * 70)
        print("✅ Tous les tests sont passés avec succès!")
        print("✅ La nouvelle architecture utilisateur fonctionne correctement")
        
    except AssertionError as e:
        print(f"\n❌ Test échoué: {e}")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("\n❌ Impossible de se connecter au serveur")
        print("   Assurez-vous que le serveur Flask est démarré sur http://localhost:5000")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1)






