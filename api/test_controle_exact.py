#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reproduire EXACTEMENT controle_intangibilite ligne par ligne
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId
from src.model import Mission

def test_controle_exact(mission_id):
    """Reproduire EXACTEMENT controle_intangibilite"""
    
    print("=" * 80)
    print(f"REPRODUCTION EXACTE DE controle_intangibilite")
    print("=" * 80)
    
    mission_obj = Mission()
    
    # Reproduire EXACTEMENT le code de controle_intangibilite
    try:
        mission = db.Mission1.find_one({"_id": ObjectId(mission_id)})
        if not mission:
            print("Mission non trouvee")
            return
            
        bal_ids = mission.get("balances", [])
        if len(bal_ids) < 2:
            print("Pas assez de balances")
            return
        
        print(f"Balances: {len(bal_ids)}")
        
        annee_auditee = int(mission.get("annee_auditee", 0)) if mission.get("annee_auditee") else 0
        
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
        
        if all(not bd.get("annee") for bd in balance_docs) and annee_auditee:
            for idx, bd in enumerate(balance_docs):
                bd["annee"] = annee_auditee - idx
        
        balance_docs.sort(key=lambda x: x.get("annee", 0))
        
        if len(balance_docs) < 2:
            print("Pas assez de balance_docs")
            return
        
        bal_N = balance_docs[-1]["data"]
        bal_N1 = balance_docs[-2]["data"]
        periode_N = str(balance_docs[-1]["annee"]) if balance_docs[-1]["annee"] else "N"
        periode_N1 = str(balance_docs[-2]["annee"]) if balance_docs[-2]["annee"] else "N-1"
        
        print(f"\nbal_N: {len(bal_N)} lignes")
        print(f"bal_N1: {len(bal_N1)} lignes")
        
        if not bal_N or len(bal_N) == 0:
            print("ERROR: bal_N vide")
            return
        if not bal_N1 or len(bal_N1) == 0:
            print("ERROR: bal_N1 vide")
            return
        
        print(f"\nIndexation...")
        idxN = mission_obj._index_by_compte(bal_N)
        idxN1 = mission_obj._index_by_compte(bal_N1)
        
        print(f"\nidxN: {len(idxN)} comptes")
        print(f"idxN1: {len(idxN1)} comptes")
        
        if len(idxN) == 0 and len(idxN1) == 0:
            print("ERROR: Aucun compte indexe")
            return
        
        # Créer tous_comptes EXACTEMENT comme dans le code
        tous_comptes = []
        print(f"\nDebut traitement des comptes...")
        
        comptes_traites_N = 0
        comptes_traites_N1 = 0
        
        # 1. Traiter tous les comptes présents en N
        print(f"\nBoucle 1: Traitement des comptes en N ({len(idxN)} comptes)")
        for num, ln in idxN.items():
            try:
                di = float(ln.get("debit_initial", 0) or 0)
                ci = float(ln.get("credit_initial", 0) or 0)
                ouvN = di - ci
                
                prev = idxN1.get(num)
                if prev:
                    df = float(prev.get("debit_fin", 0) or 0)
                    cf = float(prev.get("credit_fin", 0) or 0)
                    clotN1 = df - cf
                    ecart = clotN1 - ouvN
                    
                    tous_comptes.append({
                        "numero_compte": num,
                        "libelle": ln.get("libelle", ""),
                        "ouverture_n": ouvN,
                        "cloture_n1": clotN1,
                        "ecart": ecart,
                        "status": "ecart" if ecart != 0 else "ok",
                        "message": f"Cloture N-1 {clotN1} != Ouverture N {ouvN}" if ecart != 0 else f"Cloture N-1 {clotN1} = Ouverture N {ouvN}",
                        "justification": f"Ecart de {ecart} entre la cloture de l'exercice N-1 ({clotN1}) et l'ouverture de l'exercice N ({ouvN})." if ecart != 0 else "Aucun ecart detecte.",
                        "conclusion_audit": "Ecart significatif detecte - Necessite une justification et une documentation des causes de cette variation." if ecart != 0 else "Aucune anomalie detectee."
                    })
                    comptes_traites_N += 1
                else:
                    ecart = -ouvN
                    tous_comptes.append({
                        "numero_compte": num,
                        "libelle": ln.get("libelle", ""),
                        "ouverture_n": ouvN,
                        "cloture_n1": None,
                        "ecart": ecart,
                        "status": "nouveau",
                        "message": "Compte present en N mais absent en N-1",
                        "justification": f"Le compte {num} est present dans l'exercice N avec un solde d'ouverture de {ouvN}, mais n'existait pas dans l'exercice N-1. Cela peut indiquer une creation de compte, un reclassement ou une erreur de saisie.",
                        "conclusion_audit": "Compte nouvellement cree ou reclasse - Verifier la legitimite de cette creation et documenter les raisons."
                    })
                    comptes_traites_N += 1
            except Exception as e:
                print(f"  ERREUR compte {num}: {e}")
                continue
        
        print(f"  Comptes traites N: {comptes_traites_N}")
        
        # 2. Ajouter les comptes présents en N-1 mais absents en N
        print(f"\nBoucle 2: Traitement des comptes en N-1 absents de N ({len(idxN1)} comptes)")
        for num, ln in idxN1.items():
            try:
                if num not in idxN:
                    df = float(ln.get("debit_fin", 0) or 0)
                    cf = float(ln.get("credit_fin", 0) or 0)
                    clotN1 = df - cf
                    
                    tous_comptes.append({
                        "numero_compte": num,
                        "libelle": ln.get("libelle", ""),
                        "ouverture_n": None,
                        "cloture_n1": clotN1,
                        "ecart": clotN1,
                        "status": "supprime",
                        "message": "Compte present en N-1 mais absent en N",
                        "justification": f"Le compte {num} etait present dans l'exercice N-1 avec un solde de cloture de {clotN1}, mais n'existe plus dans l'exercice N. Cela peut indiquer une suppression de compte, un reclassement ou une erreur de saisie.",
                        "conclusion_audit": "Compte supprime ou reclasse - Verifier la legitimite de cette suppression et documenter les raisons."
                    })
                    comptes_traites_N1 += 1
            except Exception as e:
                print(f"  ERREUR compte N-1 {num}: {e}")
                continue
        
        print(f"  Comptes traites N-1: {comptes_traites_N1}")
        
        # Trier
        tous_comptes.sort(key=lambda x: x["numero_compte"])
        
        # Compter les écarts
        ecarts_count = len([c for c in tous_comptes if c["status"] in ["ecart", "nouveau", "supprime"]])
        
        print(f"\n" + "=" * 80)
        print(f"RESULTAT FINAL:")
        print(f"  tous_comptes: {len(tous_comptes)} comptes")
        print(f"  ecarts_count: {ecarts_count} ecarts")
        print(f"  Comptes OK: {len([c for c in tous_comptes if c['status'] == 'ok'])}")
        
        if len(tous_comptes) == 0:
            print(f"\nPROBLEME: tous_comptes est vide apres traitement!")
            print(f"  idxN avait {len(idxN)} comptes")
            print(f"  idxN1 avait {len(idxN1)} comptes")
            print(f"  Comptes traites N: {comptes_traites_N}")
            print(f"  Comptes traites N1: {comptes_traites_N1}")
        else:
            print(f"\nOK: {len(tous_comptes)} comptes dans tous_comptes")
            print(f"Exemples:")
            for i, c in enumerate(tous_comptes[:3]):
                print(f"  {i+1}. {c['numero_compte']}: {c['status']} - {c.get('libelle', '')[:40]}")
        
    except Exception as e:
        print(f"ERREUR GENERALE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from pymongo import MongoClient
    client = MongoClient('mongodb://localhost:27017/')
    db = client['cac_perform']
    if len(sys.argv) < 2:
        print("Usage: python test_controle_exact.py <mission_id>")
        sys.exit(1)
    
    test_controle_exact(sys.argv[1])

