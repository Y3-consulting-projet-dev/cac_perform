# 🔍 Diagnostic des Erreurs - Création de Mission

## 📋 **Étapes de Diagnostic**

### **1. Vérifier le message d'erreur exact**

Dans Insomnia, regardez :
- **Code HTTP** (ex: 400, 500)
- **Message d'erreur** dans le body de la réponse
- **Onglet "Timeline"** pour voir les détails

---

## ❌ **Erreurs Courantes et Solutions**

### **Erreur 1 : "La date de début du mandat est requise"**

**Message** :
```json
{
  "success": false,
  "error": "La date de début du mandat est requise"
}
```

**Solution** :
1. Vérifiez que le champ `date_debut_mandat` est bien présent dans Insomnia
2. Vérifiez qu'il n'y a pas d'espaces avant/après le nom du champ
3. Vérifiez que la valeur n'est pas vide

**Dans Insomnia** :
- Key : `date_debut_mandat` (exactement, sans espaces)
- Type : `Text`
- Value : `2024-01-01` (format YYYY-MM-DD)

---

### **Erreur 2 : "La date de fin du mandat est requise"**

**Message** :
```json
{
  "success": false,
  "error": "La date de fin du mandat est requise"
}
```

**Solution** :
- Même chose que pour `date_debut_mandat`
- Vérifiez le champ `date_fin_mandat`

---

### **Erreur 3 : "Format de date invalide"**

**Message** :
```json
{
  "success": false,
  "error": "Erreurs de validation",
  "errors": {
    "date_debut_mandat": ["La date doit être au format YYYY-MM-DD"]
  }
}
```

**Solution** :
- Format requis : `YYYY-MM-DD`
- ✅ Correct : `2024-01-01`, `2024-12-31`
- ❌ Incorrect : `01/01/2024`, `2024-1-1`, `01-01-2024`

---

### **Erreur 4 : "Client avec l'ID 'xxx' introuvable"**

**Message** :
```json
{
  "success": false,
  "error": "Client avec l'ID '65a1b2c3d4e5f6789abcdef0' introuvable"
}
```

**Solution** :
1. Obtenez un ID client valide :
   ```
   GET http://localhost:5000/api/v1/clients/
   ```
2. Copiez l'`_id` d'un client de la réponse
3. Utilisez cet ID dans le champ `id_client`

---

### **Erreur 5 : "Au moins 2 fichiers de balance sont requis"**

**Message** :
```json
{
  "success": false,
  "error": "Au moins 2 fichiers de balance sont requis (N et N-1)"
}
```

**Solution** :
- Assurez-vous d'avoir ajouté **2 fichiers** dans Insomnia
- Les deux doivent avoir le type **File**
- Les fichiers doivent être des fichiers Excel valides (.xlsx)

---

### **Erreur 6 : "Tous les champs sont requis"**

**Message** :
```json
{
  "error": "Tous les champs sont requis (y compris les dates du mandat)"
}
```

**Solution** :
Vérifiez que **TOUS** ces champs sont présents :
- ✅ `files[]` (2 fois)
- ✅ `annee_auditee`
- ✅ `id_client`
- ✅ `date_debut`
- ✅ `date_fin`
- ✅ `date_debut_mandat` ← **NOUVEAU**
- ✅ `date_fin_mandat` ← **NOUVEAU**

---

### **Erreur 7 : "La date de début du mandat doit être antérieure à la date de fin du mandat"**

**Message** :
```json
{
  "success": false,
  "error": "Erreurs de validation",
  "errors": {
    "date_debut_mandat": ["La date de début du mandat doit être antérieure à la date de fin du mandat"]
  }
}
```

**Solution** :
- `date_debut_mandat` doit être **avant** `date_fin_mandat`
- Exemple : `2024-01-01` < `2024-12-31` ✅

---

## 🔍 **Vérification dans Insomnia**

### **Checklist des champs**

Dans Insomnia, vérifiez que vous avez **exactement 8 champs** :

