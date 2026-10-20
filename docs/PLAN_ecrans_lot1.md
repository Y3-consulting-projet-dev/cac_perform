# Plan — Écrans lot 1 : barre latérale et Fiabilité IPE améliorée

Branche `version2`. Rien dans `api/src/model.py` ni dans les routes `/cors`.
**Plan validé le 20/10/2026**, avec les précisions reportées au §5.

Maquettes de référence : `docs/maquettes/0_Barre_laterale.html` et
`docs/maquettes/1_Fiabilite_IPE.html` (copiées dans le dépôt depuis le jeu
`maquettes_CAC_PERFORM_V2`, avec `LISEZMOI.md` et les maquettes 2 à 7 des lots suivants).

Principes, conformément à CLAUDE.md :
- On reprend la **structure et le contenu** des maquettes, pas leur code. Les couleurs et
  ombres de la maquette (`#0B3654`, `#0F3A5A`, `box-shadow` marqué) sont remplacées par
  les jetons de la charte : `blue-ycube`, `blue-ycube-1`, `green-ycube-2`, `shadow`.
- Les balises `dc-import`, `sc-for` et `sc-if` sont ignorées.
- Les valeurs entre crochets viennent des données réelles.

---

## 1. Barre latérale (`GroupingAnalyse.vue`)

| Élément de la maquette | Existant | Changement |
|---|---|---|
| « Retour » | Oui | Aucun |
| « Fichiers complémentaires » (blanc si actif) | Oui, surligné quand l'écran est ouvert | Aucun |
| Progression de l'audit | Oui (`0 / 9 étapes validées`) | Aucun |
| Phase 1 – Planification | Oui (étapes 1 et 2, cases à cocher) | Aucun |
| Fiabilité IPE + statut + « Détail » | Oui, statut seul (« En cours ») | Le sous-titre ajoute le nombre de points bloquants : « En cours · 1 écart à qualifier » (voir §3.2) |
| Phase 2 – Exécution | Oui, étapes 3 à 10 dépliables, chacune cliquable | La liste des étapes 3 à 10 **reste affichée et cliquable**. Le résumé de la maquette (« Étapes 3 à 10 · … ») n'apparaît **que lorsque la phase est repliée** |
| **Circularisation** : Sélection des tiers, Courriers, Suivi des réponses | Absent | **Nouveau bloc entre la Phase 2 et la Phase 3**, avec les sous-titres de la maquette (« Module 2 · seuils SS/SP/TS, MUS », « Module 3 · modèles, génération, envoi », « Relances J0 / J+15 / J+30 / J+45 »). Les trois entrées sont marquées **« à venir »**, en grisé et non cliquables (pas de curseur main, `aria-disabled`) |
| Phase 3 – Conclusion | Oui (étape 11) | Aucun |
| **Journal d'audit**, **Paramètres** | Absents | **Nouvelles entrées en bas**, sous la Phase 3 : « à venir », non cliquables |

Points techniques :
- Les entrées « à venir » sont déclarées dans **une seule liste** (clé, libellé,
  sous-titre, `disponible: false`). Le jour où un écran est développé, il suffit de passer
  `disponible` à vrai et de brancher l'écran dans `showComponent`, comme Fiabilité IPE et
  Fichiers complémentaires.
- Elles restent **hors de `workflowPhases`** : elles ne comptent ni dans les 11 étapes ni
  dans la progression, et ne passent pas par `isValidStepKey`. Une adresse
  `?step=selection_tiers` ne doit donc pas ouvrir un écran vide.
- Le verrou IPE : les modules de circularisation viennent après le contrôle IPE dans le
  séquencement métier. Leur verrouillage par IPE-GLOBAL-01 sera à brancher quand ils
  existeront ; rien à faire tant qu'ils sont « à venir ».

## 2. Fiabilité IPE (`FiabiliteIpeView.vue`)

Organisation visée, de haut en bas :

1. **En-tête** : titre « Fiabilité IPE » et sous-titre
   « [client] · exercice audité [année] · rapprochement des informations produites par l'entité ».
2. **Carte « Circuit de revue »** : quatre étapes, actions et raison d'un blocage.
3. **Deux colonnes** : à gauche, Synthèse, Détail du module choisi et Modules non
   évaluables ; à droite, le **panneau du compte collectif** sélectionné.
4. **Commentaires généraux**, puis **Historique**. Ces deux sections ne figurent pas dans
   la maquette mais restent en bas, sans changement (voir §5, question 4).

### 2.1 Circuit de revue

