# 🧪 Guide de Test - Création d'un Nouveau Client

## 📋 **Informations de l'API**

### **Endpoint**
```
POST http://localhost:5000/api/v1/clients/
```

### **Alternative (Legacy)**
```
POST http://localhost:5000/cors/client/nouveau_client/
```

### **Headers Requis**
```
Content-Type: application/json
```

---

## 📝 **Exemples de Données JSON**

### **Exemple 1 : Client Minimal (Tous les champs requis)**

```json
{
  "nom": "Entreprise ABC SARL",
  "activite": "Conseil en audit et expertise comptable",
  "referentiel": "syscohada",
  "forme_juridique": "SARL",
  "capital": 1000000.0,
  "siege_social": "Abidjan, Cocody Angré 7ème Tranche",
  "adresse": "123 Boulevard de la République, Cocody, Abidjan, Côte d'Ivoire",
  "n_cc": "CC123456789"
}
```

---

### **Exemple 2 : Client Sans N°CC (champ optionnel)**

```json
{
  "nom": "Société XYZ SA",
  "activite": "Commerce général",
  "referentiel": "ifrs",
  "forme_juridique": "SA",
  "capital": 5000000.0,
  "siege_social": "Abidjan, Plateau",
  "adresse": "456 Avenue Franchet d'Esperey, Plateau, Abidjan"
}
```

---

### **Exemple 3 : Client PCG**

```json
{
  "nom": "Boutique Moderne",
  "activite": "Vente de produits cosmétiques",
  "referentiel": "pcg",
  "forme_juridique": "SARL",
  "capital": 500000.0,
  "siege_social": "Yopougon, Sicogi",
  "adresse": "789 Rue du Commerce, Yopougon, Abidjan",
  "n_cc": "CC987654321"
}
```

---

### **Exemple 4 : Client IFRS (International)**

```json
{
  "nom": "Groupe International CI",
  "activite": "Services financiers et bancaires",
  "referentiel": "ifrs",
  "forme_juridique": "SA",
  "capital": 10000000.0,
  "siege_social": "Abidjan, Zone 4",
  "adresse": "10 Avenue Jean-Paul II, Zone 4, Abidjan, Côte d'Ivoire",
  "n_cc": "CC555444333"
}
```

---

## 📌 **Règles de Validation**

### **Champs Requis :**
- ✅ `nom` : 2-100 caractères
- ✅ `activite` : 2-200 caractères  
- ✅ `referentiel` : Doit être `"syscohada"`, `"ifrs"` ou `"pcg"`
- ✅ `forme_juridique` : 2-50 caractères
- ✅ `capital` : Nombre positif (≥ 0)
- ✅ `siege_social` : 5-200 caractères
- ✅ `adresse` : 5-300 caractères

### **Champs Optionnels :**
- ⚪ `n_cc` : Maximum 50 caractères

---

## 🧪 **Tests avec cURL**

### **Test 1 : Création réussie**
```bash
curl -X POST http://localhost:5000/api/v1/clients/ \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Entreprise ABC SARL",
    "activite": "Conseil en audit et expertise comptable",
    "referentiel": "syscohada",
    "forme_juridique": "SARL",
    "capital": 1000000.0,
    "siege_social": "Abidjan, Cocody",
    "adresse": "123 Boulevard de la République, Cocody, Abidjan",
    "n_cc": "CC123456789"
  }'
```

### **Test 2 : Sans N°CC**
```bash
curl -X POST http://localhost:5000/api/v1/clients/ \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Société XYZ SA",
    "activite": "Commerce général",
    "referentiel": "ifrs",
    "forme_juridique": "SA",
    "capital": 5000000.0,
    "siege_social": "Abidjan, Plateau",
    "adresse": "456 Avenue Franchet d'Esperey, Plateau, Abidjan"
  }'
```

---

## 🧪 **Tests avec Insomnia / Postman**

### **Configuration :**
- **Method** : `POST`
- **URL** : `http://localhost:5000/api/v1/clients/`
- **Headers** :
  - `Content-Type` : `application/json`

### **Body (JSON)** :
Copiez l'un des exemples JSON ci-dessus.

---

## ✅ **Réponse Attendue (Succès)**

### **Code HTTP** : `201 Created`

```json
{
  "success": true,
  "message": "Client créé avec succès",
  "data": {
    "_id": "65a1b2c3d4e5f6789abcdef0",
    "nom": "Entreprise ABC SARL",
    "activite": "Conseil en audit et expertise comptable",
    "referentiel": "syscohada",
    "forme_juridique": "SARL",
    "capital": 1000000.0,
    "siege_social": "Abidjan, Cocody",
    "adresse": "123 Boulevard de la République, Cocody, Abidjan",
    "n_cc": "CC123456789"
  }
}
```

---

## ❌ **Réponses d'Erreur**

### **400 Bad Request - Validation échouée**
```json
{
  "success": false,
  "error": "Erreurs de validation: {
    'nom': ['Le nom du client est requis'],
    'referentiel': ['Must be one of: syscohada, ifrs, pcg.']
  }"
}
```

### **400 Bad Request - Client existant**
```json
{
  "success": false,
  "error": "Un client avec le nom 'Entreprise ABC SARL' existe déjà"
}
```

### **500 Internal Server Error**
```json
{
  "success": false,
  "error": "Erreur lors de la création du client: [détails de l'erreur]"
}
```

---

## 🔍 **Vérifier la Création**

Après la création, vous pouvez vérifier avec :

### **Lister tous les clients :**
```
GET http://localhost:5000/api/v1/clients/
```

### **Obtenir un client spécifique :**
```
GET http://localhost:5000/api/v1/clients/<client_id>
```

---

## 📝 **Notes Importantes**

1. ⚠️ Le `referentiel` est **case-sensitive** : utilisez `"syscohada"`, `"ifrs"` ou `"pcg"` (en minuscules)
2. ⚠️ Le `capital` doit être un nombre (pas de chaîne de caractères)
3. ⚠️ Si un client avec le même nom existe déjà, la création échouera
4. ✅ Le champ `n_cc` est optionnel et peut être omis








