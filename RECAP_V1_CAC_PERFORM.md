# Recap V1 — CAC Perform

Sep 30, 2026 · @Dala Mariam

CLAUDE.md : absent de la racine et de tout le dépôt (vérifié, aucune occurrence).

## 1. Stack & architecture

**Backend** (`api/`) : Python 3.12, Flask 3, Flask-RESTful, Flask-Cors. Pas d'ORM : accès direct à MongoDB via `pymongo` (+ `flask-mongoengine`/`mongoengine` installés mais peu utilisés en pratique — les données sont manipulées comme des dictionnaires bruts, pas via des classes `Document`). Validation/sérialisation par `marshmallow`. Auth par JWT (`PyJWT`) + `bcrypt` pour les mots de passe. Parsing Excel : `pandas` + `openpyxl`.

**Frontend** (`clients/`) : Vue 3 (Composition API, `<script setup>`), Vite 7, Vue Router 4, Pinia (peu utilisé — un seul store `counter.js` visiblement inutilisé, `auth.js` présent), Tailwind CSS 4, Axios, Chart.js, FontAwesome.

**Base de données** : MongoDB (pas de schéma formel imposé par un ORM). Base `cac_perform`, collections principales : `Personnel` (comptes utilisateurs, ex-`Manager`), `Client_db`, `Mission1`, `Balance`, `Collaborateur` (existe mais vide, non utilisée).

**Arborescence principale**

| Dossier | Rôle |
| --- | --- |
| `api/src/routes/` | Point central d'enregistrement de tous les blueprints Flask actifs |
| `api/src/resources/` | Contrôleurs HTTP (parsing requête, appel service, réponse JSON) pour clients/users/missions |
| `api/src/services/` | Logique métier : `client_services.py`, `mission_services.py`, `user_services.py` |
| `api/src/schemas/` | Schémas `marshmallow` (validation + sérialisation) |
| `api/src/mission/` | Blueprint historique `mission` (préfixe `/cors/mission`) : la majorité des routes du workflow d'audit |
| `api/src/model.py` | Fichier historique volumineux (\~7800 lignes) : logique métier ancienne pour clients/missions, toujours utilisé par plusieurs routes |
| `api/src/model_controle_intangibilite.py`, `model_revue.py` | Logique des contrôles d'intangibilité et de la revue analytique |
| `api/src/customer/`, `api/src/collaborateur/` | Blueprints **non enregistrés** dans l'app (code mort, voir section 9) |
| `api/config.py` | Connexion Mongo, initialisation des collections au premier démarrage |
| `clients/src/views/` | Une vue par écran (ClientsView, MissionsView, NewClient, NewMission, GroupingAnalyse…) |
| `clients/src/components/` | Composants réutilisés par `GroupingAnalyse.vue` (tableaux EFI, grouping, analyses) |
| `clients/src/api/` | 3 fichiers seulement (`auth.api.js`, `grouping.api.js`, `index.js`) — la plupart des vues appellent axios directement, pas via une couche API dédiée |
| `docs/` (racine du dépôt) | Fichiers Excel de balances réelles et JSON de seed (`client_test.json`, `mission_test.json`, `balance_test.json`) |

**Lancement local**

- Backend : `cd api`, créer un venv nommé `virtualenv`, `pip install -r requirements.txt`, démarrer MongoDB, puis `python app.py` (lit `api/.env` : `FLASK_ENV`, `SECRET_KEY`, `MONGO_HOST/PORT/DB_NAME`, `CORS_ORIGINS`).
- Frontend : `cd clients`, `pnpm install`, `pnpm dev` (Vite, port 5173 par défaut). Pas de fichier `.env` requis ; l'URL de l'API est codée en dur (`http://localhost:5000`) dans deux endroits différents (voir section 6).

## 2. Modèle de données

MongoDB sans ORM : pas de schéma imposé en base, les champs réels ont été lus directement sur des documents existants (lecture seule).