| Maquette | Existant | Changement |
|---|---|---|
| Quatre étapes numérotées, l'étape en cours pleine (`blue-ycube`), les autres grises | Un seul badge de statut (« En cours ») | Bande de quatre étapes (1 · En cours, 2 · Soumis pour revue, 3 · En attente de correction, 4 · Validé) d'après `statut_circuit`. Les étapes déjà franchies sont visibles comme telles (coche discrète) |
| Badge « Antérieure au verrou » | Texte en italique sous le titre | Badge gris à droite du titre ; la phrase explicative reste en info-bulle ou en petit texte |
| « Relancer le rapprochement » | « Lancer le rapprochement IPE-1/2/3 » | Libellé « Lancer » si jamais évalué, « Relancer » sinon |
| « Soumettre pour revue » désactivé + raison à côté | Désactivé + raison en info-bulle et en liste sous les boutons | **Raison affichée à côté du bouton**, en une phrase courte : « Avant de soumettre : 1 écart à qualifier, 2 justifications à écrire ». Le même calcul sert à la barre latérale |
| « Commentaires généraux (0) » à droite | Section en bas, sans lien | **Lien d'ancrage** avec compteur, qui fait défiler vers la section |

**Actions selon le statut (décision)** : les actions **sans objet** dans le statut courant
sont masquées. L'**action attendue** reste toujours visible, **désactivée si besoin**, avec
la raison du blocage écrite à côté (comme « Soumettre pour revue » sur la maquette :
écart à qualifier, justification manquante, demande de correction non traitée,
utilisateur non identifié).

| Statut du circuit | Action attendue (toujours visible) | Autres actions affichées |
|---|---|---|
| En cours | Soumettre pour revue | Relancer le rapprochement |
| Soumis pour revue | Valider la fiabilité IPE | Demander une correction |
| En attente de correction | Soumettre pour revue | Relancer le rapprochement |
| Validé | — | Invalider |

Les fenêtres de confirmation actuelles (validation, invalidation, demande de correction,
toutes avec un commentaire de 15 caractères au moins) **sont conservées telles quelles**.

### 2.2 Synthèse

| Maquette | Existant | Changement |
|---|---|---|
| Colonnes Module, **Fichier**, Statut, Écart global | Module, Statut, Écart global | Colonne **Fichier** : « Balance auxiliaire clients · v1 » ou « Aucun fichier importé » |
| Ligne du module affiché en détail mise en avant | Pas de sélection | **Clic sur une ligne** : affiche le détail de ce module. Par défaut, le premier module en écart, sinon le premier évalué |
| Libellés « IPE-1 · Clients (racine 41) » | « IPE-1 — Clients (comptes 41x) » | Libellés de la maquette, la racine lue dans le libellé actuel |

### 2.3 Détail par compte collectif

| Maquette | Existant | Changement |
|---|---|---|
| Titre « IPE-2 · Détail par compte collectif » + lien « Voir le fichier dans Fichiers complémentaires » | Une carte par module, tous affichés | **Un seul détail**, celui du module choisi. Le lien ouvre Fichiers complémentaires dans la zone principale, comme le bouton de la barre latérale |
| Colonnes Compte, Balance générale, Auxiliaire, Tiers, Écart | Mêmes colonnes, sous d'autres libellés | Libellés de la maquette, montants avec sens D/C |
| **Qualification** : badge « À qualifier » / « Qualifiée » | Badge dans le bloc d'écart sous le tableau | Colonne du tableau. « — » pour une ligne sans écart |
| **Remarques** : bouton « Commenter · N » | Blocs de remarques sous le tableau | Colonne du tableau. Le bouton **ouvre le panneau latéral** du compte |
| Ligne sélectionnée mise en avant | — | Fond clair sur la ligne dont le panneau est ouvert |
| Encart « 16 tiers de l'auxiliaire sans compte collectif… (408, 409, 481…) » + « Voir la liste » | Deux phrases grises (orphelins des deux côtés) | Encart de la maquette. « Voir la liste » ouvre une fenêtre avec la liste complète. Les collectifs de la balance générale sans tiers restent signalés dans le même encart. Leur traitement reste `TODO(spec: CAC-IPE-01)` |
| IPE-3 (non montré dans la maquette) | Tableau propre aux immobilisations | Même principe : colonnes Qualification et Remarques ajoutées au tableau IPE-3. Il garde ses colonnes Compte, Nature, Balance générale, Fichier, Biens, Écart |

**Les blocs d'écart actuels sous le tableau disparaissent** : qualification et remarques
passent dans le panneau.

### 2.4 Panneau latéral du compte collectif (nouveau)

Contenu, dans l'ordre de la maquette :
- **Titre** « Écart · compte [n°] », avec le montant et le nombre de tiers rattachés,
  et un bouton Fermer.
- **Qualification** : liste des causes (`CAUSES_ECART`), commentaire (15 caractères au
  moins), bouton « Enregistrer la qualification ». S'il existe déjà une qualification,
  elle est affichée (auteur, date) et modifiable selon les règles actuelles : gel après
  soumission.
- **Fil des remarques (N)** : type (Information ou Demande de correction), auteur, date,
  texte. Les actions actuelles sont **conservées** dans le fil : « Répondre », et
  « Marquer traitée » ou « Rouvrir » pour l'auteur identifié, après la réponse. La
  maquette ne les montre pas, mais les supprimer casserait le circuit de revue.
