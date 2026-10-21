# Plan technique — Ossature du verrou IPE (CAC-IPE-01)

Ce document est un plan, **sans code**. Conforme à `CLAUDE.md` : tout sous `/api/v1` dans `resources/` + `services/` + `schemas/` ; rien dans `api/src/model.py` ni dans les routes `/cors/mission` (`api/src/mission/routes.py`) ; on conçoit le **mécanisme** de blocage, pas les **règles métier** (celles-ci dépendent de CAC-IPE-01, absente du dépôt).

## 0. Rappel de contexte (vérifié dans le code)

- `Mission1` est un document unique par mission (voir `RECAP_V1_CAC_PERFORM.md` §2) : chaque étape est un champ embarqué (`controle_coherence`, `materiality`, `analyse_quantitative`, etc.).
- Les routes du workflow vivent dans `api/src/mission/routes.py` (blueprint `mission`, préfixe `/cors/mission`), toutes backées par `api/src/model.py`. Aucune de ces routes n'a de contrôle d'authentification ou de rôle aujourd'hui.
- La barre de progression (`clients/src/views/GroupingAnalyse.vue`, `workflowPhases`, ligne 560) définit les étapes par une **clé** (`key`) : `coherence`(3), `intang`(4), `materialite`(5), `quantitatif`(6), `qualitatif`(7), `presentation`(8), `grouping`(9), `efi`(10), `revue`(11). La navigation passe déjà par un garde-fou (`handleStepClick`, ligne 616 : `if (step.static) return;`) — mécanisme réutilisable pour un verrou.
- Le lot "import" (commits `cc4a555`, `2eda795`) a déjà posé : `Balance.mission_id`, `Balance.type` (`auxiliaire_client`, `auxiliaire_fournisseur`, `immobilisations`, `generale`), `Balance.actif`/`version` (versionnement), et les contrôles préliminaires (`lignes_ecartees`, `bouclage_total`, `bouclage_ligne`) dans `api/src/services/controle_preliminaire_service.py` et `fichiers_complementaires_service.py`.

## 1. Indicateur — où stocker l'état IPE

Nouveau sous-document **`Mission1.ipe`**, additif, sans toucher aux champs existants :

```
Mission1.ipe = {
  "verrou_applicable": <bool>,          # FIGÉ À LA CRÉATION (voir §2 bis) — jamais recalculé ensuite
  "verrou_actif": <bool>,               # voir §2 — copie au niveau mission du paramètre global, pour traçabilité
  "ipe_fiabilite_validee": <bool|null>, # null = jamais évalué ; IPE-GLOBAL-01 porte sur ce champ
  "modules": {
    "ipe_1_clients":      { "statut": "non_evalue|ok|ecart|a_traiter", "derniere_evaluation": <doc, voir ci-dessous> },
    "ipe_2_fournisseurs":  { ... même structure ... },
    "ipe_3_immobilisations": { ... même structure ... }
  },
  "historique": [
    { "horodatage": <iso>, "utilisateur_id": <id|null>, "action": "evaluation|validation_manager|...",
      "resultat": {...}, "commentaire": <str|null> }
  ]
}
```

- **Additif et rétrocompatible** : absent sur toute mission existante tant qu'aucune évaluation IPE n'a eu lieu. Le code qui lit `Mission1` (API modernes comme `model.py`) doit traiter `ipe` manquant comme « non évalué », jamais comme une erreur.
- **`verrou_applicable`** : décidé une fois pour toutes à la création de la mission (§2 bis), jamais recalculé après — une mission créée avant l'activation du verrou reste « antérieure au verrou » même si le verrou est activé plus tard pendant qu'elle est encore en cours.
- **Historique horodaté (qui, quand)** : chaque entrée de `historique` a besoin d'un `utilisateur_id`. Aujourd'hui, aucune route mission ne reçoit d'utilisateur authentifié (pas de `jwt_required`, voir `RECAP_V1_CAC_PERFORM.md` §5) — on prévoit le champ (`utilisateur_id: null` par défaut), sans l'exiger. **Décision à faire remonter** (§8) : faut-il un minimum d'identification pour `historique.utilisateur_id`, ou `null` acceptable pour cette ossature ?
- Le détail de ce que contient `"derniere_evaluation"` 
dépend du calcul de rapprochement (§4) — structure proposée là-bas.

## 2. Activation — paramètre désactivé par défaut

