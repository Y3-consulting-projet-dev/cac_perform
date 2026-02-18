"""
Système de routes centralisé pour l'application CAC Perform
"""

from flask import Blueprint
from src.resources.client_resources import (
    new_cust,
    show_cust,
    show_info,
    update_cust,
    delete_cust,
    ClientResource
)
from src.resources.user_resources import (
    UserRegistrationResource,
    UserLoginResource,
    UserProfileResource,
    UserListResource,
    UserManagementResource,
    UserPasswordResource,
    UserStatsResource,
    UserMetadataResource,
    UserLogoutResource,
    LegacyLoginResource
)
from src.resources.mission_resources import MissionResource
from src.mission import mission

def register_routes(app):
    """
    Enregistre toutes les routes de l'application
    
    Args:
        app: Instance de l'application Flask
    """
    
    # ========================================
    # Routes Client (API REST moderne)
    # ========================================
    
    # Blueprint pour les clients avec préfixe
    client_bp = Blueprint('client_api', __name__, url_prefix='/api/v1/clients')
    
    # Routes RESTful modernes
    @client_bp.route('/', methods=['GET'])
    def list_clients():
        """GET /api/v1/clients/ - Liste tous les clients"""
        return ClientResource.get_all_clients()
    
    @client_bp.route('/', methods=['POST'])
    def create_client():
        """POST /api/v1/clients/ - Crée un nouveau client"""
        return ClientResource.create_client()
    
    @client_bp.route('/<client_id>', methods=['GET'])
    def get_client(client_id):
        """GET /api/v1/clients/<id> - Récupère un client spécifique"""
        return ClientResource.get_client_info(client_id)
    
    @client_bp.route('/<client_id>', methods=['PUT'])
    def update_client(client_id):
        """PUT /api/v1/clients/<id> - Met à jour un client"""
        from flask import request
        data = request.get_json()
        if data:
            data['_id'] = client_id
        return ClientResource.update_client()
    
    @client_bp.route('/<client_id>', methods=['DELETE'])
    def delete_client(client_id):
        """DELETE /api/v1/clients/<id> - Supprime un client"""
        return ClientResource.delete_client(client_id)
    
    @client_bp.route('/referentiels', methods=['GET'])
    def get_referentiels():
        """GET /api/v1/clients/referentiels - Liste les référentiels disponibles"""
        return ClientResource.get_referentiels()
    
    # Enregistrer le blueprint client
    app.register_blueprint(client_bp)
    
    
    # ========================================
    # Routes Mission (API REST moderne)
    # ========================================
    
    # Blueprint pour les missions avec préfixe
    mission_bp = Blueprint('mission_api', __name__, url_prefix='/api/v1/missions')
    
    @mission_bp.route('/', methods=['POST'])
    def create_mission():
        """POST /api/v1/missions/ - Crée une nouvelle mission"""
        return MissionResource.create_mission()

    @mission_bp.route('/', methods=['GET'])
    def get_all_missions():
        """GET /api/v1/missions/ - Liste toutes les missions"""
        return MissionResource.get_all_missions()
    
    @mission_bp.route('/<mission_id>', methods=['GET'])
    def get_mission(mission_id):
        """GET /api/v1/missions/<id> - Récupère une mission spécifique"""
        return MissionResource.get_mission(mission_id)
    
    @mission_bp.route('/<mission_id>', methods=['DELETE'])
    def delete_mission(mission_id):
        """DELETE /api/v1/missions/<id> - Supprime une mission"""
        return MissionResource.delete_mission(mission_id)
    
    @mission_bp.route('/client/<client_id>', methods=['GET'])
    def get_client_missions(client_id):
        """GET /api/v1/missions/client/<client_id> - Liste toutes les missions d'un client"""
        return MissionResource.get_client_missions(client_id)
    
    # Enregistrer le blueprint mission
    app.register_blueprint(mission_bp)
    
    
    # ========================================
    # Routes Utilisateurs (API REST moderne)
    # ========================================
    
    # Blueprint pour les utilisateurs avec préfixe
    user_bp = Blueprint('user_api', __name__, url_prefix='/api/v1/users')
    
    # Routes d'authentification
    @user_bp.route('/register', methods=['POST'])
    def register_user():
        """POST /api/v1/users/register - Inscription"""
        return UserRegistrationResource().post()
    
    @user_bp.route('/login', methods=['POST'])
    def login_user():
        """POST /api/v1/users/login - Connexion"""
        return UserLoginResource().post()
    
    @user_bp.route('/logout', methods=['POST'])
    def logout_user():
        """POST /api/v1/users/logout - Déconnexion"""
        return UserLogoutResource().post()
    
    # Routes de profil
    @user_bp.route('/profile', methods=['GET'])
    def get_current_profile():
        """GET /api/v1/users/profile - Profil utilisateur connecté"""
        return UserProfileResource().get()
    
    @user_bp.route('/profile', methods=['PUT'])
    def update_current_profile():
        """PUT /api/v1/users/profile - Mise à jour profil connecté"""
        return UserProfileResource().put()
    
    @user_bp.route('/<user_id>/profile', methods=['GET'])
    def get_user_profile(user_id):
        """GET /api/v1/users/<id>/profile - Profil utilisateur spécifique"""
        return UserProfileResource().get(user_id)
    
    @user_bp.route('/<user_id>/profile', methods=['PUT'])
    def update_user_profile(user_id):
        """PUT /api/v1/users/<id>/profile - Mise à jour profil spécifique"""
        return UserProfileResource().put(user_id)
    
    # Routes de gestion des mots de passe
    @user_bp.route('/password', methods=['PUT'])
    def change_current_password():
        """PUT /api/v1/users/password - Changer mot de passe connecté"""
        return UserPasswordResource().put()
    
    @user_bp.route('/<user_id>/password', methods=['PUT'])
    def change_user_password(user_id):
        """PUT /api/v1/users/<id>/password - Changer mot de passe spécifique"""
        return UserPasswordResource().put(user_id)
    
    # Routes d'administration
    @user_bp.route('/', methods=['GET'])
    def list_users():
        """GET /api/v1/users/ - Liste des utilisateurs (admin)"""
        return UserListResource().get()
    
    @user_bp.route('/<user_id>/manage', methods=['PATCH'])
    def manage_user(user_id):
        """PATCH /api/v1/users/<id>/manage - Activer/désactiver utilisateur"""
        return UserManagementResource().patch(user_id)
    
    @user_bp.route('/stats', methods=['GET'])
    def get_user_stats():
        """GET /api/v1/users/stats - Statistiques utilisateurs"""
        return UserStatsResource().get()
    
    @user_bp.route('/metadata', methods=['GET'])
    def get_user_metadata():
        """GET /api/v1/users/metadata - Métadonnées (rôles, grades, etc.)"""
        return UserMetadataResource().get()
    
    # Enregistrer le blueprint utilisateurs
    app.register_blueprint(user_bp)
    
    
    # ========================================
    # Routes de compatibilité (anciennes URLs)
    # ========================================
    
    # Blueprint pour la compatibilité avec l'ancien système
    compat_bp = Blueprint('client_compat', __name__, url_prefix='/cors/client')
    
    @compat_bp.route('/afficher_clients/', methods=['GET'])
    def show_clients_compat():
        """Compatibilité: GET /cors/client/afficher_clients/"""
        return show_cust()
    
    @compat_bp.route('/info_client/<client_id>', methods=['GET'])
    def show_client_info_compat(client_id):
        """Compatibilité: GET /cors/client/info_client/<id>"""
        return show_info(client_id)
    
    @compat_bp.route('/nouveau_client/', methods=['POST'])
    def create_client_compat():
        """Compatibilité: POST /cors/client/nouveau_client/"""
        return new_cust()
    
    @compat_bp.route('/modifier_client/', methods=['PUT'])
    def update_client_compat():
        """Compatibilité: PUT /cors/client/modifier_client/"""
        return update_cust()
    
    @compat_bp.route('/supprimer_client/<client_id>', methods=['DELETE'])
    def delete_client_compat(client_id):
        """Compatibilité: DELETE /cors/client/supprimer_client/<id>"""
        return delete_cust(client_id)
    
    # Enregistrer le blueprint de compatibilité
    app.register_blueprint(compat_bp)
    
    
    # ========================================
    # Routes de compatibilité sans préfixe /cors/ (pour le frontend)
    # ========================================
    
    # Blueprint pour les routes client sans préfixe /cors/
    client_direct_bp = Blueprint('client_direct', __name__, url_prefix='/client')
    
    @client_direct_bp.route('/afficher_clients/', methods=['GET'])
    def show_clients_direct():
        """Compatibilité: GET /client/afficher_clients/"""
        return show_cust()
    
    @client_direct_bp.route('/info_client/<client_id>', methods=['GET'])
    def show_client_info_direct(client_id):
        """Compatibilité: GET /client/info_client/<id>"""
        return show_info(client_id)
    
    @client_direct_bp.route('/nouveau_client/', methods=['POST'])
    def create_client_direct():
        """Compatibilité: POST /client/nouveau_client/"""
        return new_cust()
    
    @client_direct_bp.route('/modifier_client/', methods=['PUT'])
    def update_client_direct():
        """Compatibilité: PUT /client/modifier_client/"""
        return update_cust()
    
    @client_direct_bp.route('/supprimer_client/<client_id>', methods=['DELETE'])
    def delete_client_direct(client_id):
        """Compatibilité: DELETE /client/supprimer_client/<id>"""
        return delete_cust(client_id)
    
    # Enregistrer le blueprint direct (sans /cors/)
    app.register_blueprint(client_direct_bp)
    
    
    # ========================================
    # Routes Mission
    # ========================================
    
    # Enregistrer le blueprint mission existant
    app.register_blueprint(mission)
    
    
    # ========================================
    # Routes de compatibilité utilisateurs
    # ========================================
    
    # Blueprint pour la compatibilité avec l'ancien système d'auth
    auth_compat_bp = Blueprint('auth_compat', __name__, url_prefix='/cors/manager')
    
    @auth_compat_bp.route('/connexion/', methods=['POST'])
    def legacy_login():
        """Compatibilité: POST /cors/manager/connexion/"""
        return LegacyLoginResource().post()
    
    # Enregistrer le blueprint de compatibilité auth
    app.register_blueprint(auth_compat_bp)
    
    
    # ========================================
    # Routes système et monitoring
    # ========================================
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Endpoint de vérification de santé"""
        from flask import jsonify
        from src.utils.database import check_connection, get_database_stats
        
        try:
            db_connected = check_connection()
            db_stats = get_database_stats() if db_connected else None
            
            return jsonify({
                "status": "healthy" if db_connected else "degraded",
                "database": {
                    "connected": db_connected,
                    "stats": db_stats
                },
                "version": "1.0.0",
                "environment": app.config.get('ENV', 'unknown')
            }), 200 if db_connected else 503
            
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "error": str(e)
            }), 500
    
    
    @app.route('/api/info', methods=['GET'])
    def api_info():
        """Informations sur l'API"""
        from flask import jsonify
        
        return jsonify({
            "name": "CAC Perform API",
            "version": "1.0.0",
            "description": "API pour la gestion des missions d'audit CAC",
            "endpoints": {
                "clients": {
                    "modern": "/api/v1/clients/",
                    "legacy": "/cors/client/"
                },
                "health": "/health",
                "info": "/api/info"
            }
        })
    
    
    # ========================================
    # Logging des routes enregistrées
    # ========================================
    
    print("✅ Routes enregistrées:")
    print("   📁 Clients modernes: /api/v1/clients/")
    print("   📋 Missions modernes: /api/v1/missions/")
    print("   👤 Utilisateurs modernes: /api/v1/users/")
    print("   📁 Clients compatibilité: /cors/client/")
    print("   📁 Clients frontend: /client/")
    print("   📋 Missions compatibilité: /cors/mission/")
    print("   🔐 Auth compatibilité: /cors/manager/")
    print("   🏥 Santé: /health")
    print("   ℹ️  Info: /api/info")
