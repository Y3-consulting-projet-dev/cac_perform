# 🔒 Résoudre l'Erreur de Sécurité Insomnia

## ❌ **Erreur Rencontrée**

```
Error: Insomnia cannot access the file "C:\Users\Mariam Latifa DALLA\Downloads\BG 2023.xlsx". 
You must specify which directories Insomnia can access in Insomnia Preferences → Security
```

---

## ✅ **Solution : Autoriser l'Accès aux Fichiers**

### **Étape 1 : Ouvrir les Préférences**

1. Dans Insomnia, allez dans le menu :
   - **Windows/Linux** : `File` → `Preferences` (ou `Ctrl+,`)
   - **Mac** : `Insomnia` → `Preferences` (ou `Cmd+,`)

### **Étape 2 : Aller dans l'Onglet Security**

1. Dans la fenêtre des préférences, cliquez sur **"Security"** (ou **"Sécurité"**)
2. Vous verrez une section **"File Access"** ou **"Accès aux Fichiers"**

### **Étape 3 : Autoriser le Dossier**

Vous avez **2 options** :

#### **Option A : Autoriser un Dossier Spécifique (Recommandé)**

1. Cliquez sur **"Add Directory"** ou **"Ajouter un Dossier"**
2. Naviguez vers le dossier où se trouvent vos fichiers Excel
   - Exemple : `C:\Users\Mariam Latifa DALLA\Downloads\`
3. Sélectionnez le dossier et cliquez sur **"Select Folder"** ou **"Sélectionner le Dossier"**
4. Le dossier apparaîtra dans la liste des dossiers autorisés

#### **Option B : Autoriser Tous les Dossiers (Moins Sécurisé)**

1. Activez l'option **"Allow access to all files"** ou **"Autoriser l'accès à tous les fichiers"**
   - ⚠️ **Attention** : Cette option est moins sécurisée mais plus pratique pour le développement

---

## 📁 **Dossiers Recommandés à Autoriser**

Pour faciliter le travail, autorisez ces dossiers :

1. **Dossier Downloads** :
   ```
   C:\Users\Mariam Latifa DALLA\Downloads\
   ```

2. **Dossier de travail** (si vous avez un dossier dédié) :
   ```
   C:\Users\Mariam Latifa DALLA\Documents\Balances\
   ```
   (Créez ce dossier si nécessaire)

3. **Dossier du projet** (optionnel) :
   ```
   D:\Documents\cac-perform\docs\
   ```

---

## 🔄 **Après l'Autorisation**

1. **Fermez** la fenêtre des préférences
2. **Retournez** à votre requête dans Insomnia
3. **Réessayez** de sélectionner le fichier Excel
4. Le fichier devrait maintenant être accessible

---

## 💡 **Astuce : Déplacer les Fichiers**

Si vous préférez ne pas modifier les paramètres de sécurité, vous pouvez :

1. **Créer un dossier dédié** pour vos fichiers de test :
   ```
   C:\Users\Mariam Latifa DALLA\Documents\Balances\
   ```

2. **Déplacer** vos fichiers Excel dans ce dossier

3. **Autoriser uniquement ce dossier** dans Insomnia

4. **Utiliser** ces fichiers dans vos requêtes

---

## 📝 **Résumé des Étapes**

```
1. File → Preferences (Ctrl+,)
2. Onglet "Security"
3. Section "File Access"
4. Cliquez "Add Directory"
5. Sélectionnez le dossier Downloads (ou votre dossier)
6. Fermez les préférences
7. Réessayez de sélectionner le fichier
```

---

## ✅ **Vérification**

Une fois configuré, vous devriez pouvoir :
- ✅ Sélectionner les fichiers Excel depuis le dossier autorisé
- ✅ Voir le chemin complet dans la colonne Value
- ✅ Envoyer la requête sans erreur

---

## 🆘 **Si ça ne fonctionne toujours pas**

1. **Redémarrez Insomnia** après avoir modifié les préférences
2. **Vérifiez** que le chemin du fichier est correct
3. **Vérifiez** que le fichier existe bien à cet emplacement
4. **Essayez** de déplacer le fichier dans un autre dossier autorisé

---

## 📸 **Visualisation**

Dans les préférences, vous devriez voir quelque chose comme :

```
┌─────────────────────────────────────────┐
│ Preferences                             │
├─────────────────────────────────────────┤
│ [General] [Security] [Plugins] ...       │
├─────────────────────────────────────────┤
│ Security                                 │
│                                          │
│ File Access                              │
│ ┌─────────────────────────────────────┐ │
│ │ C:\Users\...\Downloads\            │ │
│ │ C:\Users\...\Documents\Balances\   │ │
│ └─────────────────────────────────────┘ │
│                                          │
│ [+ Add Directory]                        │
│                                          │
│ ☐ Allow access to all files             │
└─────────────────────────────────────────┘
```

