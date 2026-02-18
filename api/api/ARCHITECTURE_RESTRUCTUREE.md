# 🏗️ Architecture Restructurée - CAC Perform API

## 📋 Vue d'ensemble

Le projet a été restructuré selon une architecture en couches pour améliorer la maintenabilité, la testabilité et la séparation des responsabilités.

## 🗂️ Structure des dossiers

```
src/
├── schemas/           # Validation et sérialisation des données
│   ├── __init__.py
│   └── client_schemas.py
├── services/          # Logique métier
│   ├── __init__.py
│   └── client_services.py
├── resources/         # Contrôleurs API (gestion des requêtes HTTP)
│   ├── __init__.py
│   └── client_resources.py
└── customer/          # Routes Flask (point d'entrée)
    ├── __init__.py
    ├── routes.py      # Ancienne version (à migrer)
    └── routes_new.py  # Nouvelle version restructurée
```

## 🔄 Séparation des responsabilités

### 1. **Schemas** (`src/schemas/`)
- **Rôle** : Validation des données d'entrée et sérialisation des réponses
- **Technologie** : Marshmallow
- **Responsabilités** :
  - Validation des données reçues via l'API
  - Sérialisation des données pour les réponses
  - Définition des structures de données
  - Messages d'erreur personnalisés

**Exemple** :
```python
from src.schemas.client_schemas import validate_client_data, ClientCreateSchema

# Validation automatique
validated_data = validate_client_data(request_data, ClientCreateSchema)
```

### 2. **Services** (`src/services/`)
- **Rôle** : Logique métier et interactions avec la base de données
- **Responsabilités** :
  - Opérations CRUD sur les clients
  - Règles métier (vérification d'unicité, etc.)
  - Gestion des erreurs métier
  - Interaction avec MongoDB

**Exemple** :
```python
from src.services.client_services import ClientService

# Logique métier encapsulée
result = ClientService.create_client(validated_data)
```

### 3. **Resources** (`src/resources/`)
- **Rôle** : Contrôleurs API (gestion des requêtes/réponses HTTP)
- **Responsabilités** :
  - Gestion des requêtes HTTP
  - Orchestration entre schemas et services
  - Formatage des réponses
  - Gestion des codes de statut HTTP

**Exemple** :
```python
from src.resources.client_resources import ClientResource

# Contrôleur qui orchestre tout
def create_client_route():
    return ClientResource.create_client()
```

### 4. **Routes** (`src/customer/`)
- **Rôle** : Points d'entrée Flask (mapping URL → contrôleur)
- **Responsabilités** :
  - Définition des routes Flask
  - Mapping des URLs vers les contrôleurs
  - Configuration des méthodes HTTP

## 🚀 Avantages de cette architecture

### ✅ **Maintenabilité**
- Code organisé et facile à comprendre
- Responsabilités clairement séparées
- Facilite les modifications et évolutions

### ✅ **Testabilité**
- Chaque couche peut être testée indépendamment
- Mocking facilité entre les couches
- Tests unitaires plus simples

### ✅ **Réutilisabilité**
- Services réutilisables dans différents contextes
- Schemas partagés entre plusieurs endpoints
- Logique métier centralisée

### ✅ **Validation robuste**
- Validation automatique avec Marshmallow
- Messages d'erreur cohérents
- Sérialisation standardisée

### ✅ **Évolutivité**
- Facile d'ajouter de nouvelles fonctionnalités
- Architecture scalable
- Séparation claire des préoccupations

## 🔧 Migration depuis l'ancienne architecture

### Avant (routes.py + model.py)
```python
# routes.py
@client.post('/nouveau_client/')
def new_cust():
    data = request.get_json()
    clit = Client()
    new_customer = clit.ajouter_client(data=data)
    # ...

# model.py
class Client(Document):
    @classmethod
    def ajouter_client(cls, data):
        # Logique métier mélangée avec accès données
```

### Après (architecture en couches)
```python
# routes_new.py
@client.post('/nouveau_client/')
def create_client_route():
    return ClientResource.create_client()

# client_resources.py
class ClientResource:
    @staticmethod
    def create_client():
        data = request.get_json()
        validated_data = validate_client_data(data, ClientCreateSchema)
        result = ClientService.create_client(validated_data)
        # ...

# client_services.py
class ClientService:
    @staticmethod
    def create_client(client_data):
        # Logique métier pure
        # ...

# client_schemas.py
class ClientCreateSchema(Schema):
    nom = fields.Str(required=True, validate=validate.Length(min=2))
    # ...
```

## 📝 Utilisation

### 1. **Installation des dépendances**
```bash
pip install marshmallow==3.20.1
```

### 2. **Migration progressive**
- Les anciennes routes restent fonctionnelles
- Nouvelles routes disponibles en `/v2/`
- Migration endpoint par endpoint possible

### 3. **Endpoints disponibles**

#### Anciens endpoints (compatibilité)
- `GET /cors/client/afficher_clients/`
- `GET /cors/client/info_client/<id>`
- `POST /cors/client/nouveau_client/`
- `PUT /cors/client/modifier_client/`
- `DELETE /cors/client/supprimer_client/<id>`

#### Nouveaux endpoints (v2)
- `GET /cors/client/v2/clients/`
- `GET /cors/client/v2/clients/<id>`
- `POST /cors/client/v2/clients/`
- `PUT /cors/client/v2/clients/`
- `DELETE /cors/client/v2/clients/<id>`
- `GET /cors/client/referentiels/`

## 🎯 Prochaines étapes

1. **Tester la nouvelle architecture**
2. **Migrer progressivement les autres modules** (missions, collaborateurs, etc.)
3. **Ajouter des tests unitaires**
4. **Documenter l'API avec Swagger/OpenAPI**
5. **Optimiser les performances**

## 🔍 Exemple complet

### Création d'un client avec validation
```python
# Données d'entrée
client_data = {
    "nom": "Entreprise ABC",
    "activite": "Commerce de détail",
    "referentiel": "syscohada",
    "forme_juridique": "SARL",
    "capital": 1000000.0,
    "siege_social": "123 Rue de la Paix, Abidjan",
    "adresse": "123 Rue de la Paix, Abidjan, Côte d'Ivoire"
}

# 1. Validation automatique (schemas)
validated_data = validate_client_data(client_data, ClientCreateSchema)

# 2. Logique métier (services)
result = ClientService.create_client(validated_data)

# 3. Réponse HTTP (resources)
return make_response(jsonify({"response": result["client_id"]}), 200)
```

Cette architecture moderne et robuste facilite grandement le développement et la maintenance de l'API CAC Perform ! 🚀






