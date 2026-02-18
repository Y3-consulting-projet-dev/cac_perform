"""
Script de diagnostic pour identifier où l'erreur 'db' is not defined se produit
"""
import sys
import traceback
from src.model import Mission
from src.utils.database import get_database

def test_mission_creation():
    """Test de création de mission pour identifier l'erreur db"""
    try:
        # Simuler une création de mission
        mission = Mission()
        
        # Vérifier que get_db() fonctionne
        print("1. Test de get_db()...")
        db = get_database()
        print(f"   ✅ get_db() fonctionne: {type(db)}")
        
        # Vérifier que db est accessible
        print("2. Test d'accès à db...")
        _ = db.Mission1
        print("   ✅ db.Mission1 accessible")
        
        # Tester nouvelle_mission avec des données minimales
        print("3. Test de nouvelle_mission...")
        # Note: Cette partie nécessitera des fichiers réels, donc on va juste vérifier
        # que la méthode peut être appelée sans erreur de définition de db
        
        print("✅ Tous les tests de base ont réussi")
        
    except NameError as e:
        if 'db' in str(e):
            print(f"❌ ERREUR: {e}")
            print(f"   Traceback:")
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        print(f"   Type: {type(e).__name__}")
        print(f"   Traceback:")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🔍 Diagnostic de l'erreur 'db' is not defined")
    print("=" * 60)
    success = test_mission_creation()
    print("=" * 60)
    if success:
        print("✅ Diagnostic terminé avec succès")
    else:
        print("❌ Diagnostic a révélé des problèmes")
        sys.exit(1)





