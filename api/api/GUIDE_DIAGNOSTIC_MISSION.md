# 🔍 Guide de Diagnostic - API Mission

## ❌ **Le test ne passe pas**

Voici un guide complet pour identifier et résoudre le problème.

---

## 🧪 **Étape 1 : Exécuter le Script de Diagnostic**

Exécutez le script de diagnostic complet :

```bash
cd api
python diagnostic_mission_api.py
```

Ce script vérifie :
- ✅ Si le serveur Flask est démarré
- ✅ Si l'endpoint moderne `/api/v1/missions/` existe
- ✅ Si l'endpoint legacy `/cors/mission/nouvelle_mission` existe
- ✅ Liste toutes les routes disponibles

---

## 🔍 **Étape 2 : Vérifier les Logs du Serveur**

### **Au Démarrage du Serveur**

Vous devriez voir dans les logs :

```
✅ Routes enregistrées:
   📋 Missions modernes: /api/v1/missions/
   📋 Missions compatibilité: /cors/mission/
```

### **Si vous ne voyez pas "📋 Missions modernes"**

Le blueprint n'est pas enregistré. Vérifiez :
1. Que `from src.resources.mission_resources import MissionResource` est dans `src/routes/__init__.py`
2. Que `app.register_blueprint(mission_bp)` est appelé

---

## 🔍 **Étape 3 : Tester l'Endpoint Directement**

### **Test 1 : Vérifier que l'endpoint existe**

```bash
curl -X POST http://localhost:5000/api/v1/missions/
```

**Résultat attendu** : `400 Bad Request` (normal, données manquantes)

**Si vous obtenez 404** : L'endpoint n'est pas enregistré

---

### **Test 2 : Tester avec des données minimales**

```bash
curl -X POST http://localhost:5000/api/v1/missions/ \
  -F "annee_auditee=2024" \
  -F "id_client=test" \
  -F "date_debut=2024-01-01" \
  -F "date_fin=2024-12-31"
```

**Résultat attendu** : `400 Bad Request` avec message "Au moins 2 fichiers..."

**Si vous obtenez 404** : L'endpoint n'existe pas

**Si vous obtenez 500** : Vérifiez les logs du serveur pour l'erreur

---

## 🔍 **Étape 4 : Vérifier les Imports**

Vérifiez que tous les imports fonctionnent :

```python
python -c "from src.resources.mission_resources import MissionResource; print('✅ Import réussi')"
```

Si cela échoue, il y a un problème d'import.

---

## 🔍 **Étape 5 : Vérifier dans Insomnia**

### **Configuration à Vérifier**

1. **URL** : `http://localhost:5000/api/v1/missions/`
   - ⚠️ Pas de `/` à la fin (ou avec, ça devrait marcher aussi)
   - ⚠️ Vérifiez qu'il n'y a pas d'espaces

2. **Method** : `POST`

3. **Body Type** : `Multipart Form` (pas JSON, pas Form URL Encoded)

4. **Champs** :
   ```
   files[] (File) : Balance_2024.xlsx
   files[] (File) : Balance_2023.xlsx
   annee_auditee (Text) : 2024
   id_client (Text) : 65a1b2c3d4e5f6789abcdef0
   date_debut (Text) : 2024-01-01
   date_fin (Text) : 2024-12-31
   ```

5. **Headers** :
   - ⚠️ Ne pas ajouter `Content-Type` manuellement
   - Laissez Insomnia gérer automatiquement

---

## 🔍 **Étape 6 : Vérifier les Erreurs dans les Logs**

### **Lors de la Requête, Regardez les Logs du Serveur**

#### **Si vous voyez une erreur d'import :**
```
ImportError: cannot import name 'MissionResource' from 'src.resources.mission_resources'
```

**Solution** : Vérifiez que le fichier `src/resources/mission_resources.py` existe et contient `MissionResource`

---

#### **Si vous voyez une erreur de base de données :**
```
RuntimeError: Base de données non connectée
```

**Solution** : 
- Vérifiez que MongoDB est démarré
- Vérifiez les logs au démarrage du serveur Flask

---

#### **Si vous voyez une erreur de validation :**
```
ValidationError: Erreurs de validation: ...
```

**Solution** : Vérifiez que tous les champs sont au bon format :
- `annee_auditee` : 4 chiffres (ex: "2024")
- `date_debut` : Format YYYY-MM-DD
- `date_fin` : Format YYYY-MM-DD
- `date_debut` < `date_fin`

---

## 🔍 **Étape 7 : Vérifier le Format de Réponse**

### **Dans Insomnia, Regardez la Réponse Complète**

#### **Si vous obtenez 404 :**
```json
{
  "error": "404 Not Found"
}
```

**Problème** : L'endpoint n'est pas enregistré

