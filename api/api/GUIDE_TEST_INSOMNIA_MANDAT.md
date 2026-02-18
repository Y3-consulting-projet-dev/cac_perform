# 🧪 Guide de Test Insomnia - Création de Mission avec Mandat

## 📋 **Configuration Complète pour Insomnia**

### **1. Créer une Nouvelle Requête**

1. Ouvrez Insomnia
2. Cliquez sur **"New Request"** ou **"+"**
3. Nommez-la : `Créer Mission avec Mandat`

---

## 🔧 **Configuration de la Requête**

### **Méthode**
```
POST
```

### **URL**
```
http://localhost:5000/api/v1/missions/
```

⚠️ **IMPORTANT** :
- Pas de `/` à la fin (ou avec `/` selon votre configuration)
- Pas d'espace avant/après
- Utilisez `http://` (pas `https://`)
- Port `5000` (vérifiez que c'est le bon port)

---

## 📝 **Body Type**

Sélectionnez : **`Multipart Form`**

⚠️ **Ne pas utiliser** :
- ❌ JSON
- ❌ Form URL Encoded
- ❌ Text
- ❌ File

---

## 📋 **Champs à Ajouter (8 champs au total)**

Cliquez sur **"Add"** pour chaque champ dans l'ordre suivant :

### **Champ 1 : Premier fichier Excel (Balance N)**
- **Key** : `files[]` ⚠️ **Exactement avec les crochets**
- **Type** : `File` (dans le menu déroulant)
- **Value** : Cliquez sur **"Choose File"** et sélectionnez `Balance_2024.xlsx`

### **Champ 2 : Deuxième fichier Excel (Balance N-1)**
- **Key** : `files[]` ⚠️ **Même nom que le premier !**
- **Type** : `File`
- **Value** : Cliquez sur **"Choose File"** et sélectionnez `Balance_2023.xlsx`

### **Champ 3 : Année auditée**
- **Key** : `annee_auditee`
- **Type** : `Text`
- **Value** : `2024`

### **Champ 4 : ID Client**
- **Key** : `id_client`
- **Type** : `Text`
- **Value** : `65a1b2c3d4e5f6789abcdef0` ⚠️ **Remplacez par un ID client valide de votre base de données**

### **Champ 5 : Date de début de la mission**
- **Key** : `date_debut`
- **Type** : `Text`
- **Value** : `2024-01-01` (format YYYY-MM-DD)

### **Champ 6 : Date de fin de la mission**
- **Key** : `date_fin`
- **Type** : `Text`
- **Value** : `2024-12-31` (format YYYY-MM-DD)

### **Champ 7 : Date de début du mandat** ⭐ **NOUVEAU**
- **Key** : `date_debut_mandat`
- **Type** : `Text`
- **Value** : `2024-01-01` (format YYYY-MM-DD)

### **Champ 8 : Date de fin du mandat** ⭐ **NOUVEAU**
- **Key** : `date_fin_mandat`
- **Type** : `Text`
- **Value** : `2024-12-31` (format YYYY-MM-DD)

---

## 📊 **Résumé des Champs**

| # | Key | Type | Value Exemple | Requis |
|---|-----|------|---------------|--------|
| 1 | `files[]` | File | Balance_2024.xlsx | ✅ |
| 2 | `files[]` | File | Balance_2023.xlsx | ✅ |
| 3 | `annee_auditee` | Text | `2024` | ✅ |
| 4 | `id_client` | Text | `65a1b2c3d4e5f6789abcdef0` | ✅ |
| 5 | `date_debut` | Text | `2024-01-01` | ✅ |
| 6 | `date_fin` | Text | `2024-12-31` | ✅ |
| 7 | `date_debut_mandat` | Text | `2024-01-01` | ✅ |
| 8 | `date_fin_mandat` | Text | `2024-12-31` | ✅ |

---

## ⚠️ **Points Critiques**

### **1. Nom du champ pour les fichiers**
Le nom du champ doit être **EXACTEMENT** `files[]` avec :
- Les crochets `[]` 
- Pas d'espace
- Pas de guillemets

❌ **Faux** :
- `files`
- `files[] ` (avec espace)
- `"files[]"`
- `file[]`

✅ **Correct** :
- `files[]`

### **2. Format des dates**
Toutes les dates doivent être au format **YYYY-MM-DD** :
- ✅ `2024-01-01`
- ✅ `2024-12-31`
- ❌ `01/01/2024`
- ❌ `2024-1-1`
- ❌ `01-01-2024`

### **3. Headers**
⚠️ **Ne pas ajouter de headers manuellement !**

Insomnia ajoute automatiquement :
```
Content-Type: multipart/form-data; boundary=...
```

Si vous ajoutez manuellement `Content-Type`, cela peut causer des erreurs.

---

## ✅ **Réponse Attendue (Succès)**

**Status Code** : `201 Created`

**Body** :
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
      "balances": [
        "65a1b2c3d4e5f6789abcdef2",
        "65a1b2c3d4e5f6789abcdef3"
      ],
      "balance_variation": {},
      "grouping": {},
      "efi": {},
      "materiality": []
    }
  }
}
```

---

## ❌ **Réponses d'Erreur Possibles**

### **400 Bad Request - Dates du mandat manquantes**
```json
{
  "success": false,
  "error": "La date de début du mandat est requise",
  "debug": {
    "champs_reçus": [...],
    "date_debut_mandat_reçu": null,
    "aide": "Vérifiez que le champ 'date_debut_mandat' est bien présent dans le formulaire multipart"
  }
}
```

### **400 Bad Request - Format de date invalide**
```json
{
  "success": false,
  "error": "Erreurs de validation",
  "errors": {
    "date_debut_mandat": ["La date doit être au format YYYY-MM-DD (ex: 2024-01-01)"]
  }
}
```

### **400 Bad Request - Date de début du mandat >= Date de fin**
```json
{
  "success": false,
  "error": "Erreurs de validation",
  "errors": {
    "date_debut_mandat": ["La date de début du mandat doit être antérieure à la date de fin du mandat"]
  }
}
```

---

## 🧪 **Exemple Complet avec cURL**

Si vous préférez tester avec cURL :

```bash
curl -X POST http://localhost:5000/api/v1/missions/ \
  -F "files[]=@/chemin/vers/Balance_2024.xlsx" \
  -F "files[]=@/chemin/vers/Balance_2023.xlsx" \
  -F "annee_auditee=2024" \
  -F "id_client=65a1b2c3d4e5f6789abcdef0" \
  -F "date_debut=2024-01-01" \
  -F "date_fin=2024-12-31" \
  -F "date_debut_mandat=2024-01-01" \
  -F "date_fin_mandat=2024-12-31"
