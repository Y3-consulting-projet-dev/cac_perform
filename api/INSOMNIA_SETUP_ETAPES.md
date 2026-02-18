# 🎯 Configuration Insomnia - ÉTAPES DÉTAILLÉES

## ❌ **ERREUR COURANTE**

Vous avez mis du **JSON** dans le body :
```json
{
  "files[]": ["Balance_2024.xlsx", "Balance_2023.xlsx"],
  ...
}
```

**❌ CELA NE FONCTIONNE PAS !** Les fichiers ne peuvent pas être envoyés en JSON.

---

## ✅ **SOLUTION : Utiliser Multipart Form**

### **ÉTAPE 1 : Créer la requête**

1. Ouvrez Insomnia
2. Cliquez sur **"New Request"** (ou **Ctrl+N**)
3. Nommez-la : `Créer Mission`
4. Méthode : `POST`
5. URL : `http://localhost:5000/api/v1/missions/`

---

### **ÉTAPE 2 : Configurer le Body**

1. Cliquez sur l'onglet **"Body"** (en bas de l'écran)
2. Vous verrez plusieurs options :
   - ❌ **JSON** ← Ne pas utiliser
   - ❌ **Form URL Encoded** ← Ne pas utiliser
   - ✅ **Multipart Form** ← **UTILISER CELUI-CI**
3. Cliquez sur **"Multipart Form"**

---

### **ÉTAPE 3 : Ajouter les champs**

Dans la section **Multipart Form**, vous verrez un tableau avec 3 colonnes :
- **Key** (nom du champ)
- **Type** (Text ou File)
- **Value** (valeur ou fichier)

#### **Champ 1 : Premier fichier**

1. Cliquez sur **"Add"** ou **"+"** pour ajouter un champ
2. Dans la colonne **Key**, tapez : `files[]` (avec les crochets)
3. Dans la colonne **Type**, cliquez sur le menu déroulant et sélectionnez **"File"**
4. Dans la colonne **Value**, cliquez sur **"Choose File"** ou **"Select File"**
5. Naviguez vers votre fichier Excel (ex: `Balance_2024.xlsx`) et sélectionnez-le
6. Le chemin du fichier apparaîtra dans la colonne Value

#### **Champ 2 : Deuxième fichier**

1. Cliquez à nouveau sur **"Add"** ou **"+"**
2. Dans **Key**, tapez : `files[]` (⚠️ **MÊME NOM que le premier**)
3. Dans **Type**, sélectionnez **"File"**
4. Dans **Value**, cliquez sur **"Choose File"** et sélectionnez votre deuxième fichier (ex: `Balance_2023.xlsx`)

#### **Champ 3 : Année auditée**

1. Cliquez sur **"Add"**
2. **Key** : `annee_auditee`
3. **Type** : `Text` (laissez par défaut)
4. **Value** : `2024`

#### **Champ 4 : ID Client**

1. Cliquez sur **"Add"**
2. **Key** : `id_client`
3. **Type** : `Text`
4. **Value** : `65a1b2c3d4e5f6789abcdef0` (remplacez par un ID valide)

#### **Champ 5 : Date de début**

1. Cliquez sur **"Add"**
2. **Key** : `date_debut`
3. **Type** : `Text`
4. **Value** : `2024-01-01`

#### **Champ 6 : Date de fin**

1. Cliquez sur **"Add"**
2. **Key** : `date_fin`
3. **Type** : `Text`
4. **Value** : `2024-12-31`

---

## 📊 **À QUOI ÇA RESSEMBLE**

Votre configuration devrait ressembler à ceci :

```
┌─────────────────────────────────────────────────────────────┐
│ Body: Multipart Form                                         │
├──────────────┬────────┬──────────────────────────────────────┤
│ Key          │ Type   │ Value                               │
├──────────────┼────────┼──────────────────────────────────────┤
│ files[]      │ File   │ C:\Users\...\Balance_2024.xlsx      │
│ files[]      │ File   │ C:\Users\...\Balance_2023.xlsx      │
│ annee_auditee│ Text   │ 2024                                │
│ id_client    │ Text   │ 65a1b2c3d4e5f6789abcdef0            │
│ date_debut   │ Text   │ 2024-01-01                          │
│ date_fin     │ Text   │ 2024-12-31                          │
└──────────────┴────────┴──────────────────────────────────────┘
```

---

## ⚠️ **POINTS CRITIQUES**

1. ✅ **Body Type = Multipart Form** (pas JSON)
2. ✅ **Deux champs avec le même nom `files[]`** (c'est normal et nécessaire)
3. ✅ **Type = File** pour les fichiers (pas Text)
4. ✅ **Les fichiers doivent être sélectionnés** (le chemin apparaît dans Value)

---

## 🔍 **VÉRIFICATION**

Avant d'envoyer, vérifiez :

- [ ] Body Type est bien **"Multipart Form"**
- [ ] Vous avez **2 champs** avec `Key = files[]` et `Type = File`
- [ ] Les fichiers sont bien sélectionnés (le chemin apparaît)
- [ ] Les 4 autres champs sont remplis (Text)

---

## 🚀 **ENVOYER LA REQUÊTE**

1. Cliquez sur le bouton **"Send"** (ou **Ctrl+Enter**)
2. Regardez la réponse dans le panneau de droite
3. Si succès : Statut **201 Created** avec un JSON de confirmation
4. Si erreur : Vérifiez les logs du serveur Flask

---

## ❓ **PROBLÈMES COURANTS**

### **Problème 1 : "Au moins 2 fichiers requis"**
- Vérifiez que vous avez bien 2 champs `files[]` avec Type = File
- Vérifiez que les fichiers sont bien sélectionnés

### **Problème 2 : "Client introuvable"**
- Vérifiez que l'ID client existe dans la base de données
- Utilisez `python get_client_id.py` pour obtenir un ID valide

### **Problème 3 : Erreur 404**
- Vérifiez que le serveur Flask est démarré (`python app.py`)
- Vérifiez l'URL : `http://localhost:5000/api/v1/missions/`

---

## 📸 **RÉSUMÉ VISUEL**

```
Insomnia
├── Method: POST
├── URL: http://localhost:5000/api/v1/missions/
└── Body
    └── Multipart Form
        ├── files[] (File) → Balance_2024.xlsx
        ├── files[] (File) → Balance_2023.xlsx
        ├── annee_auditee (Text) → 2024
        ├── id_client (Text) → 65a1b2c3d4e5f6789abcdef0
        ├── date_debut (Text) → 2024-01-01
        └── date_fin (Text) → 2024-12-31
```

---

## ✅ **C'EST TOUT !**

Suivez ces étapes et votre requête devrait fonctionner. Si vous avez encore des problèmes, vérifiez les logs du serveur Flask.

