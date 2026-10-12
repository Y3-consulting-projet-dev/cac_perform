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
- **IPE-1** : clients ↔ compte `411`
- **IPE-2** : fournisseurs ↔ comptes `40x`
- **IPE-3** : immobilisations ↔ comptes `2xxx`
- **R4 croisé** : à arbitrer — **ne pas développer** tant que ce n'est pas tranché.
- **IPE-GLOBAL-01** : si `ipe_fiabilite_validee = FALSE`, le cycle est **bloqué**.

## Terminologie opposable

Toujours dire **« poste significatif »**. Ne jamais dire « PRAS ».

## Point de sécurité connu (à garder en tête, pas à régler maintenant)

Aujourd'hui, **aucune authentification ni cloisonnement par mission** ne s'applique aux clients et aux missions (voir `RECAP_V1_CAC_PERFORM.md`, section 5). Ce chantier ne refait pas l'authentification. On pose seulement, dans le nouveau code, les bases d'un filtrage par mission (ex. prévoir un champ/paramètre de mission dans les nouveaux services), sans l'appliquer rétroactivement à l'existant.

## Décisions prises durant le développement (import refondu)

- **`Mission1.balances` n'est pas restructuré** dans ce lot : on garde la liste actuelle de `_id` de balances générales, compatible avec `api/src/model.py`. Les fichiers complémentaires (auxiliaires, immobilisations) sont tracés séparément dans `Balance.mission_id` + `Balance.type`, pas dans `Mission1.balances`.
- **Collection `MappingImport`** : conçue librement côté développement, avec deux contraintes imposées — un mapping est identifié par `(id_client, logiciel_comptable)`, et chaque sauvegarde crée une nouvelle version horodatée (`version`, `created_at`) plutôt que d'écraser la précédente.
