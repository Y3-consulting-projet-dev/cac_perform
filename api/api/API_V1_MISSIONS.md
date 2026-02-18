# 🚀 API Moderne - Création de Mission `/api/v1/missions/`

## ✅ **Nouvelle API Moderne Créée !**

Une API moderne style RESTful a été créée pour les missions, similaire à celle des clients.

---

## 🔗 **Endpoints Disponibles**

### **1. Créer une Nouvelle Mission**
```
POST /api/v1/missions/
```

### **2. Récupérer une Mission**
```
GET /api/v1/missions/<mission_id>
```

### **3. Supprimer une Mission**
```
DELETE /api/v1/missions/<mission_id>
```

### **4. Lister les Missions d'un Client**
```
GET /api/v1/missions/client/<client_id>
```

---

## 📝 **API de Création de Mission**

### **Endpoint**
```
POST http://localhost:5000/api/v1/missions/
```

### **Content-Type**
```
multipart/form-data
```

### **Paramètres**

| Paramètre | Type | Requis | Description | Exemple |
|-----------|------|--------|-------------|---------|
| `files[]` | File | ✅ Oui | Fichiers Excel de balance (minimum 2) | Balance_2024.xlsx |
| `annee_auditee` | Text | ✅ Oui | Année auditée | `"2024"` |
| `id_client` | Text | ✅ Oui | ID du client (ObjectId MongoDB) | `"65a1b2c3d4e5f6789abcdef0"` |
| `date_debut` | Text | ✅ Oui | Date de début de la mission (YYYY-MM-DD) | `"2024-01-01"` |
| `date_fin` | Text | ✅ Oui | Date de fin de la mission (YYYY-MM-DD) | `"2024-12-31"` |
| `date_debut_mandat` | Text | ✅ Oui | Date de début du mandat (YYYY-MM-DD) | `"2024-01-01"` |
| `date_fin_mandat` | Text | ✅ Oui | Date de fin du mandat (YYYY-MM-DD) | `"2024-12-31"` |
| `date_debut_mandat` | Text | ✅ Oui | Date de début du mandat (YYYY-MM-DD) | `"2024-01-01"` |
| `date_fin_mandat` | Text | ✅ Oui | Date de fin du mandat (YYYY-MM-DD) | `"2024-12-31"` |

