# Plan — Circularisation (CIR-01, Modules 2 et 3) · page D

Maquettes : `docs/maquettes/2_Selection_tiers.html`, `3_Memo_selection.html`,
`4_Courriers.html`, `5_Suivi_reponses.html`. Disposition de la maquette,
couleurs et police de la charte (CLAUDE.md).

**Les specs CAC-CIR-01, CAC-SEUILS-01 et ECH-01 ne sont pas dans le dépôt.**
Ce plan ne fixe aucune règle métier : tout ce qui en dépend est listé en
questions (§5). Rien dans `api/src/model.py` ni dans `/cors` : services
dédiés dans `api/src/services/`, routes `/api/v1/missions/<id>/circularisation/...`.

Statut : plan validé le 21/10/2026. **Sous-lot a livré**, **sous-lot b livré en
partie** (voir les choix provisoires ci-dessous) ; sous-lots c, d à venir.

### Sous-lot b : choix provisoires (décidés le 21/10/2026)

- Fichiers rangés dans **GridFS** (base MongoDB, collection `cir_fichiers`),
  sans nouvelle dépendance.
- Coordonnées des tiers **saisies par l'auditeur** dans un **annuaire par
  client** (`CirCoordonnees`, une version par modification), réutilisé d'une
  mission à l'autre. Il faut une adresse ou un courriel. État d'un tiers :
  « Prêt » (courriel), « Courriel manquant » (adresse seule), « Coordonnées
  manquantes ».
- Bibliothèque `CirModele` : C1 Clients, C2 Fournisseurs, C3 Avocats,
  C4 Bailleurs, C5 Banques (maquette), **communs au cabinet**
  (`TODO(décision)`), une version par import ; champs `{{ champ }}` (syntaxe
  docxtpl) détectés dans le .docx ; champs que l'outil ne sait pas alimenter
  signalés. Liste des champs disponibles : `courriers_service.CHAMPS_DISPONIBLES`
  (`TODO(spec: CAC-CIR-01)`).
- **Non livré, en attente de décision** : génération Word / PDF et aperçu mis
  en page (bibliothèques à valider avec la personne qui gère le serveur),
  donc étapes 2 à 4 de l'écran Courriers désactivées.

### Sous-lot a : choix provisoires (en l'absence de réponse aux questions §5)

- `CirPopulation` n'est pas une collection séparée : la population est
  photographiée **dans** `CirSelection` (`population.source`, `population.ipe`,
  `population.lignes`). Même traçabilité, un document de moins.
- Circularisation **non bloquée** par le verrou (`ENDPOINTS_VERROUILLABLES`
  inchangé) et utilisable avant la validation de la fiabilité IPE : bandeau
  et état IPE figé avec la population.
- Seuls Clients et Fournisseurs ont une population ; Avocats, Bailleurs et
  Banques affichent « source à confirmer par CAC-CIR-01 ».
- Solde d'un tiers = débit − crédit (convention du rapprochement IPE) ;
  valeur de la population et valeur couverte en valeur absolue
  (`TODO(spec: CAC-CIR-01)`).
- Retenir / exclure un tiers, passer en confirmation négative : motif
  d'au moins 15 caractères et utilisateur identifié ; aucune vérification
  de rôle (« décision du Manager » enregistrée telle quelle).
- Mémo : aperçu à l'écran, figé à la soumission (`CirMemo`, une version par
  soumission), validé ou renvoyé en correction avec un commentaire d'au
  moins 15 caractères ; la sélection est figée tant que le mémo est soumis
  ou validé. Soumission refusée si le fichier source a été remplacé.
- PDF, Word, « Verser au dossier de travail », méthode automatique, graine
  et « Ajouter un tiers manuellement » : affichés, désactivés.

---

## 1. Modèle de données

Principes communs, repris du verrou IPE et de l'import :

- chaque document porte `mission_id` (base du futur cloisonnement par mission) ;
- chaque action est tracée : `utilisateur_id` (envoyé par l'écran, `null`
  accepté tant qu'il n'y a pas d'authentification, affiché « Non identifié »)
  et `horodatage` UTC ;
- rien n'est supprimé : une correction crée une nouvelle version ou une
  entrée d'historique (comme « Retirer » un fichier) ;
- les paramètres utilisés (seuils, cadence, version du modèle, graine) sont
  **figés dans le document** au moment de l'action, pour qu'un changement de
  réglage ne modifie pas un travail déjà fait ;
- un **journal de circularisation unique**, en ajout seul (`CirJournal`), est
  lu par le Journal d'audit (`journal_audit_service`, modules « Sélection des
  tiers », « Courriers », « Suivi des réponses »).

