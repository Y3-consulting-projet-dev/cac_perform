# 🚀 API Création de Mission - Guide Insomnia

## 📋 **Informations de l'API**

### **Endpoint**
```
POST http://localhost:5000/api/v1/missions/
```

### **Méthode**
`POST`

### **Content-Type**
`multipart/form-data` (⚠️ **IMPORTANT** : Ne pas utiliser JSON)

---

## 🔧 **Configuration dans Insomnia**

### ⚠️ **ATTENTION : NE PAS UTILISER JSON !**

❌ **NE FAITES PAS ÇA** :
```json
{
  "files[]": ["Balance_2024.xlsx", "Balance_2023.xlsx"],
  "annee_auditee": "2024",
  ...
}
```

✅ **UTILISEZ Multipart Form** (voir ci-dessous)

---

### **1. Créer une nouvelle requête**

- **Nom** : `Créer Mission`
- **Méthode** : `POST`
- **URL** : `http://localhost:5000/api/v1/missions/`

### **2. Configurer le Body**

1. Cliquez sur l'onglet **Body**
2. ⚠️ **IMPORTANT** : Sélectionnez **Multipart Form** 
   - ❌ **PAS** JSON
   - ❌ **PAS** Form URL Encoded
   - ✅ **OUI** Multipart Form

### **3. Ajouter les champs**

Ajoutez **exactement** ces 6 champs dans l'ordre suivant :

---

## 📝 **Champs à Ajouter**

### **Champ 1 : Premier fichier Excel (Balance N)**
- **Key** : `files[]` ⚠️ **Exactement avec les crochets**
- **Type** : `File` (dans le menu déroulant)
- **Value** : Cliquez sur "Choose File" et sélectionnez votre fichier Excel (ex: `Balance_2024.xlsx`)

### **Champ 2 : Deuxième fichier Excel (Balance N-1)**
- **Key** : `files[]` ⚠️ **Même nom que le premier !**
- **Type** : `File`
- **Value** : Cliquez sur "Choose File" et sélectionnez votre deuxième fichier Excel (ex: `Balance_2023.xlsx`)

### **Champ 3 : Année auditée**
- **Key** : `annee_auditee`
- **Type** : `Text`
- **Value** : `2024`

### **Champ 4 : ID Client**
- **Key** : `id_client`
- **Type** : `Text`
- **Value** : `65a1b2c3d4e5f6789abcdef0` ⚠️ **Remplacez par un ID client valide de votre base de données**

### **Champ 5 : Date de début**
- **Key** : `date_debut`
- **Type** : `Text`
- **Value** : `2024-01-01` (format YYYY-MM-DD)

### **Champ 6 : Date de fin**
- **Key** : `date_fin`
- **Type** : `Text`
- **Value** : `2024-12-31` (format YYYY-MM-DD)

---

## 📊 **Exemple Visuel dans Insomnia**

```
┌─────────────────────────────────────────────────────────────────┐
│ POST http://localhost:5000/api/v1/missions/                    │
├─────────────────────────────────────────────────────────────────┤
│ Body: Multipart Form                                             │
│                                                                  │
│ ┌──────────────────┬────────┬────────────────────────────────┐ │
│ │ Key              │ Type   │ Value                          │ │
│ ├──────────────────┼────────┼────────────────────────────────┤ │
│ │ files[]          │ File   │ C:\...\Balance_2024.xlsx       │ │
│ │ files[]          │ File   │ C:\...\Balance_2023.xlsx       │ │
│ │ annee_auditee    │ Text   │ 2024                           │ │
│ │ id_client        │ Text   │ 65a1b2c3d4e5f6789abcdef0       │ │
│ │ date_debut       │ Text   │ 2024-01-01                     │ │
│ │ date_fin         │ Text   │ 2024-12-31                     │ │
│ └──────────────────┴────────┴────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ **Exemples de Valeurs**

### **Exemple 1 : Mission 2024**
```
files[] (1)     : Balance_2024.xlsx
files[] (2)     : Balance_2023.xlsx
annee_auditee   : 2024
id_client       : 65a1b2c3d4e5f6789abcdef0
date_debut      : 2024-01-01
date_fin        : 2024-12-31
```

### **Exemple 2 : Mission 2023**
```
files[] (1)     : Balance_2023.xlsx
files[] (2)     : Balance_2022.xlsx
annee_auditee   : 2023
id_client       : 65a1b2c3d4e5f6789abcdef0
date_debut      : 2023-01-01
date_fin        : 2023-12-31
```

### **Exemple 3 : Mission avec dates personnalisées**
```
files[] (1)     : Balance_2024.xlsx
files[] (2)     : Balance_2023.xlsx
annee_auditee   : 2024
id_client       : 65a1b2c3d4e5f6789abcdef0
date_debut      : 2024-06-01
date_fin        : 2024-12-31
```

---

## 🔍 **Comment Obtenir un ID Client Valide**

### **Option 1 : Via l'API**
Faites une requête GET pour lister les clients :
```
GET http://localhost:5000/api/v1/clients/
```

La réponse contiendra des objets avec `_id`. Copiez un `_id` et utilisez-le.

### **Option 2 : Via la base de données**
Si vous avez accès à MongoDB, exécutez :
```javascript
db.Client.find().limit(1)
```
Copiez l'`_id` du client.

---

## 📤 **Réponse Attendue (Succès)**

### **Statut HTTP : 201 Created**

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

### **Erreur 1 : Fichiers manquants**
```json
{
  "success": false,
  "error": "Au moins 2 fichiers de balance sont requis (N et N-1)"
}
```
**Solution** : Vérifiez que vous avez bien 2 champs `files[]` avec des fichiers sélectionnés.

### **Erreur 2 : Client introuvable**
```json
{
  "success": false,
  "error": "Client avec l'ID 'xxx' introuvable"
}
```
**Solution** : Vérifiez que l'ID client existe dans la base de données.

### **Erreur 3 : Validation**
```json
{
  "success": false,
  "error": "Erreurs de validation",
  "errors": {
    "annee_auditee": ["Ce champ est requis"],
    "date_debut": ["Format invalide"]
  }
}
```
**Solution** : Vérifiez que tous les champs sont remplis correctement.

---

## ⚠️ **Points Critiques**

1. ✅ **Body Type = Multipart Form** (pas Form URL Encoded, pas JSON)
2. ✅ **Deux champs avec le même nom `files[]`** (Insomnia permet cela)
3. ✅ **Type = File** pour les fichiers (pas Text)
4. ✅ **Format de date : YYYY-MM-DD** (ex: `2024-01-01`)
5. ✅ **ID client valide** (doit exister dans la base de données)

---

## 🔍 **Debug**

Si ça ne fonctionne pas, regardez les **logs du serveur Flask**. Vous devriez voir :

```
🔍 DEBUG - Tous les clés de request.files: ['files[]', 'files[]']
🔍 DEBUG - Total fichiers reçus: 2
  📄 Fichier 1: Balance_2024.xlsx
  📄 Fichier 2: Balance_2023.xlsx
🔍 DEBUG - Données reçues:
  - annee_auditee: 2024
  - id_client: 65a1b2c3d4e5f6789abcdef0
  - date_debut: 2024-01-01
  - date_fin: 2024-12-31
```

Si vous voyez `Total fichiers reçus: 0`, les fichiers ne sont pas envoyés correctement.

---

## 📞 **Support**

Si vous rencontrez des problèmes :
1. Vérifiez les logs du serveur Flask
2. Vérifiez que le serveur est démarré (`python app.py`)
3. Vérifiez que les fichiers Excel existent et sont accessibles
4. Vérifiez que l'ID client est valide