**Note** : Le paramètre `id_client` peut aussi être `id` (compatibilité avec l'ancienne API).

---

## 🧪 **Exemple pour Insomnia**

### **Configuration**

1. **Method** : `POST`
2. **URL** : `http://localhost:5000/api/v1/missions/`
3. **Body Type** : `Multipart Form`

### **Champs à Ajouter**

| Key | Type | Value |
|-----|------|-------|
| `files[]` | File | Sélectionner `Balance_2024.xlsx` |
| `files[]` | File | Sélectionner `Balance_2023.xlsx` |
| `annee_auditee` | Text | `2024` |
| `id_client` | Text | `65a1b2c3d4e5f6789abcdef0` (ID client valide) |
| `date_debut` | Text | `2024-01-01` |
| `date_fin` | Text | `2024-12-31` |
| `date_debut_mandat` | Text | `2024-01-01` |
| `date_fin_mandat` | Text | `2024-12-31` |
| `date_debut_mandat` | Text | `2024-01-01` |
| `date_fin_mandat` | Text | `2024-12-31` |

---

## ✅ **Réponse Attendue (Succès)**

**Code HTTP** : `201 Created`

```json
{
  "success": true,
  "message": "Mission créée avec succès",
  "data": {
    "_id": "65a1b2c3d4e5f6789abcdef1",
    "mission": {
      "id_client": "65a1b2c3d4e5f6789abcdef0",
      "annee_auditee": "2024",
      "date_debut": "2024-01-01",
      "date_fin": "2024-12-31",
      "date_debut_mandat": "2024-01-01",
      "date_fin_mandat": "2024-12-31",
      "balances": [...],
      "balance_variation": {...},
      "grouping": {...},
      "efi": {...},
      "materiality": []
    }
  }
}
```

---

## ❌ **Réponses d'Erreur**

### **400 Bad Request - Fichiers manquants**
```json
{
  "success": false,
  "error": "Au moins 2 fichiers de balance sont requis (N et N-1)"
}
```

### **400 Bad Request - Validation**
```json
{
  "success": false,
  "error": "Erreurs de validation",
  "errors": {
    "date_debut": ["La date de début est requise"],
    "annee_auditee": ["L'année auditée est requise"]
  }
}
```

### **400 Bad Request - Client introuvable**
```json
{
  "success": false,
  "error": "Client avec l'ID 'xxx' introuvable"
}
```

### **500 Internal Server Error**
```json
{
  "success": false,
  "error": "Erreur serveur: [détails]"
}
```

---

## 🧪 **Test avec cURL**

```bash
curl -X POST http://localhost:5000/api/v1/missions/ \
  -F "files[]=@/chemin/vers/Balance_2024.xlsx" \
  -F "files[]=@/chemin/vers/Balance_2023.xlsx" \
  -F "annee_auditee=2024" \
  -F "id_client=65a1b2c3d4e5f6789abcdef0" \
  -F "date_debut=2024-01-01" \
  -F "date_fin=2024-12-31" \
  -F "date_debut_mandat=2024-01-01" \
  -F "date_fin_mandat=2024-12-31" \
  -F "date_debut_mandat=2024-01-01" \
  -F "date_fin_mandat=2024-12-31"
```

---

## 📋 **Autres Endpoints**

### **GET /api/v1/missions/<mission_id>**

Récupère une mission spécifique.

**Exemple** :
```bash
GET http://localhost:5000/api/v1/missions/65a1b2c3d4e5f6789abcdef1
```

**Réponse** :
```json
{
  "success": true,
  "data": {
    "_id": "65a1b2c3d4e5f6789abcdef1",
    "id_client": "65a1b2c3d4e5f6789abcdef0",
    "annee_auditee": "2024",
    ...
  }
}
```

---

### **GET /api/v1/missions/client/<client_id>**

Liste toutes les missions d'un client.

**Exemple** :
```bash
GET http://localhost:5000/api/v1/missions/client/65a1b2c3d4e5f6789abcdef0
```

**Réponse** :
```json
{
  "success": true,
  "data": [
    {
      "_id": "65a1b2c3d4e5f6789abcdef1",
      "id_client": "65a1b2c3d4e5f6789abcdef0",
      "annee_auditee": "2024",
      ...
    }
  ],
  "total": 1
}
```

---

### **DELETE /api/v1/missions/<mission_id>**

Supprime une mission.

**Exemple** :
```bash
DELETE http://localhost:5000/api/v1/missions/65a1b2c3d4e5f6789abcdef1
```

**Réponse** :
```json
{
  "success": true,
  "message": "Mission supprimée avec succès"
}
```

---

## 📍 **Architecture**

L'API moderne suit la même architecture que les clients :

```
src/
├── schemas/
│   └── mission_schemas.py      # Validation des données
├── services/
│   └── mission_services.py     # Logique métier
├── resources/
│   └── mission_resources.py    # Endpoints API
└── routes/
    └── __init__.py             # Enregistrement des routes
```

---

## ✅ **Avantages de l'API Moderne**

1. ✅ **Style RESTful** : URLs claires et cohérentes
2. ✅ **Validation** : Schémas Marshmallow pour valider les données
3. ✅ **Séparation des responsabilités** : Schemas, Services, Resources
4. ✅ **Réponses standardisées** : Format JSON cohérent
5. ✅ **Codes HTTP appropriés** : 201 Created, 400 Bad Request, etc.
6. ✅ **Documentation** : Code structuré et documenté

---

## 🔄 **Compatibilité**

L'ancienne API reste disponible :
- **Ancienne** : `POST /cors/mission/nouvelle_mission`
- **Moderne** : `POST /api/v1/missions/`

Les deux fonctionnent en parallèle !

---

## 📝 **Fichiers Créés**

1. ✅ `src/schemas/mission_schemas.py` - Schémas de validation
2. ✅ `src/services/mission_services.py` - Logique métier
3. ✅ `src/resources/mission_resources.py` - Endpoints API
4. ✅ Routes enregistrées dans `src/routes/__init__.py`

---

## 🚀 **Prochaines Étapes**

1. **Redémarrer le serveur Flask**
2. **Tester l'API** avec Insomnia ou cURL
3. **Vérifier les logs** pour voir les routes enregistrées

Vous devriez voir dans les logs :
```
✅ Routes enregistrées:
   📋 Missions modernes: /api/v1/missions/
```





