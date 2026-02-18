#!/usr/bin/env python3
"""
Script pour forcer la réexécution du contrôle d'intangibilité
Utile si le rapport stocké est obsolète ou incorrect
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.model import Mission

def reexecuter_controle(mission_id):
    """Force la réexécution du contrôle d'intangibilité"""
    
    print("=" * 80)
    print(f"🔄 RÉEXÉCUTION DU CONTRÔLE D'INTANGIBILITÉ")
    print(f"Mission ID: {mission_id}")
    print("=" * 80)
    
    try:
        mission_obj = Mission()
        
        print(f"\n📋 Exécution du contrôle d'intangibilité...")
        resultat = mission_obj.controle_intangibilite(mission_id)
        
        if resultat:
            print(f"\n✅ Contrôle exécuté avec succès!")
            print(f"   Total comptes: {resultat.get('total_comptes', 0)}")
            print(f"   Écarts: {resultat.get('ecarts_count', 0)}")
            print(f"   OK: {resultat.get('ok', False)}")
            
            if resultat.get('total_comptes', 0) == 0:
                print(f"\n   ⚠️  Toujours 0 comptes trouvés")
                print(f"   Message: {resultat.get('message', 'N/A')}")
                print(f"\n   💡 Vérifiez les logs du serveur ci-dessus pour voir pourquoi")
            else:
                print(f"\n   ✅ {resultat.get('total_comptes', 0)} comptes trouvés!")
                print(f"   Le tableau devrait maintenant afficher les données")
        else:
            print(f"❌ Le contrôle n'a retourné aucun résultat")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reexecuter_controle_intangibilite.py <mission_id>")
        print("\nExemple:")
        print("  python reexecuter_controle_intangibilite.py 690237d33b694de2f40f4329")
        sys.exit(1)
    
    mission_id = sys.argv[1]
    reexecuter_controle(mission_id)









