# 📅 Format des Dates - Guide Final

## ❌ **Erreur Reçue**

```json
{
  "success": false,
  "error": "Erreurs de validation: {'date_debut': ['La date doit être au format YYYY-MM-DD (ex: 2024-01-01)'], 'date_fin': ['La date doit être au format YYYY-MM-DD (ex: 2024-12-31)']}"
}
```

---

## ✅ **Format Requis**

Les dates doivent être au format : **`YYYY-MM-DD`**

### **Exemples Valides :**
- ✅ `2024-01-01`
- ✅ `2024-12-31`
- ✅ `2023-06-15`

### **Exemples Invalides :**
- ❌ `01/01/2024` (mauvais séparateur)
- ❌ `2024-1-1` (mois/jour sans zéro)
- ❌ `24-01-01` (année sur 2 chiffres)
- ❌ `2024-01-01 ` (espace à la fin)
- ❌ ` 2024-01-01` (espace au début)

---

## 🔧 **Configuration dans Insomnia**

Dans Insomnia, pour les champs de dates :

| Key | Type | Value |
|-----|------|-------|
| `date_debut` | Text | `2024-01-01` |
| `date_fin` | Text | `2024-12-31` |

**Points importants :**
- ✅ Format : `YYYY-MM-DD`
- ✅ Séparateur : tiret `-` (pas `/`, pas `.`)
- ✅ Année : 4 chiffres
- ✅ Mois : 2 chiffres (avec zéro si nécessaire)
- ✅ Jour : 2 chiffres (avec zéro si nécessaire)
- ✅ Pas d'espaces avant ou après

---

## 🛠️ **Conversion Automatique**

Le code essaie maintenant de convertir automatiquement certains formats courants :

- `YYYY/MM/DD` → `YYYY-MM-DD`
- `DD/MM/YYYY` → `YYYY-MM-DD`
- `DD-MM-YYYY` → `YYYY-MM-DD`
- `YYYY.MM.DD` → `YYYY-MM-DD`

Mais il est **recommandé** d'utiliser directement le format `YYYY-MM-DD` dans Insomnia.

---

## 📋 **Checklist**

Avant d'envoyer la requête, vérifiez :

- [ ] `date_debut` = Format `YYYY-MM-DD` (ex: `2024-01-01`)
- [ ] `date_fin` = Format `YYYY-MM-DD` (ex: `2024-12-31`)
- [ ] Pas d'espaces avant ou après les dates
- [ ] Année sur 4 chiffres
- [ ] Mois et jour sur 2 chiffres (avec zéro si nécessaire)
- [ ] Séparateur = tiret `-` (pas `/`)

---

## 🔍 **Debug**

Si vous avez toujours des erreurs, regardez les logs du serveur. Vous devriez voir :

```
🔍 DEBUG - Dates avant nettoyage:
  - date_debut (raw): '2024-01-01' (type: <class 'str'>)
  - date_fin (raw): '2024-12-31' (type: <class 'str'>)
  - date_debut (clean): '2024-01-01'
  - date_fin (clean): '2024-12-31'
```

Si vous voyez des formats incorrects, le code essaiera de les convertir automatiquement.

---

## ✅ **Exemple Complet Correct**

Dans Insomnia, votre configuration devrait être :

```
┌──────────────────┬────────┬──────────────────────────────┐
│ Key              │ Type   │ Value                        │
├──────────────────┼────────┼──────────────────────────────┤
│ files[]          │ File   │ BG 2024.xlsx                 │
│ files[]          │ File   │ BG 2023.xlsx                 │
│ annee_auditee    │ Text   │ 2024                         │
│ id_client        │ Text   │ 65a1b2c3d4e5f6789abcdef0     │
│ date_debut       │ Text   │ 2024-01-01                    │
│ date_fin         │ Text   │ 2024-12-31                    │
└──────────────────┴────────┴──────────────────────────────┘
```

---

## 🆘 **Si ça ne fonctionne toujours pas**

1. **Vérifiez** les logs du serveur pour voir exactement ce qui est reçu
2. **Copiez-collez** exactement les dates depuis ce document
3. **Vérifiez** qu'il n'y a pas d'espaces avant ou après
4. **Assurez-vous** que le format est exactement `YYYY-MM-DD`

Le code essaie maintenant de convertir automatiquement certains formats, mais il est préférable d'utiliser directement le format `YYYY-MM-DD`.