```

---

## 📝 **Checklist avant d'envoyer**

Avant de cliquer sur **"Send"**, vérifiez :

- [ ] Méthode : `POST`
- [ ] URL : `http://localhost:5000/api/v1/missions/`
- [ ] Body Type : `Multipart Form`
- [ ] 2 fichiers Excel ajoutés avec la clé `files[]`
- [ ] `annee_auditee` : valeur textuelle (ex: `2024`)
- [ ] `id_client` : ID client valide de votre base de données
- [ ] `date_debut` : format YYYY-MM-DD
- [ ] `date_fin` : format YYYY-MM-DD
- [ ] `date_debut_mandat` : format YYYY-MM-DD ⭐
- [ ] `date_fin_mandat` : format YYYY-MM-DD ⭐
- [ ] Date de début < Date de fin (pour mission et mandat)
- [ ] Aucun header `Content-Type` ajouté manuellement

---

## 🚀 **Étapes pour Tester**

1. **Démarrer le serveur Flask**
   ```bash
   cd api
   python app.py
   # ou
   flask run
   ```

2. **Ouvrir Insomnia** et créer la requête selon ce guide

3. **Remplacer l'ID client** par un ID valide de votre base de données

4. **Sélectionner les fichiers Excel** de balance

5. **Remplir tous les champs** y compris les dates du mandat

6. **Cliquer sur "Send"**

7. **Vérifier la réponse** :
   - ✅ Succès : Status 201 avec les données de la mission
   - ❌ Erreur : Vérifier le message d'erreur et corriger

---

## 💡 **Conseils**

- **ID Client** : Pour obtenir un ID client valide, vous pouvez :
  - Lister les clients via l'API : `GET /api/v1/clients/`
  - Ou utiliser un ID que vous connaissez déjà

- **Fichiers Excel** : Assurez-vous que les fichiers sont bien des fichiers Excel (.xlsx)

- **Dates** : Les dates du mandat peuvent être différentes des dates de la mission

- **Logs** : Vérifiez les logs du serveur Flask pour voir les détails de la requête

---

## ✅ **Test Réussi !**

Si vous recevez un status `201 Created` avec les données de la mission incluant `date_debut_mandat` et `date_fin_mandat`, c'est que tout fonctionne correctement ! 🎉

