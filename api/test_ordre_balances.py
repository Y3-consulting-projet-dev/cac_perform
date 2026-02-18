#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test pour vérifier l'ordre des balances dans controle_intangibilite
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId

def test_ordre_balances(mission_id):
    """Vérifier l'ordre exact des balances comme dans controle_intangibilite"""
    
    print("=" * 80)
    print(f"TEST: Ordre des balances dans controle_intangibilite")
    print(f"Mission ID: {mission_id}")
    print("=" * 80)
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client['cac_perform']
    
    mission = db.Mission1.find_one({"_id": ObjectId(mission_id)})
    if not mission:
        print("Mission non trouvee")
        return
    
    bal_ids = mission.get("balances", [])
    print(f"\nBalances IDs (ordre original): {bal_ids}")
    
    annee_auditee = int(mission.get("annee_auditee", 0)) if mission.get("annee_auditee") else 0
    print(f"Annee auditee: {annee_auditee}")
    
    # Charger les balances EXACTEMENT comme dans controle_intangibilite
    balance_docs = []
    for bal_id in bal_ids:
        bal_doc = db.Balance.find_one({"_id": ObjectId(bal_id)})
        if bal_doc:
            annee_balance = bal_doc.get("annee_balance") or bal_doc.get("periode") or ""
            balance_docs.append({
                "id": bal_id,
                "annee": annee_balance,
                "data": bal_doc.get("balance", [])
            })
            print(f"\nBalance {bal_id}:")
            print(f"  annee_balance: {bal_doc.get('annee_balance')}")
            print(f"  periode: {bal_doc.get('periode')}")
            print(f"  annee utilisee: {annee_balance}")
            print(f"  nombre de lignes: {len(bal_doc.get('balance', []))}")
    
    # Si aucune année n'est trouvée, utiliser l'ordre et calculer
    if all(not bd.get("annee") for bd in balance_docs) and annee_auditee:
        print(f"\nAucune annee trouvee, calcul avec annee_auditee={annee_auditee}")
        for idx, bd in enumerate(balance_docs):
            bd["annee"] = annee_auditee - idx
            print(f"  Balance {idx}: annee = {bd['annee']}")
    
    print(f"\nAvant tri:")
    for i, bd in enumerate(balance_docs):
        print(f"  [{i}] Balance {bd['id']}: annee={bd.get('annee', 'N/A')}, lignes={len(bd['data'])}")
    
    # Trier EXACTEMENT comme dans controle_intangibilite
    balance_docs.sort(key=lambda x: x.get("annee", 0))
    
    print(f"\nApres tri (du plus ancien au plus recent):")
    for i, bd in enumerate(balance_docs):
        print(f"  [{i}] Balance {bd['id']}: annee={bd.get('annee', 'N/A')}, lignes={len(bd['data'])}")
    
    if len(balance_docs) < 2:
        print("Pas assez de balances")
        return
    
    bal_N = balance_docs[-1]["data"]  # Dernière = N
    bal_N1 = balance_docs[-2]["data"]  # Avant-dernière = N-1
    
    print(f"\nSelection finale:")
    print(f"  bal_N (derniere balance): {len(bal_N)} lignes")
    print(f"  bal_N1 (avant-derniere balance): {len(bal_N1)} lignes")
    
    if len(bal_N) == 0:
        print(f"  PROBLEME: bal_N est vide!")
    if len(bal_N1) == 0:
        print(f"  PROBLEME: bal_N1 est vide!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_ordre_balances.py <mission_id>")
        sys.exit(1)
    
    test_ordre_balances(sys.argv[1])









