"""
Services pour la gestion des utilisateurs
"""

from typing import Dict, List, Optional, Any, Tuple
from bson import ObjectId
from pymongo.errors import PyMongoError, DuplicateKeyError
from marshmallow import ValidationError
from datetime import datetime, timedelta
import bcrypt
import jwt
import os
import secrets
import string

from src.schemas.user_schemas import (
    validate_user_registration,
    validate_user_login,
    validate_user_update,
    serialize_user,
    serialize_user_list,
    serialize_token_response
)
from src.utils.database import get_db

class UserService:
    """Service pour la gestion des utilisateurs"""
    
    # Configuration JWT
    JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 8
    
    @staticmethod
    def generate_user_id() -> str:
        """Génère un ID utilisateur unique"""
        return f"USR_{datetime.now().strftime('%Y%m%d')}_{secrets.token_hex(4).upper()}"
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hache un mot de passe avec bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Vérifie un mot de passe contre son hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def generate_jwt_token(user_data: Dict[str, Any]) -> Tuple[str, int]:
        """Génère un token JWT pour l'utilisateur"""
        expiration_time = datetime.utcnow() + timedelta(hours=UserService.JWT_EXPIRATION_HOURS)
        expires_in = UserService.JWT_EXPIRATION_HOURS * 3600  # en secondes
        
        payload = {
            'user_id': str(user_data.get('_id')),
            'email': user_data.get('email'),
            'role': user_data.get('role'),
            'iat': datetime.utcnow(),
            'exp': expiration_time
        }
        
        token = jwt.encode(payload, UserService.JWT_SECRET, algorithm=UserService.JWT_ALGORITHM)
        return token, expires_in
    
    @staticmethod
    def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
        """Vérifie et décode un token JWT"""
        try:
            payload = jwt.decode(token, UserService.JWT_SECRET, algorithms=[UserService.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expiré")
        except jwt.InvalidTokenError:
            raise ValueError("Token invalide")
    
    @staticmethod
    def register_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inscrit un nouvel utilisateur"""
        try:
            db = get_db()
            
            # Validation des données
            validated_data = validate_user_registration(user_data)
            
            # Vérifier si l'email existe déjà
            existing_user = db.Manager.find_one({"email": validated_data['email']})
            if existing_user:
                raise ValueError("Un utilisateur avec cet email existe déjà")
            
            # Générer l'ID utilisateur
            validated_data['user_id'] = UserService.generate_user_id()
            
            # Hacher le mot de passe
            validated_data['mot_de_passe'] = UserService.hash_password(validated_data.pop('password'))
            
            # Ajouter les champs de métadonnées
            validated_data.update({
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True,
                'login_attempts': 0,
                'locked_until': None
            })
            
            # Insérer en base
            result = db.Manager.insert_one(validated_data)
            
            # Récupérer l'utilisateur créé
            new_user = db.Manager.find_one({"_id": result.inserted_id})
            return serialize_user(new_user)
            
        except ValidationError as e:
            raise ValueError(f"Erreur de validation: {e.messages}")
        except DuplicateKeyError:
            raise ValueError("Un utilisateur avec cet email existe déjà")
        except PyMongoError as e:
            raise RuntimeError(f"Erreur de base de données lors de l'inscription: {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue lors de l'inscription: {e}")
    
    @staticmethod
    def authenticate_user(login_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authentifie un utilisateur et retourne un token"""
        try:
            db = get_db()
            
            # Validation des données
            validated_data = validate_user_login(login_data)
            
            # Rechercher l'utilisateur
            user = db.Manager.find_one({"email": validated_data['email']})
            if not user:
                raise ValueError("Email ou mot de passe incorrect")
            
            # Vérifier si le compte est actif
            if not user.get('is_active', True):
                raise ValueError("Compte désactivé")
            
            # Vérifier si le compte est verrouillé
            locked_until = user.get('locked_until')
            if locked_until and datetime.now() < locked_until:
                raise ValueError("Compte temporairement verrouillé")
            
            # Vérifier le mot de passe
            stored_password = user.get('mot_de_passe', '')
            password_valid = False
            
            # Essayer d'abord avec bcrypt
            if UserService.verify_password(validated_data['password'], stored_password):
                password_valid = True
            # Fallback pour les anciens mots de passe en clair
            elif stored_password == validated_data['password']:
                password_valid = True
                # Mettre à jour avec un hash bcrypt
                new_hash = UserService.hash_password(validated_data['password'])
                db.Manager.update_one(
                    {"_id": user['_id']},
                    {"$set": {"mot_de_passe": new_hash}}
                )
            
            if not password_valid:
                # Incrémenter les tentatives de connexion
                attempts = user.get('login_attempts', 0) + 1
                update_data = {"login_attempts": attempts}
                
                # Verrouiller après 5 tentatives
                if attempts >= 5:
                    update_data['locked_until'] = datetime.now() + timedelta(minutes=30)
                
                db.Manager.update_one({"_id": user['_id']}, {"$set": update_data})
                raise ValueError("Email ou mot de passe incorrect")
            
            # Connexion réussie - mettre à jour les informations
            db.Manager.update_one(
                {"_id": user['_id']},
                {
                    "$set": {
                        "last_login": datetime.now(),
                        "login_attempts": 0
                    },
                    "$unset": {"locked_until": ""}
                }
            )
            
            # Générer le token JWT
            token, expires_in = UserService.generate_jwt_token(user)
            
            # Sérialiser les données utilisateur
            user_data = serialize_user(user)
            
            return serialize_token_response(token, user_data, expires_in)
            
        except ValidationError as e:
            raise ValueError(f"Erreur de validation: {e.messages}")
        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Erreur de base de données lors de la connexion: {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue lors de la connexion: {e}")
    
    @staticmethod
    def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
        """Récupère le profil d'un utilisateur"""
        try:
            db = get_db()
            
            if not ObjectId.is_valid(user_id):
                raise ValueError("ID utilisateur invalide")
            
            user = db.Manager.find_one({"_id": ObjectId(user_id)})
            if user:
                return serialize_user(user)
            return None
            
        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Erreur de base de données: {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue: {e}")
    
    @staticmethod
    def update_user_profile(user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Met à jour le profil d'un utilisateur"""
        try:
            db = get_db()
            
            if not ObjectId.is_valid(user_id):
                raise ValueError("ID utilisateur invalide")
            
            # Validation des données
            validated_data = validate_user_update(update_data)
            
            # Vérifier si l'email est déjà utilisé par un autre utilisateur
            if 'email' in validated_data:
                existing = db.Manager.find_one({
                    "email": validated_data['email'],
                    "_id": {"$ne": ObjectId(user_id)}
                })
                if existing:
                    raise ValueError("Cet email est déjà utilisé par un autre utilisateur")
            
            # Mettre à jour
            result = db.Manager.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": validated_data}
            )
            
            if result.modified_count > 0:
                updated_user = db.Manager.find_one({"_id": ObjectId(user_id)})
                return serialize_user(updated_user)
            return None
            
        except ValidationError as e:
            raise ValueError(f"Erreur de validation: {e.messages}")
        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Erreur de base de données: {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue: {e}")
    
    @staticmethod
    def get_all_users(page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Récupère tous les utilisateurs avec pagination"""
        try:
            db = get_db()
            
            skip = (page - 1) * per_page
            
            # Compter le total
            total = db.Manager.count_documents({})
            
            # Récupérer les utilisateurs
            users = list(
                db.Manager.find({})
                .sort("created_at", -1)
                .skip(skip)
                .limit(per_page)
            )
            
            return {
                "users": serialize_user_list(users),
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page
                }
            }
            
        except PyMongoError as e:
            raise RuntimeError(f"Erreur de base de données: {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue: {e}")
    
    @staticmethod
    def deactivate_user(user_id: str) -> bool:
        """Désactive un utilisateur"""
        try:
            db = get_db()
            
            if not ObjectId.is_valid(user_id):
                raise ValueError("ID utilisateur invalide")
            
            result = db.Manager.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_active": False}}
            )
            
            return result.modified_count > 0
            
        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Erreur de base de données: {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue: {e}")
    
    @staticmethod
    def activate_user(user_id: str) -> bool:
        """Active un utilisateur"""
        try:
            db = get_db()
            
            if not ObjectId.is_valid(user_id):
                raise ValueError("ID utilisateur invalide")
            
            result = db.Manager.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {"is_active": True},
                    "$unset": {"locked_until": "", "login_attempts": ""}
                }
            )
            
            return result.modified_count > 0
            
        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Erreur de base de données: {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue: {e}")
    
    @staticmethod
    def change_password(user_id: str, current_password: str, new_password: str) -> bool:
        """Change le mot de passe d'un utilisateur"""
        try:
            db = get_db()
            
            if not ObjectId.is_valid(user_id):
                raise ValueError("ID utilisateur invalide")
            
            # Récupérer l'utilisateur
            user = db.Manager.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise ValueError("Utilisateur non trouvé")
            
            # Vérifier l'ancien mot de passe
            stored_password = user.get('mot_de_passe', '')
            if not UserService.verify_password(current_password, stored_password):
                # Fallback pour les anciens mots de passe
                if stored_password != current_password:
                    raise ValueError("Mot de passe actuel incorrect")
            
            # Hacher le nouveau mot de passe
            new_hash = UserService.hash_password(new_password)
            
            # Mettre à jour
            result = db.Manager.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"mot_de_passe": new_hash}}
            )
            
            return result.modified_count > 0
            
        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Erreur de base de données: {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue: {e}")
    
    @staticmethod
    def get_user_stats() -> Dict[str, Any]:
        """Récupère les statistiques des utilisateurs"""
        try:
            db = get_db()
            
            # Compter par rôle
            pipeline_role = [
                {"$group": {"_id": "$role", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            # Compter par département
            pipeline_dept = [
                {"$group": {"_id": "$departement", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            # Utilisateurs actifs/inactifs
            total_users = db.Manager.count_documents({})
            active_users = db.Manager.count_documents({"is_active": True})
            inactive_users = total_users - active_users
            
            # Dernières connexions
            recent_logins = list(
                db.Manager.find(
                    {"last_login": {"$ne": None}},
                    {"email": 1, "firstname": 1, "lastname": 1, "last_login": 1}
                ).sort("last_login", -1).limit(10)
            )
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "by_role": list(db.Manager.aggregate(pipeline_role)),
                "by_department": list(db.Manager.aggregate(pipeline_dept)),
                "recent_logins": serialize_user_list(recent_logins)
            }
            
        except PyMongoError as e:
            raise RuntimeError(f"Erreur de base de données: {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue: {e}")