| Collection | Champs observés | Relations |
| --- | --- | --- |
| `Personnel` (ex-`Manager`) | `email`, `mot_de_passe`, `firstname`, `lastname`, `role`, `grade`, `is_active`, `directory_visible`, `login_attempts`, `user_id` | Référencée par `Mission1.responsable_id` (id libre, pas de clé étrangère Mongo) |
| `Client_db` | `company_name`, `sector`, `address`, `referentiel` (SYSCOHADA/IFRS/PCG), `legal_form`, `responsable_name`, `civility`, `responsable_function`, `RCCM`, `country`, `creation_date` | `Mission1.id_client` et `Balance.id_client` pointent vers son `_id` (chaîne, non typée ObjectId de façon garantie) |
| `Mission1` | `id_client`, `annee_auditee`, `date_debut`/`date_fin`, `date_debut_mandat`/`date_fin_mandat`, `responsable_nom/grade/role/id`, **puis un sous-document par étape du workflow** : `balances`, `balance_variation`, `grouping`, `efi`, `materiality`, `controle_coherence`, `controle_intangibilite`, `classement_bilan`, `analyse_quantitative`, `analyse_qualitative`, `qualitative_simple`, `presentation_comptes_significatifs`, `revue_analytique`, `revue_analytique_finale`, `etats_financiers_preliminaires`, `quantitative_threshold_mode` | Une mission = un seul document Mongo qui accumule tout le workflow d'audit (pas de collections séparées par étape) |
| `Balance` | `id_client`, `annee_balance`, `balance` (contenu importé) | Liée au client par `id_client` ; le lien exact avec une mission précise se fait via `Mission1.balances` (à confirmer, voir section 4) |
| `Collaborateur` | — (collection créée au démarrage, vide, jamais peuplée) | Aucune, code mort |

**Point clé pour la refonte** : il n'y a pas de table/collection séparée pour « étapes d'audit » — chaque étape est un champ embarqué dans le document `Mission1`. Toute évolution du workflow (ex. verrou IPE) touche donc la structure de ce document unique.

## 3. Fonctionnalités existantes

**Clients et missions** : CRUD client et CRUD mission fonctionnent réellement (création, liste, détail, suppression), vus et vérifiés dans `ClientsView.vue`/`NewClient.vue`/`ClientSpace.vue` et `MissionsView.vue`/`NewMission.vue`.

**Étapes d'audit (barre de progression, `GroupingAnalyse.vue`)** — 11 étapes définies (`workflowPhases`, ligne 560) sur 3 phases :

| # | Étape | Statut |
| --- | --- | --- |
| 1 | Préparation de l'audit | Vide (case à cocher seule, aucun appel backend) |
| 2 | Contrôle interne | Vide (idem) |
| 3 | Contrôle de cohérence | Codée |
| 4 | Contrôle d'intangibilité (+ reclassements) | Codée |
| 5 | Calcul des seuils (matérialité) | Codée |
| 6 | Analyse quantitative | Codée |
| 7 | Analyse qualitative | Codée |
| 8 | Décision finale des comptes à tester | Codée |
| 9 | Préparation des leads (grouping) | Codée |
| 10 | États financiers préliminaires | Codée |
| 11 | Revue analytique finale | Codée |

Deux écrans supplémentaires (« classement bilan », « synthèse ») ont du code fonctionnel des deux côtés mais ne sont accessibles depuis **aucune** entrée de la barre de progression (navigation orpheline). La barre de progression elle-même ne compte que les 2 étapes vides de la phase 1 dans son calcul de `totalSteps` — l'affichage « X / 9 » n'est pas cohérent avec ce calcul.

