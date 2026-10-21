# CLAUDE.md — CAC PERFORM

Ce fichier cadre le travail sur la V2 de CAC PERFORM. Il s'appuie sur le code réel du dépôt (voir `RECAP_V1_CAC_PERFORM.md` pour l'état des lieux détaillé de la V1), pas sur des suppositions.

## Contexte

CAC PERFORM est un outil d'audit pour des missions de commissariat aux comptes en zone **OHADA/SYSCOHADA**, en **FCFA**, avec une interface entièrement en **français**.

La V2 **s'ajoute** à l'existant. La V1 a 9 des 11 étapes de son workflow d'audit réellement codées et fonctionnelles (contrôle de cohérence, contrôle d'intangibilité, matérialité, analyses quantitative/qualitative, présentation des comptes significatifs, grouping, états financiers préliminaires, revue analytique finale) : **on ne casse rien de ce qui fonctionne déjà**.

## Règle d'or

On développe contre le corpus de specs — **CAC-IPE-01 v1.0**, **CAC-CIR-01 v1.2**, **CAC-SEUILS-01 v1.4**, **ECH-01** — pas contre le cahier des charges général.

Ces specs **ne sont pas dans le dépôt**. Là où une règle précise manque pour les implémenter :
- **Ne rien inventer.**
- Poser un commentaire du type `TODO(spec: CAC-IPE-01 §2)` à l'endroit concerné.
- Demander confirmation avant de coder la règle manquante.

## Décisions d'architecture arrêtées

- La V2 se greffe sur la **génération moderne** de l'API : `/api/v1`, dossiers `api/src/resources/`, `api/src/services/`, `api/src/schemas/`.
- **On n'ajoute rien** dans `api/src/model.py` (fichier historique, ~7800 lignes) ni dans les routes `/cors/mission/...`. On construit propre, à côté, dans des services dédiés.
- Le nouveau parsing d'import va dans un **service dédié** (`api/src/services/`), pas dans `model.py`.
- **Code mort à ignorer** : `api/src/customer/` (`routes.py`, `routes_new.py`), `api/src/collaborateur/`, `api/src/model_controle_intangibilite.py`. Ne pas s'en servir de référence. Ne pas le supprimer pour l'instant.

## Priorité de campagne

1. Refonte de l'import (balances + fichiers manquants + mapping de colonnes).
2. Verrou IPE (Module 1).

## Séquencement métier

```
import → contrôle IPE / rapprochements → ouverture des cycles → sélection → courriers → transverses
```

## Module 1 (IPE-01) — le verrou

Le Module 1 est une **nouvelle brique**, pas un détournement de l'étape 3 existante (« Contrôle de cohérence »), qui reste un contrôle **arithmétique sur une seule balance** (débit = crédit) et n'est pas modifiée par ce chantier.

Règles connues :
- **IPE-1** : clients ↔ comptes `41x` (racine provisoire « 41 », paramètre par défaut du cahier des charges §2.4 — `RACINES_COLLECTIFS` dans `rapprochement_ipe_service.py`, `TODO(spec: CAC-IPE-01 §2)`)
- **IPE-2** : fournisseurs ↔ comptes `40x` (racine « 40 », même paramètre)
- **IPE-3** : immobilisations ↔ comptes `2xxx`
- **R4 croisé** : à arbitrer — **ne pas développer** tant que ce n'est pas tranché.
- **IPE-GLOBAL-01** : si `ipe_fiabilite_validee = FALSE`, le cycle est **bloqué**.

## Terminologie opposable

Toujours dire **« poste significatif »**. Ne jamais dire « PRAS ».

## Charte d'interface (obligatoire pour tout nouvel écran)

Relevée sur le code réel de `ClientSpace.vue`, `ClientsView.vue`, `MissionsView.vue` et `GroupingAnalyse.vue` — pas inventée. Tout nouvel écran V2 doit s'y conformer ; ne pas introduire une nouvelle convention sans la documenter ici.

