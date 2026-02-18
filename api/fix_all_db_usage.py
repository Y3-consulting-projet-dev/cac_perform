"""
Script pour corriger toutes les utilisations de db dans model.py
Ajoute db = get_db() au début de chaque fonction/méthode qui utilise db.
"""

import re

def fix_all_db_usage():
    """Corrige toutes les utilisations de db dans model.py"""
    
    file_path = "src/model.py"
    
    try:
        # Lire le fichier
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        i = 0
        fixed_count = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Détecter le début d'une fonction ou méthode
            # Pattern pour: def function_name ou @classmethod/@staticmethod suivi de def
            is_method_start = False
            method_start_idx = -1
            indent_level = 0
            
            # Vérifier si c'est le début d'une fonction
            def_match = re.match(r'^(\s*)def\s+(\w+)\s*\(', line)
            decorator_match = re.match(r'^(\s*)(@classmethod|@staticmethod)', line)
            
            if def_match:
                is_method_start = True
                method_start_idx = i
                indent_level = len(def_match.group(1))
            elif decorator_match:
                # C'est un décorateur, la fonction suivante sera la fonction
                new_lines.append(line)
                i += 1
                # Chercher la ligne avec "def"
                while i < len(lines) and not re.match(r'^\s*def\s+', lines[i]):
                    new_lines.append(lines[i])
                    i += 1
                
                if i < len(lines):
                    def_match = re.match(r'^(\s*)def\s+(\w+)\s*\(', lines[i])
                    if def_match:
                        is_method_start = True
                        method_start_idx = i
                        indent_level = len(def_match.group(1))
            
            if is_method_start and method_start_idx >= 0:
                # Trouver où commence le corps de la fonction (après la ligne :)
                body_start = method_start_idx + 1
                while body_start < len(lines):
                    if ':' in lines[body_start] or lines[body_start].strip().startswith(':'):
                        body_start += 1
                        break
                    body_start += 1
                
                # Trouver où se termine la signature de la fonction
                func_signature_end = body_start
                open_parens = 0
                j = method_start_idx
                while j < len(lines) and j < method_start_idx + 10:
                    for char in lines[j]:
                        if char == '(':
                            open_parens += 1
                        elif char == ')':
                            open_parens -= 1
                            if open_parens == 0:
                                func_signature_end = j + 1
                                break
                    if open_parens == 0:
                        break
                    j += 1
                
                # Chercher la première ligne du corps (après :)
                body_line_idx = func_signature_end
                while body_line_idx < len(lines) and body_line_idx < func_signature_end + 10:
                    if ':' in lines[body_line_idx]:
                        body_line_idx += 1
                        break
                    body_line_idx += 1
                
                # Chercher si cette fonction utilise db.
                uses_db = False
                method_body = ''.join(lines[method_start_idx:min(method_start_idx + 200, len(lines))])
                
                # Trouver la prochaine fonction/classe pour limiter le scope
                next_def_match = re.search(r'\n\s*(def |class |@)', method_body[100:])
                if next_def_match:
                    method_body = method_body[:100 + next_def_match.start()]
                
                # Vérifier si db. est utilisé (mais pas db =)
                if re.search(r'\bdb\.', method_body) and not re.search(r'\bdb\s*=\s*get_db\(\)', method_body[:500]):
                    uses_db = True
                
                # Si la fonction utilise db, ajouter db = get_db() après la docstring
                if uses_db:
                    # Ajouter toutes les lignes jusqu'au début du corps
                    for k in range(i, body_line_idx):
                        if k < len(lines):
                            new_lines.append(lines[k])
                    
                    # Chercher la fin de la docstring si elle existe
                    insert_idx = body_line_idx
                    docstring_started = False
                    while insert_idx < len(lines) and insert_idx < body_line_idx + 10:
                        stripped = lines[insert_idx].strip()
                        if stripped.startswith('"""') or stripped.startswith("'''"):
                            docstring_started = True
                            # Trouver la fin du docstring
                            quote_char = '"""' if stripped.startswith('"""') else "'''"
                            insert_idx += 1
                            while insert_idx < len(lines):
                                if quote_char in lines[insert_idx]:
                                    insert_idx += 1
                                    break
                                insert_idx += 1
                            break
                        elif stripped == '':
                            insert_idx += 1
                        else:
                            break
                    
                    # Vérifier si db = get_db() existe déjà
                    has_db_init = False
                    check_idx = insert_idx
                    while check_idx < len(lines) and check_idx < insert_idx + 5:
                        if 'db = get_db()' in lines[check_idx] or 'db = get_database()' in lines[check_idx]:
                            has_db_init = True
                            break
                        check_idx += 1
                    
                    # Ajouter db = get_db() si nécessaire
                    if not has_db_init:
                        # Obtenir l'indentation de la fonction
                        func_indent = indent_level + 4
                        indent_str = ' ' * func_indent
                        new_lines.append(f"{indent_str}db = get_db()\n")
                        fixed_count += 1
                        print(f"✅ Ajouté db = get_db() dans: {lines[method_start_idx].strip()}")
                    
                    i = body_line_idx
                    continue
            
            # Ajouter la ligne normale
            new_lines.append(line)
            i += 1
        
        # Écrire le fichier corrigé
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"\n✅ Fichier model.py corrigé avec succès!")
        print(f"📊 {fixed_count} méthodes corrigées")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Correction automatique de toutes les utilisations de db dans model.py...")
    print("⚠️  Cette opération peut prendre quelques instants...\n")
    fix_all_db_usage()








