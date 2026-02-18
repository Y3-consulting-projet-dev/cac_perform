# 📋 API de Création de Mission - Documentation

## ✅ **L'API existe déjà !**

L'API de création de mission est disponible via le blueprint legacy.

---

## 🔗 **Endpoint Principal**

### **Création d'une Nouvelle Mission**
```
POST http://localhost:5000/cors/mission/nouvelle_mission
```

**Content-Type** : `multipart/form-data`

---

## 📝 **Paramètres Requis**

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `files[]` | File[] | Fichiers Excel de balance (minimum 2) | Balance_2024.xlsx, Balance_2023.xlsx |
| `annee_auditee` | String | Année auditée | `"2024"` |
| `id` | String | ID du client (ObjectId MongoDB) | `"65a1b2c3d4e5f6789abcdef0"` |
| `date_debut` | String | Date de début (YYYY-MM-DD) | `"2024-01-01"` |
| `date_fin` | String | Date de fin (YYYY-MM-DD) | `"2024-12-31"` |

---

## 📡 **Routes Mission Disponibles**

Toutes ces routes sont accessibles via le préfixe `/cors/mission/` :

### **1. Création de Mission**
- **Endpoint** : `POST /cors/mission/nouvelle_mission`
- **Description** : Crée une nouvelle mission avec des fichiers de balance

### **2. Revue Analytique**
- **Endpoint** : `GET /cors/mission/revue_analytique/<id_mission>`
- **Description** : Récupère la revue analytique d'une mission

### **3. Mise à Jour Commentaire**
- **Endpoint** : `PUT /cors/mission/revue_analytique/<id_mission>/commentaire`
- **Description** : Met à jour le commentaire d'une mission

### **4. Sauvegarder Réponses Qualitatives**
- **Endpoint** : `PUT /cors/mission/save_qualitative_responses/<id_mission>`
- **Description** : Sauvegarde les réponses qualitatives

### **5. Suppression de Mission**
- **Endpoint** : `DELETE /cors/mission/supprimer_mission/<id_mission>`
- **Description** : Supprime une mission

---

## 🧪 **Exemple de Test**

### **Avec cURL**
```bash
curl -X POST http://localhost:5000/cors/mission/nouvelle_mission \
  -F "files[]=@/chemin/vers/Balance_2024.xlsx" \
  -F "files[]=@/chemin/vers/Balance_2023.xlsx" \
  -F "annee_auditee=2024" \
  -F "id=65a1b2c3d4e5f6789abcdef0" \
  -F "date_debut=2024-01-01" \
  -F "date_fin=2024-12-31"
```

### **Avec Insomnia/Postman**
1. **Method** : `POST`
2. **URL** : `http://localhost:5000/cors/mission/nouvelle_mission`
3. **Body Type** : `multipart/form-data`
4. **Champs** :
   - `files[]` (File) : Sélectionner Balance_2024.xlsx
   - `files[]` (File) : Sélectionner Balance_2023.xlsx
   - `annee_auditee` (Text) : `2024`
   - `id` (Text) : ID du client
   - `date_debut` (Text) : `2024-01-01`
   - `date_fin` (Text) : `2024-12-31`

---

## ✅ **Réponse Attendue (Succès)**

**Code HTTP** : `200 OK`

```json
{
  "success": true,
  "data": {
    "_id": "65a1b2c3d4e5f6789abcdef1",
    "mission": {
      "id_client": "65a1b2c3d4e5f6789abcdef0",
      "annee_auditee": "2024",
      "date_debut": "2024-01-01",
      "date_fin": "2024-12-31",
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
  "error": "Au moins 2 fichiers de balance sont requis (N et N-1)"
}
```

### **400 Bad Request - Champs manquants**
```json
{
  "error": "Tous les champs sont requis"
}
```

### **500 Internal Server Error**
```json
{
  "error": "Erreur serveur: [détails de l'erreur]"
}
```

---

## 📍 **Où se trouve l'API ?**

L'API est définie dans :
- **Fichier** : `src/mission/routes.py`
- **Blueprint** : `mission` (préfixe `/cors/mission`)
- **Enregistrée dans** : `src/routes/__init__.py` (système centralisé)

---

## 🔍 **Vérifier que l'API est bien enregistrée**

1. **Redémarrer le serveur Flask**
2. **Vérifier les logs** - Vous devriez voir :
   ```
   ✅ Routes enregistrées:
      📋 Missions: /cors/mission/
   ```
3. **Tester l'endpoint** : `GET http://localhost:5000/health` devrait fonctionner

---

## 💡 **Note**

Actuellement, l'API utilise le système legacy (`/cors/mission/`). Si vous souhaitez créer une API moderne style `/api/v1/missions/` comme pour les clients, cela nécessiterait de créer :
- `src/resources/mission_resources.py`
- `src/services/mission_services.py`
- `src/schemas/mission_schemas.py`

Mais l'API actuelle fonctionne parfaitement via `/cors/mission/nouvelle_mission` !





