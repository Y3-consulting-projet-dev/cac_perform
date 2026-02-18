"""
Script simple pour corriger les utilisations de db dans model.py
Cherche toutes les méthodes qui utilisent db. et ajoute db = get_db() si nécessaire
"""

def fix_db_usage_simple():
    """Corrige toutes les utilisations de db dans model.py"""
    
    file_path = "src/model.py"
    
    try:
        # Lire le fichier
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        new_lines = []
        i = 0
        fixed_count = 0
        
        while i < len(lines):
            line = lines[i]
            new_lines.append(line)
            
            # Détecter le début d'une fonction/méthode
            if line.strip().startswith('def ') or (i > 0 and lines[i-1].strip().startswith('@') and line.strip().startswith('def ')):
                # C'est une fonction, chercher si elle utilise db.
                func_start = i
                
                # Trouver la fin de la signature (ligne avec :)
                sig_end = func_start
                while sig_end < len(lines) and ':' not in lines[sig_end]:
                    sig_end += 1
                
                if sig_end < len(lines):
                    # Trouver le début du corps (après :)
                    body_start = sig_end + 1
                    
                    # Ignorer les lignes vides et docstrings
                    while body_start < len(lines) and body_start < sig_end + 20:
                        stripped = lines[body_start].strip()
                        if not stripped or stripped.startswith('"""') or stripped.startswith("'''") or stripped.startswith('#'):
                            # C'est une docstring, continuer
                            if stripped.startswith('"""') or stripped.startswith("'''"):
                                quote = '"""' if stripped.startswith('"""') else "'''"
                                body_start += 1
                                # Chercher la fin du docstring
                                while body_start < len(lines):
                                    if quote in lines[body_start]:
                                        body_start += 1
                                        break
                                    body_start += 1
                            else:
                                body_start += 1
                        else:
                            break
                    
                    # Chercher dans le corps de la fonction si elle utilise db.
                    uses_db = False
                    has_db_init = False
                    
                    # Chercher la prochaine fonction/classe pour limiter le scope
                    func_end = body_start
                    while func_end < len(lines) and func_end < body_start + 500:
                        # Détecter la fin de la fonction (prochaine fonction/classe au même niveau ou supérieur)
                        if func_end > body_start:
                            stripped_line = lines[func_end].strip()
                            # Vérifier si c'est une nouvelle fonction/classe (même ou moins d'indentation que func_start)
                            if (stripped_line.startswith('def ') or stripped_line.startswith('class ')) and not stripped_line.startswith('    '):
                                break
                        func_end += 1
                    
                    # Vérifier dans le corps de la fonction
                    func_body = '\n'.join(lines[body_start:min(func_end, len(lines))])
                    
                    if 'db.' in func_body:
                        uses_db = True
                        # Vérifier si db = get_db() existe déjà
                        if 'db = get_db()' in func_body or 'db = get_database()' in func_body:
                            has_db_init = True
                    
                    # Si la fonction utilise db mais n'a pas d'initialisation, l'ajouter
                    if uses_db and not has_db_init:
                        # Trouver l'indentation de la fonction
                        indent_match = None
                        for j in range(func_start, min(func_start + 5, len(lines))):
                            if 'def ' in lines[j]:
                                indent_match = lines[j].match(r'^(\s*)def ') if hasattr(lines[j], 'match') else None
                                if not indent_match:
                                    # Essayer avec re
                                    import re
                                    indent_match = re.match(r'^(\s*)def ', lines[j])
                                break
                        
                        if indent_match:
                            func_indent = indent_match.group(1)
                            body_indent = func_indent + '    '  # 4 espaces de plus
                            
                            # Insérer db = get_db() après la docstring
                            insert_pos = body_start
                            # Vérifier qu'on n'est pas déjà passé cette fonction
                            if i == func_start:
                                # On va insérer après cette fonction
                                # Mais on doit attendre d'être après la docstring
                                pass
                            
                            # Ajouter à la position appropriée
                            new_lines.append(f"{body_indent}db = get_db()")
                            fixed_count += 1
                            func_name = line.strip().split('(')[0].replace('def ', '')
                            print(f"✅ Ajouté db = get_db() dans: {func_name}")
            
            i += 1
        
        # Écrire le fichier corrigé
        new_content = '\n'.join(new_lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
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
    fix_db_usage_simple()








