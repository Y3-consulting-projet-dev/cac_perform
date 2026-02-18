#!/usr/bin/env python3
"""
Vérifier les missions dans la base
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId

def check_missions():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['cac_perform']

    # Vérifier toutes les missions
    missions = list(db.Mission1.find({}, {'_id': 1, 'nom': 1, 'balances': 1}).sort('_id', -1).limit(3))

    print('=== MISSIONS DANS LA BASE ===')
    for i, mission in enumerate(missions):
        mission_id = str(mission['_id'])
        nom = mission.get('nom', 'Sans nom')
        balances = mission.get('balances', [])
        print(f'{i+1}. ID: {mission_id}')
        print(f'   Nom: {nom}')
        print(f'   Balances: {len(balances)}')
        print()

if __name__ == "__main__":
    check_missions()