```
✅ files[]              → Type: File
✅ files[]              → Type: File
✅ annee_auditee        → Type: Text, Value: 2024
✅ id_client            → Type: Text, Value: [ID valide]
✅ date_debut           → Type: Text, Value: 2024-01-01
✅ date_fin             → Type: Text, Value: 2024-12-31
✅ date_debut_mandat    → Type: Text, Value: 2024-01-01
✅ date_fin_mandat      → Type: Text, Value: 2024-12-31
```

### **Vérifier les noms de champs**

⚠️ **ATTENTION** : Les noms de champs sont **sensibles** :
- ✅ Correct : `date_debut_mandat`
- ❌ Incorrect : `date_debut_mandat ` (avec espace à la fin)
- ❌ Incorrect : `dateDebutMandat` (camelCase)
- ❌ Incorrect : `date_debut_mandat_` (avec underscore à la fin)

---

## 🧪 **Test de Diagnostic**

### **Test 1 : Vérifier que tous les champs sont reçus**

Dans Insomnia, après avoir envoyé la requête, regardez la réponse. Si vous voyez un objet `debug`, il contient les champs reçus :

```json
{
  "success": false,
  "error": "...",
  "debug": {
    "champs_reçus": ["files[]", "annee_auditee", ...]
  }
}
```

Vérifiez que `date_debut_mandat` et `date_fin_mandat` sont dans la liste.

---

### **Test 2 : Vérifier le format des dates**

Toutes les dates doivent être au format `YYYY-MM-DD` :
- ✅ `2024-01-01`
- ✅ `2024-12-31`
- ✅ `2024-06-15`

---

### **Test 3 : Vérifier l'ID client**

1. Faites une requête GET :
   ```
   GET http://localhost:5000/api/v1/clients/
   ```
2. Copiez un `_id` de la réponse
3. Utilisez-le dans `id_client`

---

## 📸 **Exemple de Configuration Correcte dans Insomnia**

```
┌─────────────────────────────────────────────────────────────┐
│ Method: POST                                                 │
│ URL: http://localhost:5000/api/v1/missions/                │
│                                                             │
│ Body: Multipart Form                                        │
│ ┌─────────────────────┬────────┬──────────────────────────┐ │
│ │ Key                 │ Type   │ Value                    │ │
│ ├─────────────────────┼────────┼──────────────────────────┤ │
│ │ files[]             │ File   │ [Balance_2024.xlsx]      │ │
│ │ files[]             │ File   │ [Balance_2023.xlsx]      │ │
│ │ annee_auditee       │ Text   │ 2024                     │ │
│ │ id_client           │ Text   │ 67890abcdef1234567890123│ │
│ │ date_debut          │ Text   │ 2024-01-01              │ │
│ │ date_fin            │ Text   │ 2024-12-31              │ │
│ │ date_debut_mandat   │ Text   │ 2024-01-01              │ │
│ │ date_fin_mandat     │ Text   │ 2024-12-31              │ │
│ └─────────────────────┴────────┴──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🆘 **Si l'erreur persiste**

1. **Vérifiez les logs du serveur** :
   - Regardez la console où Flask est démarré
   - Cherchez les messages d'erreur détaillés

2. **Vérifiez que le serveur est démarré** :
   - Le serveur doit être sur `http://localhost:5000`

3. **Vérifiez MongoDB** :
   - MongoDB doit être démarré et connecté

4. **Partagez l'erreur complète** :
   - Code HTTP
   - Message d'erreur complet
   - Body de la réponse

---

## ✅ **Configuration Minimale pour Tester**

Si vous voulez tester rapidement, utilisez ces valeurs :

```
files[]              → [Vos fichiers Excel]
annee_auditee        → 2024
id_client            → [Obtenez via GET /api/v1/clients/]
date_debut           → 2024-01-01
date_fin             → 2024-12-31
date_debut_mandat    → 2024-01-01
date_fin_mandat      → 2024-12-31
```

---

**Si vous partagez le message d'erreur exact, je pourrai vous aider plus précisément !** 🚀

