# 📋 API de Création de Mission - Endpoint Exact

## ✅ **API Existante (Legacy)**

L'API de création de mission est actuellement disponible via le système legacy :

### **Endpoint**
```
POST http://localhost:5000/cors/mission/nouvelle_mission
```

**Blueprint** : `/cors/mission`  
**Route** : `/nouvelle_mission`  
**Méthode** : `POST`

---

## 📝 **Configuration Complète pour Insomnia**

### **1. Method**
```
POST
```

### **2. URL Complète**
```
http://localhost:5000/cors/mission/nouvelle_mission
```

### **3. Body Type**
```
Multipart Form
```

### **4. Champs à Ajouter**

| Key | Type | Value | Description |
|-----|------|-------|-------------|
| `files[]` | File | Balance_2024.xlsx | Premier fichier (Balance N) |
| `files[]` | File | Balance_2023.xlsx | Deuxième fichier (Balance N-1) |
| `annee_auditee` | Text | `2024` | Année auditée |
| `id` | Text | `65a1b2c3d4e5f6789abcdef0` | ID du client (ObjectId MongoDB) |
| `date_debut` | Text | `2024-01-01` | Date de début (YYYY-MM-DD) |
| `date_fin` | Text | `2024-12-31` | Date de fin (YYYY-MM-DD) |

---

## 🔍 **Comment le Frontend l'utilise**

Le frontend (`clients/src/utils/uploadFile.js`) utilise :
```javascript
baseURL: 'http://localhost:5000/cors'
// ...
axios.post(`/mission/nouvelle_mission`, formData, config)
```

Ce qui donne : `http://localhost:5000/cors/mission/nouvelle_mission`

---

## 📍 **Où est Définie cette API ?**

- **Fichier de routes** : `src/mission/routes.py`
- **Ligne** : 169-205
- **Blueprint** : `src/mission/__init__.py` (préfixe `/cors/mission`)
- **Enregistrée dans** : `src/routes/__init__.py` (ligne 239)

---

## 🧪 **Test avec cURL**

```bash
curl -X POST http://localhost:5000/cors/mission/nouvelle_mission \
  -F "files[]=@/chemin/vers/Balance_2024.xlsx" \
  -F "files[]=@/chemin/vers/Balance_2023.xlsx" \
  -F "annee_auditee=2024" \
  -F "id=65a1b2c3d4e5f6789abcdef0" \
  -F "date_debut=2024-01-01" \
  -F "date_fin=2024-12-31"
```

---

## ✅ **Réponse Attendue (Succès)**

**Status** : `200 OK`

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
  "error": "Erreur serveur: [détails]"
}
```

---

## ⚠️ **Important**

1. **URL exacte** : `http://localhost:5000/cors/mission/nouvelle_mission`
   - Pas de `/` à la fin
   - Avec le préfixe `/cors/mission`

2. **Au moins 2 fichiers** : Balance N et Balance N-1

3. **Format des fichiers** : `.xlsx` uniquement

4. **ID client valide** : Doit être un ObjectId MongoDB existant

---

## 🔄 **Note : API Moderne N'existe Pas Encore**

Actuellement, il n'y a **pas d'API moderne** style `/api/v1/missions/` comme pour les clients.

Pour créer une API moderne, il faudrait :
1. Créer `src/resources/mission_resources.py`
2. Créer `src/services/mission_services.py`
3. Créer `src/schemas/mission_schemas.py`
4. Enregistrer les routes dans `src/routes/__init__.py`

Mais l'API actuelle fonctionne via `/cors/mission/nouvelle_mission` !





