# 📘 Guide d'installation Backend

Ce dossier contient le code source du backend de l’outil CAC-Perform. Il constitue l’API qui gère la logique métier, les accès aux données, ainsi que la communication avec le frontend.

## ⚙️ Étapes d’installation

### 1. 🧪 Création d'un ennvironnement virtuel Python

Afin d’isoler les dépendances du projet et éviter les conflits avec d’autres environnements python présents sur votre machine, il est recommandé de créer un environnement virtuel dédié.

Depuis le dossier ``api``, exécutez :

```sh
python -m venv virtualenv
```

#### **➤ Activation de l’environnement virtuel**

* **Sous Windows :**

```sh
.\virtualenv\Scripts\activate
```

* **Sous Linux / macOS :**

```sh
source virtualenv/bin/activate
```

#### **➤ Désactivation**

Lorsque vous avez terminé, vous pouvez quitter l’environnement virtuel avec :

```sh
deactivate
```

> ⚠️ **Important :** Le nom de l’environnement virtuel doit être exactement ``virtualenv`` afin d’être automatiquement exclu par Git via le ``.gitignore``.

### 2. 📦 Installation des dépendances Python

Une fois l’environnement virtuel activé, installez les bibliothèques nécessaires au projet avec :

```sh
pip install -r requirements.txt
```

Cette commande installera toutes les dépendances listées, assurant ainsi le bon fonctionnement du backend.

### 3. 🗄️ Démarrage de MongoDB (OBLIGATOIRE)

**⚠️ IMPORTANT :** MongoDB doit être démarré avant de lancer l'application.

#### **Option 1 : Démarrer MongoDB en tant que service (Recommandé)**

Ouvrez PowerShell **en tant qu'administrateur** et exécutez :

```powershell
net start MongoDB
```

#### **Option 2 : Démarrer MongoDB manuellement**

Si le service ne fonctionne pas, démarrez MongoDB manuellement :

```powershell
# 1. Trouver l'installation MongoDB
Get-ChildItem "C:\Program Files\MongoDB" -Recurse -Filter "mongod.exe" | Select-Object -First 1

# 2. Créer le dossier de données (si nécessaire)
New-Item -ItemType Directory -Force -Path "C:\data\db"

# 3. Démarrer MongoDB (remplacez le chemin par celui trouvé à l'étape 1)
& "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" --dbpath "C:\data\db"
```

#### **Option 3 : Utiliser le script Python (Recommandé - Simple et fiable)**

```powershell
python demarrer_mongodb.py
```

Ce script démarre MongoDB en arrière-plan et vérifie que tout fonctionne correctement.

#### **Vérifier que MongoDB est démarré**

```powershell
# Vérifier le port 27017
netstat -an | findstr ":27017"
```

### 4. 🚀 Lancement du serveur (mode développement)

Une fois MongoDB démarré, lancez le serveur backend :

```sh
# Depuis le dossier api
# Activez l'environnement virtuel, installez les deps puis lancez
python app.py
```

Le serveur sera accessible à l'adresse suivante : <http://localhost:5000>.

> **Note :** MongoDB doit être en cours d'exécution sur ``localhost:27017``.

## 🤝 Besoin d’aide ?

Pour toute question ou problème lié au backend, vous pouvez contacter :

**Axel Hamilton AHOUMOUAN - <axelhamilton02@gmail.com>**
