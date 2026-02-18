"""
Resources (contrÃ´leurs) pour les missions
GÃ¨re les requÃªtes HTTP et les rÃ©ponses
"""

from flask import request, jsonify, make_response
from marshmallow import ValidationError
from typing import Dict, Any

from src.services.mission_services import MissionService


class MissionResource:
    """ContrÃ´leur pour les opÃ©rations sur les missions"""
    
    @staticmethod
    def create_mission():
        """
        POST /api/v1/missions/
        CrÃ©e une nouvelle mission avec des fichiers de balance
        """
        try:
            # Debug: Afficher toutes les clÃ©s disponibles
            print(f"ðŸ” DEBUG - Tous les clÃ©s de request.files: {list(request.files.keys())}")
            print(f"ðŸ” DEBUG - Tous les clÃ©s de request.form: {list(request.form.keys())}")
            
            # RÃ©cupÃ©rer les fichiers (multipart/form-data)
            # Essayer plusieurs formats de noms de champs pour compatibilitÃ©
            uploaded_files = []
            
            # Format 1: files[] (format attendu)
            files_list = request.files.getlist('files[]')
            if files_list:
                uploaded_files.extend(files_list)
                print(f"âœ… Fichiers trouvÃ©s avec 'files[]': {len(files_list)}")
            
            # Format 2: files (sans crochets - certains clients HTTP)
            if not uploaded_files:
                files_list = request.files.getlist('files')
                if files_list:
                    uploaded_files.extend(files_list)
                    print(f"âœ… Fichiers trouvÃ©s avec 'files': {len(files_list)}")
            
            # Format 3: file (singulier - certains outils)
            if not uploaded_files:
                files_list = request.files.getlist('file')
                if files_list:
                    uploaded_files.extend(files_list)
                    print(f"âœ… Fichiers trouvÃ©s avec 'file': {len(files_list)}")
            
            # Format 4: Chercher tous les fichiers disponibles
            if not uploaded_files:
                all_files = []
                for key in request.files.keys():
                    file_list = request.files.getlist(key)
                    valid_files = [f for f in file_list if f and f.filename]
                    if valid_files:
                        all_files.extend(valid_files)
                        print(f"âœ… Fichiers trouvÃ©s avec '{key}': {len(valid_files)}")
                
                if all_files:
                    uploaded_files = all_files
            
            # Debug: Afficher les fichiers reÃ§us
            print(f"ðŸ” DEBUG - Total fichiers reÃ§us: {len(uploaded_files)}")
            for i, f in enumerate(uploaded_files):
                print(f"  ðŸ“„ Fichier {i+1}: {f.filename if f and f.filename else 'AUCUN FICHIER'}")
            
            # Si aucun fichier n'est reÃ§u, retourner une erreur dÃ©taillÃ©e
            if len(uploaded_files) == 0:
                error_details = {
                    "error": "Aucun fichier reÃ§u",
                    "clÃ©s_request_files": list(request.files.keys()),
                    "clÃ©s_request_form": list(request.form.keys()),
                    "content_type": request.content_type,
                    "method": request.method
                }
                print(f"âŒ ERREUR DÃ‰TAILLÃ‰E: {error_details}")
                return make_response(jsonify({
                    "success": False,
                    "error": "Au moins 2 fichiers de balance sont requis (N et N-1)",
                    "debug": {
                        "fichiers_reÃ§us": 0,
                        "clÃ©s_fichiers": list(request.files.keys()),
                        "content_type": request.content_type,
                        "aide": "VÃ©rifiez que vous utilisez 'Multipart Form' dans Insomnia et que les fichiers sont bien sÃ©lectionnÃ©s"
                    }
                }), 400)
            
            # RÃ©cupÃ©rer les donnÃ©es du formulaire
            # Fonction helper pour rÃ©cupÃ©rer une valeur en gÃ©rant les espaces dans les noms de champs
            def get_form_value(key, alternatives=None):
                """RÃ©cupÃ¨re une valeur du formulaire en gÃ©rant les espaces dans les noms de champs"""
                if alternatives is None:
                    alternatives = []
                
                # Essayer avec le nom exact d'abord
                value = request.form.get(key)
                if value:
                    return value
                
                # Chercher dans toutes les clÃ©s disponibles en comparant aprÃ¨s suppression des espaces
                key_normalized = key.strip().lower()
                for form_key in request.form.keys():
                    form_key_normalized = form_key.strip().lower()
                    if form_key_normalized == key_normalized:
                        value = request.form.get(form_key)
                        if value:
                            print(f"  âœ… Champ trouvÃ© avec normalisation: '{form_key}' (recherchÃ©: '{key}')")
                            return value
                
                # Essayer avec des variantes (avec/sans espaces)
                variants = [key.strip(), key, key + ' ', ' ' + key]
                if alternatives:
                    variants.extend(alternatives)
                    variants.extend([alt.strip() for alt in alternatives])
                
                for variant in variants:
                    value = request.form.get(variant)
                    if value:
                        print(f"  âœ… Champ trouvÃ© avec variante: '{variant}' (recherchÃ©: '{key}')")
                        return value
                
                # DerniÃ¨re tentative : chercher par similaritÃ© (contient le nom)
                for form_key in request.form.keys():
                    if key_normalized in form_key.lower() or form_key.lower() in key_normalized:
                        value = request.form.get(form_key)
                        if value:
                            print(f"  âš ï¸  Champ trouvÃ© par similaritÃ©: '{form_key}' (recherchÃ©: '{key}')")
                            return value
                
                return None
            
            # RÃ©cupÃ©rer les valeurs en gÃ©rant les espaces
            annee_auditee = get_form_value('annee_auditee')
            id_client = get_form_value('id_client', alternatives=['id', 'client_id', 'idClient', 'clientId'])
            date_debut = get_form_value('date_debut', alternatives=['dateDebut', 'date_debut_mission'])
            date_fin = get_form_value('date_fin', alternatives=['dateFin', 'date_fin_mission'])
            date_debut_mandat = get_form_value('date_debut_mandat', alternatives=['dateDebutMandat', 'date_debut_mandat_mission', 'mandat_date_debut'])
            date_fin_mandat = get_form_value('date_fin_mandat', alternatives=['dateFinMandat', 'date_fin_mandat_mission', 'mandat_date_fin'])
            responsable_nom = get_form_value('responsable_nom', alternatives=['responsable', 'nom_responsable'])
            responsable_grade = get_form_value('responsable_grade', alternatives=['grade'])
            responsable_role = get_form_value('responsable_role', alternatives=['role'])
            responsable_id = get_form_value('responsable_id', alternatives=['user_id', 'id_responsable'])
            
            print(f"ðŸ” DEBUG - DonnÃ©es reÃ§ues:")
            print(f"  - annee_auditee: '{annee_auditee}' (type: {type(annee_auditee)})")
            print(f"  - id_client: '{id_client}' (type: {type(id_client)})")
            print(f"  - date_debut: '{date_debut}' (type: {type(date_debut)})")
            print(f"  - date_fin: '{date_fin}' (type: {type(date_fin)})")
            print(f"  - date_debut_mandat: '{date_debut_mandat}' (type: {type(date_debut_mandat)})")
            print(f"  - date_fin_mandat: '{date_fin_mandat}' (type: {type(date_fin_mandat)})")
            print(f"  - Toutes les clÃ©s de request.form: {list(request.form.keys())}")
            print(f"  - ClÃ©s avec espaces dÃ©tectÃ©es: {[k for k in request.form.keys() if k != k.strip()]}")
            
            # VÃ©rifier que les champs requis sont prÃ©sents
            if not annee_auditee or (isinstance(annee_auditee, str) and not annee_auditee.strip()):
                return make_response(jsonify({
                    "success": False,
                    "error": "L'annÃ©e auditÃ©e est requise",
                    "debug": {
                        "champs_reÃ§us": list(request.form.keys()),
                        "annee_auditee_reÃ§u": annee_auditee,
                        "aide": "VÃ©rifiez que le champ 'annee_auditee' est bien prÃ©sent dans le formulaire multipart"
                    }
                }), 400)
            
            if not id_client or (isinstance(id_client, str) and not id_client.strip()):
                # Chercher des variantes du nom de champ
                possible_keys = [k for k in request.form.keys() if 'client' in k.lower() or 'id' in k.lower()]
                return make_response(jsonify({
                    "success": False,
                    "error": "L'ID du client est requis",
                    "debug": {
                        "champs_reÃ§us": list(request.form.keys()),
                        "id_client_reÃ§u": id_client,
                        "clÃ©s_possibles": possible_keys,
                        "aide": f"VÃ©rifiez que le champ 'id_client' est bien prÃ©sent dans le formulaire multipart. ClÃ©s trouvÃ©es: {list(request.form.keys())}. âš ï¸ ATTENTION: VÃ©rifiez qu'il n'y a pas d'espaces Ã  la fin du nom du champ dans Insomnia !"
                    }
                }), 400)
            
            if not date_debut or (isinstance(date_debut, str) and not date_debut.strip()):
                return make_response(jsonify({
                    "success": False,
                    "error": "La date de dÃ©but est requise",
                    "debug": {
                        "champs_reÃ§us": list(request.form.keys()),
                        "date_debut_reÃ§u": date_debut,
                        "aide": "VÃ©rifiez que le champ 'date_debut' est bien prÃ©sent dans le formulaire multipart"
                    }
                }), 400)
            
            if not date_fin or (isinstance(date_fin, str) and not date_fin.strip()):
                return make_response(jsonify({
                    "success": False,
                    "error": "La date de fin est requise",
                    "debug": {
                        "champs_reÃ§us": list(request.form.keys()),
                        "date_fin_reÃ§u": date_fin,
                        "aide": "VÃ©rifiez que le champ 'date_fin' est bien prÃ©sent dans le formulaire multipart"
                    }
                }), 400)
            
            if not date_debut_mandat or (isinstance(date_debut_mandat, str) and not date_debut_mandat.strip()):
                return make_response(jsonify({
                    "success": False,
                    "error": "La date de dÃ©but du mandat est requise",
                    "debug": {
                        "champs_reÃ§us": list(request.form.keys()),
                        "date_debut_mandat_reÃ§u": date_debut_mandat,
                        "aide": "VÃ©rifiez que le champ 'date_debut_mandat' est bien prÃ©sent dans le formulaire multipart"
                    }
                }), 400)
            
            if not date_fin_mandat or (isinstance(date_fin_mandat, str) and not date_fin_mandat.strip()):
                return make_response(jsonify({
                    "success": False,
                    "error": "La date de fin du mandat est requise",
                    "debug": {
                        "champs_reÃ§us": list(request.form.keys()),
                        "date_fin_mandat_reÃ§u": date_fin_mandat,
                        "aide": "VÃ©rifiez que le champ 'date_fin_mandat' est bien prÃ©sent dans le formulaire multipart"
                    }
                }), 400)
            
            # CrÃ©er la mission via le service
            try:
                mission = MissionService.create_mission(
                    files=uploaded_files,
                    annee_auditee=int(annee_auditee),
                    id_client=id_client,
                    date_debut=date_debut,
                    date_fin=date_fin,
                    date_debut_mandat=date_debut_mandat,
                    date_fin_mandat=date_fin_mandat,
                    responsable_nom=responsable_nom,
                    responsable_grade=responsable_grade,
                    responsable_role=responsable_role,
                    responsable_id=responsable_id
                )
            except ValueError as ve:
                # Erreur de validation - message clair
                return make_response(jsonify({
                    "success": False,
                    "error": str(ve)
                }), 400)
            
            return make_response(jsonify(mission), 201)
            
        except ValueError as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"âŒ ERREUR ValueError dans create_mission:")
            print(f"   Message: {str(e)}")
            print(f"   Traceback: {error_trace}")
            return make_response(jsonify({
                "success": False,
                "error": str(e),
                "debug": {
                    "type": "ValueError",
                    "traceback": error_trace.split('\n')[-5:] if error_trace else []
                }
            }), 400)
            
        except ValidationError as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"âŒ ERREUR ValidationError dans create_mission:")
            print(f"   Message: {e.messages}")
            print(f"   Traceback: {error_trace}")
            return make_response(jsonify({
                "success": False,
                "error": "Erreurs de validation",
                "errors": e.messages,
                "debug": {
                    "type": "ValidationError",
                    "traceback": error_trace.split('\n')[-5:] if error_trace else []
                }
            }), 400)
            
        except RuntimeError as e:
            # Erreur de connexion Ã  la base de donnÃ©es
            import traceback
            error_trace = traceback.format_exc()
            print(f"âŒ ERREUR RuntimeError (connexion DB) dans create_mission:")
            print(f"   Message: {str(e)}")
            print(f"   Traceback: {error_trace}")
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur de connexion Ã  la base de donnÃ©es: {str(e)}",
                "debug": {
                    "type": "RuntimeError",
                    "message": str(e),
                    "traceback": error_trace.split('\n')[-10:] if error_trace else []
                }
            }), 500)
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"âŒ ERREUR DÃ‰TAILLÃ‰E dans create_mission:")
            print(f"   Type: {type(e).__name__}")
            print(f"   Message: {str(e)}")
            print(f"   Traceback complet:")
            print(error_trace)
            # Extraire les derniÃ¨res lignes du traceback pour le debug
            traceback_lines = error_trace.split('\n')
            last_lines = traceback_lines[-15:] if len(traceback_lines) > 15 else traceback_lines
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}",
                "debug": {
                    "type": type(e).__name__,
                    "traceback_last_lines": last_lines
                }
            }), 500)
    
    @staticmethod
    def get_mission(mission_id: str):
        """
        GET /api/v1/missions/<id>
        RÃ©cupÃ¨re une mission par son ID
        """
        try:
            mission = MissionService.get_mission_by_id(mission_id)
            
            if not mission:
                return make_response(jsonify({
                    "success": False,
                    "error": "Mission non trouvÃ©e"
                }), 404)
            
            return make_response(jsonify({
                "success": True,
                "data": mission
            }), 200)
            
        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)

    @staticmethod
    def get_all_missions():
        """
        GET /api/v1/missions/
        RÃ©cupÃ¨re toutes les missions
        """
        try:
            missions = MissionService.get_all_missions()
            return make_response(jsonify({
                "success": True,
                "data": missions,
                "total": len(missions)
            }), 200)
        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)
    
    @staticmethod
    def get_client_missions(client_id: str):
        """
        GET /api/v1/missions/client/<client_id>
        RÃ©cupÃ¨re toutes les missions d'un client
        """
        try:
            missions = MissionService.get_client_missions(client_id)
            
            return make_response(jsonify({
                "success": True,
                "data": missions,
                "total": len(missions)
            }), 200)
            
        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)
    
    @staticmethod
    def delete_mission(mission_id: str):
        """
        DELETE /api/v1/missions/<id>
        Supprime une mission
        """
        try:
            success = MissionService.delete_mission(mission_id)
            
            if not success:
                return make_response(jsonify({
                    "success": False,
                    "error": "Mission non trouvÃ©e"
                }), 404)
            
            return make_response(jsonify({
                "success": True,
                "message": "Mission supprimÃ©e avec succÃ¨s"
            }), 200)
            
        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)

