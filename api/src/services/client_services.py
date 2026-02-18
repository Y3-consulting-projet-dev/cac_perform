"""
Services pour la gestion des clients
Contient toute la logique métier
"""

from typing import Dict, List, Optional, Any
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from marshmallow import ValidationError

from src.schemas.client_schemas import (
    validate_client_data, 
    ClientCreateSchema, 
    ClientUpdateSchema,
    serialize_client,
    serialize_client_list
)

# Utilisation de la configuration centralisée
from src.utils.database import get_db


class ClientService:
    """Service pour la gestion des clients"""
    
    @staticmethod
    def create_client(client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau client
        
        Args:
            client_data: Données du client à créer
            
        Returns:
            Dict contenant l'ID du client créé et un message de succès
            
        Raises:
            ValidationError: Si les données ne sont pas valides
            Exception: Si erreur lors de la création
        """
        try:
            db = get_db()
            # Validation des données
            validated_data = validate_client_data(client_data, ClientCreateSchema)
            
            # Vérifier si un client avec le même nom existe déjà

            
            db = get_db()
            existing_client = db.Client.find_one({"nom": validated_data["nom"]})
            if existing_client:
                raise ValueError(f"Un client avec le nom '{validated_data['nom']}' existe déjà")
            
            # Insérer le nouveau client
            result = db.Client.insert_one(validated_data)
            client_id = str(result.inserted_id)
            
            print(f"✅ Client créé avec succès: {client_id}")
            
            return {
                "success": True,
                "client_id": client_id,
                "message": "Client créé avec succès"
            }
            
        except ValidationError as e:
            print(f"❌ Erreur de validation: {e}")
            raise e
        except ValueError as e:
            print(f"❌ Erreur métier: {e}")
            raise e
        except PyMongoError as e:
            print(f"❌ Erreur MongoDB: {e}")
            raise Exception(f"Erreur lors de la création du client: {str(e)}")
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            raise Exception(f"Erreur inattendue lors de la création: {str(e)}")
    
    
    @staticmethod
    def get_all_clients() -> List[Dict[str, Any]]:
        """
        Récupère tous les clients
        
        Returns:
            Liste des clients avec leurs informations
        """
        try:
            db = get_db()
            clients = list(db.Client.find().sort([("_id", -1)]))
            
            # Convertir les ObjectId en string
            for client in clients:
                client['_id'] = str(client['_id'])
            
            print(f"✅ {len(clients)} clients récupérés")
            return clients
            
        except PyMongoError as e:
            print(f"❌ Erreur MongoDB lors de la récupération: {e}")
            raise Exception(f"Erreur lors de la récupération des clients: {str(e)}")
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            raise Exception(f"Erreur inattendue lors de la récupération: {str(e)}")
    
    
    @staticmethod
    def get_client_by_id(client_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un client par son ID
        
        Args:
            client_id: ID du client
            
        Returns:
            Informations du client ou None si non trouvé
        """
        try:
            # Convertir en ObjectId
            object_id = ObjectId(client_id)
            
            # Récupérer le client
            db = get_db()

            client = db.Client.find_one({"_id": object_id})
            
            if not client:
                print(f"⚠️  Client non trouvé: {client_id}")
                return None
            
            # Convertir l'ObjectId en string
            client['_id'] = str(client['_id'])
            
            print(f"✅ Client récupéré: {client_id}")
            return client
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération du client {client_id}: {e}")
            raise Exception(f"Erreur lors de la récupération du client: {str(e)}")
    
    
    @staticmethod
    def get_client_with_missions(client_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un client avec ses missions
        
        Args:
            client_id: ID du client
            
        Returns:
            Client avec ses missions ou None si non trouvé
        """
        try:
            # Récupérer les informations du client
            client_info = ClientService.get_client_by_id(client_id)
            if not client_info:
                return None
            
            # Récupérer les missions du client
            missions = ClientService.get_client_missions(client_id)
            
            return {
                "info": client_info,
                "missions": missions
            }
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération du client avec missions: {e}")
            raise e
    
    
    @staticmethod
    def get_client_missions(client_id: str) -> List[Dict[str, Any]]:
        """
        Récupère les missions d'un client
        
        Args:
            client_id: ID du client
            
        Returns:
            Liste des missions du client
        """
        try:
            # Normaliser l'ID
            client_id_str = str(client_id).strip()
            
            print(f"🔍 Recherche des missions pour client ID: '{client_id_str}'")
            
            # Chercher avec l'id tel quel
            query = {"id_client": client_id_str}
            db = get_db()

            missions = list(db.Mission1.find(query))
            
            count = len(missions)
            print(f"📊 Missions trouvées avec id_client='{client_id_str}': {count}")
            
            # Si aucune mission trouvée, essayer avec ObjectId
            if count == 0:
                try:
                    query_objid = {"id_client": ObjectId(client_id_str)}
                    missions_objid = list(db.Mission1.find(query_objid))
                    if len(missions_objid) > 0:
                        missions = missions_objid
                        count = len(missions)
                        print(f"📊 Missions trouvées avec ObjectId: {count}")
                except:
                    pass
            
            # Convertir les ObjectId en string
            for mission in missions:
                mission['_id'] = str(mission['_id'])
            
            print(f"✅ Retour de {len(missions)} missions pour le client {client_id_str}")
            return missions
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des missions: {e}")
            raise Exception(f"Erreur lors de la récupération des missions: {str(e)}")
    
    
    @staticmethod
    def update_client(client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un client existant
        
        Args:
            client_data: Données du client à mettre à jour (doit contenir _id)
            
        Returns:
            Dict avec le résultat de la mise à jour
        """
        try:
            # Validation des données
            validated_data = validate_client_data(client_data, ClientUpdateSchema)
            
            # Extraire l'ID
            client_id = validated_data.pop('_id')
            object_id = ObjectId(client_id)
            
            # Vérifier que le client existe
            db = get_db()

            existing_client = db.Client.find_one({"_id": object_id})
            if not existing_client:
                raise ValueError(f"Client non trouvé: {client_id}")
            
            # Mettre à jour seulement les champs fournis
            update_data = {k: v for k, v in validated_data.items() if v is not None}
            
            if not update_data:
                raise ValueError("Aucune donnée à mettre à jour")
            
            # Effectuer la mise à jour
            result = db.Client.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                print(f"✅ Client mis à jour: {client_id}")
                return {
                    "success": True,
                    "message": "Client mis à jour avec succès",
                    "modified_count": result.modified_count
                }
            else:
                return {
                    "success": True,
                    "message": "Aucune modification nécessaire",
                    "modified_count": 0
                }
                
        except ValidationError as e:
            print(f"❌ Erreur de validation: {e}")
            raise e
        except ValueError as e:
            print(f"❌ Erreur métier: {e}")
            raise e
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour: {e}")
            raise Exception(f"Erreur lors de la mise à jour du client: {str(e)}")
    
    
    @staticmethod
    def delete_client(client_id: str) -> Dict[str, Any]:
        """
        Supprime un client et toutes ses missions associées
        
        Args:
            client_id: ID du client à supprimer
            
        Returns:
            Dict avec le résultat de la suppression
        """
        try:
            # Convertir l'ID en ObjectId
            object_id = ObjectId(str(client_id))
            
            # Vérifier que le client existe
            client_info = db.Client.find_one({"_id": object_id})
            if not client_info:
                raise ValueError(f"Client non trouvé: {client_id}")
            
            client_name = client_info.get('nom', 'Inconnu')
            
            # Supprimer toutes les missions associées au client
            missions_result = db.Mission1.delete_many({"id_client": str(client_id)})
            missions_deleted = missions_result.deleted_count
            
            # Supprimer le client
            db = get_db()

            client_result = db.Client.delete_one({"_id": object_id})
            
            if client_result.deleted_count > 0:
                print(f"✅ Client supprimé: {client_id} ({client_name})")
                print(f"✅ {missions_deleted} mission(s) supprimée(s)")
                
                return {
                    "success": True,
                    "message": f"Client supprimé avec succès. {missions_deleted} mission(s) supprimée(s).",
                    "client_name": client_name,
                    "missions_deleted": missions_deleted
                }
            else:
                raise Exception("Erreur lors de la suppression du client")
                
        except ValueError as e:
            print(f"❌ Erreur métier: {e}")
            raise e
        except Exception as e:
            print(f"❌ Erreur lors de la suppression: {e}")
            raise Exception(f"Erreur lors de la suppression du client: {str(e)}")
    
    
    @staticmethod
    def get_available_referentiels() -> List[str]:
        """
        Récupère la liste des référentiels disponibles
        
        Returns:
            Liste des référentiels comptables disponibles
        """
        return ["syscohada", "ifrs", "pcg"]
