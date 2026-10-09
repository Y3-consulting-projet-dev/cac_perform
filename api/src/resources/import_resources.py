"""
Contrôleurs HTTP pour la refonte de l'import (balances, mapping, fichiers
auxiliaires/immobilisations). Nouveau périmètre V2 — voir
docs/PLAN_import_refonte.md §3. Ne touche pas aux ressources mission/client
existantes.
"""
import json

from flask import request, jsonify, make_response
from marshmallow import ValidationError

from src.services import mapping_apercu_service
from src.services import mapping_memorise_service
from src.services import balance_auxiliaire_service
from src.services import immobilisation_service
from src.services import controle_preliminaire_service
from src.services import fichiers_complementaires_service
from src.schemas.import_schemas import MappingImportCreateSchema, validate_import_data


def _get_uploaded_file(nom_champ="fichier"):
    fichier = request.files.get(nom_champ)
    if not fichier or not fichier.filename:
        return None
    return fichier


def _lire_mapping_optionnel():
    """
    Lit un mapping explicite envoyé en option (champ de formulaire `mapping`,
    JSON sérialisé) pour imposer une correspondance de colonnes précise au
    lieu du mapping proposé automatiquement. Absent -> None (comportement
    par défaut inchangé : détection automatique).
    """
    brut = request.form.get("mapping")
    if not brut:
        return None
    try:
        valeur = json.loads(brut)
        return valeur if isinstance(valeur, dict) else None
    except (TypeError, ValueError):
        return None


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
            logiciel_comptable = request.form.get("logiciel_comptable") or None
            mapping_override = _lire_mapping_optionnel()

            if not type_auxiliaire or not id_client or not annee:
                return make_response(jsonify({
                    "success": False,
                    "error": "Champs requis manquants: 'type_auxiliaire', 'id_client', 'annee'"
                }), 400)

            resultat = balance_auxiliaire_service.importer_balance_auxiliaire(
                fichier, type_auxiliaire, id_client, mission_id, annee,
                logiciel_comptable=logiciel_comptable, mapping=mapping_override,
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
            logiciel_comptable = request.form.get("logiciel_comptable") or None
            mapping_override = _lire_mapping_optionnel()

            if not id_client or not annee:
                return make_response(jsonify({
                    "success": False,
                    "error": "Champs requis manquants: 'id_client', 'annee'"
                }), 400)

            resultat = immobilisation_service.importer_immobilisations(
                fichier, id_client, mission_id, annee,
                logiciel_comptable=logiciel_comptable, mapping=mapping_override,
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
    def lister_fichiers_complementaires(mission_id: str):
        """
        GET /api/v1/missions/<mission_id>/fichiers-complementaires
        Liste les fichiers complémentaires ACTIFS de la mission (balances
        auxiliaires clients/fournisseurs, immobilisations), groupés par type.
        Filtré strictement par mission_id (cloisonnement).
        """
        try:
            resultat = fichiers_complementaires_service.lister_fichiers_complementaires(mission_id)
            return make_response(jsonify({"success": True, "data": resultat}), 200)
        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)

    @staticmethod
    def detail_fichier_complementaire(mission_id: str, fichier_id: str):
        """
        GET /api/v1/missions/<mission_id>/fichiers-complementaires/<fichier_id>
        Détail d'un fichier complémentaire : lignes, mapping utilisé, totaux
        débit/crédit, date d'import, contrôles préliminaires. Un fichier
        d'une autre mission n'est jamais renvoyé (404, comme s'il n'existait pas).
        """
        try:
            detail = fichiers_complementaires_service.lire_detail_fichier(mission_id, fichier_id)
            if not detail:
                return make_response(jsonify({
                    "success": False,
                    "error": "Fichier non trouvé pour cette mission"
                }), 404)
            return make_response(jsonify({"success": True, "data": detail}), 200)
        except Exception as e:
            return make_response(jsonify({
                "success": False,
                "error": f"Erreur serveur: {str(e)}"
            }), 500)