**Étape « Contrôle de cohérence » (étape 3)** : confirmé, c'est un contrôle **arithmétique sur une seule balance à la fois** — total des `debit_fin` = total des `credit_fin` de la balance importée (`Mission._coherence_checks_for_year`, `api/src/model.py:4197`), exécuté séparément pour chaque année importée. **Ce n'est pas** un rapprochement entre plusieurs fichiers. Le vrai rapprochement N / N-1 (ouverture N vs clôture N-1) existe mais se trouve dans l'étape séparée « Contrôle d'intangibilité » (`Mission.controle_intangibilite_avec_reclassements`, `api/src/model.py:5551`) — le fichier `api/src/model_controle_intangibilite.py` qui semblait porter cette logique est en réalité du **code mort** (jamais importé).

## 4. Import actuel de la balance (point critique)

**Chemin complet** :

1. `clients/src/views/NewMission.vue` — 2 champs fichier `.xlsx` (balance N et N-1), contrôle de format côté client uniquement.
2. `clients/src/utils/uploadFile.js` — construit un `FormData` (`files[]`) et poste sur `POST /api/v1/missions/`.
3. Deux routes backend **redondantes** existent en parallèle : `MissionResource.create_mission` (`api/src/resources/mission_resources.py`, la vraie route utilisée par le frontend) et `POST /nouvelle_mission` (`api/src/mission/routes.py:250`, ancienne route dupliquée, appelle le même modèle directement).
4. `MissionService.create_mission` (`api/src/services/mission_services.py:26`) valide (≥2 fichiers, dates, client existant) puis délègue à `Mission().nouvelle_mission(...)`.
5. **Le parsing réel** est dans `api/src/model.py` : `Mission.nouvelle_mission()` (ligne 424) boucle sur les fichiers et appelle `Mission.creation_balance()` (ligne 542) pour chacun.

**`creation_balance()`** — lecture Excel avec **openpyxl** (pas pandas) :

- Détection de l'onglet : liste de noms codés en dur (`Balance des comptes`, `BALANCE_2023`, `Sage`, `Sheet1`, `Feuil1`…), sinon premier onglet.
- Détection du format de colonnes **automatique, codée en dur**, 4 formats reconnus selon le nombre de colonnes :
  - `standard` (8 col.) : numéro, libellé, débit/crédit initial, débit/crédit mouvement, débit/crédit final
  - `balance_simple` (6 col.) : numéro, libellé, débit/crédit initial, débit/crédit final
  - `sage` (6 col.) : numéro, libellé, solde N-1, mouvement débit/crédit, solde N
  - `simple` (3 col.) : numéro, libellé, montant

**(a) Mapping de colonnes ajustable par l'utilisateur** : **absent**. Aucune UI, aucune route ne permet de faire correspondre soi-même les colonnes ; tout repose sur la détection automatique ci-dessus. Le seul fichier « mapping » du projet, `api/mapping_efi.json`, sert à autre chose (classification des comptes SYSCOHADA pour les états financiers), pas à l'import.

**(b) Balances auxiliaires** : **absentes**, aucune trace dans le code (recherche « auxiliaire » infructueuse).

**(c) Fichier des immobilisations séparé** : **absent**. « Immobilisation » n'apparaît que comme classification de comptes (20-29) à l'intérieur de la balance déjà importée, jamais comme fichier distinct à uploader.

## 5. Rôles, droits & cloisonnement

**Rôles définis** (`api/src/schemas/user_schemas.py`) : Administrateur, Manager, Auditeur Senior, Auditeur, Stagiaire — + 9 grades.

**Application réelle des rôles** : un mécanisme JWT existe bien (`jwt_required`, `admin_required` dans `api/src/resources/user_resources.py`), mais il n'est branché **que sur les routes de gestion des comptes utilisateurs** (profil, liste, stats, changement de mot de passe, déconnexion).

**Aucune vérification de rôle ni d'authentification sur les clients et missions** : les routes de `api/src/mission/routes.py` (toutes les étapes du workflow), `api/src/resources/mission_resources.py` et `api/src/resources/client_resources.py` n'appliquent ni `jwt_required` ni contrôle de `role`/`grade`. N'importe quel appel HTTP, authentifié ou non, peut lire/écrire n'importe quel client ou mission.