- Variable d'environnement `IPE_VERROU_ACTIF` (par défaut `false`), lue dans `config.py` **n'est pas modifiable** (hors périmètre, cf. CLAUDE.md) → en pratique : nouvelle entrée dans `api/.env` / `env.template`, lue par un nouveau module `api/src/services/ipe_config_service.py` (ou directement dans le service de verrou, §3), pas dans `config.py` lui-même pour rester additif.
- Tant que `IPE_VERROU_ACTIF=false` (valeur par défaut) : le mécanisme du §3 est un **no-op** — aucune mission existante n'est bloquée, les 9 étapes actuelles fonctionnent à l'identique. C'est la seule garantie dont dépend la non-régression de ce lot.
- Le flag est global (serveur), pas par mission, pour l'ossature. `Mission1.ipe.verrou_actif` (§1) n'est qu'une **copie journalisée** de l'état du flag au moment de chaque évaluation — utile pour l'audit, pas pour la logique de blocage elle-même.

## 2 bis. `verrou_applicable` — figé à la création de la mission

Règle retenue (remplace l'ancienne décision ouverte « missions existantes à l'activation ») :

- **À la création d'une mission** (route `new_assign`, aujourd'hui dans `api/src/mission/routes.py` — on n'y touche pas ; la capture se fait côté service nouveau qui lit `IPE_VERROU_ACTIF` **au moment de l'insertion**, sans modifier `new_assign` lui-même si possible, sinon un hook `before_request`/`after_request` additif), on lit l'état courant de `IPE_VERROU_ACTIF` et on l'écrit une fois pour toutes dans `Mission1.ipe.verrou_applicable` :
  - `IPE_VERROU_ACTIF=false` au moment de la création → `verrou_applicable=false`, **définitivement** pour cette mission (même si le flag global passe à `true` plus tard pendant que la mission est encore en cours).
  - `IPE_VERROU_ACTIF=true` au moment de la création → `verrou_applicable=true`, et le blocage IPE-GLOBAL-01 (§3) s'applique à cette mission dès que ses cycles post-ouverture sont atteints.
