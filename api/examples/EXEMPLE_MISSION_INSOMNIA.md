# 📋 Exemple Complet - Création Mission avec Insomnia

## 🎯 **Exemple Pratique**

### **1. Configuration de Base**

- **Method** : `POST`
- **URL** : `http://localhost:5000/api/v1/missions/`
- **Body Type** : `Multipart Form`

---

## 📝 **Données d'Exemple**

### **Exemple 1 : Mission Année 2024**

| Key | Type | Value | Description |
|-----|------|-------|-------------|
| `files[]` | File | `Balance_2024.xlsx` | Balance de l'année 2024 |
| `files[]` | File | `Balance_2023.xlsx` | Balance de l'année 2023 (N-1) |
| `annee_auditee` | Text | `2024` | Année auditée |
| `id_client` | Text | `65a1b2c3d4e5f6789abcdef0` | ID du client (remplacer par un ID valide) |
| `date_debut` | Text | `2024-01-01` | Date de début |
| `date_fin` | Text | `2024-12-31` | Date de fin |

---

### **Exemple 2 : Mission Année 2023**

| Key | Type | Value |
|-----|------|-------|
| `files[]` | File | `Balance_2023.xlsx` |
| `files[]` | File | `Balance_2022.xlsx` |
| `annee_auditee` | Text | `2023` |
| `id_client` | Text | `65a1b2c3d4e5f6789abcdef0` |
| `date_debut` | Text | `2023-01-01` |
| `date_fin` | Text | `2023-12-31` |

---

## ✅ **Réponse de Succès Attendue**

```json
{
  "success": true,
  "message": "Mission créée avec succès",
  "data": {
    "_id": "65a1b2c3d4e5f6789abcdef1",
    "mission": {
      "id_client": "65a1b2c3d4e5f6789abcdef0",
      "annee_auditee": "2024",
      "date_debut": "2024-01-01",
      "date_fin": "2024-12-31",
      "balances": [
        "65a1b2c3d4e5f6789abcdef2",
        "65a1b2c3d4e5f6789abcdef3"
      ],
      "balance_variation": {},
      "grouping": {},
      "efi": {},
      "materiality": []
    }
  }
}
```

**Status Code** : `201 Created`

---

## ❌ **Exemples de Réponses d'Erreur**

### **Erreur 400 - Fichiers manquants**

```json
{
  "success": false,
  "error": "Au moins 2 fichiers de balance sont requis (N et N-1)"
}
```

### **Erreur 400 - Validation échouée**

```json
{
  "success": false,
  "error": "Erreurs de validation",
  "errors": {
    "date_debut": ["La date de début est requise"],
    "annee_auditee": ["L'année auditée est requise"]
  }
}
```

### **Erreur 400 - Client introuvable**

```json
{
  "success": false,
  "error": "Client avec l'ID '65a1b2c3d4e5f6789abcdef0' introuvable"
}
```

### **Erreur 400 - Dates invalides**

```json
{
  "success": false,
  "error": "Erreurs de validation",
  "errors": {
    "_schema": ["La date de début doit être antérieure à la date de fin"]
  }
}
```

---

## 🔍 **Comment Obtenir l'ID Client**

Avant de créer une mission, vous devez obtenir l'ID d'un client :

### **Option 1 : Via l'API**

```bash
GET http://localhost:5000/api/v1/clients/
```

**Réponse** :
```json
{
  "response": [
    {
      "_id": "65a1b2c3d4e5f6789abcdef0",
      "nom": "Entreprise ABC SARL",
      "activite": "Conseil en audit",
      ...
    }
  ],
  "total": 1
}
```

### **Option 2 : Créer un client d'abord**

```bash
POST http://localhost:5000/api/v1/clients/
```

**Body (JSON)** :
```json
{
  "nom": "Entreprise Test",
  "activite": "Test",
  "referentiel": "syscohada",
  "forme_juridique": "SARL",
  "capital": 1000000.0,
  "siege_social": "Abidjan",
  "adresse": "123 Rue Test"
}
```

**Réponse** :
```json
{
  "response": "65a1b2c3d4e5f6789abcdef0",
  "message": "Client créé avec succès"
}
```

Utilisez cet `_id` ou le `response` comme `id_client` dans la création de mission.

---

## 📋 **Checklist Avant d'Envoyer**

- [ ] Serveur Flask démarré
- [ ] URL correcte : `http://localhost:5000/api/v1/missions/`
- [ ] Méthode : `POST`
- [ ] Body Type : `Multipart Form`
- [ ] Au moins 2 fichiers Excel sélectionnés
- [ ] `annee_auditee` rempli (ex: "2024")
- [ ] `id_client` rempli avec un ID client valide
- [ ] `date_debut` rempli (format: YYYY-MM-DD)
- [ ] `date_fin` rempli (format: YYYY-MM-DD)
- [ ] Date de début < Date de fin

---

## 💡 **Conseils**

1. **Testez d'abord sans fichiers** pour vérifier que l'endpoint répond (devrait retourner erreur 400)
2. **Utilisez des fichiers Excel valides** au format 6 colonnes
3. **Vérifiez les logs du serveur** pour voir les détails de l'erreur si ça échoue
4. **L'ID client doit exister** dans la base de données








