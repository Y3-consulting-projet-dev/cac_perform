# 🐛 Guide de Débogage - API Création Mission

## ❌ **Problème : L'API ne fonctionne pas sur Insomnia**

Voici un guide étape par étape pour identifier et résoudre le problème.

---

## 🔍 **Étape 1 : Vérifier que le serveur Flask est démarré**

### **Vérification**
1. Le serveur Flask doit être en cours d'exécution
2. Vous devriez voir dans les logs :
   ```
   🌐 Serveur démarré sur http://127.0.0.1:5000
   ```

### **Si le serveur n'est pas démarré**
```bash
cd api
python app.py
```

---

## 🔍 **Étape 2 : Vérifier que les routes sont enregistrées**

### **Vérification dans les logs au démarrage**
Vous devriez voir :
```
✅ Routes enregistrées:
   📋 Missions: /cors/mission/
```

### **Si les routes ne sont pas enregistrées**
Vérifiez que dans `src/routes/__init__.py`, il y a :
```python
from src.mission import mission
# ...
app.register_blueprint(mission)
```

---

## 🔍 **Étape 3 : Tester l'endpoint avec cURL**

### **Test simple (sans fichiers)**
```bash
curl -X POST http://localhost:5000/cors/mission/nouvelle_mission \
  -F "annee_auditee=2024" \
  -F "id=test" \
  -F "date_debut=2024-01-01" \
  -F "date_fin=2024-12-31"
```

**Réponse attendue** : Erreur 400 avec message "Au moins 2 fichiers de balance sont requis"

Si vous obtenez **404 Not Found**, l'endpoint n'est pas enregistré.

---

## 🔍 **Étape 4 : Vérifier la configuration Insomnia**

### **Configuration Correcte**

1. **Method** : `POST`
2. **URL** : `http://localhost:5000/cors/mission/nouvelle_mission`
   - ⚠️ **IMPORTANT** : Pas de `/` à la fin de l'URL
3. **Body Type** : `Multipart Form`
4. **Champs** :
   ```
   files[] (File) : Balance_2024.xlsx
   files[] (File) : Balance_2023.xlsx
   annee_auditee (Text) : 2024
   id (Text) : 65a1b2c3d4e5f6789abcdef0
   date_debut (Text) : 2024-01-01
   date_fin (Text) : 2024-12-31
   ```

### **Erreurs Communes**

#### **❌ Erreur 404 Not Found**
- **Cause** : L'endpoint n'existe pas ou n'est pas enregistré
- **Solution** : Vérifier que le blueprint mission est enregistré dans `src/routes/__init__.py`

#### **❌ Erreur 405 Method Not Allowed**
- **Cause** : La méthode HTTP est incorrecte
- **Solution** : Utiliser `POST` (pas `GET`, `PUT`, etc.)

#### **❌ Erreur 400 Bad Request - "Tous les champs sont requis"**
- **Cause** : Un ou plusieurs champs manquent
- **Solution** : Vérifier que tous les champs sont présents :
  - `files[]` (au moins 2 fichiers)
  - `annee_auditee`
  - `id`
  - `date_debut`
  - `date_fin`

#### **❌ Erreur 500 Internal Server Error**
- **Cause** : Erreur dans le code Python
- **Solution** : Vérifier les logs du serveur Flask pour voir l'erreur exacte

---

## 🔍 **Étape 5 : Vérifier les logs du serveur Flask**

### **Lors de l'envoi de la requête, vous devriez voir :**
```
INFO:werkzeug:127.0.0.1 - - [DATE] "POST /cors/mission/nouvelle_mission HTTP/1.1" 200 -
```

### **Si vous voyez 404 :**
```
INFO:werkzeug:127.0.0.1 - - [DATE] "POST /cors/mission/nouvelle_mission HTTP/1.1" 404 -
```
→ L'endpoint n'est pas enregistré

### **Si vous voyez une erreur Python :**
```
Traceback (most recent call last):
  ...
```
→ Notez l'erreur exacte et corrigez-la

---

## 🔍 **Étape 6 : Vérifier la structure de l'application**

### **Vérifier que `app.py` utilise le bon système de routes**

Dans `app.py`, il devrait y avoir :
```python
from src.routes import register_routes
# ...
register_routes(app)
```

### **Vérifier que `src/routes/__init__.py` enregistre le blueprint mission**

Il devrait y avoir :
```python
from src.mission import mission
# ...
app.register_blueprint(mission)
```

---

## 🧪 **Test Rapide avec Python**

Créez un fichier `test_mission_api.py` :

```python
import requests

url = "http://localhost:5000/cors/mission/nouvelle_mission"

# Test sans fichiers (devrait retourner erreur 400)
response = requests.post(url, data={
    'annee_auditee': '2024',
    'id': 'test',
    'date_debut': '2024-01-01',
    'date_fin': '2024-12-31'
})

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
```

**Si vous obtenez 404** : L'endpoint n'est pas enregistré
**Si vous obtenez 400** : L'endpoint fonctionne, mais les données sont invalides (normal sans fichiers)

---

## 📋 **Checklist de Vérification**

- [ ] Le serveur Flask est démarré
- [ ] Les routes sont enregistrées (voir logs au démarrage)
- [ ] L'URL dans Insomnia est correcte : `http://localhost:5000/cors/mission/nouvelle_mission`
- [ ] La méthode est `POST`
- [ ] Le Body Type est `Multipart Form`
- [ ] Tous les champs sont présents
- [ ] Les fichiers sont bien sélectionnés
- [ ] Les logs du serveur montrent la requête reçue

---

## 💡 **Solution Rapide**

Si rien ne fonctionne, essayez cette URL alternative (si elle existe) :
```
POST http://localhost:5000/mission/nouvelle_mission
```

Ou vérifiez toutes les routes disponibles :
```bash
curl http://localhost:5000/api/info
```

---

## 📞 **Informations à Fournir pour le Débogage**

Si le problème persiste, fournissez :
1. **L'erreur exacte** renvoyée par Insomnia (code HTTP + message)
2. **Les logs du serveur Flask** lors de la requête
3. **La configuration exacte** dans Insomnia (URL, méthode, body)
4. **Le résultat de** : `curl http://localhost:5000/health`