- **Missions déjà existantes avant ce lot** (créées avant même l'introduction de `Mission1.ipe`) : `verrou_applicable` est absent → traité comme `false` par défaut (même logique que « additif, rétrocompatible », §1). Elles sont donc **« antérieures au verrou »**, jamais bloquées, et doivent être **visiblement étiquetées comme telles** côté frontend (§3, affichage).
- Ceci répond directement aux anciennes décisions 1 et 6 du §8 (ci-dessous, désormais retirées des points ouverts) : plus besoin de choisir un comportement global à la bascule, puisque chaque mission porte sa propre règle, figée à sa création.

## 3. Blocage (IPE-GLOBAL-01) — mécanisme, sans toucher à model.py ni aux routes

**Principe retenu : `Blueprint.before_request` enregistré depuis `api/src/routes/__init__.py`** (le point d'enregistrement centralisé, déjà modifié sans souci dans le lot import), jamais depuis `api/src/mission/routes.py` ni `api/src/mission/__init__.py`.

```python
# Illustratif seulement (§ sans code) :
# from src.mission import mission
# mission.before_request(verifier_verrou_ipe)   # appelé AVANT app.register_blueprint(mission)
```

Flask autorise cet appel depuis n'importe quel module détenant une référence au blueprint — `routes/__init__.py` importe déjà `mission`, donc aucune modification de `api/src/mission/` n'est nécessaire.

**Le hook devrait, pour chaque requête entrant dans le blueprint `mission` :**
1. Si `IPE_VERROU_ACTIF` est désactivé (flag global) → laisser passer (no-op), toujours.
2. Résoudre l'**endpoint Flask** (`request.endpoint`, ex. `mission.materialite_route`) contre une liste d'endpoints « verrouillables » (voir tableau ci-dessous) — jamais par correspondance sur le texte de l'URL, pour rester robuste aux alias de route.
3. Si l'endpoint n'est pas dans la liste → laisser passer (les étapes de diagnostic pré-IPE et les routes de gestion de mission restent toujours accessibles).
4. Sinon, extraire `mission_id` depuis `request.view_args` (attention : la plupart des routes utilisent `<id_mission>`, une utilise `<_id>` — voir tableau) ; si absent de l'URL → **route non gatable par ce mécanisme**, voir liste des impossibilités plus bas.
5. Lire `Mission1.ipe.verrou_applicable` pour cette mission (§2 bis) : si `false` (ou absent) → **laisser passer, toujours** — mission « antérieure au verrou », jamais bloquée, quel que soit `ipe_fiabilite_validee`.
6. Si `verrou_applicable=true` : lire `Mission1.ipe.ipe_fiabilite_validee`. Si `True` → laisser passer. Si `False` **ou absent/`null`** (jamais évaluée) → bloquer : renvoyer `403` avec un message exploitable par le frontend (`{"success": false, "error": "...", "code": "IPE_VERROU"}`), **avant** d'atteindre la vue (donc avant toute lecture/écriture par `model.py`). L'absent/`null` est traité comme bloquant par défaut pour une mission où le verrou s'applique — cohérent avec le sens même de IPE-GLOBAL-01 (« tant que la fiabilité n'est pas validée »).

**Endpoints candidats au verrou** (tout ce qui suit « ouverture des cycles » dans le séquencement de `CLAUDE.md` — matérialité/sélection et au-delà) :

| Étape (clé frontend) | Endpoints Flask concernés (`mission.<fonction>`) |
|---|---|
| `materialite` (5) | `materialite_route`, `get_benchmarks`, `save_materiality`, `validate_materiality`, `get_materiality` |
| `quantitatif` (6) | `analyse_quantitative_route`, `save_quantitative_threshold_mode`, `save_quantitative_threshold_mode_alias`, `make_quantitative_analysis`, `download_analyse_quantitative` |
| `qualitatif` (7) | `analyse_qualitative_route`, `init_qualitative_responses_route`, `save_qualitative_responses_route`, `make_qualitative_analysis`, `download_analyse_qualitative` |
| `presentation` (8) | `presentation_comptes_significatifs_route` |
| `grouping` (9) | `get_grouping_with_qualitative`, `make_final`, `download_grouping` |
| `efi` (10) | `etats_financiers_preliminaires_route`, `classement_bilan_route` |
| `revue` (11) | `revue_analytique_route`, `update_commentaire_route`, `revue_analytique_finale_route`, `save_revue_analytique_route`, `download_revue_analytique` |

**Toujours accessibles, jamais verrouillées** (diagnostics pré-IPE + gestion de mission) : `controle_coherence_route`, `controle_intangibilite_route` (+ les 3 routes de reclassement), `all_missions_route`, `show_assign_info`, `new_assign`, `supprimer_mission_route`, `make_grouping` (`/grouping_model/`, référentiel statique, pas lié à une mission).

**Implémentation retenue pour cette liste** : un **unique paramètre** (une seule liste/constante, ex. `ENDPOINTS_VERROUILLABLES` dans `verrou_ipe_service.py`), jamais des conditions `if endpoint == ...` dispersées dans le hook ou ailleurs — modifier le périmètre du verrou doit se faire en un seul endroit. **Décision métier à confirmer** : le contenu exact de cette liste (quelles étapes sont réellement concernées par IPE-GLOBAL-01) reste une hypothèse de travail déduite du séquencement de `CLAUDE.md` (« après ouverture des cycles »), pas une règle actée par CAC-IPE-01.

**Limite connue, actée (plus une question ouverte)** :
- `generate_efi` (`POST /recuperation_etats_financier/`) : **aucun `mission_id` dans la requête** (reçoit des fichiers bruts, calcule un EFI générique). Décision : **cette route reste accessible**, sans tentative de gating — le mécanisme `mission_id`-based du §3 ne peut matériellement pas s'y appliquer. Documentée ici comme **limite connue et acceptée** de ce lot, pas comme un trou à combler : si cette route devait un jour recevoir un `mission_id`, le gating pourrait s'y ajouter alors.
- `show_assign_info` utilise `<_id>` et non `<id_mission>` — sans conséquence ici puisque cette route n'est pas verrouillée, mais à garder en tête si son périmètre devait changer.

**Côté frontend** (`GroupingAnalyse.vue`) :
- Nouvel appel (au chargement de la mission) : `GET /api/v1/missions/<id>/ipe` (nouvel endpoint, §1, dans `resources/services/schemas` — pas une étape du workflow, comme `fichiers-complementaires`) renvoyant `Mission1.ipe` (incluant `verrou_applicable`).
- `workflowPhases` : ajout d'un indicateur `locked` calculé (pas stocké) à partir de la clé de l'étape (même liste que le tableau ci-dessus), de `ipe.verrou_applicable` et de `ipe.ipe_fiabilite_validee` (`locked = verrou_applicable && ipe_fiabilite_validee !== true`) — réutilise le garde-fou existant de `handleStepClick` (`if (step.static) return` → `if (step.static || step.locked) { afficherMessageVerrou(); return }`).
- Affichage : icône verrou + message (« Cycle verrouillé : fiabilité IPE non validée ») sur les étapes concernées quand `locked`, sans les retirer de la liste. Si `verrou_applicable===false`, aucune icône de verrou — l'indicateur de la barre latérale (§6) affiche plutôt « antérieure au verrou ».

## 4. Rapprochements (IPE-1, IPE-2, IPE-3) — calcul

**Correction de conception (point clé)** : la balance générale **ne contient pas les tiers**. Elle ne contient que des **comptes collectifs** (ex. une seule ligne `411` ou `401`, parfois plusieurs collectifs plus fins comme `401`/`402`/`403`). Le détail par tiers (chaque client, chaque fournisseur) n'existe que dans le fichier auxiliaire. Le rapprochement se fait donc **compte collectif par compte collectif**, jamais par une simple somme globale balance-générale-contre-tout-l'auxiliaire :

> pour chaque compte collectif présent dans la balance générale (famille IPE concernée) → solde du collectif (balance générale) **comparé à** la somme des tiers de l'auxiliaire qui s'y rattachent.

**Comment lire la balance générale importée par la V1 (vérifié dans `api/src/model.py`)** :
- Les documents `Balance` de la balance générale (créés par `Mission.creation_balance()`, appelée depuis `nouvelle_mission()`) **n'ont ni `mission_id` ni `type`** — contrairement aux documents auxiliaires/immobilisations du lot import. Schéma réel : `{_id, id_client, annee_balance, balance: [...]}`, avec `annee_balance` un entier (ou parfois une chaîne selon le chemin d'import — les deux sont acceptés).
- Ils sont retrouvés via **`Mission1.balances`** (liste de `_id` sous forme de chaînes) — jamais via `Balance.mission_id`/`type="generale"` (ce filtre ne matcherait rien sur les missions créées par la V1).
- **Correction (relecture post-implémentation) : la sélection ne se fait jamais par position (`balances[0]`)** — l'ordre n'est pas garanti stable. Le rapprochement IPE sélectionne le document dont `annee_balance` correspond exactement à `Mission1.annee_auditee` (exercice audité, année N — jamais N-1). **Introuvable ou ambigu (plusieurs documents matchent la même année) → échec explicite (`ValueError`, renvoyé en HTTP 400), rien n'est enregistré dans ce cas** — ni `evaluer_ipe` ni `valider_fiabilite(validee=True)` (qui a besoin de la même résolution pour figer sa référence, §5).
- Chaque ligne de `balance` a, de façon fiable quel que soit le format détecté (standard/balance_simple/sage/simple) : `numero_compte` (str) et `solde_reel` (float signé = débit − crédit). C'est le champ réutilisé ici, sans dépendre des champs bruts (`debit_fin`/`credit_fin`) qui varient selon le format.

