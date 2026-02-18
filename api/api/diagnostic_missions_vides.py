#!/usr/bin/env python3
"""
Script pour diagnostiquer pourquoi les missions ne s'affichent pas dans le tableau
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId

def diagnostic_missions_tableau(client_id):
    """Diagnostique pourquoi les missions ne s'affichent pas"""
    
    print("=" * 80)
    print(f"🔍 DIAGNOSTIC MISSIONS POUR CLIENT: {client_id}")
    print("=" * 80)
    
    try:
        # Connexion
        client = MongoClient('mongodb://localhost:27017/')
        db = client['cac_perform']
        
        # Vérifier que le client existe
        print(f"\n1. Vérification du client...")
        client_doc = db.Client.find_one({"_id": ObjectId(client_id)})
        
        if not client_doc:
            print(f"   ❌ Client {client_id} non trouvé")
            return
        
        print(f"   ✅ Client trouvé: {client_doc.get('nom', 'Sans nom')}")
        
        # Rechercher les missions avec id_client comme string
        print(f"\n2. Recherche des missions avec id_client='{client_id}' (string)...")
        missions_string = list(db.Mission1.find({"id_client": client_id}))
        print(f"   📊 Missions trouvées (string): {len(missions_string)}")
        
        # Rechercher les missions avec id_client comme ObjectId
        print(f"\n3. Recherche des missions avec id_client=ObjectId('{client_id}')...")
        try:
            missions_objectid = list(db.Mission1.find({"id_client": ObjectId(client_id)}))
            print(f"   📊 Missions trouvées (ObjectId): {len(missions_objectid)}")
        except:
            missions_objectid = []
            print(f"   ⚠️  Erreur lors de la recherche avec ObjectId")
        
        # Toutes les missions pour debug
        print(f"\n4. Toutes les missions dans la base...")
        toutes_missions = list(db.Mission1.find({}).limit(10))
        print(f"   📊 Total de missions en base: {db.Mission1.count_documents({})}")
        print(f"   📋 Exemples d'id_client dans les missions:")
        
        id_clients_trouves = set()
        for mission in toutes_missions[:5]:
            mission_id_client = mission.get('id_client', 'NON DÉFINI')
            id_clients_trouves.add(str(mission_id_client))
            print(f"      - Mission {mission['_id']}: id_client='{mission_id_client}' (type: {type(mission_id_client)})")
        
        # Comparaison
        print(f"\n5. Analyse...")
        print(f"   - ID du client recherché: '{client_id}' (type: string)")
        print(f"   - IDs trouvés dans les missions: {id_clients_trouves}")
        
        if client_id in id_clients_trouves:
            print(f"   ✅ L'ID correspond bien!")
        else:
            print(f"   ❌ L'ID ne correspond pas!")
            print(f"   💡 Solutions possibles:")
            print(f"      - L'id_client dans les missions est différent de l'ID du client")
            print(f"      - L'id_client est stocké comme ObjectId au lieu de string")
            
            # Essayer de trouver les missions en comparant les strings
            missions_possibles = []
            for mission in toutes_missions:
                mission_id_client = str(mission.get('id_client', ''))
                if mission_id_client == client_id or mission_id_client == str(ObjectId(client_id)):
                    missions_possibles.append(mission)
            
            if len(missions_possibles) > 0:
                print(f"\n   ✅ {len(missions_possibles)} mission(s) trouvée(s) avec comparaison de strings:")
                for mission in missions_possibles:
                    print(f"      - Mission {mission['_id']} (Année: {mission.get('annee_auditee', 'N/A')})")
        
        # Résultat final
        missions_trouvees = missions_string if len(missions_string) > 0 else missions_objectid if len(missions_objectid) > 0 else []
        
        print(f"\n" + "=" * 80)
        print(f"📊 RÉSULTAT FINAL")
        print("=" * 80)
        print(f"   Missions trouvées pour ce client: {len(missions_trouvees)}")
        
        if len(missions_trouvees) == 0:
            print(f"\n❌ PROBLÈME: Aucune mission trouvée pour ce client")
            print(f"\n💡 CAUSES POSSIBLES:")
            print(f"   1. Aucune mission n'a été créée pour ce client")
            print(f"   2. L'id_client sauvegardé ne correspond pas à l'ID du client")
            print(f"   3. Les missions ont été créées avec un id_client différent")
            print(f"\n🔧 SOLUTIONS:")
            print(f"   1. Créer une nouvelle mission via l'interface")
            print(f"   2. Vérifier les logs du serveur lors de la création")
            print(f"   3. Utiliser le script verifier_missions.py pour voir toutes les missions")
        else:
            print(f"\n✅ Missions trouvées:")
            for mission in missions_trouvees:
                print(f"   - Mission {mission['_id']}")
                print(f"     Année: {mission.get('annee_auditee', 'N/A')}")
                print(f"     Date début: {mission.get('date_debut', 'N/A')}")
                print(f"     Date fin: {mission.get('date_fin', 'N/A')}")
                print(f"     Balances: {len(mission.get('balances', []))}")
            
            print(f"\n💡 Si ces missions ne s'affichent pas dans l'interface:")
            print(f"   1. Vérifiez la console du navigateur (F12) pour les erreurs")
            print(f"   2. Vérifiez que l'API retourne bien ces missions")
            print(f"   3. Rechargez la page (F5)")
        ù
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnostic_missions_vides.py <client_id>")
        print("\nExemple:")
        print("  python diagnostic_missions_vides.py 690103f3013b374b6f390573")
        sys.exit(1)
    
    client_id = sys.argv[1]
    diagnostic_missions_tableau(client_id)

