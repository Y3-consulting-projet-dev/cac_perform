#!/usr/bin/env python3
"""
Test complet du contrôle d'intangibilité avec affichage de tous les logs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId
from src.model import Mission

def test_controle_complet(mission_id):
    """Test complet avec tous les logs"""
    
    print("=" * 80)
    print(f"🧪 TEST COMPLET DU CONTRÔLE D'INTANGIBILITÉ")
    print(f"Mission ID: {mission_id}")
    print("=" * 80)
    
    try:
        # Créer l'objet Mission
        mission_obj = Mission()
        
        print(f"\n📋 Exécution du contrôle...")
        print("=" * 80)
        
        # Exécuter le contrôle
        resultat = mission_obj.controle_intangibilite(mission_id)
        
        print("=" * 80)
        print(f"\n📊 RÉSULTAT:")
        if resultat:
            print(f"   OK: {resultat.get('ok', 'N/A')}")
            print(f"   Total comptes: {resultat.get('total_comptes', 0)}")
            print(f"   Écarts: {resultat.get('ecarts_count', 0)}")
            print(f"   Nombre de comptes dans la liste: {len(resultat.get('comptes', []))}")
            print(f"   Message: {resultat.get('message', 'N/A')}")
            
            if len(resultat.get('comptes', [])) > 0:
                print(f"\n   ✅ Exemples de comptes:")
                for i, compte in enumerate(resultat.get('comptes', [])[:5]):
                    print(f"      {i+1}. {compte.get('numero_compte')}: {compte.get('status')} - {compte.get('libelle', '')[:40]}")
            else:
                print(f"\n   ❌ Aucun compte dans la liste")
        else:
            print(f"   ❌ Aucun résultat")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_controle_complet.py <mission_id>")
        sys.exit(1)
    
    test_controle_complet(sys.argv[1])
