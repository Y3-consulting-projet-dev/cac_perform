# 🚀 Guide Insomnia - Création de Mission (Version Simplifiée)

## ⚠️ **Erreur Courante**
```
{
  "success": false,
  "error": "Au moins 2 fichiers de balance sont requis (N et N-1)"
}
```

---

## ✅ **Solution Rapide**

### **1. Configuration de la Requête**

- **Méthode** : `POST`
- **URL** : `http://localhost:5000/api/v1/missions/`
- **Body Type** : `Multipart Form` ⚠️ **IMPORTANT**

### **2. Ajouter les Champs**

Dans Insomnia, dans l'onglet **Body** → **Multipart Form**, ajoutez **exactement** ces champs :

| Key | Type | Value |
|-----|------|-------|
| `files[]` | **File** | Sélectionnez votre premier fichier Excel |
| `files[]` | **File** | Sélectionnez votre deuxième fichier Excel |
| `annee_auditee` | **Text** | `2024` |
| `id_client` | **Text** | `VOTRE_ID_CLIENT` (remplacez par un ID valide) |
| `date_debut` | **Text** | `2024-01-01` |
| `date_fin` | **Text** | `2024-12-31` |

### **3. Points Critiques**

✅ **Body Type doit être "Multipart Form"** (pas Form URL Encoded, pas JSON)

✅ **Deux champs avec le même nom `files[]`** (Insomnia permet cela)

✅ **Type = File** pour les deux fichiers (pas Text)

✅ **Les fichiers doivent être sélectionnés** (le chemin apparaît dans Value)

---

## 🔍 **Vérification**

Après avoir envoyé la requête, regardez les **logs du serveur Flask**. Vous devriez voir :

```
🔍 DEBUG - Tous les clés de request.files: ['files[]', 'files[]']
🔍 DEBUG - Total fichiers reçus: 2
  📄 Fichier 1: Balance_2024.xlsx
  📄 Fichier 2: Balance_2023.xlsx
```

Si vous voyez `Total fichiers reçus: 0`, c'est que les fichiers ne sont pas envoyés correctement.

---

## 🛠️ **Si ça ne fonctionne toujours pas**

### **Option 1: Vérifier les logs du serveur**

Les logs vous diront exactement ce qui est reçu. Cherchez les lignes qui commencent par `🔍 DEBUG`.

### **Option 2: Tester avec le script Python**

Exécutez le script de test :
```bash
python test_mission_api_debug.py
```

Ce script teste l'API avec des fichiers réels et affiche les erreurs détaillées.

### **Option 3: Vérifier l'ID client**

Assurez-vous que l'ID client existe dans la base de données. Vous pouvez :
1. Lister les clients : `GET http://localhost:5000/api/v1/clients/`
2. Copier un ID client valide
3. L'utiliser dans votre requête

---

## 📝 **Exemple Visuel**

Voici à quoi devrait ressembler votre configuration dans Insomnia :

```
┌─────────────────────────────────────────────────────────────┐
│ POST http://localhost:5000/api/v1/missions/                │
├─────────────────────────────────────────────────────────────┤
│ Body: Multipart Form                                         │
│                                                              │
│ ┌──────────────┬────────┬────────────────────────────────┐ │
│ │ Key          │ Type   │ Value                          │ │
│ ├──────────────┼────────┼────────────────────────────────┤ │
│ │ files[]      │ File   │ C:\...\Balance_2024.xlsx       │ │
│ │ files[]      │ File   │ C:\...\Balance_2023.xlsx       │ │
│ │ annee_auditee│ Text   │ 2024                           │ │
│ │ id_client    │ Text   │ 65a1b2c3d4e5f6789abcdef0       │ │
│ │ date_debut   │ Text   │ 2024-01-01                     │ │
│ │ date_fin     │ Text   │ 2024-12-31                     │ │
│ └──────────────┴────────┴────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ **Réponse Attendue**

Si tout fonctionne, vous devriez recevoir :

```json
{
  "success": true,
  "message": "Mission créée avec succès",
  "data": {
    "_id": "...",
    "annee_auditee": "2024",
    "id_client": "...",
    ...
  }
}
```

avec un **statut HTTP 201**.

