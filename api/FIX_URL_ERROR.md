# 🔧 Fix - Erreur "URL using bad/illegal format or missing URL"

## ❌ **Problème Identifié**

Erreur : `Error: URL using bad/illegal format or missing URL`

Cela se produit quand axios ne peut pas construire une URL valide pour la requête.

---

## ✅ **Corrections Appliquées**

### **1. Correction du Plugin Axios (`clients/src/plugins/axios.js`)**

Ajout d'un intercepteur pour gérer correctement FormData :

```javascript
axiosInstance.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    
    // Si les données sont un FormData, supprimer le Content-Type pour laisser axios gérer multipart/form-data
    if (config.data instanceof FormData) {
        delete config.headers['Content-Type']
    }
    
    return config
})
```

**Problème résolu** : Le Content-Type par défaut (`application/json`) était en conflit avec FormData.

---

### **2. Simplification de `uploadFile.js`**

Suppression de la configuration complexe et utilisation directe de l'instance axios injectée.

---

## 🔍 **Causes Possibles de l'Erreur URL**

### **1. BaseURL non défini**

Si `axios.defaults.baseURL` est `undefined`, l'URL sera invalide.

**Vérification** :
```javascript
console.log("BaseURL:", axios.defaults.baseURL);
```

**Solution** : Vérifiez que le plugin axios définit bien le baseURL :
```javascript
baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
```

---

### **2. Instance Axios non injectée**

Si `inject('axios')` retourne `undefined`, l'URL sera invalide.

**Vérification** :
```javascript
const axios = inject('axios');
if (!axios) {
    console.error("❌ Axios n'est pas injecté !");
}
```

**Solution** : Assurez-vous que le plugin axios est bien enregistré dans `main.js`.

---

### **3. URL malformée**

Si l'endpoint contient des caractères invalides ou est `undefined`.

**Vérification** :
```javascript
const endpoint = '/api/v1/missions/';
console.log("Endpoint:", endpoint); // Doit être une string valide
```

---

## 🧪 **Test de Diagnostic**

Ajoutez ce code dans `NewMission.vue` pour diagnostiquer :

```javascript
console.log("🔍 Diagnostic Axios:");
console.log("  - axios:", axios);
console.log("  - baseURL:", axios?.defaults?.baseURL);
console.log("  - endpoint:", '/api/v1/missions/');
console.log("  - URL complète:", axios?.defaults?.baseURL + '/api/v1/missions/');
```

---

## ✅ **Solution Complète**

### **Vérifier que le Plugin Axios est Enregistré**

Dans `clients/src/main.js`, vous devriez avoir :

```javascript
import axiosPlugin from './plugins/axios'
app.use(axiosPlugin)
```

---

### **Vérifier l'Injection**

Dans `NewMission.vue` :

```javascript
const axios = inject('axios')
if (!axios) {
    console.error("❌ Axios non injecté !");
    return;
}
```

---

## 🚀 **Test Rapide**

1. Ouvrir la console du navigateur (F12)
2. Créer une nouvelle mission
3. Regarder les logs :
   ```
   🚀 Envoi de la requête vers: /api/v1/missions/
   📦 BaseURL axios: http://localhost:5000
   ```

Si le BaseURL est `undefined`, c'est le problème.

---

## 💡 **Solution Alternative**

Si l'injection ne fonctionne pas, vous pouvez créer une instance axios directement dans `uploadFile.js` :

```javascript
import axios from 'axios';

const axiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
});
```

Mais il est préférable d'utiliser l'instance injectée pour respecter la configuration.

