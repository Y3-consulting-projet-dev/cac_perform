"""
Ressources REST pour la gestion des utilisateurs
"""

from flask import request, jsonify
from flask_restful import Resource
from marshmallow import ValidationError
from functools import wraps
import jwt

from src.services.user_services import UserService
from src.schemas.user_schemas import ROLES, GRADES, DEPARTEMENTS

def jwt_required(f):
    """Décorateur pour vérifier l'authentification JWT"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Récupérer le token depuis l'en-tête Authorization
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Format: "Bearer <token>"
            except IndexError:
                return {"message": "Format d'autorisation invalide"}, 401
        
        if not token:
            return {"message": "Token d'authentification requis"}, 401
        
        try:
            # Vérifier le token
            payload = UserService.verify_jwt_token(token)
            request.current_user = payload
        except ValueError as e:
            return {"message": str(e)}, 401
        except Exception as e:
            return {"message": "Token invalide"}, 401
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Décorateur pour vérifier les droits administrateur"""
    @wraps(f)
    @jwt_required
    def decorated_function(*args, **kwargs):
        if request.current_user.get('role') != 'Administrateur':
            return {"message": "Droits administrateur requis"}, 403
        return f(*args, **kwargs)
    return decorated_function

class UserRegistrationResource(Resource):
    """Ressource pour l'inscription des utilisateurs"""
    
    def post(self):
        """Inscrit un nouvel utilisateur"""
        try:
            user_data = request.get_json()
            if not user_data:
                return {"message": "Données utilisateur requises"}, 400
            
            new_user = UserService.register_user(user_data)
            return jsonify(new_user), 201
            
        except ValueError as e:
            return {"message": str(e)}, 400
        except RuntimeError as e:
            return {"message": str(e)}, 500

class UserLoginResource(Resource):
    """Ressource pour la connexion des utilisateurs"""
    
    def post(self):
        """Connecte un utilisateur"""
        try:
            login_data = request.get_json()
            if not login_data:
                return {"message": "Données de connexion requises"}, 400
            
            auth_result = UserService.authenticate_user(login_data)
            return jsonify(auth_result), 200
            
        except ValueError as e:
            return {"message": str(e)}, 401
        except RuntimeError as e:
            return {"message": str(e)}, 500

class UserProfileResource(Resource):
    """Ressource pour la gestion du profil utilisateur"""
    
    @jwt_required
    def get(self, user_id=None):
        """Récupère le profil utilisateur"""
        try:
            # Si aucun ID fourni, utiliser l'utilisateur connecté
            if user_id is None:
                user_id = request.current_user.get('user_id')
            
            # Vérifier les permissions
            current_user_id = request.current_user.get('user_id')
            current_user_role = request.current_user.get('role')
            
            if user_id != current_user_id and current_user_role != 'Administrateur':
                return {"message": "Accès non autorisé"}, 403
            
            user_profile = UserService.get_user_profile(user_id)
            if user_profile:
                return jsonify(user_profile), 200
            return {"message": "Utilisateur non trouvé"}, 404
            
        except ValueError as e:
            return {"message": str(e)}, 400
        except RuntimeError as e:
            return {"message": str(e)}, 500
    
    @jwt_required
    def put(self, user_id=None):
        """Met à jour le profil utilisateur"""
        try:
            # Si aucun ID fourni, utiliser l'utilisateur connecté
            if user_id is None:
                user_id = request.current_user.get('user_id')
            
            # Vérifier les permissions
            current_user_id = request.current_user.get('user_id')
            current_user_role = request.current_user.get('role')
            
            if user_id != current_user_id and current_user_role != 'Administrateur':
                return {"message": "Accès non autorisé"}, 403
            
            update_data = request.get_json()
            if not update_data:
                return {"message": "Données de mise à jour requises"}, 400
            
            # Les utilisateurs non-admin ne peuvent pas changer leur rôle
            if current_user_role != 'Administrateur' and 'role' in update_data:
                del update_data['role']
            
            updated_user = UserService.update_user_profile(user_id, update_data)
            if updated_user:
                return jsonify(updated_user), 200
            return {"message": "Utilisateur non trouvé ou aucune modification"}, 404
            
        except ValueError as e:
            return {"message": str(e)}, 400
        except RuntimeError as e:
            return {"message": str(e)}, 500

