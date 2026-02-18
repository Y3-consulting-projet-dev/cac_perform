#!/usr/bin/env python3
"""
Vérifier le format exact des balances stockées dans la base
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId

def verifier_format(mission_id):
    """Vérifier le format des balances"""
    
    print(f"Mission ID: {mission_id}")
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client['cac_perform']
    
    mission = db.Mission1.find_one({"_id": ObjectId(mission_id)})
    if not mission:
        print("Mission non trouvee")
        return
    
    bal_ids = mission.get("balances", [])
    print(f"\nBalances IDs: {bal_ids}")
    
    for bal_id in bal_ids:
        bal = db.Balance.find_one({"_id": ObjectId(bal_id)})
        if bal:
            balance_data = bal.get("balance", [])
            print(f"\nBalance {bal_id}:")
            print(f"  Nombre de lignes: {len(balance_data)}")
            if len(balance_data) > 0:
                print(f"  Premiere ligne:")
                first_line = balance_data[0]
                print(f"    Type: {type(first_line)}")
                if isinstance(first_line, dict):
                    print(f"    Cles: {list(first_line.keys())}")
                    print(f"    numero_compte: {first_line.get('numero_compte')} (type: {type(first_line.get('numero_compte'))})")
                    print(f"    Contenu complet: {first_line}")
                else:
                    print(f"    Contenu: {first_line}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verifier_format_balances.py <mission_id>")
        sys.exit(1)
    
    verifier_format(sys.argv[1])