**Maquettes (`docs/maquettes/`) et charte — règle définitive** : la maquette fait foi pour la **disposition** (ordre des cartes, panneau latéral, largeurs, espacements, arrondis, tailles de police) ; la charte ci-dessous fait foi pour les **couleurs** et la **police**. Les couleurs et la police des maquettes sont des estimations faites à partir de captures d'écran : ne jamais les reprendre (pas de jeton de couleur propre aux maquettes, pas de police propre à un écran).

**Palette** (définie en `@theme` CSS, `clients/src/assets/style.css` — Tailwind v4, pas `tailwind.config.js`) :
- `blue-ycube` `#043C5D` — couleur principale (sidebar, en-têtes de tableau, titres, boutons primaires). Variantes : `blue-ycube-1` `#053D5E`, `blue-ycube-2` `#8faadc`, `blue-ycube-3` `#156082`.
- `green-ycube` `#589654` / `green-ycube-2` `#7FC241` — vert (actions positives, validation).
- `gray-ycube` `#F2F2F2` / `gray-ycube-1` `#B2B2B2` — gris neutres.
- Les classes `.btn-*` de `style.css` existent mais ne sont utilisées par aucun des 4 écrans de référence : ne pas les introduire ; composer directement les classes Tailwind ci-dessous.

**En-tête de page** (référence : `ClientSpace.vue`, la fiche client) — barre blanche en tête du contenu, `bg-white shadow-sm px-6 py-4 flex items-center justify-between` :
- gauche : retour en **lien**, jamais un bouton plein — `text-blue-ycube font-semibold hover:underline flex items-center gap-2` + icône `fa-solid fa-arrow-left` ;
- centre : titre `text-xl font-bold text-blue-ycube`, sous-titre `text-sm text-gray-500` ;
- droite : groupe d'actions, `flex gap-3`.

