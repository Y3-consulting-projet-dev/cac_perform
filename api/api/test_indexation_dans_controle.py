#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test pour vérifier que _index_by_compte est bien appelée dans controle_intangibilite
et qu'elle reçoit les bonnes données
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId
from src.model import Mission

def test_indexation(mission_id):
    """Test l'indexation exactement comme dans controle_intangibilite"""
    
    print("=" * 80)
    print(f"TEST: Indexation dans controle_intangibilite")
    print(f"Mission ID: {mission_id}")
    print("=" * 80)
    
    try:
        # Connexion
        client = MongoClient('mongodb://localhost:27017/')
        db = client['cac_perform']
        
        # Récupérer la mission (comme dans controle_intangibilite)
        mission = db.Mission1.find_one({"_id": ObjectId(mission_id)})
        if not mission:
            print("Mission non trouvee")
            return
        
        bal_ids = mission.get("balances", [])
        print(f"\nBalances IDs: {len(bal_ids)}")
        
        # Charger les balances (comme dans controle_intangibilite)
        balance_docs = []
        for bal_id in bal_ids:
            bal_doc = db.Balance.find_one({"_id": ObjectId(bal_id)})
            if bal_doc:
                balance_docs.append({
                    "id": bal_id,
                    "annee": bal_doc.get("annee_balance") or bal_doc.get("periode") or "",
                    "data": bal_doc.get("balance", [])
                })
        
        # Trier comme dans controle_intangibilite
        balance_docs.sort(key=lambda x: x.get("annee", 0))
        
        if len(balance_docs) < 2:
            print("Pas assez de balances")
            return
        
        bal_N = balance_docs[-1]["data"]
        bal_N1 = balance_docs[-2]["data"]
        
        print(f"\nBal_N type: {type(bal_N)}")
        print(f"Bal_N length: {len(bal_N) if bal_N else 0}")
        print(f"Bal_N1 type: {type(bal_N1)}")
        print(f"Bal_N1 length: {len(bal_N1) if bal_N1 else 0}")
        
        if bal_N and len(bal_N) > 0:
            print(f"\nPremiere ligne bal_N:")
            print(f"  Type: {type(bal_N[0])}")
            if isinstance(bal_N[0], dict):
                print(f"  Cles: {list(bal_N[0].keys())}")
                print(f"  numero_compte: {bal_N[0].get('numero_compte')}")
        
        # Créer Mission et tester _index_by_compte
        mission_obj = Mission()
        
        print(f"\n" + "=" * 80)
        print("APPEL _index_by_compte(bal_N)")
        print("=" * 80)
        idxN = mission_obj._index_by_compte(bal_N)
        
        print(f"\n" + "=" * 80)
        print("APPEL _index_by_compte(bal_N1)")
        print("=" * 80)
        idxN1 = mission_obj._index_by_compte(bal_N1)
        
        print(f"\n" + "=" * 80)
        print("RESULTATS")
        print("=" * 80)
        print(f"idxN: {len(idxN)} comptes")
        print(f"idxN1: {len(idxN1)} comptes")
        
        if len(idxN) > 0:
            print(f"\nExemples idxN:")
            for i, (num, ligne) in enumerate(list(idxN.items())[:3]):
                print(f"  {i+1}. {num}: {ligne.get('libelle', 'N/A')[:40]}")
        
        if len(idxN1) > 0:
            print(f"\nExemples idxN1:")
            for i, (num, ligne) in enumerate(list(idxN1.items())[:3]):
                print(f"  {i+1}. {num}: {ligne.get('libelle', 'N/A')[:40]}")
        
        if len(idxN) == 0 or len(idxN1) == 0:
            print(f"\nPROBLEME: Indexation retourne 0 comptes")
            print(f"  idxN vide: {len(idxN) == 0}")
            print(f"  idxN1 vide: {len(idxN1) == 0}")
        else:
            print(f"\nOK: Indexation fonctionne correctement")
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_indexation_dans_controle.py <mission_id>")
        sys.exit(1)
    
    test_indexation(sys.argv[1])