Collections proposées (noms provisoires) :

| Collection | Contenu | Traçabilité |
|---|---|---|
| `CirPopulation` | Photographie de la population d'un type de tiers à une date : source (fichier `Balance` actif : `_id`, type, version — ou saisie manuelle), lignes `{numero, libelle, solde, sens}`, total, état de la fiabilité IPE à cette date (`ipe_fiabilite_validee`, `statut_circuit`, module IPE concerné) | `cree_par`, `cree_le` |
| `CirSelection` | Une sélection par (mission, type de tiers), versionnée : `population_id`, méthode (`manuelle` \| `seuils_mus`), mode (`positif` \| `negatif` + motif + décideur), graine (sous-lot d), paramètres figés (SS/SP/TS lus à l'étape 5, sous-lot d), tiers `{numero, retenu, origine (ajout_manuel, exclusion_manuelle, au_dessus_du_seuil, tirage_mus), motif, auteur, date}`, statut du circuit, `historique[]` | chaque décision par tiers et chaque changement de statut |
| `CirMemo` | Mémo de sélection versionné : `selection_id` + version, contenu figé à la soumission, statut (brouillon → soumis → validé / correction demandée), fichiers générés (PDF, Word) | soumis par/le, validé par/le, commentaire |
| `CirCoordonnees` | Coordonnées des tiers (raison sociale, adresse postale, courriel, contact) — **absentes de tous les fichiers importés aujourd'hui** | saisi/modifié par/le, source |
| `CirModele` | Bibliothèque de modèles Word : code (C1 à C5), type de tiers, version, fichier, champs de fusion détectés, actif | importé par/le ; chaque import = nouvelle version |
| `CirCourrier` | Courrier généré : `selection_id`, tiers, `modele_id` + version, valeurs fusionnées figées, fichiers (PDF/Word), statut (`genere` → `envoye`) | généré par/le |
| `CirEnvoi` | Envoi d'un courrier : canal (`courriel` \| `postal`), destinataire, date J0, preuve (identifiant de message, date de dépôt), échéances calculées depuis `CADENCE_RELANCES` et figées | envoyé par/le |
| `CirRelance` | Relance d'un envoi : rang, échéance prévue, date effective, canal, automatique ou manuelle, alerte au Manager | par/le |
| `CirReponse` | Réponse reçue (versionnée) : reçue le, canal, type (accord total, accord partiel, désaccord), solde confirmé, écart calculé, pièce jointe, commentaire (≥ 15 caractères, convention existante) | saisie par/le |
| `CirAnalyseEcart` | Feuille d'analyse d'un écart constaté : montant, explication, conclusion | par/le, revue |
| `CirProcedureAlternative` | Procédure alternative pour un tiers sans réponse : nature, documentation, pièces | par/le, revue |
| `CirJournal` | Toutes les actions ci-dessus, en ajout seul : `{mission_id, horodatage, utilisateur_id, module, action, reference, detail}` | — |

Stockage des fichiers (modèles, courriers, réponses signées, mémos) : **à
décider** (voir §5, questions transverses) — aucun stockage de fichier
n'existe aujourd'hui (les imports ne gardent que les données lues).

---

## 2. Ce que la V1 calcule déjà et qui peut être relu (lecture seule)

Lecture directe de `Mission1` par un service V2, sans modifier `model.py`.

### Étape 5 — Calcul des seuils (`Mission1.materiality`)

Liste de benchmarks ; celui retenu porte `choice = true`. Champs :
`benchmark`, `factor`, `original_value`, `materiality`,
`performance_materiality`, `trivial_misstatements`, `warning`.

Calcul V1 (lu dans `model.py`, pour information) : `performance_materiality`
= 60 / 70 / 80 % de `materiality` selon le niveau de risque (80 % par
défaut au premier calcul) ; `trivial_misstatements` = 5 % de `materiality`.

| Maquette | V1 | Équivalence |
|---|---|---|
| Seuil de signification (SS) | `materiality` | **probable, à confirmer par CAC-SEUILS-01** |
| Seuil de planification (SP) | `performance_materiality` | **probable, à confirmer** |
| Seuil de remontée (TS) | `trivial_misstatements` | **à confirmer** (« remontée » ≠ « anomalies insignifiantes » selon les cabinets) |

Limites constatées :
- le choix du benchmark n'a **ni auteur ni date**, et aucune validation
  formelle : la circularisation devra figer les valeurs lues et la date de
  lecture ;
- les seuils peuvent être absents (étape 5 non faite) ou calculés sur une
  balance générale remplacée depuis (bandeau de fraîcheur existant,
  `DONNEES_PAR_ETAPE`) : à afficher, pas à recalculer ;
- l'étape 5 est elle-même verrouillable : si le verrou s'applique et que la
  fiabilité IPE n'est pas validée, les seuils peuvent ne pas exister.

### Étape 8 — Décision finale des comptes à tester (`Mission1.presentation_comptes_significatifs`)

Une ligne par poste du grouping : `compte`, `libelle`, `solde_n`,
`is_quantitatively_significant`, `is_qualitatively_significant`,
`significativite_status`, `priorite`, `materiality_threshold`…

Usage possible : indiquer, sur l'écran de sélection, si le poste « Clients »
ou « Fournisseurs » est un **poste significatif**. La correspondance poste du
grouping ↔ type de tiers est **à confirmer** (codes de grouping concernés).

---

## 3. Lien avec Fiabilité IPE

- **Population** : Clients ← balance auxiliaire clients **active** (IPE-1),
  Fournisseurs ← balance auxiliaire fournisseurs **active** (IPE-2). Lignes
  disponibles : `numero_compte` (code tiers), `libelle_compte`,
  `solde_final_debit`, `solde_final_credit`. Avocats et Bailleurs : saisie
  manuelle (« à saisir » sur la maquette). Banques : « relevés » (source à
  confirmer).
- **Signalement** (carte « Prérequis · Fiabilité IPE » de la maquette) :
  statut lu sur l'état IPE existant (`statut_affiche`, `statut_circuit`,
  `ipe_fiabilite_validee`) avec un lien « Ouvrir Fiabilité IPE ».
  Non validée → bandeau orange (charte : attente) « Rapprochement en cours,
  non validé. La population ne doit être utilisée qu'après validation de la
  fiabilité. » ; validée → vert ; antérieure au verrou → gris, mention
  « mission antérieure au verrou ».