**Entrées :**
- Balance générale : document `Balance` sélectionné par année auditée dans `Mission1.balances` (voir ci-dessus, jamais par position) → son champ `balance` (lignes `numero_compte` + `solde_reel`).
- Fichier complémentaire : `db.Balance` où `mission_id=<id>`, `type="auxiliaire_client"` / `"auxiliaire_fournisseur"` / `"immobilisations"`, `actif=true` (version active, via `fichiers_complementaires_service.lister_fichiers_complementaires`). Chaque ligne a un champ identifiant (`numero_compte`, parfois `numero_tiers`/`numero` selon le mapping — voir `balance_auxiliaire_service.CLES_IDENTIFIANTES_POSSIBLES`) et un solde reconstitué depuis la paire `solde_final_debit`/`solde_final_credit` quand elle existe, sinon depuis `montant` (repli montant signé).

**Comptes collectifs ciblés par famille** : racine `411` (IPE-1 clients), racine `40` (IPE-2 fournisseurs — peut regrouper plusieurs collectifs distincts : `401`, `402`, `403`…), racine `2` (IPE-3 immobilisations, au sens large de CLAUDE.md — l'exclusion éventuelle des comptes d'amortissement/provision `28x`/`29x` n'est pas tranchée, voir TODO ci-dessous).

**Calcul proposé (mécanisme, pas la règle finale) :**
1. **Comptes collectifs présents** = valeurs distinctes de `numero_compte` dans la balance générale qui commencent par la racine de la famille (ex. toutes les lignes `401*`, `402*`… pour IPE-2).
2. **Rattachement d'un tiers à un collectif** : un tiers de l'auxiliaire est rattaché au collectif dont le numéro est le préfixe **le plus long** qui correspond à son propre numéro (ex. tiers `4011AAA` → rattaché à `4011` si ce collectif existe dans la balance générale, sinon à `401`, sinon à `40`). Choix du préfixe le plus spécifique pour éviter un double comptage si plusieurs collectifs emboîtés existent. **Hypothèse de travail, pas une règle vérifiée.**
3. Pour chaque collectif : **solde balance générale** = somme des `solde_reel` des lignes de la balance générale portant exactement ce `numero_compte` ; **solde auxiliaire** = somme des soldes des tiers qui s'y rattachent (étape 2) ; **écart** = différence des deux. OK si `abs(écart) <= tolérance` (0 par défaut, TODO ci-dessous).
4. **Orphelins côté auxiliaire** : tiers dont le numéro ne correspond (par préfixe) à **aucun** collectif présent dans la balance générale.
5. **Orphelins côté balance générale** : collectifs de la famille sans **aucun** tiers rattaché dans l'auxiliaire.
6. Réutilisation explicite de l'existant : les `lignes_ecartees` et `bouclage_total`/`bouclage_ligne` déjà calculés et stockés sur le document `Balance` auxiliaire (lot import) sont lus tels quels, pas recalculés — le rapprochement IPE s'appuie sur des lignes déjà qualifiées « valides ».

**`TODO(spec: CAC-IPE-01 §2)` — explicitement non inventés dans ce lot :**
- **Rattachement tiers ↔ compte collectif par préfixe le plus long** (étape 2 ci-dessus) : hypothèse de travail, à confirmer — une convention différente (ex. via `code_entite` plutôt que `numero_compte`) n'est pas exclue.
- **Tolérance d'écart** (0 strict ? un seuil ?).
- **Convention de signe harmonisée** entre `solde_reel` (balance générale) et le solde reconstitué de l'auxiliaire (répartition débit/crédit potentiellement différente d'un fichier à l'autre).
- **Périmètre exact d'IPE-3** (comptes `2xxx` : inclut-on les amortissements `28x` et provisions `29x`, ou seulement les immobilisations brutes ?).
- **Traitement des orphelins** (bloquant pour IPE-GLOBAL-01, ou juste une alerte qualifiée — §5) ?
- **Conditions exactes de passage à `TRUE`** de `ipe_fiabilite_validee` (écart nul sur les 3 modules ? validation manager en plus ? voir §5).

## 5. Qualification des écarts et validation manager

Structure de données prévue (dans `Mission1.ipe.modules.<module>.derniere_evaluation`, additive au §1) :

```
{
  "date_evaluation": <iso>,
  "ecart_global": <nombre>,
  "tiers_orphelins": { "balance_generale_seulement": [...], "auxiliaire_seulement": [...] },
  "qualification": {
    "etiquette": <str, ex. "a_traiter"|"accepte"|"corrige">,   # TODO(spec) — valeurs possibles non confirmées
    "statut": <str>,
    "commentaire": <str|null>,
    "validation": { "validee": <bool>, "par_utilisateur_id": <id|null>, "horodatage": <iso|null> }
  }
}
```

**Lien avec les droits (inexistant aujourd'hui)** : la validation manager suppose de savoir QUI valide et avec QUEL rôle — or aucune route mission n'a d'authentification (`RECAP_V1_CAC_PERFORM.md` §5 ; `CLAUDE.md`, point de sécurité connu). Ce lot ne refait pas l'authentification ; `par_utilisateur_id` reste `null`-able. **Décision à faire remonter (§8)** : qui a le droit de valider, en l'absence de tout contrôle d'accès existant sur les missions ?

**Invalidation automatique (ajout post-implémentation)** : une validation positive (`ipe_fiabilite_validee=True`) fige dans `Mission1.ipe.fichiers_references` les références (`_id`, version) de la balance générale (exercice N) et de chaque fichier complémentaire actif au moment de la validation. Tout nouvel import/remplacement d'un de ces fichiers (via `balance_auxiliaire_service`/`immobilisation_service`) compare le nouvel `_id` à la référence figée : s'il diffère, `ipe_fiabilite_validee` repasse à `False`, le module concerné repasse à `"non_evalue"`, et une entrée d'historique (`action: "invalidation_automatique"`) explique pourquoi — jamais une invalidation silencieuse. **Limite connue** : la balance générale n'a aujourd'hui aucune route de remplacement pour une mission existante (seuls les fichiers complémentaires peuvent être réimportés) ; le mécanisme est prêt à l'accueillir le jour où une telle route existerait.

## 6. Écran — recommandation (détail + point de contrôle dans la barre latérale)

Deux options pour le **détail** des calculs, recommandation explicite :

- **Option A (recommandée)** : étendre l'écran existant `clients/src/views/FichiersComplementairesView.vue`, à l'emplacement déjà réservé (« Rapprochement IPE — à venir », posé dans le lot précédent). Avantages : écran déjà accessible depuis la mission, déjà lecture-seule + import, déjà au courant des fichiers complémentaires actifs ; pas de nouvelle route de navigation à créer. C'est un écran de **données/diagnostic**, pas une étape d'audit — cohérent avec la nature du rapprochement IPE (vérification technique, pas une tâche séquentielle du workflow).
- **Option B** : étape dédiée dans `workflowPhases`, positionnée avant `materialite`. Inconvénient : ajouterait une 12ᵉ étape à la barre de progression alors que CLAUDE.md et le §0 de ce plan présentent justement le Module 1 comme une brique séparée du workflow d'audit existant — risque de confusion avec les 9 étapes qui fonctionnent déjà.

→ **Recommandation : Option A** pour le détail/calculs.

**Ajout retenu — point de contrôle visible dans la barre latérale** (indépendant du choix ci-dessus, et sans toucher au décompte des 11 étapes) :

- Dans `GroupingAnalyse.vue`, un bloc **« Fiabilité IPE »** est inséré dans le template **entre le bloc Phase 1 – Planification et le bloc Phase 2 – Exécution**, en dehors du tableau `workflowPhases` (donc jamais compté dans la progression ni dans les 11 étapes — pas de nouvelle `key` ajoutée au tableau).
- **Statuts affichés** (dérivés de `Mission1.ipe`, lu via le même appel `GET /api/v1/missions/<id>/ipe` que §3) :
  - `verrou_applicable === false` → **« Antérieure au verrou »** (libellé neutre, pas une alerte — mission créée avant l'activation du verrou, jamais bloquée, §2 bis).
  - `verrou_applicable === true` et `ipe_fiabilite_validee` absent/`null` → **« Non commencé »**.
  - `verrou_applicable === true` et une évaluation existe mais pas encore validée (au moins un module `a_traiter`/`ecart`, ou validation manager en attente, §5) → **« En cours »**.
  - `verrou_applicable === true` et `ipe_fiabilite_validee === true` → **« Validé »**.
- **Lien** : bouton/lien vers `FichiersComplementairesView.vue` (route déjà existante `fichiersComplementaires`) pour accéder au détail (Option A).
- Ce bloc est un **composant d'affichage pur** (lecture de l'état, pas de logique de blocage) — le blocage réel reste porté par le hook backend (§3), ce bloc n'est qu'un reflet pour l'utilisateur.

## 7. Tests prévus (pytest)

Dans `api/tests/`, sur le modèle du lot import (fonctions pures, pas de DB réelle nécessaire autant que possible) :

- `test_verrou_ipe_service.py` :
  - le hook/la fonction de décision renvoie *laisser passer* quand `IPE_VERROU_ACTIF` est désactivé, quel que soit l'état de `ipe_fiabilite_validee` (non-régression §2) ;
  - renvoie *bloquer* seulement pour un endpoint de la liste verrouillée, avec `ipe_fiabilite_validee=False` et le verrou actif ;
  - laisse toujours passer les endpoints de la liste « jamais verrouillée » (ex. `controle_coherence_route`), même verrou actif + `False`.
- `test_rapprochement_ipe_service.py` (sur un jeu de données fictif, comme `tests/conftest.py` du lot import) :
  - écart global correct sur un cas équilibré et un cas en écart construit ;
  - détection des tiers présents d'un seul côté (balance générale seule / auxiliaire seule) ;
  - un `TODO(spec)` non résolu (ex. tolérance) ne doit jamais faire planter le calcul — juste ne pas trancher automatiquement (valeur `None`/« non évalué » plutôt qu'une décision implicite).

## 8. Décisions à faire trancher avant de coder

**Décisions résolues par les 3 ajustements validés** (gardées ici pour mémoire, non bloquantes pour la suite) :
- ~~Missions existantes à l'activation~~ → résolu par `verrou_applicable` figé à la création (§2 bis) : chaque mission porte sa propre règle, plus de bascule globale à trancher.
- ~~`ipe_fiabilite_validee` absent/`null` au moment du contrôle de blocage~~ → résolu (§3, point 6) : absent/`null` est traité comme **bloquant** pour une mission où `verrou_applicable=true` ; **jamais bloquant** si `verrou_applicable=false`.
- ~~`generate_efi` : route où le gating serait impossible~~ → résolu : reste accessible par construction, documentée comme **limite connue et acceptée** (§3), pas une question ouverte.

**Décisions encore ouvertes :**

1. **Qui peut valider** : aucun contrôle de rôle n'existe sur les missions aujourd'hui — qui a le droit de valider `ipe_fiabilite_validee` en pratique tant que ce n'est pas réglé ?
2. **R4 croisé** : confirmé hors périmètre (CLAUDE.md) — à ne pas réintroduire par erreur dans l'implémentation du §4.
3. **Rattachement tiers ↔ compte collectif, tolérance d'écart, traitement des orphelins, conditions de passage à `TRUE`** (§4) : `TODO(spec: CAC-IPE-01 §2)`, non tranchables sans la spec.
4. **`utilisateur_id` dans l'historique** (§1) : `null` acceptable pour cette ossature, ou faut-il un minimum d'identification avant de livrer ce lot ?

## 9. Tâches de développement (ordre proposé, aucune à commencer sans validation du plan)

1. Ajouter `IPE_VERROU_ACTIF` (`env.template`, lecture dans un service dédié), désactivé par défaut.
2. Créer le schéma marshmallow du sous-document `Mission1.ipe` (`api/src/schemas/`), incluant `verrou_applicable`.
3. Créer `api/src/services/verrou_ipe_service.py` : lecture/écriture de `Mission1.ipe`, fonction de décision « cet endpoint, pour cette mission, est-il bloqué ? » (logique §3 : `verrou_applicable` d'abord, puis `ipe_fiabilite_validee`).
4. Capturer `verrou_applicable` **à la création de la mission** (§2 bis) : identifier le point d'insertion le moins intrusif (service appelé juste après `new_assign`, ou hook additif) sans modifier la logique métier existante de création de mission.
5. Enregistrer le hook `before_request` sur le blueprint `mission` depuis `api/src/routes/__init__.py` (aucune modification de `api/src/mission/` ni `model.py`).
6. Créer `api/src/services/rapprochement_ipe_service.py` (IPE-1/2/3 : sommes, écart global, tiers orphelins) en réutilisant `fichiers_complementaires_service` et `controle_preliminaire_service` existants.
7. Créer les endpoints `GET /api/v1/missions/<id>/ipe` (état actuel) et `POST /api/v1/missions/<id>/ipe/evaluer` (lance le calcul §4) dans `resources/`.
8. Frontend : composant « Fiabilité IPE » dans la barre latérale de `GroupingAnalyse.vue`, positionné entre Phase 1 et Phase 2, avec ses 4 statuts (§6) et son lien vers `FichiersComplementairesView.vue` — hors de `workflowPhases`, aucun impact sur le décompte des 11 étapes.
9. Frontend : appel de l'état IPE dans `GroupingAnalyse.vue`, indicateur `locked` par étape (§3), message explicatif, garde-fou dans `handleStepClick`.
10. Frontend : section « Rapprochement IPE » dans `FichiersComplementairesView.vue` (Option A, §6) — écarts, tiers orphelins, qualification, validation.
11. Tests pytest (§7), incluant un cas `verrou_applicable=false` (mission antérieure, jamais bloquée même avec `ipe_fiabilite_validee=False`).
12. Vérification de non-régression : `IPE_VERROU_ACTIF=false` (défaut) → les 9 étapes existantes et le lot import fonctionnent à l'identique ; puis activer le flag pour une nouvelle mission de test afin de vérifier le blocage effectif, en confirmant qu'une mission créée avant l'activation reste non bloquée.
13. Documenter dans `CLAUDE.md` les décisions prises sur le §8, au fur et à mesure.
