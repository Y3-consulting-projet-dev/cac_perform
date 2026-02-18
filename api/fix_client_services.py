"""
Script pour corriger les erreurs db dans client_services.py
"""

import re

def fix_client_services():
    """Corrige les erreurs db dans client_services.py"""
    
    file_path = "src/services/client_services.py"
    
    try:
        # Lire le fichier
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Corrections à appliquer
        corrections = [
            # Ligne 48 - create_client
            (r'(\s+)# Vérifier si un client avec le même nom existe déjà\n(\s+)existing_client = db\.Client\.find_one',
             r'\1# Vérifier si un client avec le même nom existe déjà\n\1db = get_db()\n\2existing_client = db.Client.find_one'),
            
            # Ligne 121 - get_client_by_id  
            (r'(\s+)client = db\.Client\.find_one\(\{"_id": object_id\}\)',
             r'\1db = get_db()\n\1client = db.Client.find_one({"_id": object_id})'),
            
            # Ligne 187 - get_client_missions
            (r'(\s+)missions = list\(db\.Mission1\.find\(query\)\)',
             r'\1db = get_db()\n\1missions = list(db.Mission1.find(query))'),
            
            # Ligne 236 - update_client
            (r'(\s+)existing_client = db\.Client\.find_one\(\{"_id": object_id\}\)',
             r'\1db = get_db()\n\1existing_client = db.Client.find_one({"_id": object_id})'),
            
            # Ligne 304 - delete_client
            (r'(\s+)client_result = db\.Client\.delete_one\(\{"_id": object_id\}\)',
             r'\1db = get_db()\n\1client_result = db.Client.delete_one({"_id": object_id})'),
        ]
        
        # Appliquer les corrections
        for pattern, replacement in corrections:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                print(f"✅ Correction appliquée: {pattern[:50]}...")
            else:
                print(f"⚠️  Pattern non trouvé: {pattern[:50]}...")
        
        # Écrire le fichier corrigé
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fichier client_services.py corrigé avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        return False

if __name__ == "__main__":
    fix_client_services()








