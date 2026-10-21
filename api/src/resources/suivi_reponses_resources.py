"""
Contrôleurs HTTP du suivi des réponses, sous-lot c (docs/PLAN_circularisation.md).
Aucun envoi réel : les routes enregistrent ce que l'auditeur a fait.
Réponse, analyse d'écart et procédure alternative acceptent un formulaire
multipart (pièce jointe facultative « fichier ») ou du JSON.
"""
from io import BytesIO

from flask import request, jsonify, make_response, send_file

from src.services import suivi_reponses_service as suivi


def _executer(action, code=200):
    try:
        return make_response(jsonify({"success": True, "data": action()}), code)
    except ValueError as e:
        return make_response(jsonify({"success": False, "error": str(e)}), 400)
    except Exception as e:
        return make_response(jsonify({"success": False, "error": f"Erreur serveur: {str(e)}"}), 500)


def _corps():
    """Champs du formulaire multipart, sinon du JSON ; pièce jointe facultative."""
    if request.files or request.form:
        fichier = request.files.get("fichier")
        return dict(request.form), (fichier.read() if fichier else None), (fichier.filename if fichier else None)
    corps = request.get_json(silent=True)
    if not isinstance(corps, dict):
        raise ValueError("Corps de la requête illisible : JSON UTF-8 attendu.")
    return corps, None, None


class SuiviReponsesResource:
    """Contrôleur pour /api/v1/missions/<id>/suivi[...]"""

    @staticmethod
    def lire(mission_id):
        return _executer(lambda: suivi.lire_suivi(mission_id))

    @staticmethod
    def enregistrer_envoi(mission_id):
        def action():
            c, _, _ = _corps()
            return suivi.enregistrer_envoi(mission_id, str(c.get("type_tiers") or ""), str(c.get("numero") or ""),
                                           c.get("canal"), c.get("date_envoi"), c.get("destinataire"), c.get("utilisateur_id"))
        return _executer(action, 201)

    @staticmethod
    def enregistrer_relance(mission_id, envoi_id):
        def action():
            c, _, _ = _corps()
            return suivi.enregistrer_relance(mission_id, envoi_id, c.get("date"), c.get("canal"), c.get("utilisateur_id"))
        return _executer(action)

    @staticmethod
    def enregistrer_reponse(mission_id, envoi_id):
        def action():
            c, piece, nom = _corps()
            return suivi.enregistrer_reponse(mission_id, envoi_id, c, piece, nom, c.get("utilisateur_id"))
        return _executer(action)

    @staticmethod
    def analyser_ecart(mission_id, envoi_id):
        def action():
            c, piece, nom = _corps()
            return suivi.analyser_ecart(mission_id, envoi_id, c.get("commentaire"), piece, nom, c.get("utilisateur_id"))
        return _executer(action)

    @staticmethod
    def documenter_procedure_alternative(mission_id, envoi_id):
        def action():
            c, piece, nom = _corps()
            return suivi.documenter_procedure_alternative(mission_id, envoi_id, c.get("commentaire"), piece, nom,
                                                          c.get("utilisateur_id"))
        return _executer(action)

    @staticmethod
    def telecharger_piece(mission_id, fichier_id):
        try:
            piece = suivi.lire_piece(mission_id, fichier_id)
        except Exception:
            return make_response(jsonify({"success": False, "error": "Pièce introuvable."}), 404)
        return send_file(BytesIO(piece["contenu"]), as_attachment=True, download_name=piece["nom_fichier"] or "piece")