class UserListResource(Resource):
    """Ressource pour la liste des utilisateurs"""
    
    @admin_required
    def get(self):
        """Récupère la liste des utilisateurs (admin seulement)"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100
            
            users_data = UserService.get_all_users(page, per_page)
            return jsonify(users_data), 200
            
        except RuntimeError as e:
            return {"message": str(e)}, 500

class UserManagementResource(Resource):
    """Ressource pour la gestion administrative des utilisateurs"""
    
    @admin_required
    def patch(self, user_id):
        """Active/désactive un utilisateur"""
        try:
            action_data = request.get_json()
            if not action_data or 'action' not in action_data:
                return {"message": "Action requise (activate/deactivate)"}, 400
            
            action = action_data['action']
            
            if action == 'activate':
                success = UserService.activate_user(user_id)
                message = "Utilisateur activé avec succès" if success else "Échec de l'activation"
            elif action == 'deactivate':
                success = UserService.deactivate_user(user_id)
                message = "Utilisateur désactivé avec succès" if success else "Échec de la désactivation"
            else:
                return {"message": "Action invalide. Utilisez 'activate' ou 'deactivate'"}, 400
            
            if success:
                return {"message": message}, 200
            return {"message": "Utilisateur non trouvé"}, 404
            
        except ValueError as e:
            return {"message": str(e)}, 400
        except RuntimeError as e:
            return {"message": str(e)}, 500

class UserPasswordResource(Resource):
    """Ressource pour la gestion des mots de passe"""
    
    @jwt_required
    def put(self, user_id=None):
        """Change le mot de passe d'un utilisateur"""
        try:
            # Si aucun ID fourni, utiliser l'utilisateur connecté
            if user_id is None:
                user_id = request.current_user.get('user_id')
            
            # Vérifier les permissions
            current_user_id = request.current_user.get('user_id')
            current_user_role = request.current_user.get('role')
            
            if user_id != current_user_id and current_user_role != 'Administrateur':
                return {"message": "Accès non autorisé"}, 403
            
            password_data = request.get_json()
            if not password_data:
                return {"message": "Données de mot de passe requises"}, 400
            
            current_password = password_data.get('current_password')
            new_password = password_data.get('new_password')
            
            if not current_password or not new_password:
                return {"message": "Mot de passe actuel et nouveau requis"}, 400
            
            success = UserService.change_password(user_id, current_password, new_password)
            if success:
                return {"message": "Mot de passe modifié avec succès"}, 200
            return {"message": "Échec de la modification du mot de passe"}, 400
            
        except ValueError as e:
            return {"message": str(e)}, 400
        except RuntimeError as e:
            return {"message": str(e)}, 500

class UserStatsResource(Resource):
    """Ressource pour les statistiques des utilisateurs"""
    
    @admin_required
    def get(self):
        """Récupère les statistiques des utilisateurs"""
        try:
            stats = UserService.get_user_stats()
            return jsonify(stats), 200
            
        except RuntimeError as e:
            return {"message": str(e)}, 500

class UserMetadataResource(Resource):
    """Ressource pour les métadonnées (rôles, grades, départements)"""
    
    def get(self):
        """Récupère les métadonnées disponibles"""
        return jsonify({
            "roles": ROLES,
            "grades": GRADES,
            "departements": DEPARTEMENTS
        }), 200

class UserLogoutResource(Resource):
    """Ressource pour la déconnexion"""
    
    @jwt_required
    def post(self):
        """Déconnecte l'utilisateur"""
        # Dans une implémentation JWT stateless, la déconnexion côté serveur
        # consiste principalement à invalider le token côté client
        # Pour une invalidation côté serveur, il faudrait maintenir une blacklist
        
        return {"message": "Déconnexion réussie"}, 200

# Ressources pour la compatibilité avec l'ancien système
class LegacyLoginResource(Resource):
    """Ressource de compatibilité pour l'ancien système de connexion"""
    
    def post(self):
        """Connexion compatible avec l'ancien format"""
        try:
            data = request.get_json()
            if not data:
                return {"message": "Données de connexion requises"}, 400
            
            # Adapter l'ancien format (mail/pwd) au nouveau (email/password)
            login_data = {
                'email': data.get('mail', data.get('email')),
                'password': data.get('pwd', data.get('password'))
            }
            
            auth_result = UserService.authenticate_user(login_data)
            
            # Adapter la réponse au format attendu par l'ancien frontend
            return {
                "token": auth_result['token'],
                "user": {
                    "email": auth_result['user']['email'],
                    "_id": auth_result['user']['user_id']
                }
            }, 200
            
        except ValueError as e:
            return {"error": str(e)}, 401
        except RuntimeError as e:
            return {"error": str(e)}, 500
