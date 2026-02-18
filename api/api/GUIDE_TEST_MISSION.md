# 🧪 Guide pour faire passer le test de création de mission

## ✅ Étapes à suivre

### 1. Vérifier que MongoDB est démarré

**Windows (PowerShell) :**
```powershell
# Vérifier si MongoDB est en cours d'exécution
Get-Service -Name MongoDB

# Si MongoDB n'est pas démarré, le démarrer
Start-Service -Name MongoDB
```

**Alternative :** Vérifiez que MongoDB est accessible sur `localhost:27017`

### 2. Vérifier la configuration de la base de données

Assurez-vous que le fichier `.env` existe et contient :
```env
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB_NAME=cac_perform
```

### 3. Redémarrer le serveur Flask

**Important :** Arrêtez complètement le serveur Flask (Ctrl+C) et redémarrez-le :

```powershell
# Dans le dossier api/
python app.py
# OU
flask run
```

**Vérifiez dans les logs du démarrage :**
Vous devriez voir :
```
✅ Connexion MongoDB établie: localhost:27017/cac_perform
✅ Extensions initialisées avec succès
```

Si vous ne voyez pas ces messages, la base de données n'est pas connectée.

### 4. Tester la création de mission

#### Option A : Depuis Insomnia

1. **Méthode :** `POST`
2. **URL :** `http://localhost:5000/api/v1/missions/`
3. **Body Type :** `Multipart Form`
4. **Champs :**
   - `files[]` : Sélectionnez 2 fichiers Excel de balance (N et N-1)
   - `annee_auditee` : `2024` (4 chiffres)
   - `id_client` : Un ID client valide (ex: `65a1b2c3d4e5f6789abcdef0`)
   - `date_debut` : `2024-01-01` (format YYYY-MM-DD)
   - `date_fin` : `2024-12-31` (format YYYY-MM-DD)

5. **Important :** Vérifiez qu'il n'y a **pas d'espaces** à la fin des noms de champs dans Insomnia

#### Option B : Depuis le frontend

1. Ouvrez l'application frontend
2. Allez sur la page de création de mission
3. Remplissez tous les champs
4. Sélectionnez 2 fichiers Excel
5. Cliquez sur "Créer"

### 5. Vérifier les logs du serveur

**Si l'erreur persiste, regardez les logs du serveur Flask :**

Cherchez ces messages :
- `❌ ERREUR RuntimeError (connexion DB)` → Problème de connexion MongoDB
- `❌ ERREUR DÉTAILLÉE` → Autre erreur (partagez le traceback complet)

## 🔍 Diagnostic des problèmes courants

### Problème 1 : "Base de données non connectée"

**Solution :**
1. Vérifiez que MongoDB est démarré
2. Vérifiez que le fichier `.env` est correct
3. Redémarrez le serveur Flask

### Problème 2 : "name 'db' is not defined"

**Solution :**
1. Redémarrez le serveur Flask (les modifications ont été appliquées)
2. Vérifiez les logs pour voir où exactement l'erreur se produit

### Problème 3 : Erreur 500 sans détails

**Solution :**
1. Regardez les logs du serveur Flask dans le terminal
2. Cherchez les lignes avec `❌ ERREUR`
3. Partagez ces logs pour diagnostic

## 📋 Checklist avant de tester

- [ ] MongoDB est démarré et accessible
- [ ] Le fichier `.env` existe et est correctement configuré
- [ ] Le serveur Flask a été redémarré après les modifications
- [ ] Les logs montrent `✅ Connexion MongoDB établie`
- [ ] Vous avez un ID client valide pour tester
- [ ] Vous avez 2 fichiers Excel de balance valides
- [ ] Les dates sont au format `YYYY-MM-DD`

## 🆘 Si rien ne fonctionne

1. **Partagez les logs complets du serveur Flask** (toutes les lignes avec `❌` ou `⚠️`)
2. **Partagez la réponse JSON complète** de l'API (y compris la section `debug`)
3. **Vérifiez la version de Python** : `python --version` (devrait être 3.8+)

## ✅ Message de succès attendu

Si tout fonctionne, vous devriez recevoir :
```json
{
  "success": true,
  "message": "Mission créée avec succès",
  "data": {
    "_id": "...",
    "mission": { ... }
  }
}
```

Et dans les logs du serveur :
```
✅ Balance insérée en base avec X lignes
✅ Mission créée avec ID: ...
```

