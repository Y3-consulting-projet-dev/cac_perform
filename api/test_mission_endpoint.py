"""
Script de test pour diagnostiquer l'erreur 500 lors de la création de mission
"""
import requests
import json

def test_mission_creation():
    """Test la création de mission et affiche la réponse complète"""
    
    url = "http://localhost:5000/api/v1/missions/"
    
    # Préparer les données de test
    # Note: Ce script teste seulement la structure, pas avec de vrais fichiers
    print("🧪 Test de l'endpoint de création de mission")
    print("=" * 60)
    print(f"URL: {url}")
    print()
    
    # Test 1: Vérifier que l'endpoint répond
    print("1. Test de connexion à l'endpoint...")
    try:
        response = requests.get(url, timeout=5)
        print(f"   Status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter au serveur Flask")
        print("   💡 Assurez-vous que le serveur Flask est démarré sur http://localhost:5000")
        return
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    print()
    print("2. Pour tester la création de mission avec des fichiers:")
    print("   - Utilisez Insomnia ou Postman")
    print("   - Méthode: POST")
    print(f"   - URL: {url}")
    print("   - Body Type: Multipart Form")
    print("   - Champs requis:")
    print("     * files[]: 2 fichiers Excel")
    print("     * annee_auditee: 2024")
    print("     * id_client: <un ID client valide>")
    print("     * date_debut: 2024-01-01")
    print("     * date_fin: 2024-12-31")
    print()
    print("3. Si vous recevez une erreur 500:")
    print("   - Regardez les logs du serveur Flask (terminal)")
    print("   - Cherchez les lignes avec '❌ ERREUR'")
    print("   - Partagez ces logs pour diagnostic")
    print()
    print("4. Vérifiez aussi la réponse JSON complète:")
    print("   - Elle devrait contenir une section 'debug'")
    print("   - Cette section contient le traceback de l'erreur")

if __name__ == "__main__":
    test_mission_creation()
