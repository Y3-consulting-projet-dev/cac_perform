#!/usr/bin/env python3
"""
Script pour diagnostiquer les calculs de totaux et identifier les écarts
"""

import sys
import os
from pymongo import MongoClient
from bson import ObjectId

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def diagnostic_calculs(mission_id=None):
    """Diagnostique les calculs de totaux pour une mission"""
    
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    db = client['cac_perform']
    
    if mission_id:
        missions = [db.Mission1.find_one({'_id': ObjectId(mission_id)})]
    else:
        missions = list(db.Mission1.find().limit(1))
    
    if not missions or not missions[0]:
        print("❌ Aucune mission trouvée")
        return
    
    mission = missions[0]
    print(f"🔍 Mission: {mission.get('_id')}")
    
    balances = mission.get('balances', [])
    if not balances:
        print("❌ Aucune balance trouvée")
        return
    
    # Prendre la première balance
    balance_id = balances[0]
    balance = db.Balance.find_one({'_id': ObjectId(balance_id)})
    
    if not balance:
        print("❌ Balance introuvable")
        return
    
    balance_data = balance.get('balance', [])
    print(f"\n📊 Analyse de la balance: {len(balance_data)} lignes")
    
    if not balance_data:
        print("❌ Aucune donnée dans la balance")
        return
    
    # Afficher les 5 premières lignes pour vérifier la structure
    print("\n📋 Structure des données (5 premières lignes):")
    for i, ligne in enumerate(balance_data[:5]):
        print(f"\n  Ligne {i+1}:")
        print(f"    - numero_compte: {ligne.get('numero_compte')}")
        print(f"    - libelle: {ligne.get('libelle', '')[:50]}")
        print(f"    - debit_initial: {ligne.get('debit_initial', 0)}")
        print(f"    - credit_initial: {ligne.get('credit_initial', 0)}")
        print(f"    - debit_mvt: {ligne.get('debit_mvt', 0)} | {ligne.get('mouvement_debit', 0)}")
        print(f"    - credit_mvt: {ligne.get('credit_mvt', 0)} | {ligne.get('mouvement_credit', 0)}")
        print(f"    - debit_fin: {ligne.get('debit_fin', 0)}")
        print(f"    - credit_fin: {ligne.get('credit_fin', 0)}")
    
    # Calculer les totaux comme dans le code
    print("\n🧮 CALCUL DES TOTAUX:")
    sum_deb_fin = 0
    sum_cre_fin = 0
    sum_deb_init = 0
    sum_cre_init = 0
    sum_deb_mvt = 0
    sum_cre_mvt = 0
    
    comptes_avec_valeurs = []
    
    for ligne in balance_data:
        deb_fin = int(ligne.get("debit_fin", 0) or 0)
        cre_fin = int(ligne.get("credit_fin", 0) or 0)
        deb_init = int(ligne.get("debit_initial", 0) or 0)
        cre_init = int(ligne.get("credit_initial", 0) or 0)
        
        # Essayer les deux noms possibles pour les mouvements
        deb_mvt = int(ligne.get("debit_mvt", 0) or ligne.get("mouvement_debit", 0) or 0)
        cre_mvt = int(ligne.get("credit_mvt", 0) or ligne.get("mouvement_credit", 0) or 0)
        
        sum_deb_fin += deb_fin
        sum_cre_fin += cre_fin
        sum_deb_init += deb_init
        sum_cre_init += cre_init
        sum_deb_mvt += deb_mvt
        sum_cre_mvt += cre_mvt
        
        if deb_fin > 0 or cre_fin > 0:
            comptes_avec_valeurs.append({
                'compte': ligne.get('numero_compte', ''),
                'libelle': ligne.get('libelle', '')[:30],
                'debit_fin': deb_fin,
                'credit_fin': cre_fin,
                'solde': abs(deb_fin - cre_fin)
            })
    
    print(f"\n  Total débits finaux: {sum_deb_fin:,} FCFA")
    print(f"  Total crédits finaux: {sum_cre_fin:,} FCFA")
    print(f"  ÉCART: {abs(sum_deb_fin - sum_cre_fin):,} FCFA")
    print(f"\n  Total débits initiaux: {sum_deb_init:,} FCFA")
    print(f"  Total crédits initiaux: {sum_cre_init:,} FCFA")
    print(f"  Écart initiaux: {abs(sum_deb_init - sum_cre_init):,} FCFA")
    print(f"\n  Total mouvements débits: {sum_deb_mvt:,} FCFA")
    print(f"  Total mouvements crédits: {sum_cre_mvt:,} FCFA")
    print(f"  Écart mouvements: {abs(sum_deb_mvt - sum_cre_mvt):,} FCFA")
    
    # Vérifier la formule pour chaque compte
    print("\n🔍 VÉRIFICATION DE LA FORMULE (10 premiers comptes avec valeurs):")
    erreurs_formule = []
    for compte_info in comptes_avec_valeurs[:10]:
        compte_num = compte_info['compte']
        ligne = next((l for l in balance_data if l.get('numero_compte') == compte_num), None)
        if not ligne:
            continue
        
        deb_init = int(ligne.get("debit_initial", 0) or 0)
        cre_init = int(ligne.get("credit_initial", 0) or 0)
        deb_mvt = int(ligne.get("debit_mvt", 0) or ligne.get("mouvement_debit", 0) or 0)
        cre_mvt = int(ligne.get("credit_mvt", 0) or ligne.get("mouvement_credit", 0) or 0)
        deb_fin = int(ligne.get("debit_fin", 0) or 0)
        cre_fin = int(ligne.get("credit_fin", 0) or 0)
        
        solde_init = deb_init - cre_init
        mouvement_net = deb_mvt - cre_mvt
        solde_fin_calc = solde_init + mouvement_net
        solde_fin_reel = deb_fin - cre_fin
        
        ecart = abs(solde_fin_calc - solde_fin_reel)
        
        print(f"\n  Compte {compte_num} - {compte_info['libelle']}:")
        print(f"    Solde initial: {solde_init:,} (Débit {deb_init:,} - Crédit {cre_init:,})")
        print(f"    Mouvement net: {mouvement_net:,} (Débit {deb_mvt:,} - Crédit {cre_mvt:,})")
        print(f"    Solde final calculé: {solde_fin_calc:,}")
        print(f"    Solde final réel: {solde_fin_reel:,} (Débit {deb_fin:,} - Crédit {cre_fin:,})")
        print(f"    ÉCART: {ecart:,} FCFA")
        
        if ecart > 0:
            erreurs_formule.append({
                'compte': compte_num,
                'ecart': ecart,
                'solde_calc': solde_fin_calc,
                'solde_reel': solde_fin_reel
            })
    
    if erreurs_formule:
        print(f"\n⚠️  {len(erreurs_formule)} compte(s) avec écart dans la formule")
    else:
        print("\n✅ Aucun écart détecté dans les 10 premiers comptes")
    
    # Vérifier le rapport de cohérence
    print("\n📋 RAPPORT DE COHÉRENCE:")
    coherence = mission.get('coherence', {})
    if coherence:
        for annee, report in coherence.items():
            print(f"\n  Année {annee}:")
            print(f"    Équilibre global: {report.get('equilibre_global', 'N/A')}")
            if 'verification_equilibre' in report:
                ve = report['verification_equilibre']
                print(f"    Total débits: {ve.get('total_debits', 0):,} FCFA")
                print(f"    Total crédits: {ve.get('total_credits', 0):,} FCFA")
                print(f"    Écart: {ve.get('ecart', 0):,} FCFA")
    else:
        print("  Aucun rapport de cohérence trouvé")

if __name__ == "__main__":
    mission_id = sys.argv[1] if len(sys.argv) > 1 else None
    diagnostic_calculs(mission_id)


