"""
Script pour trouver toutes les méthodes qui utilisent db sans le définir
"""

import re

def find_db_problems():
    with open('src/model.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    problems = []
    current_method = None
    method_start = 0
    method_lines = []
    
    for i, line in enumerate(lines, 1):
        # Détecter le début d'une méthode
        method_match = re.match(r'^\s+def\s+(\w+)\s*\(', line)
        if method_match:
            # Analyser la méthode précédente si elle existe
            if current_method and method_lines:
                method_content = ''.join(method_lines)
                has_db_use = bool(re.search(r'\bdb\.', method_content))
                has_db_def = bool(re.search(r'\bdb\s*=\s*get_db\(\)', method_content)) or \
                            bool(re.search(r'\bdb\s*=\s*get_database\(\)', method_content))
                
                if has_db_use and not has_db_def:
                    # Trouver les lignes exactes avec db.
                    db_lines = []
                    for j, ml in enumerate(method_lines, method_start):
                        if re.search(r'\bdb\.', ml):
                            db_lines.append((j, ml.strip()[:80]))
                    
                    problems.append({
                        'method': current_method,
                        'start': method_start,
                        'db_lines': db_lines
                    })
            
            # Nouvelle méthode
            current_method = method_match.group(1)
            method_start = i
            method_lines = [line]
        elif current_method:
            # Continuer à collecter les lignes de la méthode
            method_lines.append(line)
            
            # Détecter la fin de la méthode (méthode suivante ou fin de classe)
            if re.match(r'^\s+def\s+', line) and i > method_start:
                # C'est une nouvelle méthode, on a déjà traité la précédente
                pass
            elif re.match(r'^class\s+', line):
                # Fin de la classe
                if method_lines:
                    method_content = ''.join(method_lines)
                    has_db_use = bool(re.search(r'\bdb\.', method_content))
                    has_db_def = bool(re.search(r'\bdb\s*=\s*get_db\(\)', method_content)) or \
                                bool(re.search(r'\bdb\s*=\s*get_database\(\)', method_content))
                    
                    if has_db_use and not has_db_def:
                        db_lines = []
                        for j, ml in enumerate(method_lines, method_start):
                            if re.search(r'\bdb\.', ml):
                                db_lines.append((j, ml.strip()[:80]))
                        
                        problems.append({
                            'method': current_method,
                            'start': method_start,
                            'db_lines': db_lines
                        })
                break
    
    # Traiter la dernière méthode
    if current_method and method_lines:
        method_content = ''.join(method_lines)
        has_db_use = bool(re.search(r'\bdb\.', method_content))
        has_db_def = bool(re.search(r'\bdb\s*=\s*get_db\(\)', method_content)) or \
                    bool(re.search(r'\bdb\s*=\s*get_database\(\)', method_content))
        
        if has_db_use and not has_db_def:
            db_lines = []
            for j, ml in enumerate(method_lines, method_start):
                if re.search(r'\bdb\.', ml):
                    db_lines.append((j, ml.strip()[:80]))
            
            problems.append({
                'method': current_method,
                'start': method_start,
                'db_lines': db_lines
            })
    
    print("=" * 80)
    print("🔍 MÉTHODES UTILISANT 'db' SANS DÉFINITION")
    print("=" * 80)
    
    if problems:
        print(f"\n❌ {len(problems)} méthode(s) problématique(s):\n")
        for p in problems:
            print(f"  Méthode: {p['method']} (ligne {p['start']})")
            for line_num, line_content in p['db_lines']:
                print(f"    Ligne {line_num}: {line_content}")
            print()
    else:
        print("\n✅ Toutes les méthodes définissent 'db' correctement")
    
    print("=" * 80)
    return problems

if __name__ == '__main__':
    find_db_problems()





