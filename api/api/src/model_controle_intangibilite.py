from mongoengine import Document
from bson import ObjectId
from src.models import clit

db = clit.get_database('cac_perform')

class ControleIntangibilite(Document):
    def __init__(self):
        self.list_items = [
            "Immobilisations Corporelles",
            "Immobilisations Incorporelles",
            "Immobilisations Financières"
        ]

    def init_controle(self, mission_id):
        try:
            mission = db.Mission1.find_one({"_id": ObjectId(mission_id)}, {"_id": 0})
            if not mission:
                return {"ok": False, "message": "Mission non trouvée", "structure": []}

            balances = mission.get("balances", [])
            if len(balances) < 2:
                return {"ok": False, "message": "Balances manquantes", "structure": []}

            balance_n = db.Balance.find_one({"_id": ObjectId(balances[0])}, {"balance": 1})
            balance_n1 = db.Balance.find_one({"_id": ObjectId(balances[1])}, {"balance": 1})

            if not balance_n or not balance_n1:
                return {"ok": False, "message": "Balances introuvables", "structure": []}

            structure = []
            for item in self.list_items:
                solde_n = sum(
                    ((b.get("debit_fin", 0) or 0) - (b.get("credit_fin", 0) or 0))
                    for b in balance_n.get("balance", [])
                    if str(b.get("numero_compte", "")).startswith(str(item))
                )
                solde_n1 = sum(
                    ((b.get("debit_fin", 0) or 0) - (b.get("credit_fin", 0) or 0))
                    for b in balance_n1.get("balance", [])
                    if str(b.get("numero_compte", "")).startswith(str(item))
                )
                structure.append({
                    "item": item,
                    "OuvertureN": solde_n,
                    "ClotureN1": solde_n1
                })

            return {"ok": True, "mission_id": mission_id, "structure": structure}

        except Exception as e:
            return {"ok": False, "message": str(e), "structure": []}
