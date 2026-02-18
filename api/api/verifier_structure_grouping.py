#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier la structure du grouping et si les comptes sont bien groupés
"""

from pymongo import MongoClient
from bson import ObjectId
import json
import sys

def verifier_grouping(mission_id=None):
    """
    Vérifie la structure du grouping pour une mission
    """
    try:
        # Connexion MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['cac_perform']
        
        # Si mission_id fourni, chercher cette mission
        if mission_id:
            mission = db.Mission1.find_one({"_id": ObjectId(mission_id)})
            if not mission:
                print(f"❌ Mission {mission_id} non trouvée")
                return
            missions = [mission]
        else:
            # Sinon, prendre toutes les missions avec grouping
            missions = list(db.Mission1.find({"grouping": {"$exists": True, "$ne": []}}).limit(5))
        
        if not missions:
            print("❌ Aucune mission avec grouping trouvée")
            return
        
        print(f"📊 Analyse de {len(missions)} mission(s)\n")
        print("=" * 80)
        
        for idx, mission in enumerate(missions, 1):
            mission_id = str(mission['_id'])
            print(f"\n🔍 Mission {idx}: {mission_id}")
            print("-" * 80)
            
            grouping = mission.get("grouping", [])
            if not grouping:
                print("⚠️  Pas de grouping dans cette mission")
                continue
            
            print(f"✅ Nombre de groupes: {len(grouping)}")
            
            # Analyser chaque groupe
            groupes_avec_comptes = 0
            groupes_sans_comptes = 0
            total_comptes = 0
            
            print(f"\n📋 Détail des groupes:")
            print("-" * 80)
            
            for i, groupe in enumerate(grouping[:5], 1):  # Afficher les 5 premiers groupes
                compte = groupe.get('compte', 'N/A')
                libelle = groupe.get('libelle', 'N/A')
                solde_n = groupe.get('solde_n', 0)
                solde_n1 = groupe.get('solde_n1', 0)
                
                # Vérifier si le champ 'comptes' existe
                comptes = groupe.get('comptes', None)
                
                if comptes is not None:
                    nb_comptes = len(comptes)
                    total_comptes += nb_comptes
                    groupes_avec_comptes += 1
                    status = "✅"
                    detail = f"({nb_comptes} comptes)"
                else:
                    groupes_sans_comptes += 1
                    status = "⚠️"
                    detail = "(pas de champ 'comptes')"
                
                print(f"{status} Groupe {i}: {compte} - {libelle}")
                print(f"   Solde N: {solde_n:,.0f} | Solde N-1: {solde_n1:,.0f} {detail}")
                
                # Afficher quelques exemples de comptes si disponibles
                if comptes and len(comptes) > 0:
                    print(f"   Exemples de comptes:")
                    for compte_detail in comptes[:3]:
                        num = compte_detail.get('numero_compte', 'N/A')
                        lib = compte_detail.get('libelle', 'N/A')
                        solde_n_detail = compte_detail.get('solde_n', 0)
                        print(f"      - {num}: {lib} (N={solde_n_detail:,.0f})")
                    if len(comptes) > 3:
                        print(f"      ... et {len(comptes) - 3} autres comptes")
            
            # Statistiques globales
            print(f"\n📊 Statistiques:")
            print(f"   - Groupes avec champ 'comptes': {groupes_avec_comptes}")
            print(f"   - Groupes sans champ 'comptes': {groupes_sans_comptes}")
            print(f"   - Total comptes détaillés: {total_comptes}")
            
            # Vérifier tous les groupes
            if len(grouping) > 5:
                print(f"\n   ... ({len(grouping) - 5} autres groupes non affichés)")
                
                # Compter tous les groupes
                total_avec_comptes = sum(1 for g in grouping if g.get('comptes') is not None)
                total_sans_comptes = len(grouping) - total_avec_comptes
                total_tous_comptes = sum(len(g.get('comptes', [])) for g in grouping)
                
                print(f"\n   Statistiques complètes:")
                print(f"   - Total groupes: {len(grouping)}")
                print(f"   - Groupes avec comptes: {total_avec_comptes}")
                print(f"   - Groupes sans comptes: {total_sans_comptes}")
                print(f"   - Total comptes détaillés: {total_tous_comptes}")
        
        print("\n" + "=" * 80)
        print("✅ Vérification terminée")
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    mission_id = sys.argv[1] if len(sys.argv) > 1 else None
    verifier_grouping(mission_id)




