#!/usr/bin/env python3
"""
Script simple pour tester un seul fichier ODS
"""

import os
from odf import table
from odf.opendocument import load

def test_single_ods():
    try:
        print("🧪 Test d'un fichier ODS...")
        
        # REMPLACEZ CE CHEMIN PAR CELUI DE VOTRE FICHIER ODS
        file_path = "C:/Users/Mariam Latifa DALLA/Documents/balance_2024.ods"
        
        if not os.path.exists(file_path):
            print(f"❌ Fichier non trouvé: {file_path}")
            print("⚠️  Modifiez le script avec le vrai chemin de votre fichier ODS")
            return False
        
        print(f"🔍 Test du fichier: {file_path}")
        
        # Test de lecture ODS
        doc = load(file_path)
        tables = doc.getElementsByType(table.Table)
        print(f"📊 Tableaux trouvés: {len(tables)}")
        
        if not tables:
            print("❌ Aucun tableau trouvé dans le fichier ODS")
            return False
        
        sheet = tables[0]
        rows = sheet.getElementsByType(table.TableRow)
        print(f"📋 Lignes trouvées: {len(rows)}")
        
        if not rows:
            print("❌ Aucune ligne trouvée dans le tableau")
            return False
        
        # Analyser la première ligne (en-tête)
        first_row = rows[0]
        cells = first_row.getElementsByType(table.TableCell)
        print(f"🔍 Cellules dans la première ligne: {len(cells)}")
        
        if cells:
            print("📝 Contenu de la première ligne (en-têtes):")
            for i, cell in enumerate(cells):
                cell_text = ""
                for child in cell.childNodes:
                    if hasattr(child, 'data'):
                        cell_text += child.data
                    elif hasattr(child, 'text'):
                        cell_text += child.text
                print(f"  - Colonne {i}: '{cell_text.strip()}'")
        
        # Analyser quelques lignes de données
        if len(rows) > 1:
            print(f"\n📊 Analyse des lignes de données:")
            for i in range(1, min(4, len(rows))):  # Premières 3 lignes de données
                row = rows[i]
                cells = row.getElementsByType(table.TableCell)
                if cells:
                    row_data = []
                    for cell in cells:
                        cell_text = ""
                        for child in cell.childNodes:
                            if hasattr(child, 'data'):
                                cell_text += child.data
                            elif hasattr(child, 'text'):
                                cell_text += child.text
                        row_data.append(cell_text.strip())
                    print(f"  - Ligne {i}: {row_data}")
                    
                    # Vérifier si c'est une ligne de données valide
                    if row_data[0] and row_data[1]:  # Numéro de compte et libellé
                        print(f"    ✅ Ligne de données valide détectée")
                    else:
                        print(f"    ⚠️ Ligne potentiellement vide ou en-tête")
        else:
            print("❌ Aucune ligne de données trouvée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la lecture ODS: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Test d'un fichier ODS...")
    print("⚠️  IMPORTANT: Modifiez le script avec le vrai chemin de votre fichier ODS")
    test_single_ods()


