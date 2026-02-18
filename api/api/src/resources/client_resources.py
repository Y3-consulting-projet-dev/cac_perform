"""
Resources (contrôleurs) pour les clients
Gère les requêtes HTTP et les réponses
"""

from flask import request, jsonify, make_response
from marshmallow import ValidationError
from typing import Dict, Any

from src.services.client_services import ClientService
from src.schemas.client_schemas import serialize_client, serialize_client_list


class ClientResource:
    """Contrôleur pour les opérations sur les clients"""
    
    @staticmethod
    def create_client():
        """
        POST /cors/client/nouveau_client/
        Crée un nouveau client
        """
        try:
            # Récupérer les données JSON
            data = request.get_json()
            
            if not data:
                return make_response(jsonify({
                    "response": "error",
                    "message": "Aucune donnée reçue"
                }), 400)
            
            # Créer le client via le service
            result = ClientService.create_client(data)
            
            return make_response(jsonify({
                "response": result["client_id"],
                "message": result["message"]
            }), 200)
            
        except ValidationError as e:
            return make_response(jsonify({
                "response": "error",
                "message": "Erreurs de validation",
                "errors": e.messages
            }), 400)
            
        except ValueError as e:
            return make_response(jsonify({
                "response": "error",
                "message": str(e)
            }), 400)
            
        except Exception as e:
            return make_response(jsonify({
                "response": "error",
                "message": f"Erreur serveur: {str(e)}"
            }), 500)
    
    
    @staticmethod
    def get_all_clients():
        """
        GET /cors/client/afficher_clients/
        Récupère tous les clients
        """
        try:
            clients = ClientService.get_all_clients()
            
            if clients:
                return make_response(jsonify({
                    "response": clients,
                    "total": len(clients)
                }), 200)
            else:
                return make_response(jsonify({
                    "response": [],
                    "total": 0
                }), 200)
                
        except Exception as e:
            return make_response(jsonify({
                "response": "error",
                "message": f"Erreur serveur: {str(e)}"
            }), 500)
    
    
    @staticmethod
    def get_client_info(client_id: str):
        """
        GET /cors/client/info_client/<id>
        Récupère les informations d'un client avec ses missions
        """
        try:
            if not client_id:
                return make_response(jsonify({
                    "response": "error",
                    "message": "ID client requis"
                }), 400)
            
            # Récupérer le client avec ses missions
            client_data = ClientService.get_client_with_missions(client_id)
            
            if client_data:
                return make_response(jsonify({
                    "response": client_data
                }), 200)
            else:
                return make_response(jsonify({
                    "response": "error",
                    "message": "Client non trouvé"
                }), 404)
                
        except Exception as e:
            return make_response(jsonify({
                "response": "error",
                "message": f"Erreur serveur: {str(e)}"
            }), 500)
    
    
    @staticmethod
    def update_client():
        """
        PUT /cors/client/modifier_client/
        Met à jour un client existant
        """
        try:
            # Récupérer les données JSON
            data = request.get_json()
            
            if not data:
                return make_response(jsonify({
                    "response": "error",
                    "message": "Aucune donnée reçue"
                }), 400)
            
            if '_id' not in data:
                return make_response(jsonify({
                    "response": "error",
                    "message": "ID client requis pour la modification"
                }), 400)
            
            # Mettre à jour le client via le service
            result = ClientService.update_client(data)
            
            return make_response(jsonify({
                "response": "success",
                "message": result["message"],
                "modified_count": result["modified_count"]
            }), 200)
            
        except ValidationError as e:
            return make_response(jsonify({
                "response": "error",
                "message": "Erreurs de validation",
                "errors": e.messages
            }), 400)
            
        except ValueError as e:
            return make_response(jsonify({
                "response": "error",
                "message": str(e)
            }), 400)
            
        except Exception as e:
            return make_response(jsonify({
                "response": "error",
                "message": f"Erreur serveur: {str(e)}"
            }), 500)
    
    
    @staticmethod
    def delete_client(client_id: str):
        """
        DELETE /cors/client/supprimer_client/<id>
        Supprime un client et toutes ses missions associées
        """
        try:
            if not client_id:
                return make_response(jsonify({
                    "response": "error",
                    "message": "ID client requis"
                }), 400)
            
            # Supprimer le client via le service
            result = ClientService.delete_client(client_id)
            
            return make_response(jsonify({
                "response": "success",
                "message": result["message"],
                "client_name": result["client_name"],
                "missions_deleted": result["missions_deleted"]
            }), 200)
            
        except ValueError as e:
            return make_response(jsonify({
                "response": "error",
                "message": str(e)
            }), 404)
            
        except Exception as e:
            return make_response(jsonify({
                "response": "error",
                "message": f"Erreur serveur: {str(e)}"
            }), 500)
    
    
    @staticmethod
    def get_referentiels():
        """
        GET /cors/client/referentiels/
        Récupère la liste des référentiels disponibles
        """
        try:
            referentiels = ClientService.get_available_referentiels()
            
            return make_response(jsonify({
                "response": referentiels
            }), 200)
            
        except Exception as e:
            return make_response(jsonify({
                "response": "error",
                "message": f"Erreur serveur: {str(e)}"
            }), 500)


# Fonctions de compatibilité avec l'ancienne structure
def new_cust():
    """Fonction de compatibilité pour la création de client"""
    return ClientResource.create_client()


def show_cust():
    """Fonction de compatibilité pour l'affichage des clients"""
    return ClientResource.get_all_clients()


def show_info(client_id: str):
    """Fonction de compatibilité pour les infos client"""
    return ClientResource.get_client_info(client_id)


def update_cust():
    """Fonction de compatibilité pour la modification de client"""
    return ClientResource.update_client()


def delete_cust(client_id: str):
    """Fonction de compatibilité pour la suppression de client"""
    return ClientResource.delete_client(client_id)
