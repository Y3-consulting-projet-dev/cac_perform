# 📋 EXACTEMENT CE QU'IL FAUT METTRE DANS LE BODY INSOMNIA

## ⚙️ **Configuration du Body**

1. Dans Insomnia, cliquez sur l'onglet **"Body"**
2. Sélectionnez **"Multipart Form"** (⚠️ PAS JSON, PAS Form URL Encoded)

---

## 📝 **Les 6 Champs à Ajouter**

Ajoutez ces champs **un par un** en cliquant sur **"Add"** ou **"+"** :

---

### **Champ 1 : Premier fichier Excel**

```
Key   : files[]
Type  : File
Value : [Cliquez sur "Choose File" et sélectionnez Balance_2024.xlsx]
```

**Action** : Cliquez sur le bouton "Choose File" ou "Select File" dans la colonne Value, puis naviguez vers votre fichier Excel et sélectionnez-le.

---

### **Champ 2 : Deuxième fichier Excel**

```
Key   : files[]
Type  : File
Value : [Cliquez sur "Choose File" et sélectionnez Balance_2023.xlsx]
```

**Action** : Même chose, ajoutez un deuxième champ avec le même nom `files[]` et sélectionnez votre deuxième fichier.

---

### **Champ 3 : Année auditée**

```
Key   : annee_auditee
Type  : Text
Value : 2024
```

**Action** : Tapez simplement `2024` dans la colonne Value.

---

### **Champ 4 : ID Client**

```
Key   : id_client
Type  : Text
Value : 65a1b2c3d4e5f6789abcdef0
```

**Action** : Remplacez `65a1b2c3d4e5f6789abcdef0` par un ID client valide de votre base de données.

**Pour obtenir un ID client valide** :
- Exécutez : `python get_client_id.py`
- Ou faites : `GET http://localhost:5000/api/v1/clients/`

---

### **Champ 5 : Date de début**

```
Key   : date_debut
Type  : Text
Value : 2024-01-01
```

**Action** : Tapez la date au format `YYYY-MM-DD`.

---

### **Champ 6 : Date de fin**

```
Key   : date_fin
Type  : Text
Value : 2024-12-31
```

**Action** : Tapez la date au format `YYYY-MM-DD`.

---

## 📊 **Résumé Visuel du Tableau**

Voici à quoi devrait ressembler votre tableau dans Insomnia :

```
┌──────────────────┬────────┬──────────────────────────────────────┐
│ Key              │ Type   │ Value                                │
├──────────────────┼────────┼──────────────────────────────────────┤
│ files[]          │ File   │ C:\Users\...\Balance_2024.xlsx       │
│ files[]          │ File   │ C:\Users\...\Balance_2023.xlsx       │
│ annee_auditee    │ Text   │ 2024                                 │
│ id_client        │ Text   │ 65a1b2c3d4e5f6789abcdef0             │
│ date_debut       │ Text   │ 2024-01-01                           │
│ date_fin         │ Text   │ 2024-12-31                           │
└──────────────────┴────────┴──────────────────────────────────────┘
```

---

## ✅ **Checklist de Vérification**

Avant d'envoyer, vérifiez :

- [ ] Body Type = **"Multipart Form"** (pas JSON)
- [ ] Vous avez **2 champs** avec `Key = files[]` et `Type = File`
- [ ] Les fichiers sont bien sélectionnés (le chemin complet apparaît dans Value)
- [ ] Les 4 autres champs sont de type **Text**
- [ ] Toutes les valeurs sont remplies

---

## 🎯 **Exemple Concret**

Si vos fichiers sont dans `C:\Documents\Balances\` :

```
Champ 1:
  Key: files[]
  Type: File
  Value: C:\Documents\Balances\Balance_2024.xlsx

Champ 2:
  Key: files[]
  Type: File
  Value: C:\Documents\Balances\Balance_2023.xlsx

Champ 3:
  Key: annee_auditee
  Type: Text
  Value: 2024

Champ 4:
  Key: id_client
  Type: Text
  Value: 65a1b2c3d4e5f6789abcdef0

Champ 5:
  Key: date_debut
  Type: Text
  Value: 2024-01-01

Champ 6:
  Key: date_fin
  Type: Text
  Value: 2024-12-31
```

---

## ⚠️ **ERREURS À ÉVITER**

❌ **Ne pas mettre** :
- Du JSON dans le body
- Les noms de fichiers en texte (ex: `"Balance_2024.xlsx"`)
- Type = Text pour les fichiers

✅ **Faire** :
- Utiliser Multipart Form
- Sélectionner les fichiers avec "Choose File"
- Type = File pour les fichiers

---

## 🚀 **C'est Tout !**

Une fois ces 6 champs configurés, cliquez sur **"Send"** et la requête devrait fonctionner.





