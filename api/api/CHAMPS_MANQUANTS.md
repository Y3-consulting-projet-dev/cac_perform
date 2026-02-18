# ⚠️ Erreur : Champs Manquants dans Insomnia

## ❌ **Erreur Reçue**

```json
{
  "success": false,
  "error": "L'année auditée est requise"
}
```

---

## 🔍 **Diagnostic**

Cette erreur signifie que le champ `annee_auditee` n'est **pas reçu** par le serveur ou est **vide**.

---

## ✅ **Solution : Vérifier les Champs dans Insomnia**

### **1. Vérifier que tous les champs sont présents**

Dans Insomnia, dans l'onglet **Body** → **Multipart Form**, vous devez avoir **exactement 6 champs** :

| # | Key | Type | Value |
|---|-----|------|-------|
| 1 | `files[]` | **File** | [Fichier sélectionné] |
| 2 | `files[]` | **File** | [Fichier sélectionné] |
| 3 | `annee_auditee` | **Text** | `2024` |
| 4 | `id_client` | **Text** | `65a1b2c3d4e5f6789abcdef0` |
| 5 | `date_debut` | **Text** | `2024-01-01` |
| 6 | `date_fin` | **Text** | `2024-12-31` |

---

### **2. Vérifier le nom des champs**

Les noms des champs doivent être **exactement** :
- `annee_auditee` (pas `annee`, pas `année_auditée`, pas `anneeAuditee`)
- `id_client` (pas `idClient`, pas `client_id`)
- `date_debut` (pas `dateDebut`, pas `date_debut_mission`)
- `date_fin` (pas `dateFin`, pas `date_fin_mission`)

---

### **3. Vérifier que les valeurs ne sont pas vides**

- ✅ `annee_auditee` : `2024` (pas vide, pas seulement des espaces)
- ✅ `id_client` : Un ID valide (pas vide)
- ✅ `date_debut` : `2024-01-01` (pas vide)
- ✅ `date_fin` : `2024-12-31` (pas vide)

---

### **4. Vérifier le Type des champs**

- Les fichiers : **Type = File**
- Les données : **Type = Text** (pas File, pas autre chose)

---

## 🔍 **Debug : Vérifier ce qui est reçu**

Après avoir envoyé la requête, regardez les **logs du serveur Flask**. Vous devriez voir :

```
🔍 DEBUG - Données reçues:
  - annee_auditee: '2024' (type: <class 'str'>)
  - id_client: '65a1b2c3d4e5f6789abcdef0' (type: <class 'str'>)
  - date_debut: '2024-01-01' (type: <class 'str'>)
  - date_fin: '2024-12-31' (type: <class 'str'>)
  - Toutes les clés de request.form: ['annee_auditee', 'id_client', 'date_debut', 'date_fin']
```

**Si vous voyez** :
- `annee_auditee: None` ou `annee_auditee: ''` → Le champ n'est pas envoyé ou est vide
- `clés de request.form: []` → Aucun champ de formulaire n'est reçu

---

## ✅ **Checklist de Vérification**

Avant d'envoyer la requête, vérifiez dans Insomnia :

- [ ] Body Type = **Multipart Form**
- [ ] Vous avez **6 champs** dans le tableau
- [ ] Le champ `annee_auditee` existe avec **Type = Text**
- [ ] La valeur de `annee_auditee` est `2024` (pas vide)
- [ ] Le champ `id_client` existe avec **Type = Text**
- [ ] La valeur de `id_client` est un ID valide (pas vide)
- [ ] Le champ `date_debut` existe avec **Type = Text**
- [ ] La valeur de `date_debut` est `2024-01-01` (pas vide)
- [ ] Le champ `date_fin` existe avec **Type = Text**
- [ ] La valeur de `date_fin` est `2024-12-31` (pas vide)

---

## 🛠️ **Actions Correctives**

### **Si le champ n'existe pas :**

1. Dans Insomnia, cliquez sur **"Add"** ou **"+"**
2. **Key** : `annee_auditee` (exactement ce nom)
3. **Type** : `Text`
4. **Value** : `2024`

### **Si le champ existe mais est vide :**

1. Cliquez sur le champ dans le tableau
2. Vérifiez que la colonne **Value** contient bien `2024`
3. Si vide, tapez `2024` dans la colonne Value

### **Si le nom du champ est incorrect :**

1. Supprimez le champ avec le mauvais nom
2. Créez un nouveau champ avec le bon nom : `annee_auditee`

---

## 📋 **Configuration Complète Correcte**

Voici la configuration exacte à avoir dans Insomnia :

```
┌──────────────────┬────────┬──────────────────────────────┐
│ Key              │ Type   │ Value                        │
├──────────────────┼────────┼──────────────────────────────┤
│ files[]          │ File   │ C:\Users\...\BG 2024.xlsx   │
│ files[]          │ File   │ C:\Users\...\BG 2023.xlsx   │
│ annee_auditee    │ Text   │ 2024                         │
│ id_client        │ Text   │ 65a1b2c3d4e5f6789abcdef0     │
│ date_debut       │ Text   │ 2024-01-01                    │
│ date_fin         │ Text   │ 2024-12-31                    │
└──────────────────┴────────┴──────────────────────────────┘
```

---

## 🆘 **Si ça ne fonctionne toujours pas**

1. **Faites une capture d'écran** de votre configuration Insomnia (onglet Body)
2. **Regardez les logs du serveur** et copiez les lignes avec `🔍 DEBUG`
3. **Vérifiez** que le serveur Flask est bien démarré

Les messages d'erreur incluent maintenant des informations de debug pour vous aider à identifier le problème.





