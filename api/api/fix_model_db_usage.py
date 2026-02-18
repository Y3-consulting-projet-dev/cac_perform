"""
Script pour corriger toutes les utilisations de db dans model.py
Ajoute db = get_db() au début de chaque méthode qui utilise db
"""

import re

def fix_model_db_usage():
    """Corrige les utilisations de db dans model.py"""
    
    file_path = "src/model.py"
    
    try:
        # Lire le fichier
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            new_lines.append(line)
            
            # Détecter le début d'une méthode ou fonction
            # Pattern pour les méthodes de classe ou méthodes d'instance
            method_pattern = r'^\s*(def|@classmethod|@staticmethod)'
            if re.match(method_pattern, line):
                # Trouver la ligne suivante avec "def"
                if line.strip().startswith('def') or (i + 1 < len(lines) and 'def' in lines[i + 1]):
                    # Avancer jusqu'à la ligne avec "def"
                    if not line.strip().startswith('def'):
                        i += 1
                        if i < len(lines):
                            new_lines.append(lines[i])
                    
                    # Trouver la première ligne du corps de la fonction (après :)
                    start_body = i + 1
                    found_colon = False
                    while start_body < len(lines) and start_body < i + 10:
                        if ':' in lines[start_body]:
                            found_colon = True
                            break
                        start_body += 1
                    
                    # Chercher si cette fonction utilise db
                    uses_db = False
                    function_body = '\n'.join(lines[i:min(i+100, len(lines))])
                    
                    # Chercher db. dans le corps de la fonction (avant la prochaine fonction/classe)
                    next_func_match = re.search(r'\n\s*(def|class)\s', function_body)
                    if next_func_match:
                        function_body = function_body[:next_func_match.start()]
                    
                    if 'db.' in function_body:
                        uses_db = True
                    
                    # Si la fonction utilise db, ajouter db = get_db() après la ligne avec :
                    if uses_db and found_colon:
                        # Trouver l'indentation de la fonction
                        def_line_idx = i
                        while def_line_idx >= 0 and not lines[def_line_idx].strip().startswith('def'):
                            def_line_idx -= 1
                        
                        if def_line_idx >= 0:
                            indent_match = re.match(r'^(\s*)', lines[def_line_idx])
                            if indent_match:
                                indent = indent_match.group(1)
                                
                                # Trouver où insérer db = get_db()
                                insert_idx = start_body + 1
                                # Ignorer les docstrings
                                while insert_idx < len(lines) and insert_idx < start_body + 5:
                                    if lines[insert_idx].strip().startswith('"""') or lines[insert_idx].strip().startswith("'''"):
                                        # Trouver la fin du docstring
                                        doc_start = insert_idx
                                        insert_idx += 1
                                        while insert_idx < len(lines):
                                            if '"""' in lines[insert_idx] or "'''" in lines[insert_idx]:
                                                insert_idx += 1
                                                break
                                            insert_idx += 1
                                    elif lines[insert_idx].strip() == '':
                                        insert_idx += 1
                                    else:
                                        break
                                
                                # Insérer db = get_db() si ce n'est pas déjà là
                                need_insert = True
                                check_idx = insert_idx
                                while check_idx < min(insert_idx + 5, len(lines)):
                                    if 'db = get_db()' in lines[check_idx] or 'db = get_database()' in lines[check_idx]:
                                        need_insert = False
                                        break
                                    check_idx += 1
                                
                                if need_insert and insert_idx < len(lines):
                                    # Insérer la ligne
                                    new_lines.append(f"{indent}    db = get_db()")
            
            i += 1
        
        # Écrire le fichier corrigé
        new_content = '\n'.join(new_lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Fichier model.py corrigé avec succès!")
        print("⚠️  Vérifiez manuellement que toutes les méthodes ont bien db = get_db() au début")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Correction automatique des utilisations de db dans model.py...")
    print("⚠️  Cette opération peut prendre quelques instants...")
    fix_model_db_usage()