**Cloisonnement par mission : inexistant.** `get_all_missions()` renvoie toutes les missions sans filtre (`db.Mission1.find()` sans condition). Le document mission stocke bien `responsable_nom`, `responsable_grade`, `responsable_role`, `responsable_id` (rempli à la création), mais ces champs ne sont **jamais utilisés dans une requête de filtrage** ailleurs dans le code — uniquement écrits, jamais lus pour restreindre l'accès. Même constat pour les clients (`get_all_clients()` sans filtre).

## 6. API / points d'entrée

Enregistrement centralisé dans `api/src/routes/__init__.py` (`register_routes`), avec plusieurs préfixes qui coexistent pour les mêmes ressources — signe d'une transition d'API jamais terminée :

| Préfixe | Utilisé par le frontend ? | Contenu |
| --- | --- | --- |
| `/api/v1/clients`, `/api/v1/missions`, `/api/v1/users` | Partiellement (`auth.api.js` utilise `/api/v1`, dont la création de mission) | Routes « modernes », logique dans `api/src/resources/` + `api/src/services/` |
| `/cors/mission/...` | Oui, majoritairement (`inject('axios')` pointe ici par défaut) | Tout le workflow d'audit, logique dans `api/src/model.py` (fichier historique) |
| `/cors/client/...`, `/client/...` | Oui (`ClientsView`, `NewClient`…) | Doublon de compatibilité vers la même logique client |
| `api/src/customer/routes.py`, `routes_new.py`, `api/src/collaborateur/routes.py` | **Non** | Jamais enregistrés dans l'app (`register_routes` ne les importe pas) — code mort |

**Deux instances Axios différentes côté frontend** pointent vers deux préfixes différents : `clients/src/api/index.js` (`/api/v1`) et `clients/src/plugins/axios.js` (`/cors`, injecté globalement et utilisé par la majorité des vues).

La logique métier du workflow d'audit (cohérence, intangibilité, matérialité, analyses, grouping, EFI, revue analytique) vit presque entièrement dans `api/src/model.py` (\~7800 lignes), appelée depuis les routes de `api/src/mission/routes.py`.

## 7. Tests & conventions

**Tests** : aucun test automatisé dans le dépôt actuel, ni backend ni frontend (aucun fichier `test_*.py`, `*.spec.js`, `*.test.js`). Le frontend a bien `vitest` listé comme outil possible mais aucun test écrit avec.

**Lint / format** : côté frontend, ESLint (`.eslintrc.cjs`) et Prettier (`.prettierrc.json`) configurés avec scripts `pnpm lint` / `pnpm format`. Côté backend, aucun outil de lint/format configuré (pas de `pyproject.toml`, `.flake8` ni `black`).

**CI** : un seul workflow GitHub Actions (`.github/workflows/deploy-pages.yml`), qui build et publie uniquement la landing page marketing sur GitHub Pages — aucune étape de test, lint ou build de vérification sur les pull requests.

**Conventions de code observées** : mélange de styles (ancien code métier concentré dans `api/src/model.py`, nouveau code organisé en `resources/services/schemas`) ; plusieurs endpoints dupliqués entre l'ancien et le nouveau style pour la même ressource (clients, missions).

## 8. Points de greffe pour la V2 (emplacements, pas d'implémentation)

**(a) Import refondu** :

