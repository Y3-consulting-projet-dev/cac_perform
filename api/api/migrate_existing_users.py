"""
Script de migration pour les utilisateurs existants vers la nouvelle architecture
"""

import sys
import os
from datetime import datetime
from bson import ObjectId

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.database import get_db
from src.services.user_services import UserService

def migrate_users():
    """Migre les utilisateurs existants vers le nouveau format"""
    
    print("🔄 Migration des utilisateurs existants...")
    print("=" * 50)
    
    try:
        db = get_db()
        
        # Récupérer tous les utilisateurs existants
        existing_users = list(db.Manager.find({}))
        
        if not existing_users:
            print("ℹ️  Aucun utilisateur existant trouvé.")
            return
        
        print(f"📊 {len(existing_users)} utilisateur(s) trouvé(s)")
        
        migrated_count = 0
        error_count = 0
        
        for user in existing_users:
            try:
                user_id = str(user.get('_id'))
                email = user.get('email', '')
                
                print(f"\n🔄 Migration de {email}...")
                
                # Vérifier si l'utilisateur a déjà les nouveaux champs
                if user.get('user_id') and user.get('firstname'):
                    print(f"   ✅ {email} déjà migré")
                    continue
                
                # Préparer les données de migration
                update_data = {}
                
                # Générer un user_id si absent
                if not user.get('user_id'):
                    update_data['user_id'] = UserService.generate_user_id()
                
                # Extraire prénom et nom du champ 'name' si disponible
                full_name = user.get('name', '')
                if full_name and not user.get('firstname'):
                    name_parts = full_name.split(' ', 1)
                    update_data['firstname'] = name_parts[0]
                    update_data['lastname'] = name_parts[1] if len(name_parts) > 1 else name_parts[0]
                
                # Valeurs par défaut si les champs sont manquants
                if not user.get('firstname'):
                    update_data['firstname'] = update_data.get('firstname', 'Utilisateur')
                if not user.get('lastname'):
                    update_data['lastname'] = update_data.get('lastname', 'Système')
                
                # Rôle par défaut
                if not user.get('role'):
                    update_data['role'] = 'Auditeur'
                
                # Grade par défaut
                if not user.get('grade'):
                    update_data['grade'] = 'Confirmé'
                
                # Département par défaut
                if not user.get('departement'):
                    update_data['departement'] = 'Audit'
                
                # Champs de métadonnées
                if not user.get('created_at'):
                    update_data['created_at'] = datetime.now()
                
                if not user.get('is_active'):
                    update_data['is_active'] = True
                
                # Migrer le mot de passe si nécessaire
                stored_password = user.get('mot_de_passe', '')
                if stored_password and len(stored_password) < 60:  # Probablement en clair
                    print(f"   🔐 Migration du mot de passe pour {email}")
                    update_data['mot_de_passe'] = UserService.hash_password(stored_password)
                
                # Appliquer les mises à jour
                if update_data:
                    result = db.Manager.update_one(
                        {"_id": user['_id']},
                        {"$set": update_data}
                    )
                    
                    if result.modified_count > 0:
                        print(f"   ✅ {email} migré avec succès")
                        migrated_count += 1
                    else:
                        print(f"   ⚠️  Aucune modification pour {email}")
                else:
                    print(f"   ℹ️  {email} déjà à jour")
                
            except Exception as e:
                print(f"   ❌ Erreur lors de la migration de {email}: {e}")
                error_count += 1
        
        print("\n" + "=" * 50)
        print(f"✅ Migration terminée:")
        print(f"   📊 Total: {len(existing_users)} utilisateur(s)")
        print(f"   ✅ Migrés: {migrated_count}")
        print(f"   ❌ Erreurs: {error_count}")
        
        if error_count == 0:
            print("🎉 Migration réussie!")
        else:
            print("⚠️  Migration terminée avec des erreurs")
        
    except Exception as e:
        print(f"❌ Erreur critique lors de la migration: {e}")
        return False
    
    return True

def verify_migration():
    """Vérifie que la migration s'est bien déroulée"""
    
    print("\n🔍 Vérification de la migration...")
    print("=" * 40)
    
    try:
        db = get_db()
        
        # Compter les utilisateurs
        total_users = db.Manager.count_documents({})
        users_with_user_id = db.Manager.count_documents({"user_id": {"$exists": True}})
        users_with_names = db.Manager.count_documents({
            "firstname": {"$exists": True},
            "lastname": {"$exists": True}
        })
        
        print(f"📊 Statistiques:")
        print(f"   Total utilisateurs: {total_users}")
        print(f"   Avec user_id: {users_with_user_id}")
        print(f"   Avec prénom/nom: {users_with_names}")
        
        # Afficher quelques exemples
        sample_users = list(db.Manager.find({}).limit(3))
        
        print(f"\n📋 Exemples d'utilisateurs migrés:")
        for user in sample_users:
            print(f"   - {user.get('email', 'N/A')}")
            print(f"     ID: {user.get('user_id', 'N/A')}")
            print(f"     Nom: {user.get('firstname', 'N/A')} {user.get('lastname', 'N/A')}")
            print(f"     Rôle: {user.get('role', 'N/A')}")
            print(f"     Grade: {user.get('grade', 'N/A')}")
            print(f"     Département: {user.get('departement', 'N/A')}")
            print()
        
        if users_with_user_id == total_users and users_with_names == total_users:
            print("✅ Migration vérifiée avec succès!")
            return True
        else:
            print("⚠️  Migration incomplète détectée")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Script de migration des utilisateurs")
    print("=" * 60)
    
    # Vérifier la connexion à la base
    try:
        from flask import Flask
        from config import Config
        
        app = Flask(__name__)
        app.config.from_object(Config)
        
        with app.app_context():
            # Lancer la migration
            if migrate_users():
                # Vérifier la migration
                verify_migration()
            else:
                print("❌ Migration échouée")
                sys.exit(1)
    
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        print("   Assurez-vous que MongoDB est démarré et que la configuration est correcte")
        sys.exit(1)
    
    print("\n🎉 Script terminé!")






