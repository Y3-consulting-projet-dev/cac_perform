# 🔍 Debug - Fichiers Non Reçus dans Insomnia

## ❌ **Erreur Reçue**

```json
{
  "success": false,
  "error": "Au moins 2 fichiers de balance sont requis (N et N-1)"
}
```

---

## 🔍 **Étapes de Diagnostic**

### **1. Vérifier les Logs du Serveur Flask**

Après avoir envoyé la requête depuis Insomnia, regardez les **logs du serveur Flask** (dans le terminal où vous avez lancé `python app.py`).

Vous devriez voir des lignes qui commencent par `🔍 DEBUG`. 

**Exemple de logs attendus :**
```
🔍 DEBUG - Tous les clés de request.files: []
🔍 DEBUG - Tous les clés de request.form: ['annee_auditee', 'id_client', ...]
🔍 DEBUG - Total fichiers reçus: 0
❌ ERREUR DÉTAILLÉE: {...}
```

**Si vous voyez `clés de request.files: []`**, cela signifie que les fichiers ne sont **pas envoyés** depuis Insomnia.

---

### **2. Vérifier la Configuration Insomnia**

#### **A. Body Type**

1. Dans Insomnia, ouvrez votre requête
2. Cliquez sur l'onglet **Body**
3. Vérifiez que **"Multipart Form"** est sélectionné (pas JSON, pas Form URL Encoded)

#### **B. Champs de Fichiers**

Vérifiez que vous avez **exactement 2 champs** avec :

| Key | Type | Value |
|-----|------|-------|
| `files[]` | **File** | [Chemin vers le fichier] |
| `files[]` | **File** | [Chemin vers le fichier] |

**Points critiques :**
- ✅ Le nom du champ doit être **exactement** `files[]` (avec les crochets)
- ✅ Le Type doit être **File** (pas Text)
- ✅ Les fichiers doivent être **sélectionnés** (le chemin complet doit apparaître)

#### **C. Vérification Visuelle**

Dans Insomnia, votre configuration devrait ressembler à ceci :

```
┌──────────────────┬────────┬──────────────────────────────────┐
│ Key              │ Type   │ Value                            │
├──────────────────┼────────┼──────────────────────────────────┤
│ files[]          │ File   │ C:\Users\...\BG 2024.xlsx       │
│ files[]          │ File   │ C:\Users\...\BG 2023.xlsx        │
│ annee_auditee    │ Text   │ 2024                             │
│ id_client        │ Text   │ 65a1b2c3d4e5f6789abcdef0         │
│ date_debut       │ Text   │ 2024-01-01                       │
│ date_fin         │ Text   │ 2024-12-31                       │
└──────────────────┴────────┴──────────────────────────────────┘
```

---

### **3. Problèmes Courants et Solutions**

#### **Problème 1 : Body Type = JSON**

❌ **Symptôme** : Les logs montrent `clés de request.files: []`

✅ **Solution** : Changez le Body Type en **"Multipart Form"**

---

#### **Problème 2 : Type = Text au lieu de File**

❌ **Symptôme** : Les fichiers apparaissent comme du texte dans les logs

✅ **Solution** : Changez le Type en **"File"** pour les deux champs `files[]`

---

#### **Problème 3 : Nom de champ incorrect**

❌ **Symptôme** : Les fichiers ne sont pas reçus

✅ **Solution** : Le nom doit être **exactement** `files[]` (avec les crochets, pas d'espace)

---

#### **Problème 4 : Fichiers non sélectionnés**

❌ **Symptôme** : La colonne Value est vide ou contient juste le nom du fichier

✅ **Solution** : Cliquez sur **"Choose File"** et sélectionnez les fichiers depuis votre ordinateur

---

### **4. Test Rapide**

Pour vérifier que tout fonctionne :

1. **Créez une nouvelle requête** dans Insomnia
2. **Configurez-la** exactement comme indiqué ci-dessus
3. **Envoyez la requête**
4. **Regardez les logs du serveur** - vous devriez voir :
   ```
   🔍 DEBUG - Tous les clés de request.files: ['files[]', 'files[]']
   ✅ Fichiers trouvés avec 'files[]': 2
   🔍 DEBUG - Total fichiers reçus: 2
     📄 Fichier 1: BG 2024.xlsx
     📄 Fichier 2: BG 2023.xlsx
   ```

---

### **5. Si ça ne fonctionne toujours pas**

1. **Copiez les logs du serveur** et partagez-les
2. **Faites une capture d'écran** de votre configuration Insomnia (onglet Body)
3. **Vérifiez** que le serveur Flask est bien démarré et écoute sur le port 5000

---

## 📋 **Checklist Complète**

Avant d'envoyer la requête, vérifiez :

- [ ] Body Type = **Multipart Form**
- [ ] 2 champs avec `Key = files[]` et `Type = File`
- [ ] Les fichiers sont bien sélectionnés (chemin complet visible)
- [ ] Les 4 autres champs sont remplis (Text)
- [ ] Le serveur Flask est démarré
- [ ] L'URL est correcte : `http://localhost:5000/api/v1/missions/`

---

## 🆘 **Message d'Erreur Amélioré**

Si vous recevez toujours l'erreur, la réponse JSON contiendra maintenant des informations de debug :

```json
{
  "success": false,
  "error": "Au moins 2 fichiers de balance sont requis (N et N-1)",
  "debug": {
    "fichiers_reçus": 0,
    "clés_fichiers": [],
    "content_type": "...",
    "aide": "Vérifiez que vous utilisez 'Multipart Form' dans Insomnia..."
  }
}
```

Utilisez ces informations pour diagnostiquer le problème.





