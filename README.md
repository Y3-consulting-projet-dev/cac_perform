# 📘 Guide de démarrage - Outil CAC PERFORM

Ce document a pour objectif de vous accompagner dans l'installation et le lancement de l'outil CAC-Perform.

## Qu'est ce que CAC-Perform ?

CAC-Perform est un outil conçu pour assister les auditeurs dans le cadre de leurs missions de commissariat aux comptes (CAC). Développé par le cabinet Y3 Audit & Conseils, il permet d’effectuer une analyse préliminaire des fichiers comptables, notamment des états financiers, utilisés au cours des missions d’audit.

## 🧾 Version actuelle

```json
version : 1.0.0
```

## ⚙️ Fonctionnalités principales

La version actuelle de l'outil permet :

* La création de dossiers clients ;
* L'initialisation de missions d’audit ;
* L’importation des balances N et N-1 relatives à une mission ;
* La réalisation des groupings (regroupements de comptes) ;
* La génération d'états financiers provisoires ;
* Le calcul des variations entre les balances ;
* L'identification des comptes significatifs ;
* La production automatique de pistes d’audit.

## 📁 Structure du dépôt Git

Le dépôt contient les trois dossiers essentiels suivants :

| Dossier   | Description                                            |
| --------- | ------------------------------------------------------ |
| `api`     | Contient le code du backend                            |
| `clients` | Contient le code du frontend                           |
| `docs`    | Contient les fichiers utiles à la base de données (BD) |

## ✅ Prérequis à l’installation

Avant de cloner le dépôt et de lancer l’application, assurez-vous d’avoir installé les éléments suivants :

### Node js + pnpm

pnpm est un gestionnaire de packages, alternative à npm ou yarn.

* Version minimale requise de Node.js : `22.17.1`
* Version minimale requise de pnpm : `10.13.1`

***Vérifier des versions***

```sh
node -v
pnpm -v
```

### Python

* Version minimale requise : `3.12.1`

### Mongo DB

* Version minimale recommandée : `2.5.5`

Pour la visualisation graphique des collections MongoDB, vous pouvez utiliser MongoDB Compass (facultatif mais pratique).

## 🚀 Mise en route

Une fois tous les prérequis installés, vous pouvez cloner le dépôt Git.

Chaque dossier (à l’exception de `docs`) contient un guide d’installation spécifique pour démarrer le frontend et le backend de manière autonome.

## 🧑‍💻 Besoin d’aide ?

Pour toute question technique ou assistance, vous pouvez contacter :

**Axel Hamilton AHOUMOUAN - <axelhamilton02@gmail.com>**





