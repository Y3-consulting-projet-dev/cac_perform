"""
Contrôleurs HTTP pour le verrou IPE (Module 1, CAC-IPE-01) et son circuit de
revue. Nouveau périmètre V2 — voir docs/PLAN_verrou_IPE.md §3, §4, §5. Ne
touche pas aux ressources mission/client existantes.
"""
from flask import request, jsonify, make_response
from marshmallow import ValidationError

from src.services import verrou_ipe_service
from src.services import rapprochement_ipe_service
from src.services import revue_ipe_service
from src.schemas.ipe_schemas import (
    ValidationFiabiliteSchema,
    SoumissionRevueSchema,
    DemandeCorrectionSchema,
    RemarqueCreationSchema,
    ReponseRemarqueSchema,
    TraiterRemarqueSchema,
    validate_ipe_data,
)


class IpeResource:
    """Contrôleur pour /api/v1/missions/<id>/ipe[...]"""

    @staticmethod
    def obtenir_etat(mission_id: str):
        """
        GET /api/v1/missions/<id>/ipe — état IPE courant (+ statut affiché
        pour la barre latérale). Passe par verifier_coherence_fichiers : si un
        fichier référencé par la dernière validation a changé depuis (ex. la
        balance générale, remplacée via le flux V1 sans invalidation à
        l'écriture), l'état renvoyé reflète l'invalidation détectée.
        """
        try:
            etat = verrou_ipe_service.verifier_coherence_fichiers(mission_id)
            etat["statut_affiche"] = verrou_ipe_service.statut_affiche(etat)
            return make_response(jsonify({"success": True, "data": etat}), 200)
        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)

    @staticmethod
    def evaluer(mission_id: str):
        """
        POST /api/v1/missions/<id>/ipe/evaluer — lance le rapprochement IPE-1/2/3.
        Échec explicite (400) si la balance générale de l'exercice audité est
        introuvable ou ambiguë (docs/PLAN_verrou_IPE.md §4) : rien n'est
        enregistré dans ce cas.
        """
        try:
            etat = rapprochement_ipe_service.evaluer_ipe(mission_id)
            etat["statut_affiche"] = verrou_ipe_service.statut_affiche(etat)
            return make_response(jsonify({"success": True, "data": etat}), 200)
        except ValueError as e:
            return make_response(jsonify({"success": False, "error": str(e)}), 400)
        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)

    @staticmethod
    def valider(mission_id: str):
        """
        POST /api/v1/missions/<id>/ipe/validation — validation manager de la
        fiabilité IPE. Une validation positive fige les références des
        fichiers utilisés ; échoue en 400 (sans rien valider) si la balance
        générale de l'exercice audité est introuvable/ambiguë.
        """
        try:
            data = validate_ipe_data(request.get_json() or {}, ValidationFiabiliteSchema)
            etat = rapprochement_ipe_service.valider_fiabilite(
                mission_id,
                validee=data["validee"],
                utilisateur_id=data.get("utilisateur_id"),
                commentaire=data.get("commentaire"),
            )
            etat["statut_affiche"] = verrou_ipe_service.statut_affiche(etat)
            return make_response(jsonify({"success": True, "data": etat}), 200)
        except ValidationError as e:
            return make_response(jsonify({
                "success": False,
                "error": "Erreurs de validation",
                "errors": e.messages,
            }), 400)
        except ValueError as e:
            return make_response(jsonify({"success": False, "error": str(e)}), 400)
        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)

    @staticmethod
    def soumettre(mission_id: str):
        """
        POST /api/v1/missions/<id>/ipe/soumettre — action auditeur : soumet
        le contrôle IPE pour revue. Refusée (400) si un écart n'a aucune
        remarque attachée, ou si le statut actuel ne le permet pas.
        TODO(décision) : qui a le droit de soumettre n'est pas vérifié.
        """
        try:
            data = validate_ipe_data(request.get_json() or {}, SoumissionRevueSchema)
            etat = revue_ipe_service.soumettre_pour_revue(
                mission_id,
                utilisateur_id=data.get("utilisateur_id"),
                commentaire=data.get("commentaire"),
            )
            etat["statut_affiche"] = verrou_ipe_service.statut_affiche(etat)
            return make_response(jsonify({"success": True, "data": etat}), 200)
        except ValidationError as e:
            return make_response(jsonify({"success": False, "error": "Erreurs de validation", "errors": e.messages}), 400)
        except ValueError as e:
            return make_response(jsonify({"success": False, "error": str(e)}), 400)
        except Exception as e:
            return make_response(jsonify({"success": False, "error": f"Erreur serveur: {str(e)}"}), 500)

    @staticmethod
    def demander_correction(mission_id: str):
        """
        POST /api/v1/missions/<id>/ipe/demander-correction — action manager :
        demande une correction (commentaire obligatoire), fait repasser le
        circuit à "en_attente_correction". Ne valide ni n'invalide.
        TODO(décision) : qui a le droit de demander une correction n'est
        pas vérifié.
        """
        try:
            data = validate_ipe_data(request.get_json() or {}, DemandeCorrectionSchema)
            etat = revue_ipe_service.demander_correction(
                mission_id,
                commentaire=data["commentaire"],
                utilisateur_id=data.get("utilisateur_id"),
            )
            etat["statut_affiche"] = verrou_ipe_service.statut_affiche(etat)
            return make_response(jsonify({"success": True, "data": etat}), 200)
        except ValidationError as e:
            return make_response(jsonify({"success": False, "error": "Erreurs de validation", "errors": e.messages}), 400)
        except ValueError as e:
            return make_response(jsonify({"success": False, "error": str(e)}), 400)
        except Exception as e:
            return make_response(jsonify({"success": False, "error": f"Erreur serveur: {str(e)}"}), 500)

    @staticmethod
    def ajouter_remarque(mission_id: str):
        """
        POST /api/v1/missions/<id>/ipe/remarques — remarque à deux niveaux :
        générale (module/numero_compte absents) ou sur un écart précis par
        compte collectif.
        """
        try:
            data = validate_ipe_data(request.get_json() or {}, RemarqueCreationSchema)
            etat = revue_ipe_service.ajouter_remarque(
                mission_id,
                commentaire=data["commentaire"],
                utilisateur_id=data.get("utilisateur_id"),
                module=data.get("module"),
                numero_compte=data.get("numero_compte"),
            )
            etat["statut_affiche"] = verrou_ipe_service.statut_affiche(etat)
            return make_response(jsonify({"success": True, "data": etat}), 201)
        except ValidationError as e:
            return make_response(jsonify({"success": False, "error": "Erreurs de validation", "errors": e.messages}), 400)
        except Exception as e:
            return make_response(jsonify({"success": False, "error": f"Erreur serveur: {str(e)}"}), 500)

    @staticmethod
    def repondre_remarque(mission_id: str, remarque_id: str):
        """PUT /api/v1/missions/<id>/ipe/remarques/<remarque_id>/reponse — réponse de l'auditeur."""
        try:
            data = validate_ipe_data(request.get_json() or {}, ReponseRemarqueSchema)
            etat = revue_ipe_service.repondre_remarque(
                mission_id,
                remarque_id,
                commentaire=data["commentaire"],
                utilisateur_id=data.get("utilisateur_id"),
            )
            etat["statut_affiche"] = verrou_ipe_service.statut_affiche(etat)
            return make_response(jsonify({"success": True, "data": etat}), 200)
        except ValidationError as e:
            return make_response(jsonify({"success": False, "error": "Erreurs de validation", "errors": e.messages}), 400)
        except Exception as e:
            return make_response(jsonify({"success": False, "error": f"Erreur serveur: {str(e)}"}), 500)

    @staticmethod
    def marquer_remarque_traitee(mission_id: str, remarque_id: str):
        """PUT /api/v1/missions/<id>/ipe/remarques/<remarque_id>/traitee — marque (ou démarque) une remarque comme traitée."""
        try:
            data = validate_ipe_data(request.get_json() or {}, TraiterRemarqueSchema)
            etat = revue_ipe_service.marquer_remarque_traitee(
                mission_id,
                remarque_id,
                traitee=data["traitee"],
                utilisateur_id=data.get("utilisateur_id"),
            )
            etat["statut_affiche"] = verrou_ipe_service.statut_affiche(etat)
            return make_response(jsonify({"success": True, "data": etat}), 200)
        except ValidationError as e:
            return make_response(jsonify({"success": False, "error": "Erreurs de validation", "errors": e.messages}), 400)
        except Exception as e:
            return make_response(jsonify({"success": False, "error": f"Erreur serveur: {str(e)}"}), 500)
