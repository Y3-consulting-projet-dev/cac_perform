# 👤 API de Gestion des Utilisateurs - CAC Perform

## 📋 Vue d'ensemble

Cette API fournit un système complet de gestion des utilisateurs avec authentification JWT, validation des données, et architecture en couches.

## 🏗️ Architecture

```
src/
├── schemas/
│   └── user_schemas.py      # Validation et sérialisation des données
├── services/
│   └── user_services.py     # Logique métier
├── resources/
│   └── user_resources.py    # Contrôleurs REST
└── routes/
    └── __init__.py          # Routes centralisées
```

## 🔐 Authentification

L'API utilise **JWT (JSON Web Tokens)** pour l'authentification :

- **Durée de vie** : 8 heures
- **Algorithme** : HS256
- **Format d'en-tête** : `Authorization: Bearer <token>`

## 👥 Modèle Utilisateur

### Champs requis pour l'inscription :
- `firstname` : Prénom (2-50 caractères)
- `lastname` : Nom (2-50 caractères)
- `email` : Email valide (unique)
- `password` : Mot de passe sécurisé (min 8 caractères, majuscule, minuscule, chiffre)
- `role` : Rôle dans l'organisation
- `grade` : Grade professionnel
- `departement` : Département d'affectation

### Rôles disponibles :
- `Administrateur`
- `Manager`
- `Auditeur Senior`
- `Auditeur`
- `Stagiaire`

### Grades disponibles :
- `Junior`
- `Confirmé`
- `Senior`
- `Expert`
- `Directeur`

### Départements disponibles :
- `Audit`
- `Conseil`
- `Expertise Comptable`
- `Juridique`
- `Administration`

## 🛣️ Endpoints API

### 📝 Authentification

#### `POST /api/v1/users/register`
Inscription d'un nouvel utilisateur.

**Corps de la requête :**
```json
{
  "firstname": "Jean",
  "lastname": "Dupont",
  "email": "jean.dupont@example.com",
  "password": "MotDePasse123!",
  "role": "Auditeur",
  "grade": "Senior",
  "departement": "Audit"
}
```

**Réponse (201) :**
```json
{
  "user_id": "USR_20241127_A1B2C3D4",
  "firstname": "Jean",
  "lastname": "Dupont",
  "email": "jean.dupont@example.com",
  "role": "Auditeur",
  "grade": "Senior",
  "departement": "Audit",
  "is_active": true,
  "created_at": "2024-11-27T10:30:00Z"
}
```

#### `POST /api/v1/users/login`
Connexion d'un utilisateur.

**Corps de la requête :**
```json
{
  "email": "jean.dupont@example.com",
  "password": "MotDePasse123!"
}
```

