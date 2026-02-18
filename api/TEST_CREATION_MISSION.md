# 🧪 Guide de Test - Création d'une Nouvelle Mission

## 📋 **Informations de l'API**

### **Endpoint**
```
POST http://localhost:5000/cors/mission/nouvelle_mission
```

### **Content-Type**
```
multipart/form-data
```

---

## 📝 **Paramètres Requis**

### **1. Fichiers (files[])**
- **Type** : Fichiers Excel (.xlsx)
- **Nombre minimum** : 2 fichiers
  - **Balance N** : Balance de l'année auditée (ex: 2024)
  - **Balance N-1** : Balance de l'année précédente (ex: 2023)
- **Format attendu** : Excel avec 6 colonnes
  ```
  Numéro de compte | Libellé | Débit initial | Crédit initial | Débit final | Crédit final
  ```

### **2. Paramètres Form**

| Paramètre | Type | Requis | Description | Exemple |
|-----------|------|--------|-------------|---------|
| `files[]` | File[] | ✅ Oui | Fichiers Excel de balance (min 2) | `Balance_2024.xlsx`, `Balance_2023.xlsx` |
| `annee_auditee` | String | ✅ Oui | Année auditée | `"2024"` |
| `id` | String | ✅ Oui | ID du client (ObjectId MongoDB) | `"65a1b2c3d4e5f6789abcdef0"` |
| `date_debut` | String | ✅ Oui | Date de début de mission (format: YYYY-MM-DD) | `"2024-01-01"` |
| `date_fin` | String | ✅ Oui | Date de fin de mission (format: YYYY-MM-DD) | `"2024-12-31"` |

---

## 🧪 **Exemples de Test**

### **Exemple 1 : Création Standard**

**Données Form :**
```
files[]: Balance_2024.xlsx (fichier)
files[]: Balance_2023.xlsx (fichier)
annee_auditee: "2024"
id: "65a1b2c3d4e5f6789abcdef0"
date_debut: "2024-01-01"
date_fin: "2024-12-31"
```

**Format Excel attendu (6 colonnes) :**
| Numéro | Libellé | Débit Initial | Crédit Initial | Débit Final | Crédit Final |
|--------|---------|---------------|----------------|-------------|--------------|
| 101 | Capital social | 0 | 1000000 | 0 | 1000000 |
| 411 | Clients | 500000 | 0 | 750000 | 0 |
| 512 | Banque | 200000 | 0 | 350000 | 0 |

---

### **Exemple 2 : Mission avec 3 Balances**

**Données Form :**
```
files[]: Balance_2024.xlsx (fichier)
files[]: Balance_2023.xlsx (fichier)
files[]: Balance_2022.xlsx (fichier)
annee_auditee: "2024"
id: "65a1b2c3d4e5f6789abcdef0"
date_debut: "2024-01-01"
date_fin: "2024-12-31"
```

---

## 🧪 **Tests avec cURL**

### **Test 1 : Création avec 2 fichiers**

```bash
curl -X POST http://localhost:5000/cors/mission/nouvelle_mission \
  -F "files[]=@/chemin/vers/Balance_2024.xlsx" \
  -F "files[]=@/chemin/vers/Balance_2023.xlsx" \
  -F "annee_auditee=2024" \
  -F "id=65a1b2c3d4e5f6789abcdef0" \
  -F "date_debut=2024-01-01" \
  -F "date_fin=2024-12-31"
```

**⚠️ Important :** Remplacez :
- `/chemin/vers/Balance_2024.xlsx` par le chemin réel de vos fichiers
- `65a1b2c3d4e5f6789abcdef0` par un ID de client valide

---

## 🧪 **Tests avec Insomnia / Postman**

### **Configuration :**
1. **Method** : `POST`
2. **URL** : `http://localhost:5000/cors/mission/nouvelle_mission`
3. **Body Type** : `multipart/form-data`

### **Champs à ajouter :**

| Key | Type | Value |
|-----|------|-------|
| `files[]` | File | Sélectionner `Balance_2024.xlsx` |
| `files[]` | File | Sélectionner `Balance_2023.xlsx` |
| `annee_auditee` | Text | `2024` |
| `id` | Text | `65a1b2c3d4e5f6789abcdef0` (ID client) |
| `date_debut` | Text | `2024-01-01` |
| `date_fin` | Text | `2024-12-31` |

