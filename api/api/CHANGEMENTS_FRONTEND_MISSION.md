# 🔄 Changements Frontend - API Mission Moderne

## ✅ **Mise à Jour Effectuée**

Le frontend a été mis à jour pour utiliser la nouvelle API moderne `/api/v1/missions/` au lieu de l'ancienne API `/cors/mission/nouvelle_mission`.

---

## 📝 **Fichiers Modifiés**

### **1. `clients/src/utils/uploadFile.js`**

#### **Changements :**
- ✅ **URL mise à jour** : `/mission/nouvelle_mission` → `/api/v1/missions/`
- ✅ **Champ mis à jour** : `id` → `id_client` (pour correspondre à la nouvelle API)
- ✅ **Suppression du baseURL hardcodé** : Utilise maintenant l'instance axios injectée
- ✅ **Gestion d'erreur améliorée** : Meilleure extraction des messages d'erreur
- ✅ **Support du code 201** : Accepte maintenant 201 Created (nouvelle API) et 200 OK (compatibilité)

#### **Avant :**
```javascript
const config = {
    baseURL: 'http://localhost:5000/cors'
};
formData.append('id', id_client);
const response = await axios.post(`/mission/nouvelle_mission`, formData, config);
```

#### **Après :**
```javascript
formData.append('id_client', id_client); // Nouveau nom de champ
const response = await axios.post(`/api/v1/missions/`, formData);
// Utilise l'instance axios injectée avec le bon baseURL
```

---

### **2. `clients/src/views/NewMission.vue`**

#### **Changements :**
- ✅ **Injection d'axios** : Utilise `inject('axios')` pour obtenir l'instance axios configurée
- ✅ **Passage d'axios à uploadFile** : Passe l'instance axios à la fonction `uploadFile`
- ✅ **Gestion d'erreur améliorée** : Utilise try/catch pour mieux gérer les erreurs
- ✅ **Messages d'erreur améliorés** : Affiche les messages d'erreur de l'API

#### **Avant :**
```javascript
const result = await uploadFile(...)
if (result && result._id) {
    // ...
} else {
    notyf.trigger("Erreur lors de la création de la mission", "error")
}
```

#### **Après :**
```javascript
const axios = inject('axios') // Injection de l'instance axios

try {
    const result = await uploadFile(..., axios) // Passage de l'instance
    if (result && result._id) {
        notyf.trigger("Mission ajoutée avec succès", "success")
        back()
    }
} catch (error) {
    const errorMsg = error.message || "Erreur lors de la création de la mission"
    notyf.trigger(errorMsg, "error")
}
```

---

## 🔄 **Compatibilité**

### **Ancienne API (toujours disponible)**
```
POST /cors/mission/nouvelle_mission
Champ: id
```

### **Nouvelle API (utilisée maintenant)**
```
POST /api/v1/missions/
Champ: id_client
```

---

## ✅ **Avantages de la Mise à Jour**

1. ✅ **API moderne** : Utilise le style RESTful `/api/v1/missions/`
2. ✅ **Meilleure gestion d'erreur** : Messages d'erreur plus clairs
3. ✅ **Cohérence** : Même style que l'API des clients
4. ✅ **Validation** : La nouvelle API valide mieux les données
5. ✅ **Codes HTTP appropriés** : 201 Created pour succès

---

## 🧪 **Test**

Pour tester la mise à jour :

1. **Redémarrer le serveur Flask** (si nécessaire)
2. **Redémarrer le serveur frontend** (si nécessaire)
3. **Créer une nouvelle mission** via l'interface web
4. **Vérifier les logs** dans la console du navigateur :
   ```
   🚀 Envoi de la requête vers: /api/v1/missions/
   ✅ Mission créée avec succès: {...}
   ```

---

## 📋 **Format de Réponse**

### **Succès (201 Created)**
```json
{
  "success": true,
  "message": "Mission créée avec succès",
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

### **Erreur (400 Bad Request)**
```json
{
  "success": false,
  "error": "Au moins 2 fichiers de balance sont requis (N et N-1)"
}
```

---

## ⚠️ **Notes Importantes**

1. **Le champ `id_client` est maintenant utilisé** au lieu de `id`
2. **L'API retourne 201 Created** au lieu de 200 OK pour succès
3. **Les messages d'erreur sont plus détaillés** grâce à la validation Marshmallow
4. **L'instance axios injectée est utilisée** pour respecter la configuration du plugin axios

---

## 🔍 **Vérification**

Pour vérifier que tout fonctionne :

1. Ouvrir la console du navigateur (F12)
2. Créer une nouvelle mission
3. Vérifier les logs :
   - ✅ `🚀 Envoi de la requête vers: /api/v1/missions/`
   - ✅ `✅ Mission créée avec succès: {...}`
4. Vérifier que la mission apparaît dans l'espace client

