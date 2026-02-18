# 🗄️ Configuration Centralisée de la Base de Données

## 📋 Vue d'ensemble

La configuration de la base de données a été centralisée pour suivre les bonnes pratiques Flask et améliorer la maintenabilité du projet.

## 🏗️ Architecture

### Avant (Problématique)
- Connexions MongoDB dispersées dans plusieurs fichiers
- Configuration hardcodée (`localhost:27017`)
- Difficile à maintenir et à déployer
- Pas de gestion centralisée des erreurs

### Après (Solution)
- Configuration centralisée dans `config.py`
- Gestionnaire de base de données unifié
- Support des variables d'environnement
- Gestion d'erreurs robuste

## 📁 Structure des fichiers

```
api/
├── config.py                    # Configuration centralisée
├── .env.template                # Template des variables d'environnement
├── .env                         # Variables d'environnement (à créer)
├── src/
│   ├── utils/
│   │   ├── __init__.py
│   │   └── database.py          # Utilitaires d'accès à la DB
│   └── __init__.py              # Initialisation Flask mise à jour
└── migrate_database_connections.py  # Script de migration
```

## 🔧 Configuration

### 1. Variables d'environnement

Créez un fichier `.env` basé sur `.env.template` :

```bash
# Configuration Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Configuration MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB_NAME=cac_perform
# MONGO_USERNAME=your-username      # Optionnel
# MONGO_PASSWORD=your-password      # Optionnel
# MONGO_AUTH_SOURCE=admin           # Optionnel

# Configuration CORS
CORS_ORIGINS=http://localhost:5173
```

### 2. Classes de configuration

#### DevelopmentConfig (par défaut)
- MongoDB local sans authentification
- Debug activé
- Logs détaillés

#### ProductionConfig
- Variables d'environnement obligatoires
- Sécurité renforcée
- Authentification MongoDB

#### TestingConfig
- Base de données de test séparée
- Configuration isolée

## 🚀 Utilisation

### Dans votre code Python

```python
# Ancienne méthode (à éviter)
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['cac_perform']

# Nouvelle méthode (recommandée)
from src.utils.database import get_database
db = get_database()
```

### Fonctions utilitaires disponibles

```python
from src.utils.database import (
    get_database,           # Base de données complète
    get_mongo_collection,   # Collection spécifique
    check_connection,       # Vérifier la connexion
    ensure_connection,      # Reconnecter si nécessaire
    get_database_stats      # Statistiques de la DB
)

# Collections spécifiques
from src.utils.database import (
    get_client_collection,
    get_mission_collection,
    get_balance_collection
)
```

## 🔄 Migration

### Script automatique

```bash
python migrate_database_connections.py
```

Ce script :
- ✅ Trouve tous les fichiers avec des connexions directes
- ✅ Crée des sauvegardes automatiques
- ✅ Remplace les connexions par la nouvelle architecture
- ✅ Génère le template `.env`

### Migration manuelle

Si vous préférez migrer manuellement :

1. **Remplacer les imports** :
   ```python
   # Ancien
   from pymongo import MongoClient
   client = MongoClient('mongodb://localhost:27017/')
   db = client['cac_perform']
   
   # Nouveau
   from src.utils.database import get_database
   db = get_database()
   ```

2. **Supprimer la configuration hardcodée** :
   ```python
   # Ancien
   MONGO_HOST = "localhost"
   MONGO_PORT = 27017
   DB_NAME = "cac_perform"
   
   # Nouveau
   # Configuration dans config.py et .env
   ```

## 🛠️ Gestionnaire de base de données

### Fonctionnalités

- **Connexion automatique** au démarrage de l'application
- **Reconnexion automatique** en cas de perte de connexion
- **Initialisation des collections** si la base est vide
- **Gestion d'erreurs** robuste
- **Statistiques** et monitoring

### Méthodes principales

```python
from config import db_manager

# Vérifier la connexion
if db_manager.is_connected():
    print("✅ Base de données connectée")

# Obtenir des statistiques
stats = db_manager.get_stats()
print(f"Collections: {stats['collections']}")

# Reconnecter si nécessaire
db_manager.connect()
```

## 🔍 Débogage

### Vérifier la configuration

```python
from config import db_manager
from src.utils.database import get_database_stats

# Statistiques de la base
stats = get_database_stats()
print(stats)

# Tester la connexion
from src.utils.database import check_connection
if check_connection():
    print("✅ Connexion OK")
else:
    print("❌ Problème de connexion")
```

### Logs

Les logs sont automatiquement générés :

```
✅ Connexion MongoDB établie: localhost:27017/cac_perform
📚 Collections existantes: ['Client', 'Mission1', 'Balance']
🔧 Configuration de développement chargée
```

## 🚨 Gestion d'erreurs

### Erreurs courantes

1. **Base de données non connectée**
   ```
   RuntimeError: Base de données non connectée. Appelez connect() d'abord.
   ```
   **Solution** : Vérifiez que l'application Flask est bien initialisée

2. **Variables d'environnement manquantes (production)**
   ```
   ValueError: Variables d'environnement manquantes: SECRET_KEY, MONGO_HOST
   ```
   **Solution** : Créez le fichier `.env` avec toutes les variables requises

3. **Connexion MongoDB échouée**
   ```
   ConnectionFailure: [Errno 111] Connection refused
   ```
   **Solution** : Vérifiez que MongoDB est démarré

### Récupération automatique

Le système tente automatiquement de :
- Reconnecter en cas de perte de connexion
- Initialiser les collections manquantes
- Logger les erreurs pour faciliter le débogage

## 🎯 Avantages

### ✅ Maintenabilité
- Configuration centralisée
- Code plus propre et organisé
- Facilite les modifications

### ✅ Déploiement
- Support des variables d'environnement
- Configuration par environnement
- Sécurité améliorée

### ✅ Robustesse
- Gestion d'erreurs centralisée
- Reconnexion automatique
- Initialisation automatique

### ✅ Développement
- Configuration de développement simplifiée
- Logs détaillés
- Outils de débogage intégrés

## 📝 Checklist de migration

- [ ] Exécuter le script de migration
- [ ] Créer le fichier `.env`
- [ ] Tester l'application
- [ ] Vérifier les logs
- [ ] Supprimer les fichiers `.backup` après validation
- [ ] Mettre à jour la documentation d'équipe

## 🔗 Fichiers concernés

### Modifiés automatiquement
- `src/model.py`
- `src/services/client_services.py`
- `src/__init__.py`
- Tous les scripts de diagnostic

### Nouveaux fichiers
- `config.py` (restructuré)
- `src/utils/database.py`
- `src/utils/__init__.py`
- `.env.template`

Cette nouvelle architecture respecte les bonnes pratiques Flask et facilite grandement la maintenance et le déploiement de l'application ! 🚀