- **Nouvelle remarque** : texte, type, bouton « Ajouter ». « Demande de correction » reste
  impossible sans utilisateur identifié.

Comportement :
- **Grand écran** : colonne de droite, qui reste visible au défilement (`sticky`).
- **Écran étroit** : le panneau passe sous le détail.
- **Style** : la maquette lui donne une ombre marquée. La charte réserve `shadow-lg` aux
  modales : j'utilise `shadow` et une bordure `blue-ycube` pour le distinguer.
- **Ouverture** : il s'ouvre par « Commenter » ou par un clic sur une ligne en écart.
  Un seul panneau est ouvert à la fois.

### 2.5 Modules non évaluables

| Maquette | Existant | Changement |
|---|---|---|
| Carte « Modules non évaluables · Justification », un champ par module | Un bloc de justification dans chaque carte de module | **Regroupés dans une seule carte** sous le détail. Mêmes règles : 15 caractères au moins, gel après soumission, auteur et date affichés |

### 2.6 Hors maquette mais conservé

- **Commentaires généraux** (remarques sans compte) : section actuelle, atteinte par le
  lien du circuit de revue.
- **Historique** : tableau actuel, inchangé.
- **Fenêtres de confirmation** : inchangées.

## 3. Côté serveur

### 3.1 Ce qui ne demande aucun changement

Toutes les données affichées par les deux maquettes existent déjà.

| Besoin | Source existante |
|---|---|
| Statut du circuit, étape en cours | `GET /api/v1/missions/<id>/ipe` → `statut_circuit`, `statut_affiche`, `verrou_applicable` |
| Écarts, tiers rattachés, orphelins | `derniere_evaluation.detail_collectifs` (`nb_tiers_rattaches`), `tiers_orphelins` |
| Qualifications, remarques par compte, justifications | `qualifications_ecarts`, `remarques` (`module` + `numero_compte`), `justifications_non_evaluables` |
| Colonne « Fichier » (nom, version) | `GET /api/v1/missions/<id>/fichiers-complementaires` |
| Client et exercice de l'en-tête | `GET /api/v1/missions/<id>` puis `GET /api/v1/clients/<id_client>` |
| Toutes les actions (évaluer, soumettre, qualifier, remarquer, valider…) | Endpoints `/api/v1/missions/<id>/ipe/...` existants, sans changement |
| Barre latérale : « 1 écart à qualifier » | Même `GET .../ipe`, déjà chargé par `GroupingAnalyse.vue` |

### 3.2 Ce qui demande un changement

- **Aucun endpoint à créer, aucune donnée absente.**
- **Côté écran seulement : un calcul partagé.** Le décompte « N écarts à qualifier,
  N justifications à écrire, N demandes de correction non traitées » existe aujourd'hui
  dans `FiabiliteIpeView.vue`. Il reproduit `revue_ipe_service.ecarts_non_qualifies` et
  les fonctions voisines. Je le déplace dans `clients/src/utils/circuitIpe.js` pour que
  la barre latérale et l'écran utilisent le même. Le serveur reste la référence et refuse
  toujours une action non permise.

## 4. Découpage en incréments (après validation)

Chaque incrément : build propre, `npm run test:parcours`, captures dans Chrome comparées
à la maquette, commit sur `version2`.

1. `circuitIpe.js` (calcul partagé), sans changement visible. Pytest, build, test de parcours.
2. Barre latérale : bloc Circularisation, Journal d'audit, Paramètres « à venir », sous-titre
   IPE. Test de parcours : nouvelle étape qui vérifie que les entrées « à venir » ne
   changent pas d'écran.
3. Fiabilité IPE, haut d'écran : en-tête, circuit en quatre étapes, actions selon le
   statut, raison du blocage, lien vers les commentaires généraux.
4. Synthèse avec colonne Fichier, sélection du module, détail unique avec colonnes
   Qualification et Remarques, encart des tiers orphelins avec « Voir la liste », lien
   vers Fichiers complémentaires.
5. Panneau latéral : qualification et fil des remarques. Suppression des blocs sous le
   tableau. Carte « Modules non évaluables ». Test de parcours : ouverture du panneau par
   « Commenter », et lien « Voir le fichier dans Fichiers complémentaires ».

Le circuit de revue complet (qualifier, remarquer, soumettre, demander une correction,
répondre, marquer traitée, valider, invalider) sera rejoué dans Chrome sur une mission
fictive avant le dernier commit.

## 5. Décisions (20/10/2026)

1. **Maquettes** copiées dans `docs/maquettes/`.
2. **Actions** : actions sans objet masquées ; l'action attendue reste visible,
   désactivée si besoin, avec la raison du blocage à côté (§2.1).
3. **Phase 2** : la liste des étapes 3 à 10 reste affichée et cliquable ; le résumé
   n'apparaît que lorsque la phase est repliée (§1).
4. **Historique et commentaires généraux** gardés en bas de l'écran, avec en plus le lien
   « Commentaires généraux (n) » en haut, dans la carte du circuit de revue (§2.1).
