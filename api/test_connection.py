#!/usr/bin/env python3
"""
Script de test pour vérifier la connexion
"""

import requests
import time
import subprocess
import sys
import os

def test_connection():
    """Teste la connexion à l'API"""
    print("🧪 Test de connexion à l'API")
    print("=" * 50)
    
    # Attendre que le serveur démarre
    print("⏳ Attente du démarrage du serveur...")
    time.sleep(3)
    
    try:
        # Test de connexion
        response = requests.post(
            'http://localhost:5000/cors/manager/connexion/',
            json={
                'mail': 'admin@cac-perform.local',
                'pwd': 'MonMotDePasse!2026'
            },
            timeout=10
        )
        
        print(f"✅ Status: {response.status_code}")
        print(f"📊 Response: {response.json()}")
        
        if response.status_code == 200:
            print("🎉 Connexion réussie !")
            return True
        else:
            print("❌ Échec de la connexion")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
        print("💡 Assurez-vous que l'application est démarrée")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def start_temp_app():
    """Démarre l'application temporaire"""
    print("🚀 Démarrage de l'application temporaire...")
    
    try:
        # Démarrer l'application en arrière-plan
        process = subprocess.Popen([
            sys.executable, 'app_temp.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✅ Application démarrée")
        return process
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        return None

if __name__ == "__main__":
    print("🔧 Test de l'application CAC Perform")
    print("=" * 60)
    
    # Vérifier si l'application est déjà démarrée
    try:
        response = requests.get('http://localhost:5000', timeout=2)
        print("✅ L'application est déjà démarrée")
    except:
        print("⚠️  L'application n'est pas démarrée")
        print("🚀 Démarrage de l'application temporaire...")
        
        # Démarrer l'application
        process = start_temp_app()
        if not process:
            print("❌ Impossible de démarrer l'application")
            sys.exit(1)
    
    # Tester la connexion
    success = test_connection()
    
    if success:
        print("\n🎉 Test réussi !")
        print("📋 Vous pouvez maintenant :")
        print("   1. Ouvrir votre navigateur")
        print("   2. Aller sur http://localhost:5173")
        print("   3. Vous connecter avec :")
        print("      Email: admin@cac-perform.local")
        print("      Mot de passe: MonMotDePasse!2026")
    else:
        print("\n❌ Test échoué")
        print("💡 Vérifiez que l'application est démarrée")
