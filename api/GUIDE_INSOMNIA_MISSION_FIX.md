# 🔧 Guide Insomnia - Création de Mission (Correction)

## ❌ **Erreur Courante**
```
{
  "success": false,
  "error": "Au moins 2 fichiers de balance sont requis (N et N-1)"
}
```

Cette erreur indique que les fichiers ne sont pas correctement envoyés depuis Insomnia.

---

## ✅ **Configuration Correcte dans Insomnia**

### **1. Méthode et URL**
- **Méthode** : `POST`
- **URL** : `http://localhost:5000/api/v1/missions/`

---

### **2. Body Type**
- **Body Type** : `Multipart Form` (⚠️ IMPORTANT : Ne pas utiliser "Form URL Encoded" ou "JSON")

---

### **3. Champs du Formulaire**

Dans Insomnia, ajoutez les champs suivants dans l'ordre :

#### **Champ 1 : Premier fichier**
- **Key** : `files[]` ⚠️ **Obligatoire : exactement ce nom avec les crochets**
- **Type** : `File` (dans le menu déroulant)
- **Value** : Sélectionnez votre fichier `Balance_2024.xlsx` (ou autre)

#### **Champ 2 : Deuxième fichier**
- **Key** : `files[]` ⚠️ **Même nom que le premier !**
- **Type** : `File`
- **Value** : Sélectionnez votre fichier `Balance_2023.xlsx` (ou autre)

#### **Champ 3 : Année auditée**
- **Key** : `annee_auditee`
- **Type** : `Text`
- **Value** : `2024` (ou l'année souhaitée)

#### **Champ 4 : ID Client**
- **Key** : `id_client`
- **Type** : `Text`
- **Value** : `65a1b2c3d4e5f6789abcdef0` (remplacez par un ID client valide)

#### **Champ 5 : Date de début**
- **Key** : `date_debut`
- **Type** : `Text`
- **Value** : `2024-01-01` (format YYYY-MM-DD)

#### **Champ 6 : Date de fin**
- **Key** : `date_fin`
- **Type** : `Text`
- **Value** : `2024-12-31` (format YYYY-MM-DD)

---

## ⚠️ **Points Critiques**

### **1. Nom du champ pour les fichiers**
Le nom du champ doit être **EXACTEMENT** `files[]` avec :
- Les crochets `[]` 
- Pas d'espace
- Pas de guillemets

❌ **Faux** :
- `files`
- `files[] `
- `"files[]"`
- `file[]`

✅ **Correct** :
- `files[]`

---

### **2. Body Type**
⚠️ **Ne pas utiliser "Form URL Encoded" ou "JSON"**

✅ **Utiliser uniquement "Multipart Form"**

---

### **3. Plusieurs fichiers avec le même nom**
Insomnia permet d'avoir plusieurs champs avec le même nom `files[]`. C'est **normal et nécessaire**.

Voici comment ça apparaît dans Insomnia :
```
┌─────────────────┬──────────┬─────────────────────┐
│ Key             │ Type     │ Value               │
├─────────────────┼──────────┼─────────────────────┤
│ files[]         │ File     │ Balance_2024.xlsx   │
│ files[]         │ File     │ Balance_2023.xlsx   │
│ annee_auditee   │ Text     │ 2024                │
│ id_client       │ Text     │ 65a1b2c3d...        │
│ date_debut      │ Text     │ 2024-01-01          │
│ date_fin        │ Text     │ 2024-12-31          │
└─────────────────┴──────────┴─────────────────────┘
```

---

## 🔍 **Vérification**

### **1. Vérifier que vous avez bien 2 champs `files[]`**

Dans Insomnia, vous devriez voir :
- ✅ 2 lignes avec `Key = files[]` et `Type = File`
- ✅ Les autres champs avec `Type = Text`

### **2. Vérifier les fichiers**

Assurez-vous que :
- ✅ Les fichiers sont bien sélectionnés (le chemin apparaît dans la colonne Value)
- ✅ Les fichiers existent et sont accessibles
- ✅ Les fichiers sont au format `.xlsx`

---

## 📝 **Exemple Visuel dans Insomnia**

```
POST http://localhost:5000/api/v1/missions/
Body: Multipart Form

┌──────────────────┬────────┬──────────────────────────────────┐
│ Key              │ Type   │ Value                            │
├──────────────────┼────────┼──────────────────────────────────┤
│ files[]          │ File   │ C:\...\Balance_2024.xlsx         │
│ files[]          │ File   │ C:\...\Balance_2023.xlsx         │
│ annee_auditee    │ Text   │ 2024                             │
│ id_client        │ Text   │ 65a1b2c3d4e5f6789abcdef0         │
│ date_debut       │ Text   │ 2024-01-01                       │
│ date_fin         │ Text   │ 2024-12-31                       │
└──────────────────┴────────┴──────────────────────────────────┘
```

---

## 🧪 **Test Rapide**

1. Ouvrez Insomnia
2. Créez une nouvelle requête POST
3. URL : `http://localhost:5000/api/v1/missions/`
4. Onglet **Body** → Sélectionnez **Multipart Form**
5. Ajoutez les 6 champs comme indiqué ci-dessus
6. ⚠️ **Vérifiez que vous avez bien 2 champs avec le nom `files[]`**
7. Cliquez sur **Send**

---

## ❓ **Toujours des erreurs ?**

Si vous recevez toujours l'erreur, vérifiez :

1. ✅ Le Body Type est bien **"Multipart Form"** (pas Form URL Encoded)
2. ✅ Vous avez exactement **2 champs** avec le nom `files[]` (avec les crochets)
3. ✅ Les deux champs sont de type **File** (pas Text)
4. ✅ Les fichiers sont bien sélectionnés
5. ✅ L'ID client existe dans la base de données

---

## 🔍 **Debug**

Si vous voulez vérifier ce qui est envoyé, ajoutez ces logs côté backend :

Dans `src/resources/mission_resources.py`, ligne 25, ajoutez :
```python
uploaded_files = request.files.getlist('files[]')
print(f"🔍 Fichiers reçus: {len(uploaded_files)}")
for i, f in enumerate(uploaded_files):
    print(f"  Fichier {i+1}: {f.filename if f else 'None'}")
```

Cela vous montrera combien de fichiers sont reçus par le backend.








