#!/usr/bin/env python3
"""
Script pour diagnostiquer et résoudre les problèmes MongoDB
"""

import subprocess
import sys
import os
import time

def run_command(cmd, shell=True):
    """Exécute une commande et retourne le résultat"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def check_mongodb_service():
    """Vérifie l'état du service MongoDB"""
    print("🔍 Vérification du service MongoDB...")
    
    # Vérifier les services MongoDB
    cmd = 'Get-Service -Name "*mongo*"'
    returncode, stdout, stderr = run_command(f'powershell -Command "{cmd}"')
    
    if returncode == 0:
        print("✅ Services MongoDB trouvés :")
        print(stdout)
        
        # Analyser l'état
        if "Stopped" in stdout:
            print("⚠️  MongoDB est arrêté")
            return "stopped"
        elif "Running" in stdout:
            print("✅ MongoDB est en cours d'exécution")
            return "running"
        else:
            print("❓ État inconnu")
            return "unknown"
    else:
        print("❌ Aucun service MongoDB trouvé")
        print(f"Erreur: {stderr}")
        return "not_found"

def start_mongodb_service():
    """Démarre le service MongoDB"""
    print("🚀 Tentative de démarrage de MongoDB...")
    
    # Essayer de démarrer le service
    cmd = 'Start-Service -Name "MongoDB"'
    returncode, stdout, stderr = run_command(f'powershell -Command "{cmd}"')
    
    if returncode == 0:
        print("✅ MongoDB démarré avec succès")
        return True
    else:
        print("❌ Échec du démarrage de MongoDB")
        print(f"Erreur: {stderr}")
        return False

def find_mongodb_installation():
    """Trouve l'installation de MongoDB"""
    print("🔍 Recherche de l'installation MongoDB...")
    
    # Chemins possibles pour MongoDB
    possible_paths = [
        r"C:\Program Files\MongoDB\Server\*\bin\mongod.exe",
        r"C:\Program Files (x86)\MongoDB\Server\*\bin\mongod.exe",
        r"C:\MongoDB\bin\mongod.exe"
    ]
    
    for path_pattern in possible_paths:
        cmd = f'Get-ChildItem -Path "{path_pattern}" -ErrorAction SilentlyContinue'
        returncode, stdout, stderr = run_command(f'powershell -Command "{cmd}"')
        
        if returncode == 0 and stdout.strip():
            print(f"✅ MongoDB trouvé : {stdout.strip()}")
            return stdout.strip()
    
    print("❌ Installation MongoDB non trouvée")
    return None

def start_mongodb_manually(mongod_path):
    """Démarre MongoDB manuellement"""
    print(f"🚀 Démarrage manuel de MongoDB : {mongod_path}")
    
    try:
        # Créer le dossier de données s'il n'existe pas
        data_dir = r"C:\data\db"
        os.makedirs(data_dir, exist_ok=True)
        
        # Démarrer MongoDB
        process = subprocess.Popen([mongod_path, "--dbpath", data_dir])
        print("✅ MongoDB démarré manuellement")
        return process
    except Exception as e:
        print(f"❌ Erreur lors du démarrage manuel : {e}")
        return None

def test_mongodb_connection():
    """Teste la connexion à MongoDB"""
    print("🧪 Test de connexion à MongoDB...")
    
    try:
        import pymongo
        client = pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        client.server_info()
        print("✅ Connexion à MongoDB réussie")
        return True
    except Exception as e:
        print(f"❌ Échec de la connexion : {e}")
        return False

def create_mongodb_user():
    """Crée l'utilisateur par défaut dans MongoDB"""
    print("👤 Création de l'utilisateur par défaut...")
    
    try:
        import pymongo
        import bcrypt
        
        client = pymongo.MongoClient('mongodb://localhost:27017/')
        db = client['cac_perform']
        
        # Créer l'utilisateur
        email = "admin@cac-perform.local"
        password = "MonMotDePasse!2026"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()
        
        # Insérer ou mettre à jour l'utilisateur
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
        print(f"❌ Erreur lors de la création de l'utilisateur : {e}")
        return False

def main():
    """Fonction principale"""
    print("🔧 Diagnostic et réparation de MongoDB")
    print("=" * 60)
    
    # Étape 1 : Vérifier l'état du service
    service_status = check_mongodb_service()
    
    if service_status == "running":
        print("✅ MongoDB est déjà en cours d'exécution")
    elif service_status == "stopped":
        print("⚠️  MongoDB est arrêté, tentative de démarrage...")
        if not start_mongodb_service():
            print("❌ Impossible de démarrer le service MongoDB")
            return False
    elif service_status == "not_found":
        print("❌ Service MongoDB non trouvé")
        mongod_path = find_mongodb_installation()
        if mongod_path:
            start_mongodb_manually(mongod_path)
        else:
            print("❌ Installation MongoDB non trouvée")
            return False
    
    # Attendre que MongoDB démarre
    print("⏳ Attente du démarrage de MongoDB...")
    time.sleep(5)
    
    # Étape 2 : Tester la connexion
    if not test_mongodb_connection():
        print("❌ Impossible de se connecter à MongoDB")
        return False
    
    # Étape 3 : Créer l'utilisateur
    if not create_mongodb_user():
        print("❌ Impossible de créer l'utilisateur")
        return False
    
    print("\n🎉 MongoDB est maintenant opérationnel !")
    print("📋 Vous pouvez maintenant :")
    print("   1. Démarrer l'application : python app.py")
    print("   2. Démarrer le frontend : pnpm dev")
    print("   3. Se connecter avec :")
    print("      Email: admin@cac-perform.local")
    print("      Mot de passe: MonMotDePasse!2026")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Échec de la réparation de MongoDB")
        print("💡 Essayez de :")
        print("   1. Redémarrer votre ordinateur")
        print("   2. Réinstaller MongoDB")
        print("   3. Utiliser l'application temporaire (app_temp.py)")
        sys.exit(1)
    else:
        print("\n✅ MongoDB réparé avec succès !")
