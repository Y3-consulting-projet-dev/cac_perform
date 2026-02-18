#!/usr/bin/env python3
"""
Script simple pour démarrer MongoDB en arrière-plan
"""
import subprocess
import os
import time
import glob
import sys

def find_mongod():
    """Trouve l'exécutable mongod.exe"""
    search_paths = [
        r"C:\Program Files\MongoDB\Server\*\bin\mongod.exe",
        r"C:\Program Files (x86)\MongoDB\Server\*\bin\mongod.exe"
    ]
    
    for path_pattern in search_paths:
        matches = glob.glob(path_pattern)
        if matches:
            return matches[0]
    
    return None

def check_mongodb_running():
    """Vérifie si MongoDB est déjà en cours d'exécution"""
    try:
        result = subprocess.run(
            ['netstat', '-an'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if ':27017' in result.stdout and 'LISTENING' in result.stdout:
            return True
    except:
        pass
    return False

def main():
    print("=" * 60)
    print("  Demarrage de MongoDB")
    print("=" * 60)
    print()
    
    # Vérifier si MongoDB est déjà en cours d'exécution
    if check_mongodb_running():
        print("[OK] MongoDB est deja en cours d'execution")
        print("[OK] MongoDB est accessible sur localhost:27017")
        return 0
    
    # Trouver MongoDB
    print("[1/3] Recherche de MongoDB...")
    mongod_path = find_mongod()
    
    if not mongod_path:
        print("[ERREUR] MongoDB non trouve")
        print("[INFO] Installez MongoDB depuis: https://www.mongodb.com/try/download/community")
        return 1
    
    print(f"[OK] MongoDB trouve: {mongod_path}")
    
    # Créer le dossier de données
    print("[2/3] Preparation du dossier de donnees...")
    data_dir = r"C:\data\db"
    os.makedirs(data_dir, exist_ok=True)
    print(f"[OK] Dossier de donnees: {data_dir}")
    
    # Démarrer MongoDB
    print("[3/3] Demarrage de MongoDB en arriere-plan...")
    try:
        # Démarrer MongoDB en arrière-plan
        process = subprocess.Popen(
            [mongod_path, "--dbpath", data_dir],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        print(f"[OK] MongoDB demarre (PID: {process.pid})")
        print("[INFO] Attente de 5 secondes pour que MongoDB demarre...")
        time.sleep(5)
        
        # Vérifier que MongoDB écoute
        if check_mongodb_running():
            print("[OK] MongoDB est maintenant accessible sur localhost:27017")
            print()
            print("=" * 60)
            print("  MongoDB est pret !")
            print("=" * 60)
            print()
            print("Vous pouvez maintenant lancer l'application avec:")
            print("  python app.py")
            print()
            print("IMPORTANT: MongoDB continuera de fonctionner en arriere-plan")
            print("Pour arreter MongoDB, utilisez: taskkill /F /IM mongod.exe")
            print()
            return 0
        else:
            print("[ATTENTION] MongoDB a demarre mais le port 27017 n'est pas encore actif")
            print("[INFO] Attendez quelques secondes et verifiez avec: netstat -an | findstr :27017")
            return 0
            
    except Exception as e:
        print(f"[ERREUR] Impossible de demarrer MongoDB: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())