**Réponse (200) :**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "user_id": "USR_20241127_A1B2C3D4",
    "firstname": "Jean",
    "lastname": "Dupont",
    "email": "jean.dupont@example.com",
    "role": "Auditeur"
  },
  "expires_in": 28800
}
```

#### `POST /api/v1/users/logout`
Déconnexion (nécessite authentification).

**En-têtes :** `Authorization: Bearer <token>`

**Réponse (200) :**
```json
{
  "message": "Déconnexion réussie"
}
```

### 👤 Gestion du profil

#### `GET /api/v1/users/profile`
Récupère le profil de l'utilisateur connecté.

**En-têtes :** `Authorization: Bearer <token>`

#### `PUT /api/v1/users/profile`
Met à jour le profil de l'utilisateur connecté.

**En-têtes :** `Authorization: Bearer <token>`

**Corps de la requête :**
```json
{
  "grade": "Expert",
  "departement": "Conseil"
}
```

#### `GET /api/v1/users/<user_id>/profile`
Récupère le profil d'un utilisateur spécifique (admin ou propriétaire).

#### `PUT /api/v1/users/<user_id>/profile`
Met à jour le profil d'un utilisateur spécifique (admin ou propriétaire).

### 🔑 Gestion des mots de passe

#### `PUT /api/v1/users/password`
Change le mot de passe de l'utilisateur connecté.

**En-têtes :** `Authorization: Bearer <token>`

**Corps de la requête :**
```json
{
  "current_password": "AncienMotDePasse123!",
  "new_password": "NouveauMotDePasse456!"
}
```

#### `PUT /api/v1/users/<user_id>/password`
Change le mot de passe d'un utilisateur spécifique (admin ou propriétaire).

### 👑 Administration (Administrateur uniquement)

#### `GET /api/v1/users/`
Liste tous les utilisateurs avec pagination.

**Paramètres de requête :**
- `page` : Numéro de page (défaut: 1)
- `per_page` : Éléments par page (défaut: 20, max: 100)

**Réponse (200) :**
```json
{
  "users": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "pages": 3
  }
}
```

#### `PATCH /api/v1/users/<user_id>/manage`
Active ou désactive un utilisateur.

**Corps de la requête :**
```json
{
  "action": "activate"  // ou "deactivate"
}
```

#### `GET /api/v1/users/stats`
Récupère les statistiques des utilisateurs.

**Réponse (200) :**
```json
{
  "total_users": 25,
  "active_users": 23,
  "inactive_users": 2,
  "by_role": [
    {"_id": "Auditeur", "count": 10},
    {"_id": "Manager", "count": 5}
  ],
  "by_department": [
    {"_id": "Audit", "count": 15},
    {"_id": "Conseil", "count": 8}
  ],
  "recent_logins": [...]
}
```

### 📊 Métadonnées

#### `GET /api/v1/users/metadata`
Récupère les rôles, grades et départements disponibles.

**Réponse (200) :**
```json
{
  "roles": ["Administrateur", "Manager", "Auditeur Senior", "Auditeur", "Stagiaire"],
  "grades": ["Junior", "Confirmé", "Senior", "Expert", "Directeur"],
  "departements": ["Audit", "Conseil", "Expertise Comptable", "Juridique", "Administration"]
}
```

## 🔄 Compatibilité

### Route de compatibilité avec l'ancien système :

#### `POST /cors/manager/connexion/`
Connexion compatible avec l'ancien format.

**Corps de la requête :**
```json
{
  "mail": "jean.dupont@example.com",
  "pwd": "MotDePasse123!"
}
```

## 🛡️ Sécurité

### Validation des mots de passe :
- Minimum 8 caractères
- Au moins une majuscule
- Au moins une minuscule  
- Au moins un chiffre

### Protection contre les attaques :
- **Limitation des tentatives** : Compte verrouillé après 5 échecs (30 minutes)
- **Hachage sécurisé** : bcrypt avec salt
- **Validation stricte** : Marshmallow schemas
- **JWT sécurisé** : Expiration automatique

### Permissions :
- **Utilisateur** : Peut voir/modifier son propre profil
- **Administrateur** : Accès complet à tous les utilisateurs

## 🧪 Tests

### Script de test complet :
```bash
python test_user_architecture.py
```

### Migration des utilisateurs existants :
```bash
python migrate_existing_users.py
```

## 📝 Codes d'erreur

| Code | Description |
|------|-------------|
| 200  | Succès |
| 201  | Créé avec succès |
| 400  | Données invalides |
| 401  | Non authentifié |
| 403  | Accès refusé |
| 404  | Ressource non trouvée |
| 500  | Erreur serveur |

## 🔧 Configuration

### Variables d'environnement :
```bash
JWT_SECRET=your-secret-key-change-in-production
MONGO_URI=mongodb://localhost:27017
DB_NAME=cac_perform
```

### Démarrage du serveur :
```bash
python app.py
```

Le serveur démarre sur `http://localhost:5000` avec toutes les routes utilisateur disponibles.

## 📚 Exemples d'utilisation

### JavaScript/Fetch :
```javascript
// Inscription
const registerUser = async (userData) => {
  const response = await fetch('/api/v1/users/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData)
  });
  return response.json();
};

// Connexion
const loginUser = async (email, password) => {
  const response = await fetch('/api/v1/users/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await response.json();
  localStorage.setItem('token', data.token);
  return data;
};

// Requête authentifiée
const getProfile = async () => {
  const token = localStorage.getItem('token');
  const response = await fetch('/api/v1/users/profile', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
};
```

### Python/Requests :
```python
import requests

# Inscription
user_data = {
    "firstname": "Jean",
    "lastname": "Dupont", 
    "email": "jean.dupont@example.com",
    "password": "MotDePasse123!",
    "role": "Auditeur",
    "grade": "Senior",
    "departement": "Audit"
}
response = requests.post('http://localhost:5000/api/v1/users/register', json=user_data)

# Connexion
login_data = {"email": "jean.dupont@example.com", "password": "MotDePasse123!"}
response = requests.post('http://localhost:5000/api/v1/users/login', json=login_data)
token = response.json()['token']

# Requête authentifiée
headers = {"Authorization": f"Bearer {token}"}
response = requests.get('http://localhost:5000/api/v1/users/profile', headers=headers)
```

