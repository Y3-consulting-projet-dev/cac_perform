# ✅ Formats de Validation - API Création de Mission

## 📋 **Formats Requis**

### **1. Année Auditée (`annee_auditee`)**

- **Format** : Exactement 4 caractères
- **Exemple valide** : `2024`
- **Exemples invalides** :
  - `24` (trop court)
  - `20245` (trop long)
  - ` 2024 ` (espaces)
  - `` (vide)

---

### **2. ID Client (`id_client`)**

- **Format** : String non vide (minimum 1 caractère)
- **Exemple valide** : `65a1b2c3d4e5f6789abcdef0`
- **Exemples invalides** :
  - `` (vide)
  - ` ` (espaces uniquement)

**Pour obtenir un ID client valide** :
- Exécutez : `python get_client_id.py`
- Ou faites : `GET http://localhost:5000/api/v1/clients/`

---

### **3. Date de Début (`date_debut`)**

- **Format** : `YYYY-MM-DD` (exactement)
- **Exemple valide** : `2024-01-01`
- **Exemples invalides** :
  - `01/01/2024` (mauvais séparateur)
  - `2024-1-1` (mois/jour sans zéro)
  - `24-01-01` (année sur 2 chiffres)
  - `2024-13-01` (mois invalide)
  - `2024-01-32` (jour invalide)

---

### **4. Date de Fin (`date_fin`)**

- **Format** : `YYYY-MM-DD` (exactement)
- **Exemple valide** : `2024-12-31`
- **Exemples invalides** :
  - `31/12/2024` (mauvais séparateur)
  - `2024-12-31 ` (espaces)
  - `2024-12-1` (jour sans zéro)

**Important** : La date de fin doit être **postérieure** à la date de début.

---

## 📝 **Exemple de Configuration Insomnia**

Dans Insomnia, configurez les champs comme suit :

| Key | Type | Value |
|-----|------|-------|
| `files[]` | File | BG 2024.xlsx |
| `files[]` | File | BG 2023.xlsx |
| `annee_auditee` | Text | `2024` |
| `id_client` | Text | `65a1b2c3d4e5f6789abcdef0` |
| `date_debut` | Text | `2024-01-01` |
| `date_fin` | Text | `2024-12-31` |

---

## ⚠️ **Erreurs Courantes**

### **Erreur 1 : Année invalide**

```json
{
  "error": "L'année doit faire exactement 4 caractères (ex: 2024)"
}
```

**Solution** : Utilisez exactement 4 chiffres, ex: `2024` (pas `24`, pas `20245`)

---

### **Erreur 2 : ID Client vide**

```json
{
  "error": "L'ID du client ne peut pas être vide"
}
```

**Solution** : 
1. Obtenez un ID client valide : `python get_client_id.py`
2. Copiez l'ID et utilisez-le dans le champ `id_client`

---

### **Erreur 3 : Format de date invalide**

```json
{
  "error": "La date doit être au format YYYY-MM-DD (ex: 2024-01-01)"
}
```

**Solution** : Utilisez le format `YYYY-MM-DD` :
- ✅ `2024-01-01`
- ❌ `01/01/2024`
- ❌ `2024-1-1`
- ❌ `24-01-01`

---

### **Erreur 4 : Date de fin antérieure à la date de début**

```json
{
  "error": "La date de début doit être antérieure à la date de fin"
}
```

**Solution** : Assurez-vous que `date_fin` est postérieure à `date_debut`

---

## ✅ **Checklist de Validation**

Avant d'envoyer la requête, vérifiez :

- [ ] `annee_auditee` = 4 chiffres exactement (ex: `2024`)
- [ ] `id_client` = ID valide non vide (ex: `65a1b2c3d4e5f6789abcdef0`)
- [ ] `date_debut` = Format `YYYY-MM-DD` (ex: `2024-01-01`)
- [ ] `date_fin` = Format `YYYY-MM-DD` (ex: `2024-12-31`)
- [ ] `date_fin` > `date_debut`
- [ ] Aucun espace avant/après les valeurs
- [ ] Les fichiers sont bien sélectionnés

---

## 🧪 **Exemple Complet Valide**

```json
{
  "files[]": [fichier1.xlsx, fichier2.xlsx],
  "annee_auditee": "2024",
  "id_client": "65a1b2c3d4e5f6789abcdef0",
  "date_debut": "2024-01-01",
  "date_fin": "2024-12-31"
}
```

---

## 📞 **Si vous avez encore des erreurs**

1. **Vérifiez les formats** ci-dessus
2. **Copiez-collez** exactement les valeurs (sans espaces)
3. **Vérifiez** que l'ID client existe dans la base de données
4. **Regardez** les messages d'erreur détaillés dans la réponse JSON





