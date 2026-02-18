"""
Script pour mettre à jour le grouping des missions existantes
en ajoutant le champ 'comptes' à chaque groupe
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from bson import ObjectId
from src.model import Mission
from src import mongo

# Connexion à la base de données
try:
    db = mongo.get_db
    if db is None:
        raise Exception("mongo.get_db est None")
except:
    print("⚠️  Utilisation de la connexion MongoDB directe")
    from pymongo import MongoClient
    client = MongoClient('mongodb://localhost:27017/')
    db = client['cac_perform']

def update_all_missions_grouping():
    """Met à jour le grouping de toutes les missions pour inclure les comptes détaillés"""
    
    # Récupérer toutes les missions
    missions = db.Mission1.find({})
    total_missions = db.Mission1.count_documents({})
    
    print(f"📊 {total_missions} mission(s) trouvée(s)")
    
    updated_count = 0
    error_count = 0
    
    for mission in missions:
        mission_id = mission.get('_id')
        mission_id_str = str(mission_id)
        
        try:
            # Récupérer balance_variation
            balance_variation = mission.get("balance_variation", [])
            if not balance_variation:
                print(f"⚠️ Mission {mission_id_str}: Pas de balance_variation, ignorée")
                continue
            
            # Récupérer le référentiel
            referentiel = mission.get("referentiel", "syscohada")
            
            # Créer une nouvelle instance de Mission pour utiliser create_grouping
            cls = Mission()
            
            # Régénérer le grouping avec les nouvelles règles
            print(f"🔄 Mise à jour de la mission {mission_id_str}...")
            grouping_model = cls.create_grouping(balance_variation, referentiel)
            
            # Compter les groupes avec des comptes
            groupes_avec_comptes = sum(1 for g in grouping_model if g.get('comptes') and len(g.get('comptes', [])) > 0)
            total_comptes = sum(len(g.get('comptes', [])) for g in grouping_model)
            
            # Sauvegarder le nouveau grouping dans la mission
            result = db.Mission1.update_one(
                {"_id": ObjectId(mission_id_str)},
                {"$set": {"grouping": grouping_model}}
            )
            
            if result.modified_count > 0:
                updated_count += 1
                print(f"✅ Mission {mission_id_str}: Grouping mis à jour ({len(grouping_model)} groupes, {groupes_avec_comptes} avec comptes, {total_comptes} comptes totaux)")
            else:
                print(f"⚠️ Mission {mission_id_str}: Aucune modification nécessaire")
                
        except Exception as e:
            error_count += 1
            print(f"❌ Erreur pour la mission {mission_id_str}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 Résumé:")
    print(f"   - Missions mises à jour: {updated_count}")
    print(f"   - Erreurs: {error_count}")
    print(f"   - Total traité: {updated_count + error_count}")

if __name__ == "__main__":
    print("🚀 Démarrage de la mise à jour du grouping pour toutes les missions...\n")
    update_all_missions_grouping()
    print("\n✅ Mise à jour terminée!")