- **Trace** : l'état IPE est figé dans `CirPopulation` et repris dans le mémo
  (« Fiabilité IPE : [statut à la date du mémo] »).
- **Fichier remplacé après la sélection** : la sélection est signalée « à
  refaire » avec la raison (même mécanisme que `rapprochement_a_jour`), sans
  être modifiée.
- **Blocage** : décision à prendre (§5) — soit les routes de circularisation
  entrent dans `ENDPOINTS_VERROUILLABLES` (paramètre unique, rien de
  dispersé), soit elles restent ouvertes avec le bandeau et la trace.

---

## 4. Découpage en sous-lots

Ordre imposé : a → b → c → d, arrêt et validation après chacun. Chaque
sous-lot : écran(s) de la maquette, entrée de la barre latérale activée,
entrées du Journal d'audit, tests serveur, test de parcours.

### a) Population, sélection manuelle, mode, mémo

Écrans 2 (sans la méthode automatique) et 3.
Population des cinq types de tiers (onglets Clients, Fournisseurs, Avocats,
Bailleurs, Banques), sélection manuelle avec motif obligatoire, mode positif
par défaut ou négatif avec motif, indicateurs (sélectionnés, valeur de la
population, valeur couverte, taux), mémo de sélection avec circuit de revue
et téléchargement PDF/Word.

### b) Modèles et courriers

Écran 4, étapes 1 à 3. Bibliothèque de modèles Word versionnés (C1 à C5),
champs de fusion, aperçu avec champs fusionnés surlignés, liste des tiers
retenus avec leur état (« Prêt », « Courriel manquant »), génération
unitaire et en lot (PDF, Word).

### c) Envoi, suivi, relances, réponses

