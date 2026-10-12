# Plan technique — Refonte de l'import (balances, mapping, fichiers manquants)

Ce document est un plan, pas du code. Il s'appuie sur le code réel de la V1 (voir `RECAP_V1_CAC_PERFORM.md`) et sur `CLAUDE.md` pour le cadrage. Toute règle métier non confirmée par les specs (CAC-IPE-01, CAC-CIR-01, CAC-SEUILS-01, ECH-01) est marquée `TODO(spec: ...)` plutôt que devinée.

## 0. Rappel du point confirmé : lien `Balance` ↔ `Mission1.balances`

Vérifié dans `api/src/model.py` (fonctions `Mission.nouvelle_mission()`, ligne 424, et `Mission.creation_balance()`, ligne 542) :

- `creation_balance()` insère un document dans la collection `Balance` : `{id_client, annee_balance, balance: <lignes parsées>}`, et retourne `(inserted_id, data)`.
- `nouvelle_mission()` appelle `creation_balance()` pour chaque fichier uploadé (balance N puis balance N-1, `annee_auditee` étant décrémenté entre les deux appels) et empile les `inserted_id` retournés dans une liste `balance_ids`.
- Cette liste devient **directement** le champ `Mission1.balances` au moment de l'insertion de la mission (`mission_data["balances"] = balance_ids`).

**Conclusion** : `Mission1.balances` est une liste de **chaînes égales aux `_id` de documents `Balance`**, dans l'ordre `[balance N, balance N-1]`. Aucune ambiguïté résiduelle sur ce point — la refonte peut s'appuyer dessus tel quel, ou le faire évoluer sciemment (voir §2).

Point non couvert par ce tracé et resté ouvert : les données parsées (`les_balance_n_n1`) sont aussi gardées **en mémoire** dans `nouvelle_mission()` pour alimenter immédiatement `rapprochement_des_balances`, `create_grouping`, `prod_efi` — elles ne sont pas relues depuis `Balance` à ce moment-là. Une refonte qui change la forme des données parsées doit donc rester compatible avec ce qu'attendent ces trois fonctions, **sans les modifier** (elles restent dans `model.py`, hors périmètre V2 d'après `CLAUDE.md`).

## 1. Périmètre

**(a) Correspondance de colonnes explicite, configurable et mémorisée**
- Par **client** et par **logiciel comptable** (ex. Sage, un export « standard » 8 colonnes, etc.).
- La détection automatique actuelle (4 formats codés en dur dans `creation_balance()` : `standard`, `balance_simple`, `sage`, `simple`) devient la **valeur par défaut proposée** à l'utilisateur, pas le mécanisme final — l'utilisateur confirme ou corrige avant import définitif.
- `TODO(spec: CAC-IPE-01 / CAC-CIR-01 — format exact de mapping attendu, le cas échéant)` si une spec impose une structure précise de mapping.

**(b) Import des balances auxiliaires (clients et fournisseurs)**
- Absent aujourd'hui (confirmé dans le récap V1 — aucune trace de « auxiliaire » dans le code).
- Nouveau flux d'upload distinct de la balance générale, avec son propre parsing (structure différente : compte tiers, sous-compte, solde par tiers).

**(c) Import du fichier des immobilisations**
- Absent aujourd'hui (le mot « immobilisation » n'existe que comme classification de comptes 20-29 à l'intérieur de la balance générale déjà importée).
- Nouveau flux d'upload distinct, avec une structure propre (valeur brute, amortissements, valeur nette, durée/taux...). `TODO(spec: CAC-IPE-01 §3 — champs exacts attendus pour IPE-3)`.

**(d) Contrôles préliminaires**
- Intégrité du fichier (lisible, non vide, extension correcte).
- Doublons (même numéro de compte apparaissant deux fois dans une même balance).
- Anomalies de sens (ex. compte de classe censé être débiteur qui ressort créditeur) — à ne pas confondre avec le contrôle de cohérence de l'étape 3, qui reste inchangé.
- Cohérence des dates de clôture entre les fichiers importés dans une même mission (balance N, balance N-1, auxiliaires, immobilisations doivent porter sur des clôtures cohérentes entre elles).

## 2. Modèle de données

