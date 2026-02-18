# 📋 Guide : Comment consulter les logs du serveur Flask

## 📍 Où sont les logs ?

Les logs du serveur Flask s'affichent **dans le terminal où vous avez lancé le serveur**.

## 🚀 Étapes pour voir les logs

### 1. Ouvrir un terminal PowerShell

Ouvrez PowerShell dans le dossier `api` :

```powershell
cd D:\Documents\cac-perform\cac-perform\cac-perform\cac-perform-main\api
```

### 2. Activer l'environnement virtuel (si nécessaire)

```powershell
.\virtualenv\Scripts\activate
```

### 3. Lancer le serveur Flask

```powershell
python app.py
```

### 4. Observer les logs en temps réel

Une fois le serveur lancé, vous verrez dans le terminal :
- Les messages de démarrage du serveur
- Tous les `print()` de votre code Python
- Les requêtes HTTP reçues (dates, méthodes, URLs)
- Les erreurs Python avec stack traces complètes

**Exemple de ce que vous devriez voir :**

```
Server de développement lancée
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production setting.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!

🔍 Contrôle intangibilité pour mission 690237d33b694de2f40f4329
📊 Nombre de balances: 2
📊 Avant indexation: bal_N contient 271 lignes, bal_N1 contient 233 lignes
📊 _index_by_compte: traitement de 271 lignes
✅ _index_by_compte: 271 comptes indexés
...
```

## 🔍 Ce que chercher dans les logs

Quand vous cliquez sur le contrôle d'intangibilité dans l'interface, cherchez ces messages dans le terminal :

1. **Messages de démarrage :**
   - `🔍 Contrôle intangibilité pour mission ...`
   - `📊 Nombre de balances: ...`

2. **Messages d'indexation :**
   - `📊 Avant indexation: bal_N contient X lignes`
   - `📊 _index_by_compte: traitement de X lignes`
   - `✅ _index_by_compte: X comptes indexés`
   - `📊 APRÈS indexation: Comptes indexés dans N: X`

3. **Messages de traitement :**
   - `🔍 Début du traitement: X comptes en N, Y comptes en N-1`
   - `📊 Après traitement des comptes N: X comptes ajoutés`
   - `📊 Résumé final: X comptes traités`

4. **Messages d'erreur (si problème) :**
   - `❌ ERREUR CRITIQUE: tous_comptes est vide avant sauvegarde!`
   - `⚠️  Erreur lors du traitement du compte ...`
   - `❌ Erreur dans controle_intangibilite: ...`

## ⚠️ Problèmes courants

### Le terminal n'affiche rien ?
- Vérifiez que le serveur est bien lancé (`python app.py`)
- Vérifiez que vous êtes dans le bon terminal (celui qui a lancé Flask)
- Vérifiez qu'il n'y a pas d'erreur au démarrage

### Les logs sont tronqués ou illisibles ?
- En Windows, le problème peut venir de l'encodage UTF-8
- Essayez de changer l'encodage de PowerShell :
  ```powershell
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  ```

## 💡 Astuce : Rediriger les logs vers un fichier

Si vous voulez sauvegarder les logs dans un fichier :

```powershell
python app.py 2>&1 | Tee-Object -FilePath "logs_server.txt"
```

Les logs seront affichés dans le terminal ET sauvegardés dans `logs_server.txt`.

## 🔄 Forcer la réexécution du contrôle

Pour forcer le contrôle d'intangibilité à se réexécuter :

1. Gardez le terminal des logs ouvert
2. Allez sur l'interface web
3. Cliquez sur l'onglet "Contrôle d'intangibilité"
4. Observez immédiatement les logs dans le terminal

Les messages que j'ai ajoutés (avec emojis 📊, ✅, ❌) apparaîtront en temps réel !









