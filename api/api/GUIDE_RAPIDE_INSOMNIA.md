# ⚡ Guide Rapide - Insomnia - Résoudre l'Erreur

## 🎯 **Configuration Exacte dans Insomnia**

### **Étape 1 : Créer la requête**

1. **Nouvelle requête** → Nommez-la "Créer Mission"
2. **Method** : `POST`
3. **URL** : `http://localhost:5000/api/v1/missions/`
4. **Body** : Sélectionnez `Multipart Form`

---

### **Étape 2 : Ajouter les 8 champs (IMPORTANT : Dans l'ordre)**

Cliquez sur **"Add"** ou **"+"** pour chaque champ :

| # | Key (EXACTEMENT) | Type | Value Exemple |
|---|------------------|------|--------------|
| 1 | `files[]` | **File** | Sélectionner Balance_2024.xlsx |
| 2 | `files[]` | **File** | Sélectionner Balance_2023.xlsx |
| 3 | `annee_auditee` | **Text** | `2024` |
| 4 | `id_client` | **Text** | `67890abcdef1234567890123` ← **OBTENEZ-LE D'ABORD** |
| 5 | `date_debut` | **Text** | `2024-01-01` |
| 6 | `date_fin` | **Text** | `2024-12-31` |
| 7 | `date_debut_mandat` | **Text** | `2024-01-01` |
| 8 | `date_fin_mandat` | **Text** | `2024-12-31` |

---

## ⚠️ **Points Critiques**

### **1. Noms des champs (EXACTS, sans espaces)**

```
✅ CORRECT :
   date_debut_mandat
   date_fin_mandat

❌ INCORRECT :
   date_debut_mandat  (avec espace à la fin)
   dateDebutMandat    (camelCase)
   date_debut_mandat_ (avec underscore à la fin)
```

### **2. Format des dates**

```
✅ CORRECT : 2024-01-01
❌ INCORRECT : 01/01/2024, 2024-1-1, 01-01-2024
```

### **3. ID Client (OBLIGATOIRE - Obtenez-le d'abord)**

**Avant de créer la mission, obtenez un ID client valide :**

1. Créez une **nouvelle requête GET** :
   - Method : `GET`
   - URL : `http://localhost:5000/api/v1/clients/`
2. Envoyez la requête
3. Dans la réponse, copiez un `_id` :
   ```json
   {
     "success": true,
     "data": [
       {
         "_id": "67890abcdef1234567890123",  ← COPIEZ CELUI-CI
         "nom": "Client Test"
       }
     ]
   }
   ```
4. Utilisez cet ID dans le champ `id_client`

---

## 🔍 **Si vous recevez une erreur**

### **Regardez le message d'erreur dans Insomnia**

Dans la réponse, vous verrez quelque chose comme :

```json
{
  "success": false,
  "error": "La date de début du mandat est requise",
  "debug": {
    "champs_reçus": ["files[]", "annee_auditee", ...]
  }
}
```

**Vérifiez** :
1. Est-ce que `date_debut_mandat` est dans `champs_reçus` ?
2. Si NON → Vous ne l'avez pas ajouté dans Insomnia
3. Si OUI → Vérifiez qu'il n'y a pas d'espaces dans le nom

---

## ✅ **Checklist Avant d'Envoyer**

- [ ] 8 champs au total (pas 6, pas 10, exactement 8)
- [ ] 2 fichiers Excel sélectionnés
- [ ] `date_debut_mandat` présent (vérifiez l'orthographe)
- [ ] `date_fin_mandat` présent (vérifiez l'orthographe)
- [ ] Toutes les dates au format `YYYY-MM-DD`
- [ ] ID client valide (obtenu via GET /api/v1/clients/)
- [ ] Pas d'espaces dans les noms de champs

---

## 📸 **Exemple Visuel dans Insomnia**

```
┌─────────────────────────────────────────────────────────┐
│ Body: Multipart Form                                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [Add]                                                  │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Key: files[]                    Type: [File ▼]    │ │
│  │ Value: [Sélectionner fichier...]                  │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Key: files[]                    Type: [File ▼]    │ │
│  │ Value: [Sélectionner fichier...]                  │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Key: annee_auditee             Type: [Text ▼]      │ │
│  │ Value: 2024                                        │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Key: id_client                Type: [Text ▼]      │ │
│  │ Value: 67890abcdef1234567890123                    │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Key: date_debut               Type: [Text ▼]      │ │
│  │ Value: 2024-01-01                                  │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Key: date_fin                 Type: [Text ▼]      │ │
│  │ Value: 2024-12-31                                  │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Key: date_debut_mandat        Type: [Text ▼]      │ │
│  │ Value: 2024-01-01                                  │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Key: date_fin_mandat          Type: [Text ▼]      │ │
│  │ Value: 2024-12-31                                  │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🆘 **Erreurs Fréquentes**

### **"La date de début du mandat est requise"**

**Cause** : Le champ `date_debut_mandat` n'est pas présent ou est vide

**Solution** :
1. Vérifiez que vous avez bien ajouté le champ
2. Vérifiez l'orthographe : `date_debut_mandat` (pas `date_debut_mandat ` avec espace)
3. Vérifiez que la valeur n'est pas vide

---

### **"Client avec l'ID 'xxx' introuvable"**

**Cause** : L'ID client n'existe pas dans la base de données

**Solution** :
1. Obtenez un ID valide : `GET http://localhost:5000/api/v1/clients/`
2. Copiez un `_id` de la réponse
3. Utilisez-le dans `id_client`

---

### **"Format de date invalide"**

**Cause** : La date n'est pas au format `YYYY-MM-DD`

**Solution** :
- ✅ Utilisez : `2024-01-01`
- ❌ Pas : `01/01/2024` ou `2024-1-1`

---

## 💡 **Astuce**

Si vous n'êtes pas sûr, **copiez-collez exactement** ces noms de champs dans Insomnia :

```
files[]
files[]
annee_auditee
id_client
date_debut
date_fin
date_debut_mandat
date_fin_mandat
```

---

**Partagez le message d'erreur exact si le problème persiste !** 🚀

