#!/usr/bin/env python3
"""
Script de migration pour centraliser les connexions MongoDB
Remplace toutes les connexions directes par l'utilisation du gestionnaire centralisé
"""

import os
import re
import glob
from pathlib import Path

# Configuration
API_DIR = Path(__file__).parent
BACKUP_SUFFIX = ".backup"

# Patterns à remplacer
PATTERNS_TO_REPLACE = [
    # Connexions directes
    (
        r"from pymongo import MongoClient\s*\n.*?client = MongoClient\([^)]*\)\s*\n.*?db = client\[[^]]*\]",
        "from src.utils.database import get_database\n\n# Utilisation de la configuration centralisée\ndb = get_database()"
    ),
    (
        r"client = MongoClient\([^)]*\)\s*\ndb = client\[[^]]*\]",
        "from src.utils.database import get_database\ndb = get_database()"
    ),
    (
        r"MongoClient\('mongodb://localhost:27017/'\)",
        "# Utilisation de la configuration centralisée - voir config.py"
    ),
    # Configuration hardcodée
    (
        r'MONGO_HOST = "localhost"\s*\nMONGO_PORT = 27017\s*\nDB_NAME = "cac_perform"',
        '# Configuration centralisée dans config.py'
    ),
    # Imports inutiles après migration
    (
        r"from pymongo import MongoClient\s*\n",
        ""
    )
]

def backup_file(file_path):
    """Crée une sauvegarde du fichier"""
    backup_path = str(file_path) + BACKUP_SUFFIX
    if not os.path.exists(backup_path):
        with open(file_path, 'r', encoding='utf-8') as original:
            with open(backup_path, 'w', encoding='utf-8') as backup:
                backup.write(original.read())
        print(f"✅ Sauvegarde créée: {backup_path}")

def migrate_file(file_path):
    """Migre un fichier vers la nouvelle architecture"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # Appliquer les patterns de remplacement
        for pattern, replacement in PATTERNS_TO_REPLACE:
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
            if new_content != content:
                content = new_content
                modified = True
        
        # Sauvegarder si modifié
        if modified:
            backup_file(file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Migré: {file_path}")
            return True
        else:
            print(f"⏭️  Aucune modification nécessaire: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la migration de {file_path}: {e}")
        return False

def find_files_to_migrate():
    """Trouve tous les fichiers Python à migrer"""
    files_to_check = []
    
    # Fichiers Python dans le répertoire API
    for pattern in ["**/*.py"]:
        files_to_check.extend(glob.glob(str(API_DIR / pattern), recursive=True))
    
    # Filtrer les fichiers qui contiennent des connexions MongoDB
    files_to_migrate = []
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if any([
                    "MongoClient" in content,
                    "mongodb://localhost" in content,
                    'MONGO_HOST = "localhost"' in content
                ]):
                    files_to_migrate.append(file_path)
        except:
            continue
    
    return files_to_migrate

def create_env_template():
    """Crée un fichier .env.template avec les variables d'environnement"""
    env_template = """# Configuration CAC Perform - Template
# Copiez ce fichier vers .env et ajustez les valeurs

# Configuration Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Configuration MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB_NAME=cac_perform
# MONGO_USERNAME=your-username
# MONGO_PASSWORD=your-password
# MONGO_AUTH_SOURCE=admin

# Configuration CORS
CORS_ORIGINS=http://localhost:5173

# Configuration uploads
UPLOAD_FOLDER=uploads
"""
    
    env_template_path = API_DIR / ".env.template"
    with open(env_template_path, 'w', encoding='utf-8') as f:
        f.write(env_template)
    print(f"✅ Template d'environnement créé: {env_template_path}")

def main():
    """Fonction principale de migration"""
    print("🚀 Migration des connexions MongoDB vers la configuration centralisée")
    print("=" * 70)
    
    # Créer le template d'environnement
    create_env_template()
    
    # Trouver les fichiers à migrer
    files_to_migrate = find_files_to_migrate()
    
    if not files_to_migrate:
        print("✅ Aucun fichier à migrer trouvé")
        return
    
    print(f"📁 {len(files_to_migrate)} fichier(s) à migrer:")
    for file_path in files_to_migrate:
        print(f"   - {file_path}")
    
    print("\n🔄 Début de la migration...")
    
    # Migrer chaque fichier
    migrated_count = 0
    for file_path in files_to_migrate:
        if migrate_file(file_path):
            migrated_count += 1
    
    print("\n" + "=" * 70)
    print(f"✅ Migration terminée: {migrated_count}/{len(files_to_migrate)} fichiers migrés")
    
    if migrated_count > 0:
        print("\n📋 Actions recommandées après migration:")
        print("   1. Testez l'application pour vérifier que tout fonctionne")
        print("   2. Créez un fichier .env basé sur .env.template")
        print("   3. Supprimez les fichiers .backup une fois les tests validés")
        print("   4. Mettez à jour la documentation si nécessaire")

if __name__ == "__main__":
    main()


