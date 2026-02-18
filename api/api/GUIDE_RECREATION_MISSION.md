# 📋 Guide : Recréation d'une mission depuis zéro

## ✅ Étapes recommandées

### 1. Créer un nouveau client
- Allez sur l'interface web
- Créez un nouveau client
- Notez l'ID du client créé (vous pouvez le voir dans l'URL ou dans la console du navigateur)

### 2. Créer une nouvelle mission

**IMPORTANT :** Assurez-vous que vos fichiers Excel sont :
- **Format 6 colonnes** : `Numéro de compte | Libellé | Débit initial | Crédit initial | Débit final | Crédit final`
- **Au moins 2 fichiers** : Balance N et Balance N-1
- **Avec des données valides** : numéros de compte non vides

**Lors de la création de la mission :**
1. Sélectionnez le client créé
2. Entrez l'année auditée (ex: 2024)
3. Entrez les dates de début et fin
4. Uploadez **DEUX fichiers Excel** (Balance N et N-1)
5. Cliquez sur "Créer la mission"

### 3. Vérifier les logs du serveur Flask

**Pendant la création :** Regardez le terminal Flask. Vous devriez voir :
```
Fichiers reçus: [...]
Données reçues: annee=2024, client=..., debut=..., fin=...
📂 Fichier chargé: Balance 2024.xlsx
📊 Format détecté: balance_simple
📊 Traitement format balance simple (6 colonnes)...
📝 En-tête détecté à la ligne X
✅ Balance créée avec succès: X lignes
```

### 4. Vérifier que les balances sont bien créées

**Méthode 1 : Via l'interface web**
- Allez sur l'espace client
- Vérifiez que la mission apparaît
- Le nombre de lignes devrait être affiché (pas 0 !)

**Méthode 2 : Via un script Python**
```powershell
python lister_missions_simple.py
```

Vous devriez voir :
```
💰 Balances: 2 (XXX lignes, XXX lignes)  ← PAS (0 lignes, 0 lignes)
```

### 5. Tester le contrôle d'intangibilité

1. Allez sur la page de la mission
2. Cliquez sur l'onglet "Contrôle d'intangibilité"
3. **Observez IMMÉDIATEMENT le terminal Flask**

**Vous devriez voir :**
```
[ROUTE] GET /controle_intangibilite/XXXXX
[CONTROLE_INTANGIBILITE] ========== DEBUT ==========
[CONTROLE_INTANGIBILITE] Mission ID: XXXXX
[CONTROLE_INTANGIBILITE] Nombre de balances: 2
[CONTROLE_INTANGIBILITE] Indexation des comptes...
[CONTROLE_INTANGIBILITE] Avant indexation: bal_N contient XXX lignes, bal_N1 contient XXX lignes
[INDEX_BY_COMPTE] traitement de XXX lignes
[INDEX_BY_COMPTE] XXX comptes indexes
[CONTROLE_INTANGIBILITE] APRES indexation:
[CONTROLE_INTANGIBILITE]    - Comptes indexes dans N: XXX
[CONTROLE_INTANGIBILITE]    - Comptes indexes dans N-1: XXX
[CONTROLE_INTANGIBILITE] Debut du traitement: XXX comptes en N, XXX comptes en N-1
[CONTROLE_INTANGIBILITE] Apres traitement des comptes N: XXX comptes ajoutes
[CONTROLE_INTANGIBILITE] Rapport sauvegarde dans la base de donnees
[CONTROLE_INTANGIBILITE] Rapport retourne: total_comptes=XXX, ecarts=XXX
[CONTROLE_INTANGIBILITE] ========== FIN (SUCCES) ==========
```

**Dans l'interface web :**
- Le tableau devrait afficher : `⚠️ X écart(s) détecté(s) sur Y compte(s)` avec Y > 0
- Le tableau devrait contenir des lignes de comptes

## 🔍 Points de vérification

### ✅ Balances vides ?
Si vous voyez "0 lignes" après import :
1. Vérifiez les logs du serveur pour voir pourquoi les lignes sont ignorées
2. Vérifiez que vos fichiers Excel ont bien le format attendu
3. Vérifiez que les numéros de compte ne sont pas vides

### ✅ Contrôle d'intangibilité vide ?
Si le contrôle affiche "0 compte(s)" :
1. Vérifiez les logs `[CONTROLE_INTANGIBILITE]`
2. Regardez `[CONTROLE_INTANGIBILITE] APRES indexation:` - les comptes doivent être > 0
3. Si les comptes sont indexés mais le résultat est 0, il y a un problème dans le traitement

## 🛠️ Scripts utiles

### Lister toutes les missions
```powershell
python lister_missions_simple.py
```

### Vérifier une mission spécifique
```powershell
python diagnostic_controle_intangibilite_complet.py <MISSION_ID>
```

### Vérifier le format des balances d'une mission
```powershell
python verifier_format_balances.py <MISSION_ID>
```

## 💡 Astuces

1. **Gardez le terminal Flask ouvert** pendant tous les tests
2. **Créez d'abord une mission de test** avec peu de données pour vérifier rapidement
3. **Vérifiez les logs à chaque étape** - ils vous diront exactement ce qui se passe
4. **Si problème, consultez les logs** - ils contiennent maintenant toutes les informations nécessaires

## ❌ Si ça ne fonctionne toujours pas

1. **Copiez tous les logs du terminal Flask** (tout ce qui commence par `[CONTROLE_INTANGIBILITE]` ou `[INDEX_BY_COMPTE]`)
2. **Notez l'ID de la mission problématique**
3. **Décrivez ce qui s'affiche dans l'interface** vs ce que vous attendez

Les logs vous indiqueront précisément où le problème se situe !









