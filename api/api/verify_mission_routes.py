"""
Script pour vérifier que les routes de mission sont bien enregistrées
"""

import requests
import sys

BASE_URL = "http://localhost:5000"

def check_server_running():
    """Vérifie si le serveur Flask est en cours d'exécution"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def check_mission_route():
    """Vérifie si la route de mission est accessible"""
    try:
        # Test OPTIONS pour voir si la route existe (CORS preflight)
        response = requests.options(f"{BASE_URL}/cors/mission/nouvelle_mission", timeout=2)
        return response.status_code in [200, 204, 405]  # 405 = Method Not Allowed mais route existe
    except Exception as e:
        print(f"   Erreur: {e}")
        return False

def main():
    print("="*60)
    print("🔍 VÉRIFICATION DES ROUTES DE MISSION")
    print("="*60)
    
    # Vérifier si le serveur est en cours d'exécution
    print("\n1️⃣  Vérification du serveur Flask...")
    if not check_server_running():
        print("   ❌ Le serveur Flask n'est pas en cours d'exécution")
        print("   💡 Démarrez le serveur avec: python app.py")
        sys.exit(1)
    else:
        print("   ✅ Serveur Flask est en cours d'exécution")
    
    # Vérifier la route de mission
    print("\n2️⃣  Vérification de la route /cors/mission/nouvelle_mission...")
    if check_mission_route():
        print("   ✅ La route est accessible")
    else:
        print("   ❌ La route n'est pas accessible")
        print("   💡 Vérifiez que le blueprint mission est bien enregistré")
        print("   💡 Consultez les logs du serveur Flask au démarrage")
    
    # Afficher l'endpoint complet
    print("\n3️⃣  Endpoint de création de mission:")
    print(f"   POST {BASE_URL}/cors/mission/nouvelle_mission")
    
    print("\n" + "="*60)
    print("✅ Vérification terminée")
    print("="*60)

if __name__ == "__main__":
    main()








