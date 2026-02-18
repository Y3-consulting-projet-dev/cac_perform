"""
Script pour obtenir un ID client valide depuis la base de données
Utile pour tester l'API de création de mission
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.database import get_database

def get_client_ids():
    """Récupère la liste des IDs clients disponibles"""
    
    print("=" * 70)
    print("🔍 RÉCUPÉRATION DES IDS CLIENTS")
    print("=" * 70)
    
    try:
        db = get_database()
        clients = list(db.Client.find().limit(10))
        
        if not clients:
            print("❌ Aucun client trouvé dans la base de données")
            print("   Créez d'abord un client via l'API /api/v1/clients/")
            return
        
        print(f"\n✅ {len(clients)} client(s) trouvé(s) :\n")
        
        for i, client in enumerate(clients, 1):
            client_id = str(client['_id'])
            nom = client.get('nom', 'Sans nom')
            activite = client.get('activite', 'N/A')
            
            print(f"{i}. ID: {client_id}")
            print(f"   Nom: {nom}")
            print(f"   Activité: {activite}")
            print()
        
        print("=" * 70)
        print("💡 Utilisez l'un de ces IDs dans votre requête Insomnia")
        print("=" * 70)
        
        # Afficher le premier ID pour copier-coller
        if clients:
            first_id = str(clients[0]['_id'])
            print(f"\n📋 ID à copier (premier client) :")
            print(f"   {first_id}")
            print()
        
    except Exception as e:
        print(f"❌ Erreur: {type(e).__name__}: {str(e)}")
        print("   Vérifiez que MongoDB est démarré et que la connexion fonctionne")


if __name__ == '__main__':
    get_client_ids()