**Note :** Dans Insomnia/Postman, ajoutez plusieurs champs `files[]` pour chaque fichier.

---

## ✅ **Réponse Attendue (Succès)**

### **Code HTTP** : `200 OK`

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
      "balances": [
        "65a1b2c3d4e5f6789abcdef2",
        "65a1b2c3d4e5f6789abcdef3"
      ],
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

### **400 Bad Request - Fichiers invalides**
```json
{
  "error": "Seulement 1 fichier(s) valide(s) reçu(s), 2 requis"
}
```

### **500 Internal Server Error**
```json
{
  "error": "Erreur lors de la création de la mission"
}
```
ou
```json
{
  "error": "Erreur serveur: [détails de l'erreur]"
}
```

---

## 📋 **Comment Obtenir l'ID du Client**

### **Option 1 : Via l'API de liste des clients**
```
GET http://localhost:5000/api/v1/clients/
```

La réponse contiendra les clients avec leurs `_id` :
```json
{
  "response": [
    {
      "_id": "65a1b2c3d4e5f6789abcdef0",
      "nom": "Entreprise ABC SARL",
      ...
    }
  ]
}
```

### **Option 2 : Via l'interface web**
- Créer ou ouvrir un client
- L'ID se trouve dans l'URL : `/client/{id}`
- Ou dans la console du navigateur lors de la création

---

## ⚠️ **Exigences Importantes**

### **Format des Fichiers Excel**

1. **Extension** : `.xlsx` uniquement (Excel 2007+)
2. **Structure** : 6 colonnes minimum
   - Colonne 1 : Numéro de compte (obligatoire, non vide)
   - Colonne 2 : Libellé du compte
   - Colonne 3 : Débit initial
   - Colonne 4 : Crédit initial
   - Colonne 5 : Débit final
   - Colonne 6 : Crédit final

3. **Ordre des fichiers** :
   - Premier fichier : Balance de l'année N (année auditée)
   - Deuxième fichier : Balance de l'année N-1
   - Fichiers suivants (optionnels) : Balance N-2, etc.

### **Dates**
- Format : `YYYY-MM-DD` (ISO 8601)
- `date_debut` doit être antérieure à `date_fin`
- Les dates doivent être dans l'année auditée ou proche

---

## 🔍 **Vérifier la Création**

### **1. Vérifier dans les logs du serveur Flask**

Lors de la création, vous devriez voir :
```
Fichiers reçus: ['Balance_2024.xlsx', 'Balance_2023.xlsx']
Données reçues: annee=2024, client=65a1b2c3d4e5f6789abcdef0, debut=2024-01-01, fin=2024-12-31
📂 Fichier chargé: Balance_2024.xlsx
📊 Format détecté: balance_simple
✅ Balance créée avec succès: XXX lignes
✅ Mission créée avec ID: 65a1b2c3d4e5f6789abcdef1
```

### **2. Vérifier via l'API**

**Lister les missions d'un client :**
```
GET http://localhost:5000/cors/client/info_client/{client_id}
```

### **3. Vérifier via l'interface web**

- Aller sur l'espace client
- Vérifier que la mission apparaît dans la liste
- Le nombre de lignes devrait être affiché (pas 0 !)

---

## 📝 **Notes Importantes**

1. ⚠️ **Au moins 2 fichiers** sont obligatoires (Balance N et N-1)
2. ⚠️ Les fichiers doivent être au format **Excel (.xlsx)**
3. ⚠️ L'**ID du client** doit être un ObjectId MongoDB valide
4. ⚠️ Les **dates** doivent être au format `YYYY-MM-DD`
5. ✅ Vous pouvez uploader **plus de 2 fichiers** si nécessaire
6. ✅ L'API accepte plusieurs fichiers via `files[]` (tableau)

---

## 🚀 **Ordre Recommandé de Test**

1. **Créer un client** (si vous n'en avez pas)
   ```
   POST /api/v1/clients/
   ```

2. **Noter l'ID du client** créé

3. **Préparer les fichiers Excel**
   - Balance N (ex: Balance_2024.xlsx)
   - Balance N-1 (ex: Balance_2023.xlsx)

4. **Créer la mission**
   ```
   POST /cors/mission/nouvelle_mission
   ```

5. **Vérifier la création** dans les logs et via l'API