- Entrée HTTP à choisir entre les deux routes actuelles : `MissionResource.create_mission` (`api/src/resources/mission_resources.py`, celle réellement appelée par le frontend) ou sa remplaçante ; l'ancienne route dupliquée `/nouvelle_mission` (`api/src/mission/routes.py:250`) est un candidat à retirer plutôt qu'à faire évoluer.
- Le parsing lui-même est isolé dans deux méthodes de `api/src/model.py` : `Mission.nouvelle_mission()` (orchestration) et `Mission.creation_balance()` (lecture Excel + détection de format) — c'est le point d'entrée naturel pour brancher un mapping de colonnes explicite, la gestion de balances auxiliaires ou d'un fichier immobilisations.
- Le document `Balance` (collection séparée, `id_client` + `annee_balance` + `balance`) est l'endroit logique pour stocker le résultat d'un import refondu, indépendamment de la structure choisie pour le mapping.

**(b) Verrou IPE (Module 1)** :

- Chaque étape du workflow est un champ embarqué dans le document unique `Mission1` (section 2) — un verrou doit donc agir au niveau de ce document, pas d'une collection séparée.
- Le point de passage obligé de toutes les étapes est `GroupingAnalyse.vue` (`showComponent()`, gestion des clics de la sidebar) côté frontend, et les routes de `api/src/mission/routes.py` côté backend — chaque route d'étape (ex. `/analyse_quantitative/<id>`, `/materialite/<id>`…) est un point où insérer une vérification de verrou avant lecture/écriture.
- Comme le contrôle de cohérence (étape 3) est actuellement un calcul sur une balance à la fois (`Mission._coherence_checks_for_year`), c'est l'endroit le plus direct pour conditionner l'avancement des étapes suivantes au résultat de ce contrôle, si c'est la logique voulue pour le verrou IPE.

## 9. Zones d'ombre / questions à confirmer

- **Code mort à clarifier avant de s'en servir de référence** : `api/src/customer/routes.py`, `routes_new.py`, `api/src/collaborateur/routes.py` (jamais enregistrés), et `api/src/model_controle_intangibilite.py` (jamais importé) — à confirmer qu'ils peuvent être ignorés ou supprimés sans risque pour la V2.
- **Lien exact `Balance` ↔ `Mission1.balances`** : la collection `Balance` est distincte de la mission ; le mécanisme précis de référencement (quel champ pointe vers quel `_id`) n'a pas été tracé en détail — à vérifier avant de refondre l'import.
- **Écart entre 2 endpoints de création de mission** (`/api/v1/missions/` vs `/cors/mission/nouvelle_mission`) : lequel est la cible officielle pour la V2 ? Le frontend actuel n'utilise que le premier.
- **Incohérence de la barre de progression** (« X / 9 » affiché vs calcul réel sur 2 items) : bug préexistant, à confirmer si c'est dans le périmètre de la V2 ou à corriger séparément.
- **Absence totale d'authentification/autorisation sur clients et missions** : à confirmer si la V2 doit corriger ce point en même temps que l'import et le verrou IPE, ou si c'est un chantier séparé.
- **Deux écrans orphelins** (« classement bilan », « synthèse ») : à décider s'ils doivent être re-rattachés à la navigation, supprimés, ou laissés tels quels.
- **CLAUDE.md demandé mais absent** : aucune convention de développement documentée pour l'agent ou l'équipe — à créer si souhaité.

## Résumé (5 lignes)

1. Stack Flask/MongoDB (sans ORM) + Vue 3/Vite fonctionnelle, mais avec deux générations d'API et de routes coexistantes, dont une partie en code mort.
2. 9 des 11 étapes du workflow d'audit sont réellement codées ; le contrôle de cohérence est un calcul débit=crédit sur une seule balance, pas un rapprochement multi-fichiers.
3. L'import de balance est entièrement automatique (détection de format codée en dur dans `api/src/model.py`) : pas de mapping de colonnes, pas de balances auxiliaires, pas de fichier immobilisations.
4. Les rôles existent en base mais ne sont appliqués que sur la gestion des comptes utilisateurs — aucune authentification ni cloisonnement par mission sur les données métier.
5. Aucun test automatisé ni CI de vérification n'existe actuellement sur le dépôt.
