#!/usr/bin/env python3
"""
Script simple pour démarrer MongoDB et l'application
"""

import subprocess
import sys
import time
import os

def run_command(cmd):
    """Exécute une commande"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_mongodb():
    """Vérifie si MongoDB est démarré"""
    print("🔍 Vérification de MongoDB...")
    
    # Vérifier les services MongoDB
    success, stdout, stderr = run_command('powershell -Command "Get-Service -Name \'*mongo*\'"')
    
    if success and "Running" in stdout:
        print("✅ MongoDB est déjà en cours d'exécution")
        return True
    elif success and "Stopped" in stdout:
        print("⚠️  MongoDB est arrêté, tentative de démarrage...")
        return start_mongodb()
    else:
        print("❌ Service MongoDB non trouvé")
        return find_and_start_mongodb()

def start_mongodb():
    """Démarre le service MongoDB"""
    print("🚀 Démarrage du service MongoDB...")
    
    success, stdout, stderr = run_command('powershell -Command "Start-Service -Name \'MongoDB\'"')
    
    if success:
        print("✅ MongoDB démarré avec succès")
        time.sleep(3)  # Attendre que MongoDB démarre
        return True
    else:
        print(f"❌ Échec du démarrage: {stderr}")
        return False

def find_and_start_mongodb():
    """Trouve et démarre MongoDB manuellement"""
    print("🔍 Recherche de l'installation MongoDB...")
    
    # Chercher mongod.exe
    paths = [
        r"C:\Program Files\MongoDB\Server\*\bin\mongod.exe",
        r"C:\Program Files (x86)\MongoDB\Server\*\bin\mongod.exe"
    ]
    
    mongod_path = None
    for path in paths:
        success, stdout, stderr = run_command(f'powershell -Command "Get-ChildItem -Path \'{path}\' -ErrorAction SilentlyContinue"')
        if success and stdout.strip():
            mongod_path = stdout.strip().split('\n')[0]
            break
    
    if not mongod_path:
        print("❌ Installation MongoDB non trouvée")
        print("💡 Installez MongoDB depuis: https://www.mongodb.com/try/download/community")
        return False
    
    print(f"✅ MongoDB trouvé: {mongod_path}")
    
    # Créer le dossier de données
    data_dir = r"C:\data\db"
    os.makedirs(data_dir, exist_ok=True)
    print(f"📁 Dossier de données créé: {data_dir}")
    
    # Démarrer MongoDB
    print("🚀 Démarrage de MongoDB...")
    try:
        process = subprocess.Popen([mongod_path, "--dbpath", data_dir])
        print("✅ MongoDB démarré manuellement")
        time.sleep(5)  # Attendre que MongoDB démarre
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def create_user():
    """Crée l'utilisateur par défaut"""
    print("👤 Création de l'utilisateur par défaut...")
    
    try:
        import pymongo
        import bcrypt
        
        client = pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        db = client['cac_perform']
        
        email = "admin@cac-perform.local"
        password = "MonMotDePasse!2026"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()
        
        db.Manager.update_one(
            {"email": email},
            {"$set": {"email": email, "mot_de_passe": hashed_password}},
            upsert=True
        )
        
        print("✅ Utilisateur créé avec succès")
        print(f"   Email: {email}")
        print(f"   Mot de passe: {password}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'utilisateur: {e}")
        return False

def start_application():
    """Démarre l'application principale"""
    print("🚀 Démarrage de l'application...")
    
    try:
        # Démarrer l'application en arrière-plan
        process = subprocess.Popen([sys.executable, 'app.py'])
        print("✅ Application démarrée")
        print("🌐 Backend disponible sur: http://localhost:5000")
        print("🔗 Frontend: http://localhost:5173")
        return process
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        return None

def main():
    """Fonction principale"""
    print("🔧 Démarrage de CAC Perform avec MongoDB")
    print("=" * 60)
    
    # Étape 1: Vérifier et démarrer MongoDB
    if not check_mongodb():
        print("❌ Impossible de démarrer MongoDB")
        print("💡 Essayez de redémarrer votre ordinateur ou réinstaller MongoDB")
        return False
    
    # Étape 2: Tester la connexion
    print("🧪 Test de connexion à MongoDB...")
    try:
        import pymongo
        client = pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        client.server_info()
        print("✅ Connexion à MongoDB réussie")
    except Exception as e:
        print(f"❌ Échec de la connexion: {e}")
        return False
    
    # Étape 3: Créer l'utilisateur
    if not create_user():
        print("❌ Impossible de créer l'utilisateur")
        return False
    
    # Étape 4: Démarrer l'application
    process = start_application()
    if not process:
        return False
    
    print("\n🎉 CAC Perform est maintenant opérationnel !")
    print("📋 Prochaines étapes:")
    print("   1. Ouvrir un nouveau terminal")
    print("   2. Aller dans le dossier clients: cd clients")
    print("   3. Démarrer le frontend: pnpm dev")
    print("   4. Se connecter avec:")
    print("      Email: admin@cac-perform.local")
    print("      Mot de passe: MonMotDePasse!2026")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Échec du démarrage")
        sys.exit(1)
    else:
        print("\n✅ Démarrage réussi !")
        input("Appuyez sur Entrée pour continuer...")