**Cartes** : fond blanc, coins `rounded-xl`, `shadow` simple (jamais `shadow-lg`/`shadow-xl` hors modale) — `bg-white rounded-xl shadow p-6` (carte d'information, `ClientSpace.vue`) ou `p-4` pour une carte plus dense (liste, `ClientsView.vue`).

**Tableaux** — en-tête **bleu marine**, texte blanc (référence : tableau des missions dans `ClientSpace.vue`) :
```html
<table class="min-w-full text-sm">
  <thead class="bg-blue-ycube text-white h-12 text-left">
    <tr><th class="px-3">…</th></tr>
  </thead>
  <tbody>
    <tr class="h-12 border-b hover:bg-gray-50"><td class="px-3">…</td></tr>
  </tbody>
</table>
```
(`ClientsView.vue`/`MissionsView.vue` ont par endroits un en-tête `bg-gray-100 text-gray-700`, plus ancien — **l'en-tête bleu marine de `ClientSpace.vue` est la convention à suivre pour tout nouvel écran**.)

**Boutons** :
- *Primaire* : fond plein coloré (`bg-blue-ycube text-white` ou `bg-green-ycube-2 text-white` selon la nature de l'action), `font-semibold`, coins `rounded-lg`/`rounded-xl`, `hover:` fonce la couleur. Ex. `ClientSpace.vue` « Nouvelle mission » : `px-5 py-2 rounded-lg bg-green-ycube-2 text-white font-semibold hover:bg-green-ycube transition`.
- *Secondaire* : contour, pas de fond — `border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition` (« Annuler »), ou variante colorée `border border-blue-ycube text-blue-ycube font-semibold hover:bg-blue-ycube hover:text-white transition` (« Modifier client »).
- *Destructeur* : `bg-red-500 text-white rounded hover:bg-red-600` (petit, dans une ligne de tableau).
- *Pagination* : `px-3 py-1 border rounded disabled:opacity-50`.

**Titres / libellés / valeurs** : titre de page `text-xl font-bold text-blue-ycube` ; titre de section `font-semibold text-sm uppercase text-blue-ycube` ; libellé `text-gray-500 text-sm` ; valeur `font-semibold text-gray-800`.

**Badges de statut** (référence : statut de mission, `MissionsView.vue`) — pilule `px-3 py-1 rounded-full text-xs font-semibold`, couleur selon le sens : positif `bg-green-100 text-green-700`, négatif/écart `bg-red-100 text-red-700`, neutre/en attente `bg-orange-100 text-orange-700`, « rien à signaler »/non applicable `bg-gray-100 text-gray-700`. Le rouge est réservé à un vrai écart, jamais à « rien à comparer ».

**Modales** (référence : `ClientsView.vue`) — fond `fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4` ; panneau `bg-white rounded-2xl w-full max-w-3xl p-6 relative max-h-[90vh] overflow-auto`.

**Mise en page/défilement** : toute vue rendue par `pageLayout.vue` porte sa propre hauteur et son propre défilement à la racine — `h-full w-full overflow-y-auto` (jamais `h-screen`/`min-h-screen`, qui dépasse la hauteur réellement allouée dès que le `Header` est affiché, et rend le bas de l'écran inaccessible).

## Test de parcours de l'interface

**Après chaque lot qui touche au frontend, lancer le test de parcours** : `npm run test:parcours` depuis `clients/` (API Flask et Vite démarrés). Il clique sur les boutons de navigation principaux (liste des clients, fiche client, liste des missions, barre latérale, Fichiers complémentaires) et vérifie l'écran ouvert et l'absence d'erreur en console. Il crée puis supprime un client et une mission fictifs (`api/parcours_donnees_test.py`, marqueur `test_parcours`). Captures dans `clients/tests/parcours/captures/` (non commitées). Ajouter une étape au parcours pour tout nouveau bouton de navigation.

## Fins de ligne

**Ne jamais modifier les fins de ligne d'un fichier. Avant chaque commit, vérifier `git diff --stat` : un nombre de lignes anormalement élevé signale un problème de fins de ligne.** Ce dépôt a `core.autocrlf=true` et des fichiers enregistrés en CRLF (ex. `GroupingAnalyse.vue`) comme en LF : une réécriture complète d'un fichier peut convertir toutes ses lignes. Contrôle : `git diff --stat` comparé à `git diff --stat --ignore-cr-at-eol` (les deux doivent donner le même nombre de lignes). Pour enregistrer un fichier CRLF tel quel : `git -c core.autocrlf=false add <fichier>`.

## Point de sécurité connu (à garder en tête, pas à régler maintenant)

Aujourd'hui, **aucune authentification ni cloisonnement par mission** ne s'applique aux clients et aux missions (voir `RECAP_V1_CAC_PERFORM.md`, section 5). Ce chantier ne refait pas l'authentification. On pose seulement, dans le nouveau code, les bases d'un filtrage par mission (ex. prévoir un champ/paramètre de mission dans les nouveaux services), sans l'appliquer rétroactivement à l'existant.

## Décisions prises durant le développement (import refondu)

- **`Mission1.balances` n'est pas restructuré** dans ce lot : on garde la liste actuelle de `_id` de balances générales, compatible avec `api/src/model.py`. Les fichiers complémentaires (auxiliaires, immobilisations) sont tracés séparément dans `Balance.mission_id` + `Balance.type`, pas dans `Mission1.balances`.
- **Collection `MappingImport`** : conçue librement côté développement, avec deux contraintes imposées — un mapping est identifié par `(id_client, logiciel_comptable)`, et chaque sauvegarde crée une nouvelle version horodatée (`version`, `created_at`) plutôt que d'écraser la précédente.
- **Contrôles avant import d'un fichier complémentaire** (`api/src/services/verification_fichier_service.py`) — provisoires : ce sont des **alertes**, jamais un refus (l'utilisateur annule ou importe quand même). Type : alerte si moins de la moitié des comptes reconnus relèvent de la famille attendue (41x clients, 40x fournisseurs, 2x immobilisations) — seuil `TODO(décision)` ; codes tiers alphanumériques = non vérifiable, pas d'alerte. Exercice : alerte si des années sont lues (nom du fichier, lignes de titre) et qu'aucune n'est l'exercice audité — tolérance exacte `TODO(spec)`.
- **Action « Retirer »** : archive la version active (`actif=False` + `retrait` {utilisateur, commentaire ≥ 15 caractères, horodatage}), rien n'est supprimé ; utilisateur identifié obligatoire. La version précédente n'est **pas** réactivée. Si le fichier avait servi à une validation IPE positive, celle-ci est invalidée automatiquement (comme un remplacement).

- **Balance générale N — import V2** (`api/src/services/balance_generale_service.py`, `POST /api/v1/missions/<id>/balance-generale`, carte « Balance générale » de Fichiers complémentaires) : remplacement de la balance N d'une mission **existante** ; la création de mission reste sur l'import V1. Document `Balance` de **même forme** que l'import V1 (lu par `model.py` sans changement), remplacé à la **même position** dans `Mission1.balances` (la V1 lit N en `[0]`, N-1 en `[1]`) ; l'ancien document n'est jamais supprimé (`remplace_balance_id`). Invalide une validation IPE positive.
- **Sous-totaux d'une balance générale** (règle validée, complétée) : une ligne est écartée si son numéro est le préfixe d'autres comptes du fichier **et** si, pour les trois paires (ouverture, mouvements, solde final), ses montants égalent la somme de ces comptes, **en brut ou en net** (débit − crédit) ; numéros les plus longs d'abord (pas de double comptage) ; **jamais de lecture du libellé** ; lignes écartées tracées et visibles.
- **Ligne ambiguë** (forme de sous-total, montants qui ne correspondent pas) : ni gardée ni écartée en silence. Alerte avant l'enregistrement avec l'écart par paire ; l'auditeur choisit « Écarter » ou « Garder » ; chaque choix relance la vérification (le parent peut changer de statut) ; l'import est refusé tant qu'une ligne n'a pas de décision. Choix tracé (utilisateur, horodatage) dans le document Balance et dans `Mission1.balance_generale_remplacements`.
- **Équilibre** : après retrait des sous-totaux, total débit = total crédit pour chaque paire, sinon alerte avec l'écart (alerte, pas un refus).
- **Données V1 dérivées non recalculées** au remplacement de la balance N (`balance_variation`, `grouping`, `efi`) — `TODO(décision)` pour le recalcul. Bandeau « Calculée sur une version précédente de la balance générale (version X, remplacée le …) » sur les étapes qui les utilisent (`DONNEES_PAR_ETAPE` dans `balance_generale_service.py` : seuils, analyses quantitative/qualitative, décision finale, états financiers, revue). Une donnée est considérée à jour si son empreinte a changé depuis le remplacement (recalcul par la V1, ex. étape 9 pour `balance_variation`/`grouping` ; `efi` n'est jamais recalculé).
- **Mesure d'impact** : `api/mesure_impact_sous_totaux.py --uri … [--base …]`, lecture seule (accès limité à `find`/`find_one`). **Ne la lancer sur aucune autre base que celle de développement sans accord explicite.**

## Décisions prises durant le développement (verrou IPE) — provisoires, à documenter/réviser avec CAC-IPE-01

Voir `docs/PLAN_verrou_IPE.md` pour le détail technique. Décisions tranchées pour pouvoir coder, explicitement provisoires :

- **`verrou_applicable`** : chaque mission fige, à sa création, l'état du flag global `IPE_VERROU_ACTIF` dans `Mission1.ipe.verrou_applicable` (jamais recalculé ensuite). Mission avec `verrou_applicable=true` et `ipe_fiabilite_validee` inconnu (absent/`null`) → **bloquée** (prudence par défaut). Mission avec `verrou_applicable=false` → **« antérieure au verrou »**, jamais bloquée, signalée comme telle à l'écran.
- **Validation sans contrôle de rôle** : en l'absence de tout système d'authentification/droits sur les missions (point de sécurité connu, ci-dessus), la validation manager de `ipe_fiabilite_validee` est enregistrée sans vérifier qui valide ; `utilisateur_id` à `null` est accepté dans l'historique pour cette ossature.
- **⚠️ Ne jamais activer `IPE_VERROU_ACTIF` en production tant que les droits (qui valide ?) et la spec CAC-IPE-01 (rattachement tiers↔collectif, tolérance, orphelins, conditions de `TRUE`) ne sont pas intégrés.** Le flag reste à `false` par défaut précisément pour ça.
- **R4 croisé** : confirmé hors périmètre, non développé (inchangé).
- **Liste des endpoints verrouillables** : un paramètre unique (`ENDPOINTS_VERROUILLABLES` dans `api/src/services/verrou_ipe_service.py`), pas des conditions dispersées — son contenu exact reste une **décision métier à confirmer**, déduite du séquencement ci-dessus, pas une règle actée par CAC-IPE-01.
- **Rattachement tiers ↔ compte collectif, tolérance d'écart, périmètre exact IPE-3, traitement des orphelins, conditions de passage à `TRUE`** : `TODO(spec: CAC-IPE-01 §2)`, non tranchés — voir le code pour les hypothèses de travail explicitement marquées comme telles.
- **Circuit de revue** (`api/src/services/revue_ipe_service.py`) : statuts `en_cours` → `soumis_pour_revue` → `valide`, retour `en_attente_correction` sur demande du manager ; `ipe_fiabilite_validee` reste le champ de blocage et vaut `True` seulement au statut `valide`.
- **Qualification d'un écart** = une cause choisie dans `CAUSES_ECART` + un commentaire, par compte collectif. Liste **provisoire** issue du cahier des charges §2.3.4 (« Cut-off », « Erreur d'imputation », « En cours de justification », « Partie liée ») — `TODO(spec: CAC-IPE-01)`, à modifier à ce seul endroit. Exigée pour soumettre et pour valider ; une simple remarque ne qualifie pas.
- **Demandes de correction** : remarques de type `demande_correction` (dont celle créée par « Demander une correction ») ; non traitées, elles bloquent la validation (pas la re-soumission). **Une demande de correction ne peut pas être créée sans utilisateur identifié.** Seul l'auteur enregistré, identifié, peut marquer une remarque traitée ou la rouvrir, et « traitée » seulement après la réponse de l'auditeur — contrôle sur l'utilisateur envoyé par le frontend, **pas un contrôle d'accès** (`TODO(décision)` : rôles). Un utilisateur non identifié ne peut marquer aucune remarque ; une remarque informative d'auteur non identifié reste donc non traitable, sans conséquence (elle ne bloque rien).
- **Rapprochement exigé avant « Soumettre pour revue »** (décision du 20/10/2026), serveur et écran : le rapprochement doit avoir été lancé **sur les versions actuelles des fichiers**. Chaque rapprochement enregistre les fichiers utilisés (`ipe.fichiers_evalues`) ; si un fichier a été remplacé, importé ou retiré depuis, la soumission est refusée avec la raison (« Relancez le rapprochement : le fichier « … » a été remplacé. »). `revue_ipe_service.refus_rapprochement`. Modules exigés : `TODO(spec: CAC-IPE-01)`.
- **Gel après soumission** : la qualification des écarts et la justification des modules non évaluables ne sont modifiables qu'« En cours » ou « En attente de correction ».
- **Modules non évaluables** : une justification écrite par module concerné est exigée **dès « Soumettre pour revue »** (comme la qualification des écarts) et à nouveau à la validation ; leur traitement métier reste `TODO(spec: CAC-IPE-01)`.
- **Longueur minimale de 15 caractères** pour tout commentaire du circuit (validation, invalidation, demande de correction, qualification d'écart, justification).
