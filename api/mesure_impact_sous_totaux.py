"""
Mesure d'impact, EN LECTURE SEULE, de la règle des sous-totaux de la balance
générale (balance_generale_service.detecter_sous_totaux) sur toutes les
balances générales rattachées à une mission.

Aucune écriture possible : la base n'est manipulée qu'à travers la classe
LectureSeule ci-dessous, qui n'expose que des méthodes de lecture.

Usage :
    python mesure_impact_sous_totaux.py --uri "mongodb://hote:27017" --base cac_perform
    python mesure_impact_sous_totaux.py --uri "mongodb://utilisateur:motdepasse@hote:27017/cac_perform?authSource=admin"

--uri est OBLIGATOIRE (aucune base par défaut) : on sait toujours sur quelle
base on lit. --base est facultatif si l'URI contient le nom de la base.
Le mot de passe éventuel de l'URI n'est jamais affiché.

Sortie : tableau Markdown sur la sortie standard. Les lignes « ambiguës »
(forme de sous-total, montants qui ne correspondent pas) sont listées ; pour
la mesure, elles sont GARDÉES (aucune décision d'auditeur n'est simulée).
"""
import argparse
import re
import sys
from urllib.parse import urlsplit

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient

from src.services.balance_generale_service import controler_equilibre, detecter_sous_totaux


class LectureSeule:
    """Accès à une collection limité à la lecture : aucune méthode d'écriture n'existe."""

    def __init__(self, collection):
        self._collection = collection

    def find(self, *args, **kwargs):
        return self._collection.find(*args, **kwargs)

    def find_one(self, *args, **kwargs):
        return self._collection.find_one(*args, **kwargs)


def uri_masquee(uri: str) -> str:
    return re.sub(r"//([^:/@]+):([^@]+)@", r"//\1:***@", uri)


def montant(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


def mesurer(db_missions: LectureSeule, db_balances: LectureSeule, db_clients: LectureSeule):
    clients = {str(c["_id"]): c.get("company_name") for c in db_clients.find({}, {"company_name": 1})}
    lignes, nb_missions, nb_balances, missions_touchees = [], 0, 0, set()
    for mission in db_missions.find({}, {"balances": 1, "annee_auditee": 1, "id_client": 1}):
        nb_missions += 1
        for position, balance_id in enumerate(mission.get("balances") or []):
            try:
                doc = db_balances.find_one({"_id": ObjectId(balance_id)})
            except (InvalidId, TypeError):
                continue
            if not doc:
                continue
            nb_balances += 1
            avant = doc.get("balance") or []
            apres, sous_totaux, ambigus = detecter_sous_totaux(avant)
            if not sous_totaux and not ambigus:
                continue
            missions_touchees.add(str(mission["_id"]))
            somme = lambda ls, k: sum((l.get(k) or 0) for l in ls)
            solde = lambda ls, r: sum((l.get("solde_reel") or 0) for l in ls if str(l.get("numero_compte")).startswith(r))
            equilibre = controler_equilibre(apres)
            desequilibres = "; ".join(
                f"{p} {montant(v['ecart'])}" for p, v in equilibre["paires"].items() if not v["ok"]
            ) or "équilibrée"
            lignes.append([
                clients.get(str(mission.get("id_client")), "?"), str(mission["_id"])[:8], mission.get("annee_auditee"),
                "N" if position == 0 else f"N-{position}", doc.get("annee_balance"), len(avant), len(sous_totaux),
                ", ".join(f"{a['numero_compte']}" for a in ambigus) or "—",
                montant(somme(avant, "debit_fin")), montant(somme(apres, "debit_fin")),
                montant(somme(avant, "credit_fin")), montant(somme(apres, "credit_fin")),
                montant(solde(avant, "28")), montant(solde(apres, "28")), desequilibres,
            ])
    return nb_missions, nb_balances, missions_touchees, lignes


def main():
    parser = argparse.ArgumentParser(description="Mesure d'impact (lecture seule) de la règle des sous-totaux.")
    parser.add_argument("--uri", required=True, help="Adresse MongoDB (obligatoire, aucune valeur par défaut)")
    parser.add_argument("--base", help="Nom de la base (sinon celui de l'URI)")
    args = parser.parse_args()

    nom_base = args.base or urlsplit(args.uri).path.lstrip("/") or None
    if not nom_base:
        parser.error("nom de la base introuvable : précisez --base")

    client = MongoClient(args.uri, serverSelectionTimeoutMS=5000)
    db = client[nom_base]
    print(f"Base lue (lecture seule) : {uri_masquee(args.uri)} — base « {nom_base} »", file=sys.stderr)

    nb_missions, nb_balances, touchees, lignes = mesurer(
        LectureSeule(db["Mission1"]), LectureSeule(db["Balance"]), LectureSeule(db["Client_db"]),
    )
    print(f"Missions examinées : {nb_missions} · balances générales lues : {nb_balances} · "
          f"missions concernées : {len(touchees)} · balances concernées : {len(lignes)}\n")
    print("| Client | Mission | Exercice audité | Balance | Année | Lignes | Sous-totaux écartés | Lignes ambiguës (gardées) "
          "| Débit final avant | après | Crédit final avant | après | Solde 28 avant | après | Équilibre après (débit − crédit) |")
    print("|" + "---|" * 15)
    for ligne in sorted(lignes, key=lambda l: (str(l[0]), l[1], l[3])):
        print("| " + " | ".join(str(c) for c in ligne) + " |")
    client.close()


if __name__ == "__main__":
    main()
