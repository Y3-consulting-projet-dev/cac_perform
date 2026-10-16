"""
Données FICTIVES du test de parcours de l'interface
(clients/tests/parcours/parcours.mjs) : un client, une mission et ses deux
balances générales (N, N-1), créés avant le test puis supprimés.

    python parcours_donnees_test.py creer          -> affiche les identifiants (JSON)
    python parcours_donnees_test.py supprimer <id_client> <id_mission>

La suppression ne touche QUE des documents portant le marqueur
`test_parcours: True` : jamais une donnée réelle, même avec un mauvais
identifiant.
"""
import json
import sys
from datetime import datetime

from bson import ObjectId

from app import create_app

MARQUEUR = {"test_parcours": True}


def _db():
    app = create_app()
    app = app[0] if isinstance(app, tuple) else app
    app.app_context().push()
    from src.utils.database import get_database
    return get_database()


def _ligne(numero, libelle, debit_fin=0.0, credit_fin=0.0):
    solde = debit_fin - credit_fin
    return {"numero_compte": numero, "libelle": libelle, "debit_initial": debit_fin, "credit_initial": credit_fin,
            "debit_mvt": 0.0, "credit_mvt": 0.0, "debit_fin": debit_fin, "credit_fin": credit_fin,
            "solde_reel": solde, "solde": abs(solde), "sign_solde": "D" if solde >= 0 else "C"}


def creer():
    db = _db()
    nom = f"CLIENT PARCOURS TEST {datetime.now():%Y%m%d%H%M%S}"
    client_id = db["Client_db"].insert_one({
        **MARQUEUR, "company_name": nom, "sector": "Test", "address": "Adresse fictive", "referentiel": "SYSCOHADA",
        "legal_form": "SA", "responsable_name": "Responsable Test", "civility": "M", "responsable_function": "DG",
        "RCCM": "CI-TEST-0000", "country": "Côte d'Ivoire", "creation_date": "2015-01-01",
    }).inserted_id
    lignes = [_ligne("101000", "CAPITAL", credit_fin=1_000_000), _ligne("521000", "BANQUE", debit_fin=1_000_000)]
    balance_n = db["Balance"].insert_one({**MARQUEUR, "id_client": str(client_id), "annee_balance": 2025, "balance": lignes}).inserted_id
    balance_n1 = db["Balance"].insert_one({**MARQUEUR, "id_client": str(client_id), "annee_balance": 2024, "balance": lignes}).inserted_id
    mission_id = db["Mission1"].insert_one({
        **MARQUEUR, "id_client": str(client_id), "annee_auditee": "2025", "date_debut": "2025-01-01", "date_fin": "2025-12-31",
        "balances": [str(balance_n), str(balance_n1)], "balance_variation": [], "grouping": [], "efi": {}, "materiality": [],
        "ipe": {"verrou_applicable": False},
    }).inserted_id
    print(json.dumps({"client_id": str(client_id), "client_nom": nom, "mission_id": str(mission_id)}))


def supprimer(client_id, mission_id):
    db = _db()
    mission = db["Mission1"].find_one({"_id": ObjectId(mission_id), **MARQUEUR}) or {}
    ids_balances = [ObjectId(b) for b in mission.get("balances") or []]
    balances = db["Balance"].delete_many({"_id": {"$in": ids_balances}, **MARQUEUR}).deleted_count
    if mission:
        # Fichiers importés pendant le test (sans marqueur) : seulement ceux
        # d'une mission de test, identifiée par son marqueur ci-dessus.
        balances += db["Balance"].delete_many({"mission_id": mission_id}).deleted_count
    resultat = {
        "balances": balances,
        "missions": db["Mission1"].delete_many({"$or": [{"_id": ObjectId(mission_id)}, {"id_client": client_id}], **MARQUEUR}).deleted_count,
        "clients": db["Client_db"].delete_one({"_id": ObjectId(client_id), **MARQUEUR}).deleted_count,
    }
    print(json.dumps(resultat))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "creer":
        creer()
    elif len(sys.argv) == 4 and sys.argv[1] == "supprimer":
        supprimer(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
