"""
Contrôleurs HTTP du journal d'audit d'une mission (page B, maquette
docs/maquettes/6_Journal_audit.html). LECTURE SEULE : deux routes GET, aucune
route d'écriture ni de suppression.
"""
from datetime import date

from flask import request, jsonify, make_response

from src.services import journal_audit_service as journal


def _parametres():
    """Filtres de la requête. Une date ou un décalage illisible -> ValueError (400)."""
    def lire_date(nom):
        valeur = (request.args.get(nom) or "").strip()
        if not valeur:
            return None
        try:
            return date.fromisoformat(valeur)
        except ValueError:
            raise ValueError(f"Date « {nom} » invalide (attendu : AAAA-MM-JJ).")

    try:
        decalage = int(request.args.get("decalage") or 0)
    except ValueError:
        raise ValueError("Décalage horaire invalide.")
    du, au = lire_date("du"), lire_date("au")
    if du and au and du > au:
        raise ValueError("La date « Du » est postérieure à la date « Au ».")
    return {
        "module": request.args.get("module") or None,
        "utilisateur": request.args.get("utilisateur") or None,
        "du": du,
        "au": au,
        "decalage_minutes": decalage,
    }


def _erreur(e, code):
    return make_response(jsonify({"success": False, "error": str(e) if code == 400 else f"Erreur serveur: {e}"}), code)


class JournalResource:
    """Contrôleur pour /api/v1/missions/<id>/journal[...]"""

    @staticmethod
    def lister(mission_id: str):
        """GET /api/v1/missions/<id>/journal — entrées filtrées, paginées, + options des filtres."""
        try:
            filtres = _parametres()
            try:
                page = int(request.args.get("page") or 1)
            except ValueError:
                page = 1
            toutes = journal.lire_journal(mission_id)
            resultat = journal.paginer(journal.filtrer(toutes, **filtres), page)
            resultat["modules"] = list(journal.MODULES)
            resultat["utilisateurs"] = journal.utilisateurs(toutes)
            return make_response(jsonify({"success": True, "data": resultat}), 200)
        except ValueError as e:
            return _erreur(e, 400)
        except Exception as e:
            return _erreur(e, 500)

    @staticmethod
    def exporter(mission_id: str):
        """GET /api/v1/missions/<id>/journal/export — classeur .xlsx des entrées filtrées (toutes les pages)."""
        try:
            filtres = _parametres()
            entrees = journal.filtrer(journal.lire_journal(mission_id), **filtres)
            contenu = journal.exporter_excel(entrees, filtres["decalage_minutes"])
            reponse = make_response(contenu)
            reponse.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            reponse.headers["Content-Disposition"] = f'attachment; filename="journal_audit_{mission_id}.xlsx"'
            return reponse
        except ValueError as e:
            return _erreur(e, 400)
        except Exception as e:
            return _erreur(e, 500)
