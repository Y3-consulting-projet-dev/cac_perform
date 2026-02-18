#!/usr/bin/env python3
"""
Test direct de l'indexation pour une mission spécifique
Simule exactement ce que fait controle_intangibilite
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId
from src.model import Mission

def test_indexation_directe(mission_id):
    """Test l'indexation directement comme dans controle_intangibilite"""
    
    print("=" * 80)
    print(f"🧪 TEST INDEXATION DIRECTE")
    print(f"Mission ID: {mission_id}")
    print("=" * 80)
    
    try:
        # Connexion
        client = MongoClient('mongodb://localhost:27017/')
        db = client['cac_perform']
        
        # Récupérer la mission
        mission = db.Mission1.find_one({"_id": ObjectId(mission_id)})
        if not mission:
            print(f"❌ Mission non trouvée")
            return
        
        bal_ids = mission.get("balances", [])
        print(f"\n📊 Balances: {len(bal_ids)}")
        
        # Récupérer les balances
        balance_docs = []
        for bal_id in bal_ids:
            bal_doc = db.Balance.find_one({"_id": ObjectId(bal_id)})
            if bal_doc:
                balance_docs.append({
                    "id": bal_id,
                    "annee": bal_doc.get("annee_balance", ""),
                    "data": bal_doc.get("balance", [])
                })
        
        # Trier par année
        balance_docs.sort(key=lambda x: x.get("annee", 0))
        
        if len(balance_docs) < 2:
            print(f"❌ Pas assez de balances")
            return
        
        bal_N = balance_docs[-1]["data"]
        bal_N1 = balance_docs[-2]["data"]
        
        print(f"\n📊 Balance N: {len(bal_N)} lignes")
        print(f"📊 Balance N-1: {len(bal_N1)} lignes")
        
        # Test avec la fonction de Mission
        mission_obj = Mission()
        
        print(f"\n🔍 Test _index_by_compte avec Mission._index_by_compte...")
        idxN = mission_obj._index_by_compte(bal_N)
        idxN1 = mission_obj._index_by_compte(bal_N1)
        
        print(f"\n📊 RÉSULTATS:")
        print(f"   Comptes indexés N: {len(idxN)}")
        print(f"   Comptes indexés N-1: {len(idxN1)}")
        
        if len(idxN) > 0:
            print(f"\n   ✅ Exemples comptes N:")
            for i, (num, ligne) in enumerate(list(idxN.items())[:5]):
                print(f"      {i+1}. {num}: {ligne.get('libelle', 'N/A')[:40]}")
        
        if len(idxN1) > 0:
            print(f"\n   ✅ Exemples comptes N-1:")
            for i, (num, ligne) in enumerate(list(idxN1.items())[:5]):
                print(f"      {i+1}. {num}: {ligne.get('libelle', 'N/A')[:40]}")
        
        if len(idxN) == 0 and len(idxN1) == 0:
            print(f"\n❌ PROBLÈME: La fonction _index_by_compte trouve 0 comptes")
            print(f"   Mais le diagnostic direct trouve {271 + 233} comptes")
            print(f"   Il y a une différence entre les deux méthodes")
        else:
            print(f"\n✅ La fonction _index_by_compte fonctionne!")
            print(f"   Elle devrait trouver {len(idxN) + len(idxN1)} comptes")
            print(f"   Le problème est ailleurs dans controle_intangibilite")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_indexation_directe.py <mission_id>")
        sys.exit(1)
    
    test_indexation_directe(sys.argv[1])









