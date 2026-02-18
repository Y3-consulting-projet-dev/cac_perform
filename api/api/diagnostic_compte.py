#!/usr/bin/env python3
"""
Script pour diagnostiquer un compte spécifique et comprendre pourquoi une erreur n'est pas détectée
"""

import sys
import os
from pymongo import MongoClient
from bson import ObjectId

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def diagnostic_compte(mission_id, numero_compte):
    """Diagnostique un compte spécifique"""
    
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    db = client['cac_perform']
    
    mission = db.Mission1.find_one({'_id': ObjectId(mission_id)})
    if not mission:
        print("❌ Mission non trouvée")
        return
    
    balances = mission.get('balances', [])
    if not balances:
        print("❌ Aucune balance trouvée")
        return
    
    # Prendre la première balance (année N)
    balance_id = balances[0]
    balance = db.Balance.find_one({'_id': ObjectId(balance_id)})
    
    if not balance:
        print("❌ Balance introuvable")
        return
    
    balance_data = balance.get('balance', [])
    print(f"\n📊 Analyse du compte {numero_compte}")
    print(f"   Total lignes dans la balance: {len(balance_data)}\n")
    
    # Chercher le compte
    compte_trouve = None
    for ligne in balance_data:
        if str(ligne.get('numero_compte', '')).strip() == str(numero_compte).strip():
            compte_trouve = ligne
            break
    
    if not compte_trouve:
        print(f"❌ Compte {numero_compte} non trouvé dans la balance")
        print(f"\n📋 Comptes disponibles (10 premiers):")
        for i, ligne in enumerate(balance_data[:10]):
            num = ligne.get('numero_compte', 'N/A')
            lib = ligne.get('libelle', '')[:30]
            print(f"   {i+1}. {num} - {lib}")
        return
    
    print(f"✅ Compte trouvé!\n")
    
    # Afficher toutes les données du compte
    print(f"📋 DONNÉES DU COMPTE:")
    di = int(compte_trouve.get("debit_initial", 0) or 0)
    ci = int(compte_trouve.get("credit_initial", 0) or 0)
    df = int(compte_trouve.get("debit_fin", 0) or 0)
    cf = int(compte_trouve.get("credit_fin", 0) or 0)
    md_explicite = int(compte_trouve.get("mouvement_debit", 0) or compte_trouve.get("debit_mvt", 0) or 0)
    mc_explicite = int(compte_trouve.get("mouvement_credit", 0) or compte_trouve.get("credit_mvt", 0) or 0)
    
    print(f"   Débit initial: {di:,} FCFA")
    print(f"   Crédit initial: {ci:,} FCFA")
    print(f"   Débit fin: {df:,} FCFA")
    print(f"   Crédit fin: {cf:,} FCFA")
    print(f"   Mouvement débit (explicite): {md_explicite:,} FCFA")
    print(f"   Mouvement crédit (explicite): {mc_explicite:,} FCFA")
    print(f"   Libellé: {compte_trouve.get('libelle', 'N/A')}")
    
    # Calculer les soldes
    solde_initial = di - ci
    solde_fin = df - cf
    
    print(f"\n🧮 CALCULS:")
    print(f"   Solde initial (Débit init - Crédit init): {solde_initial:,} FCFA")
    print(f"   Solde fin (Débit fin - Crédit fin): {solde_fin:,} FCFA")
    
    # Calculer les mouvements
    mouvement_debit_calcule = df - di
    mouvement_credit_calcule = cf - ci
    
    print(f"\n📊 MOUVEMENTS:")
    print(f"   Mouvement débit calculé (Débit fin - Débit init): {mouvement_debit_calcule:,} FCFA")
    print(f"   Mouvement crédit calculé (Crédit fin - Crédit init): {mouvement_credit_calcule:,} FCFA")
    print(f"   Mouvement débit explicite: {md_explicite:,} FCFA")
    print(f"   Mouvement crédit explicite: {mc_explicite:,} FCFA")
    
    # Déterminer quels mouvements utiliser
    if md_explicite != 0 or mc_explicite != 0:
        mouvement_debit = md_explicite
        mouvement_credit = mc_explicite
        source = "explicites"
    else:
        mouvement_debit = mouvement_debit_calcule
        mouvement_credit = mouvement_credit_calcule
        source = "calculés"
    
    print(f"\n✅ MOUVEMENTS UTILISÉS (source: {source}):")
    print(f"   Mouvement débit: {mouvement_debit:,} FCFA")
    print(f"   Mouvement crédit: {mouvement_credit:,} FCFA")
    print(f"   Mouvement net: {mouvement_debit - mouvement_credit:,} FCFA")
    
    # Calculer le solde attendu
    solde_cloture_attendu = solde_initial + (mouvement_debit - mouvement_credit)
    
    print(f"\n🔍 VÉRIFICATION DE LA FORMULE:")
    print(f"   Formule: Solde de clôture = Solde d'ouverture + Mouvements de période")
    print(f"   Solde attendu: {solde_initial:,} + ({mouvement_debit:,} - {mouvement_credit:,}) = {solde_cloture_attendu:,} FCFA")
    print(f"   Solde réel: {solde_fin:,} FCFA")
    
    # Calculer l'écart
    ecart = abs(solde_fin - solde_cloture_attendu)
    print(f"   ÉCART: {ecart:,} FCFA")
    
    # Vérifier avec la tolérance
    tolerance = 0.01
    print(f"\n⚠️  TOLÉRANCE: {tolerance} FCFA")
    if ecart > tolerance:
        print(f"   ✅ ERREUR DÉTECTÉE (écart > tolérance)")
        print(f"   L'outil DEVRAIT signaler cette erreur")
    else:
        print(f"   ❌ PAS D'ERREUR (écart <= tolérance)")
        print(f"   L'outil ne signalera PAS cette erreur car l'écart est trop petit")
    
    # Vérifier le rapport de cohérence
    print(f"\n📋 RAPPORT DE COHÉRENCE:")
    coherence = mission.get('coherence', {})
    if coherence:
        for annee, report in coherence.items():
            print(f"\n   Année {annee}:")
            erreurs = report.get('erreurs', [])
            erreur_trouvee = False
            for erreur in erreurs:
                if erreur.get('numero_compte') == str(numero_compte) and erreur.get('type') == 'arithmetique':
                    erreur_trouvee = True
                    print(f"      ✅ Erreur trouvée dans le rapport:")
                    print(f"         Type: {erreur.get('type')}")
                    print(f"         Message: {erreur.get('message', '')[:200]}...")
                    break
            if not erreur_trouvee:
                print(f"      ❌ Aucune erreur trouvée pour ce compte dans le rapport")
    else:
        print("   Aucun rapport de cohérence trouvé")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python diagnostic_compte.py <mission_id> <numero_compte>")
        sys.exit(1)
    
    mission_id = sys.argv[1]
    numero_compte = sys.argv[2]
    diagnostic_compte(mission_id, numero_compte)