Écran 4, étape 4, et écran 5. Envoi par courriel et postal, tableau de bord
(envoyés, réponses, en relance, écarts, sans réponse après J+45), relances
selon `CADENCE_RELANCES`, saisie des réponses dans le panneau latéral,
écarts constatés et feuille d'analyse, procédures alternatives.

### d) Sélection automatique

Écran 2, méthode « Seuils SS/SP/TS et échantillonnage MUS (ECH-01) » :
sélection au-dessus des seuils, tirage MUS reproductible avec graine
enregistrée au journal, rejouable à l'identique.

---

## 5. Par sous-lot : ce qui peut être fait sans spec, et les questions

### Questions transverses (avant le sous-lot a)

1. **Authentification** : sans elle, n'importe qui peut sélectionner,
   valider un mémo, décider d'une confirmation négative ou envoyer un
   courrier à un tiers réel. Faut-il, comme pour le verrou, livrer le
   circuit sans contrôle de rôle et interdire l'**envoi réel** tant que
   l'authentification n'existe pas ?
2. **Stockage des fichiers** (modèles, courriers, mémos, réponses signées) :
   GridFS (MongoDB) ou dossier serveur (`UPLOAD_FOLDER`) ? Durée de
   conservation ?
3. **Bibliothèques de génération** : aucune n'est installée. Proposition :
   `docxtpl` (Word, fusion) ; pour le PDF, conversion par LibreOffice en
   mode sans interface ou génération HTML → PDF (WeasyPrint). Accord sur les
   nouvelles dépendances et sur ce qui est installable sur le serveur cible ?
4. **Verrou** : la circularisation est-elle bloquée par IPE-GLOBAL-01
   (ajout dans `ENDPOINTS_VERROUILLABLES`) ?
5. **« Dossier de travail »** (« Verser au dossier de travail ») : il n'existe
   pas dans l'outil. Qu'est-ce que c'est ?

### a) Population, sélection manuelle, mode, mémo

**Faisable sans spec** : photographie de la population clients et
fournisseurs depuis les balances auxiliaires actives, avec la trace de l'état
IPE ; affichage et filtres (Tous, Sélectionnés, Non sélectionnés) ;
retenir / exclure un tiers avec motif obligatoire (≥ 15 caractères,
convention existante) ; mode positif par défaut, négatif avec motif ;
indicateurs calculés sur les soldes ; circuit du mémo (brouillon → soumis →
validé / correction demandée, même logique que le circuit IPE) ; aperçu HTML
du mémo avec les données réelles ; journal.

**Questions de spec (CAC-CIR-01)** :
1. Les cinq types de tiers sont-ils définitifs (Clients, Fournisseurs,
   Avocats, Bailleurs, Banques) ?
2. Avocats et Bailleurs : saisie libre, ou population tirée de comptes de la
   balance générale (lesquels) ?
3. Banques : population depuis les comptes 52x de la balance générale, ou
   depuis les relevés ? Toutes les banques sont-elles circularisées ?
4. Solde retenu : solde final net ? Tiers à solde nul, soldes de sens
   inverse (fournisseur débiteur, client créditeur) : inclus, exclus,
   signalés ?
5. Confirmation négative : conditions d'emploi, qui décide (le Manager —
   donc des rôles), motif minimal, mention au mémo ?
6. Mémo : contenu et mentions obligatoires (ISA 505 ?), qui le revoit,
   une version par type de tiers ou un mémo global ?
7. Une sélection peut-elle être faite avant la validation de la fiabilité
   IPE ?

**Documents manquants** : CAC-CIR-01 ; modèle de mémo du cabinet (Word) ;
référentiel des mentions ISA 505 retenu par le cabinet.

### b) Modèles et courriers

**Faisable sans spec** : import d'un modèle Word, versionnement, liste C1 à
C5 ; détection des champs de fusion ; aperçu avec champs surlignés ;
génération unitaire et en lot une fois la bibliothèque choisie (question
transverse 3) ; état « Prêt » / « Courriel manquant » ; journal.

**Questions de spec** :
1. Modèles officiels C1 à C5 (fichiers Word) et liste des champs de fusion
   attendus, avec leur syntaxe.
2. Modèles communs au cabinet ou propres à chaque client ? Qui peut les
   modifier (« profils seniors et au-delà » : rôles) ?
