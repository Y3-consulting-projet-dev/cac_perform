# 📋 Guide Insomnia - Création de Mission

## 🎯 **Configuration Exacte pour Insomnia**

### **1. Créer une Nouvelle Requête**

1. Cliquez sur **"New Request"** ou **"+"**
2. Nommez-la : `Créer Mission`

---

### **2. Configuration de la Requête**

#### **Method**
```
POST
```

#### **URL**
```
http://localhost:5000/cors/mission/nouvelle_mission
```

⚠️ **IMPORTANT** :
- Pas de `/` à la fin
- Pas d'espace avant/après
- Utilisez `http://` (pas `https://`)
- Port `5000` (vérifiez que c'est le bon port)

---

### **3. Body Type**

Sélectionnez : **`Multipart Form`**

⚠️ **Ne pas utiliser** :
- ❌ JSON
- ❌ Form URL Encoded
- ❌ Text
- ❌ File

---

### **4. Champs à Ajouter**

Cliquez sur **"Add"** pour chaque champ :

#### **Champ 1 : files[]**
- **Key** : `files[]`
- **Type** : `File` (dans le menu déroulant)
- **Value** : Cliquez sur **"Choose File"** et sélectionnez `Balance_2024.xlsx`

#### **Champ 2 : files[]** (deuxième fichier)
- **Key** : `files[]` (exactement le même nom)
- **Type** : `File`
- **Value** : Cliquez sur **"Choose File"** et sélectionnez `Balance_2023.xlsx`

#### **Champ 3 : annee_auditee**
- **Key** : `annee_auditee`
- **Type** : `Text`
- **Value** : `2024`

#### **Champ 4 : id**
- **Key** : `id`
- **Type** : `Text`
- **Value** : `65a1b2c3d4e5f6789abcdef0` (remplacez par un ID client valide)

#### **Champ 5 : date_debut**
- **Key** : `date_debut`
- **Type** : `Text`
- **Value** : `2024-01-01`

#### **Champ 6 : date_fin**
- **Key** : `date_fin`
- **Type** : `Text`
- **Value** : `2024-12-31`

---

### **5. Headers**

⚠️ **Ne pas ajouter de headers manuellement !**

Insomnia ajoute automatiquement :
```
Content-Type: multipart/form-data; boundary=...
```

Si vous ajoutez manuellement `Content-Type`, cela peut causer des erreurs.

---

### **6. Envoyer la Requête**

Cliquez sur **"Send"**

---

## ✅ **Réponse Attendue (Succès)**

**Status** : `200 OK`

**Body** :
```json
{
  "success": true,
  "data": {
    "_id": "65a1b2c3d4e5f6789abcdef1",
    "mission": {
      "id_client": "65a1b2c3d4e5f6789abcdef0",
      "annee_auditee": "2024",
      ...
    }
  }
}
```

---

## ❌ **Erreurs Communes et Solutions**

### **Erreur 404 Not Found**

**Message** :
```json
{
  "error": "404 Not Found"
}
```

**Causes possibles** :
1. ❌ URL incorrecte
2. ❌ Le serveur Flask n'est pas démarré
3. ❌ Le blueprint mission n'est pas enregistré

**Solutions** :
1. ✅ Vérifiez l'URL : `http://localhost:5000/cors/mission/nouvelle_mission`
2. ✅ Vérifiez que le serveur Flask est démarré
3. ✅ Vérifiez les logs du serveur au démarrage (devrait voir "📋 Missions: /cors/mission/")

---

### **Erreur 405 Method Not Allowed**

**Message** :
```json
{
  "error": "405 Method Not Allowed"
}
```

**Cause** : La méthode HTTP est incorrecte

**Solution** : Utilisez `POST` (pas `GET`, `PUT`, etc.)

---

### **Erreur 400 Bad Request - "Tous les champs sont requis"**

**Message** :
```json
{
  "error": "Tous les champs sont requis"
}
```

**Cause** : Un ou plusieurs champs manquent

**Solution** : Vérifiez que tous les champs sont présents :
- ✅ `files[]` (au moins 2 fichiers)
- ✅ `annee_auditee`
- ✅ `id`
- ✅ `date_debut`
- ✅ `date_fin`

---

### **Erreur 400 Bad Request - "Au moins 2 fichiers de balance sont requis"**

**Message** :
```json
{
  "error": "Au moins 2 fichiers de balance sont requis (N et N-1)"
}
```

**Cause** : Moins de 2 fichiers envoyés

**Solution** : Ajoutez au moins 2 fichiers dans les champs `files[]`

---

### **Erreur 500 Internal Server Error**

**Message** :
```json
{
  "error": "Erreur serveur: [détails]"
}
```

**Cause** : Erreur dans le code Python

**Solution** : 
1. Vérifiez les logs du serveur Flask
2. Notez l'erreur exacte
3. Corrigez le problème dans le code

---

## 🔍 **Vérification Rapide**

### **Test 1 : Le serveur répond-il ?**

Dans Insomnia, créez une nouvelle requête :
- **Method** : `GET`
- **URL** : `http://localhost:5000/health`
- **Send**

**Résultat attendu** : `200 OK` avec JSON

---

### **Test 2 : L'endpoint existe-t-il ?**

Dans Insomnia :
- **Method** : `POST`
- **URL** : `http://localhost:5000/cors/mission/nouvelle_mission`
- **Body Type** : `Multipart Form`
- Ajoutez seulement les champs textuels (sans fichiers)
- **Send**

**Résultat attendu** : `400 Bad Request` avec message "Au moins 2 fichiers..."

Si vous obtenez **404**, l'endpoint n'est pas enregistré.

---

## 📝 **Checklist de Configuration**

Avant d'envoyer la requête, vérifiez :

- [ ] Le serveur Flask est démarré
- [ ] L'URL est exactement : `http://localhost:5000/cors/mission/nouvelle_mission`
- [ ] La méthode est `POST`
- [ ] Le Body Type est `Multipart Form`
- [ ] Il y a au moins 2 champs `files[]` avec des fichiers sélectionnés
- [ ] Tous les champs textuels sont présents :
  - [ ] `annee_auditee`
  - [ ] `id` (ID client valide)
  - [ ] `date_debut`
  - [ ] `date_fin`
- [ ] Aucun header `Content-Type` n'est ajouté manuellement

---

## 💡 **Conseils**

1. **Testez d'abord sans fichiers** pour vérifier que l'endpoint répond
2. **Vérifiez les logs du serveur Flask** pendant l'envoi de la requête
3. **Utilisez un ID client valide** (obtenez-le via `GET /api/v1/clients/`)
4. **Les fichiers doivent être au format `.xlsx`**

---

## 🆘 **Si Rien Ne Fonctionne**

1. **Exécutez le script de test** :
   ```bash
   python test_mission_endpoint.py
   ```

2. **Vérifiez les logs du serveur Flask** au démarrage

3. **Testez avec cURL** :
   ```bash
   curl -X POST http://localhost:5000/cors/mission/nouvelle_mission \
     -F "files[]=@Balance_2024.xlsx" \
     -F "files[]=@Balance_2023.xlsx" \
     -F "annee_auditee=2024" \
     -F "id=65a1b2c3d4e5f6789abcdef0" \
     -F "date_debut=2024-01-01" \
     -F "date_fin=2024-12-31"
   ```

4. **Fournissez ces informations** :
   - Code HTTP de la réponse
   - Message d'erreur exact
   - Logs du serveur Flask
   - Configuration exacte dans Insomnia

