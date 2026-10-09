"""
Contrôleurs HTTP pour la refonte de l'import (balances, mapping, fichiers
auxiliaires/immobilisations). Nouveau périmètre V2 — voir
docs/PLAN_import_refonte.md §3. Ne touche pas aux ressources mission/client
existantes.
"""
from flask import request, jsonify, make_response
from marshmallow import ValidationError

from src.services import mapping_apercu_service
from src.services import mapping_memorise_service
from src.services import balance_auxiliaire_service
from src.services import immobilisation_service
from src.services import controle_preliminaire_service
from src.schemas.import_schemas import MappingImportCreateSchema, validate_import_data


def _get_uploaded_file(nom_champ="fichier"):
    fichier = request.files.get(nom_champ)
    if not fichier or not fichier.filename:
        return None
    return fichier


class ImportResource:
    """Contrôleur pour les nouveaux endpoints /api/v1/imports/... et les
    imports complémentaires rattachés à une mission."""

    @staticmethod
    def apercu_mapping():
        """POST /api/v1/imports/apercu — aperçu du mapping proposé pour un fichier (ne rien écrire en base)."""
        try:
            fichier = _get_uploaded_file("fichier")
            if not fichier:
                return make_response(jsonify({
                    "success": False,
                    "error": "Aucun fichier reçu (champ attendu : 'fichier')"
                }), 400)

            resultat = mapping_apercu_service.generer_apercu_mapping(fichier)
            return make_response(jsonify({"success": True, "data": resultat}), 200)

        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur lors de l'analyse du fichier: {str(e)}"
            }), 500)

    @staticmethod
    def enregistrer_mapping():
        """POST /api/v1/imports/mapping — mémorise un mapping (client + logiciel comptable), versionné."""
        try:
            data = validate_import_data(request.get_json() or {}, MappingImportCreateSchema)
            document = mapping_memorise_service.enregistrer_mapping(
                id_client=data["id_client"],
                logiciel_comptable=data["logiciel_comptable"],
                mapping=data["mapping"],
            )
            return make_response(jsonify({"success": True, "data": document}), 201)

        except ValidationError as e:
            return make_response(jsonify({
                "success": False,
                "error": "Erreurs de validation",
                "errors": e.messages,
            }), 400)
        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)

    @staticmethod
    def recuperer_mapping():
        """GET /api/v1/imports/mapping?id_client=...&logiciel_comptable=... — relit le dernier mapping mémorisé."""
        try:
            id_client = request.args.get("id_client")
            logiciel_comptable = request.args.get("logiciel_comptable")

            if not id_client or not logiciel_comptable:
                return make_response(jsonify({
                    "success": False,
                    "error": "Paramètres 'id_client' et 'logiciel_comptable' requis"
                }), 400)

            document = mapping_memorise_service.recuperer_mapping(id_client, logiciel_comptable)
            return make_response(jsonify({"success": True, "data": document}), 200)

        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)

    @staticmethod
    def controles_preliminaires():
        """
        POST /api/v1/imports/controles-preliminaires
        Exécute les contrôles préliminaires réalisables sans spec externe
        (intégrité, colonnes requises via le mapping détecté, doublons).
        Ne modifie rien en base.
        """
        try:
            fichier = _get_uploaded_file("fichier")
            if not fichier:
                return make_response(jsonify({
                    "success": False,
                    "error": "Aucun fichier reçu (champ attendu : 'fichier')"
                }), 400)

            integrite = controle_preliminaire_service.controler_integrite(fichier)
            resultat = {"integrite": integrite}

            if integrite["ok"]:
                apercu = mapping_apercu_service.generer_apercu_mapping(fichier)
                champs_requis = ["numero", "libelle"]
                resultat["colonnes_requises"] = controle_preliminaire_service.controler_colonnes_requises(
                    apercu["mapping_propose"], champs_requis
                )

            return make_response(jsonify({"success": True, "data": resultat}), 200)

        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur lors des contrôles préliminaires: {str(e)}"
            }), 500)

    @staticmethod
    def importer_balance_auxiliaire(mission_id: str):
        """POST /api/v1/missions/<mission_id>/balances-auxiliaires"""
        try:
            fichier = _get_uploaded_file("fichier")
            if not fichier:
                return make_response(jsonify({
                    "success": False,
                    "error": "Aucun fichier reçu (champ attendu : 'fichier')"
                }), 400)

            type_auxiliaire = request.form.get("type_auxiliaire")
            id_client = request.form.get("id_client")
            annee = request.form.get("annee")

            if not type_auxiliaire or not id_client or not annee:
                return make_response(jsonify({
                    "success": False,
                    "error": "Champs requis manquants: 'type_auxiliaire', 'id_client', 'annee'"
                }), 400)

            resultat = balance_auxiliaire_service.importer_balance_auxiliaire(
                fichier, type_auxiliaire, id_client, mission_id, annee
            )
            return make_response(jsonify({"success": True, "data": resultat}), 201)

        except ValueError as e:
            return make_response(jsonify({"success": False, "error": str(e)}), 400)
        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)

    @staticmethod
    def importer_immobilisations(mission_id: str):
        """POST /api/v1/missions/<mission_id>/immobilisations"""
        try:
            fichier = _get_uploaded_file("fichier")
            if not fichier:
                return make_response(jsonify({
                    "success": False,
                    "error": "Aucun fichier reçu (champ attendu : 'fichier')"
                }), 400)

            id_client = request.form.get("id_client")
            annee = request.form.get("annee")

            if not id_client or not annee:
                return make_response(jsonify({
                    "success": False,
                    "error": "Champs requis manquants: 'id_client', 'annee'"
                }), 400)

            resultat = immobilisation_service.importer_immobilisations(
                fichier, id_client, mission_id, annee
            )
            return make_response(jsonify({"success": True, "data": resultat}), 201)

        except ValueError as e:
            return make_response(jsonify({"success": False, "error": str(e)}), 400)
        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)
