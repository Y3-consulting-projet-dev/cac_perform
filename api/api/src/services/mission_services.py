"""
Services pour les missions
Gère la logique métier pour les opérations sur les missions
"""

from typing import Dict, Any, List, Optional
from werkzeug.datastructures import FileStorage
from src.utils.database import get_database
from src.model import Mission
from src.schemas.mission_schemas import validate_mission_data


class MissionService:
    """Service pour les opérations sur les missions"""
    
    @staticmethod
    def create_mission(
        files: List[FileStorage],
        annee_auditee: str,
        id_client: str,
        date_debut: str,
        date_fin: str,
        date_debut_mandat: str = None,
        date_fin_mandat: str = None,
        responsable_nom: str = None,
        responsable_grade: str = None,
        responsable_role: str = None,
        responsable_id: str = None
    ) -> Dict[str, Any]:
        """
        Crée une nouvelle mission avec des fichiers de balance
        
        Args:
            files: Liste des fichiers Excel de balance (minimum 2)
            annee_auditee: Année auditée
            id_client: ID du client
            date_debut: Date de début (YYYY-MM-DD)
            date_fin: Date de fin (YYYY-MM-DD)
            date_debut_mandat: Date de début du mandat (YYYY-MM-DD)
            date_fin_mandat: Date de fin du mandat (YYYY-MM-DD)
            
        Returns:
            Dictionnaire avec les données de la mission créée
            
        Raises:
            ValueError: Si les données sont invalides
            Exception: En cas d'erreur lors de la création
        """
        try:
            # Validation des fichiers
            if not files or len(files) < 2:
                raise ValueError("Au moins 2 fichiers de balance sont requis (N et N-1)")
            
            # Filtrer les fichiers valides
            valid_files = [f for f in files if f and f.filename]
            if len(valid_files) < 2:
                raise ValueError(f"Seulement {len(valid_files)} fichier(s) valide(s) reçu(s), 2 requis")
            
            # Nettoyer et préparer les données avant validation
            annee_auditee_clean = str(annee_auditee).strip() if annee_auditee else ""
            id_client_clean = str(id_client).strip() if id_client else ""
            
            # Nettoyer les dates : supprimer les espaces et normaliser
            date_debut_clean = str(date_debut).strip() if date_debut else ""
            date_fin_clean = str(date_fin).strip() if date_fin else ""
            date_debut_mandat_clean = str(date_debut_mandat).strip() if date_debut_mandat else ""
            date_fin_mandat_clean = str(date_fin_mandat).strip() if date_fin_mandat else ""
            
            # Logs pour debug
            print(f"🔍 DEBUG - Dates avant nettoyage:")
            print(f"  - date_debut (raw): '{date_debut}' (type: {type(date_debut)})")
            print(f"  - date_fin (raw): '{date_fin}' (type: {type(date_fin)})")
            print(f"  - date_debut_mandat (raw): '{date_debut_mandat}' (type: {type(date_debut_mandat)})")
            print(f"  - date_fin_mandat (raw): '{date_fin_mandat}' (type: {type(date_fin_mandat)})")
            print(f"  - date_debut (clean): '{date_debut_clean}'")
            print(f"  - date_fin (clean): '{date_fin_clean}'")
            print(f"  - date_debut_mandat (clean): '{date_debut_mandat_clean}'")
            print(f"  - date_fin_mandat (clean): '{date_fin_mandat_clean}'")
            
            # Vérifier le format des dates et essayer de les corriger si nécessaire
            import re
            date_pattern = r'^\d{4}-\d{2}-\d{2}$'
            
            # Si la date ne correspond pas au format, essayer de la convertir
            if date_debut_clean and not re.match(date_pattern, date_debut_clean):
                print(f"⚠️  Format de date_debut incorrect: '{date_debut_clean}'")
                # Essayer de convertir depuis d'autres formats courants
                from datetime import datetime
                try:
                    # Essayer différents formats
                    for fmt in ['%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y', '%Y.%m.%d']:
                        try:
                            dt = datetime.strptime(date_debut_clean, fmt)
                            date_debut_clean = dt.strftime('%Y-%m-%d')
                            print(f"  ✅ Date convertie: '{date_debut_clean}'")
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    print(f"  ❌ Impossible de convertir la date: {e}")
            
            if date_fin_clean and not re.match(date_pattern, date_fin_clean):
                print(f"⚠️  Format de date_fin incorrect: '{date_fin_clean}'")
                # Essayer de convertir depuis d'autres formats courants
                from datetime import datetime
                try:
                    # Essayer différents formats
                    for fmt in ['%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y', '%Y.%m.%d']:
                        try:
                            dt = datetime.strptime(date_fin_clean, fmt)
                            date_fin_clean = dt.strftime('%Y-%m-%d')
                            print(f"  ✅ Date convertie: '{date_fin_clean}'")
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    print(f"  ❌ Impossible de convertir la date: {e}")
            
            # Convertir les dates du mandat si nécessaire
            if date_debut_mandat_clean and not re.match(date_pattern, date_debut_mandat_clean):
                print(f"⚠️  Format de date_debut_mandat incorrect: '{date_debut_mandat_clean}'")
                from datetime import datetime
                try:
                    for fmt in ['%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y', '%Y.%m.%d']:
                        try:
                            dt = datetime.strptime(date_debut_mandat_clean, fmt)
                            date_debut_mandat_clean = dt.strftime('%Y-%m-%d')
                            print(f"  ✅ Date convertie: '{date_debut_mandat_clean}'")
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    print(f"  ❌ Impossible de convertir la date: {e}")
            
            if date_fin_mandat_clean and not re.match(date_pattern, date_fin_mandat_clean):
                print(f"⚠️  Format de date_fin_mandat incorrect: '{date_fin_mandat_clean}'")
                from datetime import datetime
                try:
                    for fmt in ['%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y', '%Y.%m.%d']:
                        try:
                            dt = datetime.strptime(date_fin_mandat_clean, fmt)
                            date_fin_mandat_clean = dt.strftime('%Y-%m-%d')
                            print(f"  ✅ Date convertie: '{date_fin_mandat_clean}'")
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    print(f"  ❌ Impossible de convertir la date: {e}")
            
            # Vérifier que les champs de base ne sont pas vides
            if not annee_auditee_clean:
                raise ValueError("L'année auditée est requise")
            if not id_client_clean:
                raise ValueError("L'ID du client est requis")
            if not date_debut_clean:
                raise ValueError("La date de début est requise")
            if not date_fin_clean:
                raise ValueError("La date de fin est requise")
            if not date_debut_mandat_clean:
                raise ValueError("La date de début du mandat est requise")
            if not date_fin_mandat_clean:
                raise ValueError("La date de fin du mandat est requise")
            
            # Validation des données - toutes les dates du mandat sont requises
            mission_data = {
                "annee_auditee": annee_auditee_clean,
                "id_client": id_client_clean,
                "date_debut": date_debut_clean,
                "date_fin": date_fin_clean,
                "date_debut_mandat": date_debut_mandat_clean,
                "date_fin_mandat": date_fin_mandat_clean
            }
            
            validated_data = validate_mission_data(mission_data)
            
            # Vérifier que le client existe
            db = get_database()
            from bson import ObjectId
            
            # Essayer d'abord avec l'ID tel quel (string)
            client = db.Client.find_one({"_id": validated_data["id_client"]})
            
            # Si non trouvé, essayer avec ObjectId
            if not client:
                try:
                    client = db.Client.find_one({"_id": ObjectId(validated_data["id_client"])})
                    if client:
                        validated_data["id_client"] = str(client["_id"])
                except Exception as e:
                    print(f"⚠️  Erreur lors de la conversion en ObjectId: {e}")
            
            if not client:
                # Récupérer quelques clients pour aider l'utilisateur
                sample_clients = list(db.Client.find().limit(3))
                client_info = []
                for c in sample_clients:
                    client_info.append({
                        "id": str(c["_id"]),
                        "nom": c.get("nom", "Sans nom")
                    })
                
                error_msg = f"Client avec l'ID '{id_client}' introuvable"
                if client_info:
                    error_msg += f". Exemples d'IDs clients valides: {[c['id'] for c in client_info]}"
                
                raise ValueError(error_msg)
            
            # S'assurer que db est disponible pour nouvelle_mission
            # (db est déjà défini à la ligne 126, mais on le redéfinit pour être sûr)
            db = get_database()
            
            # Créer la mission via le modèle
            cls = Mission()
            donnees = cls.nouvelle_mission(
                valid_files,
                validated_data["annee_auditee"],
                validated_data["id_client"],
                validated_data["date_debut"],
                validated_data["date_fin"],
                validated_data.get("date_debut_mandat"),
                validated_data.get("date_fin_mandat"),
                responsable_nom,
                responsable_grade,
                responsable_role,
                responsable_id
            )
            
            if not donnees:
                raise Exception("Erreur lors de la création de la mission")
            
            return {
                "success": True,
                "message": "Mission créée avec succès",
                "data": donnees
            }
            
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            import traceback
            # Capturer l'exception sans référencer db directement
            error_type = type(e).__name__
            error_message = str(e)
            
            # Essayer de formater le traceback de manière sécurisée
            try:
                error_trace = traceback.format_exc()
            except Exception as trace_error:
                # Si le formatage échoue (peut-être à cause de db), utiliser une version simplifiée
                error_trace = f"Traceback (dernière erreur): {error_type}: {error_message}"
            
            print(f"❌ ERREUR DÉTAILLÉE lors de la création de la mission:")
            print(f"   Type: {error_type}")
            print(f"   Message: {error_message}")
            print(f"   Traceback complet:")
            print(error_trace)
            
            # Extraire les informations importantes du traceback de manière sécurisée
            try:
                traceback_lines = error_trace.split('\n')
                # Trouver la ligne qui mentionne 'db'
                db_error_line = None
                for i, line in enumerate(traceback_lines):
                    if 'db' in line.lower() and ('not defined' in line.lower() or 'NameError' in line):
                        db_error_line = line
                        # Afficher quelques lignes de contexte
                        start = max(0, i-3)
                        end = min(len(traceback_lines), i+3)
                        print(f"\n🔍 CONTEXTE DE L'ERREUR 'db':")
                        for j in range(start, end):
                            marker = ">>> " if j == i else "    "
                            print(f"{marker}{traceback_lines[j]}")
                        break
            except Exception:
                # Si l'extraction échoue, ignorer
                pass
            
            raise Exception(f"Erreur lors de la création de la mission: {error_message}")
    
    @staticmethod
    def get_mission_by_id(mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère une mission par son ID
        
        Args:
            mission_id: ID de la mission
            
        Returns:
            Données de la mission ou None si non trouvée
        """
        try:
            db = get_database()
            from bson import ObjectId
            
            try:
                mission = db.Mission1.find_one({"_id": ObjectId(mission_id)})
            except:
                mission = None
            
            if not mission:
                return None
            
            mission["_id"] = str(mission["_id"])
            return mission
            
        except Exception as e:
            raise Exception(f"Erreur lors de la récupération de la mission: {str(e)}")
    
    @staticmethod
    def get_client_missions(client_id: str) -> List[Dict[str, Any]]:
        """
        Récupère toutes les missions d'un client
        
        Args:
            client_id: ID du client
            
        Returns:
            Liste des missions du client
        """
        try:
            db = get_database()
            
            # Chercher avec l'id tel quel
            query = {"id_client": str(client_id)}
            missions = list(db.Mission1.find(query))
            
            # Si aucune mission trouvée, essayer avec ObjectId
            if not missions:
                from bson import ObjectId
                try:
                    query_objid = {"id_client": ObjectId(client_id)}
                    missions = list(db.Mission1.find(query_objid))
                except:
                    pass
            
            # Sérialiser les IDs
            for mission in missions:
                mission["_id"] = str(mission["_id"])
            
            return missions
            
        except Exception as e:
            raise Exception(f"Erreur lors de la récupération des missions: {str(e)}")

    @staticmethod
    def get_all_missions() -> List[Dict[str, Any]]:
        """
        Récupère toutes les missions (tous clients confondus)

        Returns:
            Liste des missions
        """
        try:
            db = get_database()

            missions = list(db.Mission1.find())

            # Enrichir avec le nom du client si possible
            client_ids = {str(m.get("id_client")) for m in missions if m.get("id_client")}
            clients = {}
            if client_ids:
                from bson import ObjectId
                for cid in client_ids:
                    try:
                        client = db.Client.find_one({"_id": ObjectId(cid)})
                    except Exception:
                        client = db.Client.find_one({"_id": cid})
                    if client:
                        clients[cid] = client.get("nom")

            for mission in missions:
                mission["_id"] = str(mission["_id"])
                cid = str(mission.get("id_client")) if mission.get("id_client") else None
                if cid:
                    mission["client_nom"] = clients.get(cid)

            # Trier par date de fin décroissante (fallback sur date_debut)
            def sort_key(m):
                return m.get("date_fin") or m.get("date_debut") or ""

            missions.sort(key=sort_key, reverse=True)
            return missions

        except Exception as e:
            raise Exception(f"Erreur lors de la récupération des missions: {str(e)}")
    
    @staticmethod
    def delete_mission(mission_id: str) -> bool:
        """
        Supprime une mission
        
        Args:
            mission_id: ID de la mission
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        try:
            db = get_database()
            from bson import ObjectId
            
            try:
                result = db.Mission1.delete_one({"_id": ObjectId(mission_id)})
                return result.deleted_count > 0
            except:
                return False
                
        except Exception as e:
            raise Exception(f"Erreur lors de la suppression de la mission: {str(e)}")
