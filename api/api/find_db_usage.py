"""
Script pour trouver toutes les utilisations de 'db' dans model.py
et vérifier si elles sont définies dans la méthode
"""

import re

def find_db_usage():
    """Trouve toutes les utilisations de db dans model.py"""
    
    with open('src/model.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Trouver toutes les méthodes
    methods = []
    current_method = None
    current_indent = 0
    
    for i, line in enumerate(lines, 1):
        # Détecter le début d'une méthode
        method_match = re.match(r'^\s+def\s+(\w+)\s*\(', line)
        if method_match:
            if current_method:
                methods.append({
                    'name': current_method['name'],
                    'start': current_method['start'],
                    'end': i - 1,
                    'lines': lines[current_method['start']-1:i-1]
                })
            current_method = {
                'name': method_match.group(1),
                'start': i
            }
    
    # Ajouter la dernière méthode
    if current_method:
        methods.append({
            'name': current_method['name'],
            'start': current_method['start'],
            'end': len(lines),
            'lines': lines[current_method['start']-1:]
        })
    
    # Vérifier chaque méthode pour les utilisations de db
    print("=" * 80)
    print("🔍 RECHERCHE DES UTILISATIONS DE 'db' SANS DÉFINITION")
    print("=" * 80)
    
    problems = []
    
    for method in methods:
        method_content = '\n'.join(method['lines'])
        
        # Chercher les utilisations de db
        db_uses = re.findall(r'\bdb\.', method_content)
        
        if db_uses:
            # Vérifier si db est défini dans la méthode
            db_defined = re.search(r'\bdb\s*=\s*get_db\(\)', method_content) or \
                        re.search(r'\bdb\s*=\s*get_database\(\)', method_content)
            
            if not db_defined:
                # Trouver les lignes exactes
                for j, line in enumerate(method['lines'], method['start']):
                    if re.search(r'\bdb\.', line):
                        problems.append({
                            'method': method['name'],
                            'line': j,
                            'content': line.strip()
                        })
    
    if problems:
        print(f"\n❌ {len(problems)} problème(s) trouvé(s):\n")
        for problem in problems:
            print(f"  Méthode: {problem['method']}")
            print(f"  Ligne {problem['line']}: {problem['content']}")
            print()
    else:
        print("\n✅ Aucun problème trouvé - toutes les utilisations de 'db' sont définies")
    
    print("=" * 80)

if __name__ == '__main__':
    find_db_usage()





