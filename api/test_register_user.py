"""
Script de test pour l'enregistrement d'utilisateurs
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_register_user():
    """Test d'enregistrement d'un nouvel utilisateur"""
    
    # Exemple d'utilisateur à enregistrer
    user_data = {
        "firstname": "Jean",
        "lastname": "Dupont",
        "email": "jean.dupont@cacperform.com",
        "password": "MotDePasse123!",
        "role": "Auditeur Senior",
        "grade": "Senior",
        "departement": "Audit"
    }
    
    print("🧪 Test d'enregistrement d'utilisateur")
    print("=" * 50)
    print(f"📤 Données envoyées:")
    print(json.dumps(user_data, indent=2, ensure_ascii=False))
    print()
    
    try:
        # Envoyer la requête POST
        response = requests.post(
            f"{BASE_URL}/api/v1/users/register",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Statut de la réponse: {response.status_code}")
        print(f"📥 Réponse du serveur:")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Utilisateur créé avec succès!")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return result
        else:
            print("❌ Erreur lors de la création:")
            try:
                error = response.json()
                print(json.dumps(error, indent=2, ensure_ascii=False))
            except:
                print(response.text)
            return None
                
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
        print("   Assurez-vous que le serveur Flask est démarré sur http://localhost:5000")
        return None
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return None

def test_multiple_users():
    """Test d'enregistrement de plusieurs utilisateurs"""
    
    users = [
        {
            "firstname": "Marie",
            "lastname": "Martin",
            "email": "marie.martin@cacperform.com",
            "password": "SecurePass456!",
            "role": "Manager",
            "grade": "Expert",
            "departement": "Conseil"
        },
        {
            "firstname": "Pierre",
            "lastname": "Durand",
            "email": "pierre.durand@cacperform.com",
            "password": "StrongPass789!",
            "role": "Auditeur",
            "grade": "Confirmé",
            "departement": "Audit"
        },
        {
            "firstname": "Sophie",
            "lastname": "Bernard",
            "email": "sophie.bernard@cacperform.com",
            "password": "MyPassword123!",
            "role": "Stagiaire",
            "grade": "Junior",
            "departement": "Expertise Comptable"
        }
    ]
    
    print("\n🧪 Test d'enregistrement de plusieurs utilisateurs")
    print("=" * 60)
    
    created_users = []
    
    for i, user_data in enumerate(users, 1):
        print(f"\n👤 Utilisateur {i}: {user_data['firstname']} {user_data['lastname']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/users/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                result = response.json()
                print(f"   ✅ Créé avec succès - ID: {result.get('user_id', 'N/A')}")
                created_users.append(result)
            else:
                print(f"   ❌ Erreur {response.status_code}")
                try:
                    error = response.json()
                    print(f"   📝 Détail: {error.get('message', 'Erreur inconnue')}")
                except:
                    print(f"   📝 Détail: {response.text}")
                    
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    print(f"\n📊 Résumé: {len(created_users)}/{len(users)} utilisateurs créés")
    return created_users

def test_validation_errors():
    """Test des erreurs de validation"""
    
    print("\n🧪 Test des erreurs de validation")
    print("=" * 40)
    
    # Test avec email invalide
    invalid_data = {
        "firstname": "Test",
        "lastname": "User",
        "email": "email-invalide",  # Email invalide
        "password": "weak",         # Mot de passe faible
        "role": "RoleInvalide",     # Rôle invalide
        "grade": "Junior",
        "departement": "Audit"
    }
    
    print("📤 Test avec données invalides:")
    print(json.dumps(invalid_data, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/users/register",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📊 Statut: {response.status_code}")
        if response.status_code == 400:
            print("✅ Validation correctement rejetée")
            error = response.json()
            print("📝 Erreurs détectées:")
            print(json.dumps(error, indent=2, ensure_ascii=False))
        else:
            print("❌ La validation aurait dû échouer")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("🚀 Tests d'enregistrement d'utilisateurs - CAC Perform")
    print("=" * 70)
    
    # Test simple
    user = test_register_user()
    
    # Test multiple
    users = test_multiple_users()
    
    # Test validation
    test_validation_errors()
    
    print("\n" + "=" * 70)
    print("🎉 Tests terminés!")