**Collection `Balance`** — évolutions proposées, en conservant la forme actuelle (`id_client`, `annee_balance`, `balance`) pour ne pas casser la lecture existante par `model.py` :
- Ajouter un champ `type` (`"generale"` par défaut pour rester compatible avec les documents existants, puis `"auxiliaire_client"`, `"auxiliaire_fournisseur"`, `"immobilisations"` pour les nouveaux flux).
- Ajouter un champ `format_source` (le format détecté/choisi à l'import — traçabilité).
- Ajouter un champ `mission_id` en plus de `id_client` : aujourd'hui le lien se fait uniquement dans l'autre sens (`Mission1.balances` référence `Balance._id`) ; avoir la référence dans les deux sens simplifie les requêtes et prépare le filtrage par mission mentionné dans `CLAUDE.md`.

**Document `Mission1`** — chaque étape étant un sous-document embarqué (rappel : pas de collection séparée par étape), la refonte ajoute :
- `Mission1.balances` : garder la liste actuelle de `_id` de balances générales (compatibilité V1), ou la faire évoluer en `{generale: [...], auxiliaires_clients: [...], auxiliaires_fournisseurs: [...], immobilisations: [...]}` — **à trancher** (voir §7), car ça touche la forme lue par le code existant.
- Un nouveau sous-document `import_meta` : mapping de colonnes retenu par fichier, résultats des contrôles préliminaires (§1d), horodatage/auteur de l'import.

**Mapping mémorisé (client × logiciel comptable)**
- Nouvelle collection dédiée (ex. `MappingImport`) plutôt qu'un champ sur `Client_db`, pour permettre plusieurs mappings par client (un par logiciel comptable) et les faire évoluer indépendamment de la fiche client.
- Clé logique : `id_client` + identifiant du logiciel comptable (libre saisie au départ, `TODO(spec)` si une liste fermée est exigée).

## 3. API (sous `/api/v1`)

Nouveaux endpoints, dans `api/src/resources/` + `api/src/services/` + `api/src/schemas/` (pas dans `api/src/mission/routes.py` ni `model.py`) :

- `POST /api/v1/imports/apercu` — reçoit un fichier, renvoie les colonnes détectées + le mapping proposé (détection auto actuelle) sans rien écrire en base. Sert à alimenter l'écran de correspondance de colonnes.
- `POST /api/v1/imports/mapping` — enregistre/à jour un mapping mémorisé pour un client + logiciel comptable.
- `GET /api/v1/imports/mapping?id_client=...&logiciel=...` — relit un mapping mémorisé.
- `POST /api/v1/missions/{id}/balances` — importe balance générale N/N-1 pour une mission existante, avec mapping validé ; remplace à terme l'usage de `MissionResource.create_mission` pour la partie import (la création de mission elle-même reste gérée séparément).
- `POST /api/v1/missions/{id}/balances-auxiliaires` — importe balance auxiliaire clients ou fournisseurs.
- `POST /api/v1/missions/{id}/immobilisations` — importe le fichier des immobilisations.
- `POST /api/v1/imports/controles-preliminaires` — exécute les contrôles du §1d sur un ou plusieurs fichiers déjà uploadés (avant validation définitive).

**Route dupliquée existante** : `POST /cors/mission/nouvelle_mission` (`api/src/mission/routes.py:250`) reste en place, **candidate au retrait** mais non touchée dans ce chantier (conforme à `CLAUDE.md`).

**`MissionResource.create_mission`** (`api/src/resources/mission_resources.py`) : à terme, ne devrait plus porter la logique d'import de fichiers — sa responsabilité se limite à créer la mission (métadonnées), l'import étant délégué aux nouveaux endpoints ci-dessus. Découpage exact à confirmer en tâche de développement (§8).

## 4. Frontend

**`clients/src/views/NewMission.vue`**
- Nouvel écran/étape de correspondance des colonnes après sélection du fichier balance générale (avant soumission) : affiche le mapping proposé, permet de le corriger, propose de le mémoriser pour ce client/logiciel.
- Ajout de deux champs fichier supplémentaires (facultatifs dans un premier temps) : balances auxiliaires clients/fournisseurs, fichier des immobilisations.
- Affichage des résultats des contrôles préliminaires (§1d) avant validation finale de l'import.

**`clients/src/utils/uploadFile.js`**
- Actuellement poste directement sur `http://localhost:5000/api/v1/missions/`. À faire évoluer pour appeler la séquence des nouveaux endpoints (§3) plutôt qu'un seul appel monolithique.

**Deux instances Axios** — point relevé dans le récap V1 :
- `clients/src/api/index.js` (`baseURL: /api/v1`) — c'est celle-ci que doivent utiliser tous les nouveaux appels, puisque la V2 se greffe sur `/api/v1`.
- `clients/src/plugins/axios.js` (`inject('axios')`, `baseURL: /cors`) — reste utilisée par le code existant (workflow d'audit dans `GroupingAnalyse.vue`), non touchée par ce chantier.
- À faire en tâche de développement : vérifier si `uploadFile.js` utilise l'instance `/api/v1` (`clients/src/api/index.js`) ou `/cors` (`inject('axios')`) aujourd'hui, et s'assurer que les nouveaux appels utilisent bien la première.

## 5. Impact sur l'existant

- **Aucune régression sur les 9 étapes codées** : celles-ci lisent `Mission1` et `Balance` via `model.py`, qui n'est pas modifié. Toute évolution de forme (ex. `Mission1.balances` restructuré, nouveau champ `type` sur `Balance`) doit rester **additive et rétrocompatible** avec la forme actuelle que `model.py` sait lire.
- **Données existantes** : les missions déjà créées n'ont pas de balances auxiliaires ni d'immobilisations, et leurs documents `Balance` n'ont pas de champ `type`. Le code de lecture (nouveau et ancien) doit traiter l'absence de `type` comme `"generale"` par défaut plutôt que d'exiger une migration immédiate.
- **Pas de migration de données obligatoire avant bascule** : le nouveau flux d'import peut cohabiter avec l'ancien (`/cors/mission/nouvelle_mission` et `MissionResource.create_mission` restent fonctionnels) le temps de la transition, conformément à la consigne de ne rien casser.

## 6. Points de greffe pour le futur verrou IPE (emplacements seulement)

- **IPE-1 (clients ↔ 411) et IPE-2 (fournisseurs ↔ 40x)** : consommeront directement les balances auxiliaires clients/fournisseurs introduites par ce chantier (§1b) — le point de greffe est le nouveau service d'import de balances auxiliaires, qui doit conserver les soldes par tiers dans une forme exploitable pour un rapprochement ultérieur avec le compte collectif correspondant de la balance générale.
- **IPE-3 (immobilisations ↔ 2xxx)** : consommera le fichier des immobilisations introduit par ce chantier (§1c) — point de greffe : le nouveau service d'import d'immobilisations.
- **IPE-GLOBAL-01** (blocage du cycle si `ipe_fiabilite_validee = FALSE`) : nécessitera un nouveau champ sur `Mission1` (ex. dans un futur sous-document `ipe`), à ajouter lors du développement du Module 1 — pas dans ce chantier, mais la structure `import_meta` proposée au §2 est conçue pour rester à côté sans collision de nom.
- **R4 croisé** : non développé (conforme à `CLAUDE.md`) ; aucun point de greffe à prévoir tant que ce n'est pas arbitré.

## 7. Questions ouvertes / décisions à remonter

1. **Forme de `Mission1.balances`** (§2) : garder une simple liste (compatibilité stricte avec `model.py`) ou passer à une structure par type de fichier ? Impacte directement le code de lecture existant.
2. **Contenu exact attendu pour IPE-1/IPE-2/IPE-3** (colonnes des balances auxiliaires et du fichier immobilisations) : `TODO(spec: CAC-IPE-01)`, non trouvé dans le dépôt.
3. **Contrôles préliminaires (§1d)** : quels seuils/règles précises pour « anomalie de sens » et « cohérence des dates de clôture » ? `TODO(spec: CAC-CIR-01)`.
4. **Sécurité / cloisonnement par mission** : ce chantier pose la base (`mission_id` sur `Balance`, §2) mais ne implémente aucun contrôle d'accès — à confirmer que c'est bien le périmètre voulu (cf. `CLAUDE.md`, point de sécurité connu).
5. **R4 croisé** : reste à arbitrer avant tout développement le concernant (rappel, pas une question de ce chantier mais une dépendance amont du Module 1).
6. **Devenir de `MissionResource.create_mission`** et de la route dupliquée `/cors/mission/nouvelle_mission` : retrait de la seconde prévu « plus tard » — à quel jalon ?
7. **Format du mapping mémorisé** : collection dédiée proposée au §2 — à valider avant développement du schéma `marshmallow` correspondant.

## 8. Tâches de développement (ordre proposé, à valider avant tout code)

1. Trancher la question ouverte n°1 (forme de `Mission1.balances`) et n°7 (format du mapping mémorisé).
2. Créer les schémas `marshmallow` (`api/src/schemas/`) pour : aperçu de mapping, mapping mémorisé, balance auxiliaire, fichier immobilisations.
3. Créer le service de détection/aperçu de mapping (reprend la logique de détection actuelle de `creation_balance()` comme valeur par défaut, sans toucher à `model.py`).
4. Créer le service de mapping mémorisé (lecture/écriture de la nouvelle collection dédiée).
5. Créer le service d'import des balances auxiliaires.
6. Créer le service d'import du fichier des immobilisations.
7. Créer le service des contrôles préliminaires (§1d).
8. Créer les ressources/routes `/api/v1/imports/...` et `/api/v1/missions/{id}/balances-auxiliaires`, `/immobilisations` correspondantes.
9. Adapter `clients/src/utils/uploadFile.js` pour appeler la nouvelle séquence d'endpoints via l'instance Axios `/api/v1`.
10. Ajouter l'écran de correspondance des colonnes dans `clients/src/views/NewMission.vue`.
11. Ajouter les champs d'upload (auxiliaires, immobilisations) et l'affichage des contrôles préliminaires dans `clients/src/views/NewMission.vue`.
12. Vérifier de bout en bout qu'une mission créée par l'ancien flux (`MissionResource.create_mission` / `/cors/mission/nouvelle_mission`) reste lisible sans erreur par les 9 étapes existantes.
13. Documenter dans `CLAUDE.md` ou un fichier dédié les décisions prises sur les questions ouvertes du §7, au fur et à mesure qu'elles sont tranchées.