**Solution** :
1. Vérifiez les logs au démarrage
2. Vérifiez que `app.register_blueprint(mission_bp)` est appelé
3. Redémarrez le serveur

---

#### **Si vous obtenez 400 avec "Tous les champs sont requis" :**
```json
{
  "success": false,
  "error": "Tous les champs sont requis"
}
```

**Problème** : Des champs manquent ou ne sont pas envoyés correctement

**Solution** :
1. Vérifiez que tous les champs sont présents dans Insomnia
2. Vérifiez que les noms des champs sont exacts :
   - `files[]` (pas `files`)
   - `id_client` (pas `id`)
   - `annee_auditee`
   - `date_debut`
   - `date_fin`

---

#### **Si vous obtenez 400 avec "Au moins 2 fichiers..." :**
```json
{
  "success": false,
  "error": "Au moins 2 fichiers de balance sont requis (N et N-1)"
}
```

**Problème** : Les fichiers ne sont pas envoyés correctement

**Solution** :
1. Vérifiez que vous avez sélectionné 2 fichiers dans Insomnia
2. Vérifiez que les fichiers sont bien des fichiers Excel (.xlsx)
3. Vérifiez que les champs `files[]` sont de type `File` (pas `Text`)

---

#### **Si vous obtenez 500 Internal Server Error :**
```json
{
  "success": false,
  "error": "Erreur serveur: ..."
}
```

**Problème** : Erreur dans le code Python

**Solution** :
1. Regardez les logs du serveur Flask pour l'erreur complète
2. Notez le message d'erreur exact
3. Vérifiez que MongoDB est démarré
4. Vérifiez que tous les imports fonctionnent

---

## 🔍 **Étape 8 : Vérifier le Frontend**

### **Dans la Console du Navigateur (F12)**

Regardez les erreurs dans la console :

#### **Si vous voyez 404 :**
```
POST http://localhost:5000/api/v1/missions/ 404 (Not Found)
```

**Problème** : L'endpoint n'existe pas ou l'URL est incorrecte

**Solution** : Vérifiez que l'endpoint est enregistré

---

#### **Si vous voyez CORS Error :**
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**Problème** : Problème de CORS

**Solution** : Vérifiez la configuration CORS dans `config.py`

---

## 🛠️ **Checklist Complète**

- [ ] Serveur Flask démarré
- [ ] MongoDB démarré
- [ ] Routes enregistrées dans les logs (voir "📋 Missions modernes")
- [ ] Script de diagnostic exécuté et passé
- [ ] URL correcte dans Insomnia : `http://localhost:5000/api/v1/missions/`
- [ ] Method : `POST`
- [ ] Body Type : `Multipart Form`
- [ ] Au moins 2 fichiers sélectionnés
- [ ] Tous les champs textuels remplis
- [ ] Format des dates : YYYY-MM-DD
- [ ] ID client valide (existe dans la base de données)
- [ ] Aucun header `Content-Type` ajouté manuellement

---

## 📞 **Informations à Fournir**

Si le problème persiste, fournissez :

1. **Le résultat du script de diagnostic** : `python diagnostic_mission_api.py`
2. **Les logs du serveur Flask** au démarrage
3. **Les logs du serveur Flask** lors de la requête
4. **La réponse complète** d'Insomnia (code HTTP + body)
5. **Les erreurs dans la console du navigateur** (si testé depuis le frontend)

---

## 💡 **Solutions Rapides**

### **Solution 1 : Redémarrer le Serveur**

Parfois, un simple redémarrage résout les problèmes :

```bash
# Arrêter le serveur (Ctrl+C)
# Redémarrer
python app.py
```

---

### **Solution 2 : Vérifier les Imports**

```bash
cd api
python -c "from src.resources.mission_resources import MissionResource; print('OK')"
python -c "from src.services.mission_services import MissionService; print('OK')"
python -c "from src.schemas.mission_schemas import MissionCreateSchema; print('OK')"
```

Si l'un de ces échoue, il y a un problème d'import.

---

### **Solution 3 : Utiliser l'API Legacy Temporairement**

Si l'API moderne ne fonctionne pas, utilisez l'API legacy :

```
POST http://localhost:5000/cors/mission/nouvelle_mission
Champ: id (au lieu de id_client)
```

---

## 🔧 **Fichiers à Vérifier**

Si rien ne fonctionne, vérifiez ces fichiers :

1. ✅ `src/routes/__init__.py` - Les routes sont-elles enregistrées ?
2. ✅ `src/resources/mission_resources.py` - Le fichier existe-t-il ?
3. ✅ `src/services/mission_services.py` - Le fichier existe-t-il ?
4. ✅ `src/schemas/mission_schemas.py` - Le fichier existe-t-il ?
5. ✅ `app.py` - Utilise-t-il `register_routes(app)` ?