3. **Coordonnées des tiers** (adresse, courriel) : aucun fichier importé ne
   les contient. Source : fichier à importer, saisie manuelle, annuaire par
   client réutilisable d'une mission à l'autre ?
4. « Tableau des postes composant le solde · à alimenter depuis le grand
   livre » : **aucun grand livre n'est importé aujourd'hui.** Faut-il un
   import du grand livre (nouveau chantier), ou ce tableau est-il facultatif ?
5. Adresse de l'entité, adresse de retour Y3, référence de mission, lieu et
   date du courrier, signature : d'où viennent ces valeurs ?
6. Langue des courriers (français seul ?), papier à en-tête, logo.

**Documents manquants** : modèles Word C1 à C5 ; liste des champs de
fusion ; éventuel format d'import des coordonnées des tiers.

### c) Envoi, suivi, relances, réponses

**Faisable sans spec** : enregistrement d'un envoi (canal, destinataire,
date J0) ; échéances calculées depuis `CADENCE_RELANCES` et figées à
l'envoi ; tableau de bord et filtres de la maquette ; liste des relances
« dues » ; saisie d'une réponse (date, canal, type, solde confirmé) et
calcul de l'écart (solde comptable − solde confirmé) ; commentaire
obligatoire ; journal. Envoi postal : génération à imprimer et date de
dépôt saisie.

**Questions de spec** :
1. **Envoi par courriel** : serveur d'envoi (SMTP du cabinet ?), adresse
   d'expédition (« depuis [adresse de l'auditeur] »), suivi de remise.
   Aucune infrastructure d'envoi n'existe aujourd'hui.
2. Relances « générées automatiquement » : il n'existe aucune tâche
   planifiée dans l'outil. Relance envoyée automatiquement, ou proposée à
   l'auditeur à l'échéance ?
3. « Alerte du Manager » à J+30 : par quel canal (courriel, écran) ?
4. Rôle exact de chaque échéance (J0, J+15, J+30, J+45) et de l'échéance
   « Alternative » : délais en jours calendaires ou ouvrés ?
5. Réponses : tolérance d'écart (seuil TS ?), traitement d'un accord
   partiel, d'une réponse reçue via l'entité plutôt que directement.
6. Confirmation négative : une absence de réponse vaut-elle accord ?
7. Feuille d'analyse d'écart : contenu, conclusion, revue.
8. Procédures alternatives : liste des procédures admises (règlements
   postérieurs, factures…) et documentation exigée.

**Documents manquants** : CAC-CIR-01 (cadence, statuts, relances,
procédures alternatives) ; modèle de feuille d'analyse d'écart ;
paramètres d'envoi (SMTP, expéditeur).

### d) Sélection automatique par seuils et MUS

**Faisable sans spec** : uniquement l'infrastructure technique — générateur
pseudo-aléatoire initialisé par une graine enregistrée, tirage rejouable à
l'identique et tracé au journal ; lecture et affichage des seuils de
l'étape 5 (§2). **Aucune règle de sélection ne peut être codée sans
CAC-SEUILS-01 et ECH-01.**

**Questions de spec** :
1. Équivalence SS / SP / TS ↔ `materiality` / `performance_materiality` /
   `trivial_misstatements` de l'étape 5 (§2) ?
2. « Au-dessus du seuil » : quel seuil (SS, SP) et quelle comparaison
   (solde absolu, net) ?
3. Rôle de TS dans la sélection (exclusion des petits soldes ?).
4. MUS (ECH-01) : formule de l'intervalle d'échantillonnage, niveau de
   confiance, anomalie attendue, point de départ, traitement des éléments
   clés, des soldes de sens inverse et des soldes nuls, taille minimale ou
   maximale de l'échantillon.
5. Génération et format de la graine ; algorithme de tirage imposé ?
6. Seuils absents (étape 5 non faite) ou calculés sur une balance remplacée :
   sélection automatique refusée ou permise avec avertissement ?

**Documents manquants** : CAC-SEUILS-01 ; ECH-01 ; un exemple de tirage MUS
attendu (données et résultat) pour tester la reproductibilité.

---

## 6. Suite

Après validation de ce plan : sous-lot a, puis arrêt ; sous-lot b, arrêt ;
etc. Pour chaque sous-lot : plan court, incréments, captures comparées à la
maquette, test de parcours, fins de ligne, commit sur `version2` sans push.
