# 🚀 GUIDE D'INTÉGRATION DU MAPPING OHADA

## 📋 Vue d'ensemble

Deux structures JSON ont été créées pour différents cas d'usage :

### ✅ **SOLUTION 1 : Structure Simple** (RECOMMANDÉE)
- **Fichier** : `mapping_simple.json`
- **Taille** : ~150 KB
- **Performance** : O(1) pour recherche de compte
- **Usage** : Grouping automatique, recherche rapide

### 📊 **SOLUTION 2 : Structure Hiérarchique**
- **Fichier** : `mapping_hierarchique.json`
- **Taille** : ~200 KB
- **Performance** : O(n) pour recherche
- **Usage** : Affichage hiérarchique, export complet

---

## 🎯 SOLUTION RECOMMANDÉE : Structure Simple

### Structure du JSON

```json
{
  "version": "1.0",
  "date": "2026-02-13",
  "source": "Plan Comptable OHADA 2000",
  
  // Mapping direct : compte → métadonnées
  "comptes": {
    "101": {
      "grouping": 10,
      "nature": "Passif",
      "ref": "CA",
      "libelle": "Capital social",
      "libelle_groupe": "TOTAL CAPITAUX PROPRES ET RESSOURCES ASSIMILEES"
    },
    "409": {
      "grouping": 40,
      "nature": "Actif",  // ⚠️ Compte mixte !
      "ref": "BH",
      "libelle": "Fournisseurs débiteurs",
      "libelle_groupe": "CREANCES ET EMPLOIS ASSIMILES"
    }
  },
  
  // Grands groupes pour affichage
  "grands_groupes": {
    "10": {
      "sous_comptes": ["10"],
      "nature": "Passif",
      "ref": "CA",
      "libelle": "TOTAL CAPITAUX PROPRES ET RESSOURCES ASSIMILEES"
    }
  },
  
  // Index inverse : grouping → [comptes]
  "groupings": {
    "10": ["101", "102", "103", "104", "105", "106", "109"],
    "40": ["401", "402", "408", "409"]
  }
}
```

---

## 💻 INTÉGRATION BACKEND

### 1. Chargement du mapping (une seule fois au démarrage)

```python
import json

class OHADAMapper:
    def __init__(self, json_path='mapping_simple.json'):
        with open(json_path, 'r', encoding='utf-8') as f:
            self.mapping = json.load(f)
        
        self.comptes = self.mapping['comptes']
        self.grands_groupes = self.mapping['grands_groupes']
        self.groupings = self.mapping['groupings']
    
    def get_compte_info(self, numero_compte):
        """Récupérer les infos d'un compte (O(1))"""
        return self.comptes.get(str(numero_compte))
    
    def get_grouping(self, numero_compte):
        """Récupérer le numéro de grouping d'un compte"""
        info = self.get_compte_info(numero_compte)
        return info['grouping'] if info else None
    
    def get_comptes_by_grouping(self, grouping_num):
        """Récupérer tous les comptes d'un grouping"""
        return self.groupings.get(str(grouping_num), [])
    
    def get_grand_groupe_info(self, grouping_num):
        """Récupérer les infos d'un grand groupe"""
        return self.grands_groupes.get(str(grouping_num))

# Initialiser une fois
mapper = OHADAMapper()
```

### 2. Grouping automatique d'une balance

```python
def grouper_balance(balance_df, mapper):
    """
    Grouper une balance selon le mapping OHADA
    
    Args:
        balance_df: DataFrame avec colonnes ['N° compte', 'Solde N', 'Solde N-1']
        mapper: Instance de OHADAMapper
    
    Returns:
        DataFrame groupé avec totaux par grouping
    """
    
    # Ajouter les métadonnées de grouping
    balance_df['grouping'] = balance_df['N° compte'].apply(
        lambda x: mapper.get_grouping(x)
    )
    
    balance_df['nature'] = balance_df['N° compte'].apply(
        lambda x: mapper.get_compte_info(x)['nature'] if mapper.get_compte_info(x) else None
    )
    
    balance_df['ref'] = balance_df['N° compte'].apply(
        lambda x: mapper.get_compte_info(x)['ref'] if mapper.get_compte_info(x) else None
    )
    
    balance_df['libelle_groupe'] = balance_df['N° compte'].apply(
        lambda x: mapper.get_compte_info(x)['libelle_groupe'] if mapper.get_compte_info(x) else None
    )
    
    # Grouper et sommer
    grouping_result = balance_df.groupby([
        'grouping', 'nature', 'ref', 'libelle_groupe'
    ]).agg({
        'Solde N': 'sum',
        'Solde N-1': 'sum',
        'N° compte': lambda x: list(x)  # Garder la liste des comptes
    }).reset_index()
    
    # Renommer pour clarté
    grouping_result.rename(columns={'N° compte': 'comptes_detailles'}, inplace=True)
    
    return grouping_result


# Exemple d'utilisation
import pandas as pd

balance = pd.DataFrame({
    'N° compte': ['101', '102', '111', '121', '401', '409'],
    'Solde N': [1000000, 500000, 200000, 50000, -300000, 10000],
    'Solde N-1': [900000, 500000, 150000, 40000, -250000, 5000]
})

resultat = grouper_balance(balance, mapper)
print(resultat)
```

### 3. Génération du Bilan SYSCOHADA

```python
def generer_bilan(grouping_result, mapper):
    """
    Générer le Bilan SYSCOHADA à partir du grouping
    
    Returns:
        dict avec 'actif' et 'passif'
    """
    
    bilan = {
        'actif': [],
        'passif': []
    }
    
    # Séparer Actif et Passif
    for _, row in grouping_result.iterrows():
        nature = row['nature']
        
        if nature == 'Actif':
            bilan['actif'].append({
                'grouping': row['grouping'],
                'ref': row['ref'],
                'libelle': row['libelle_groupe'],
                'solde_n': row['Solde N'],
                'solde_n1': row['Solde N-1'],
                'comptes': row['comptes_detailles']
            })
        elif nature == 'Passif':
            bilan['passif'].append({
                'grouping': row['grouping'],
                'ref': row['ref'],
                'libelle': row['libelle_groupe'],
                'solde_n': row['Solde N'],
                'solde_n1': row['Solde N-1'],
                'comptes': row['comptes_detailles']
            })
    
    # Trier par ordre du Bilan (selon Ref EFI)
    bilan['actif'].sort(key=lambda x: x['ref'])
    bilan['passif'].sort(key=lambda x: x['ref'])
    
    return bilan
```

### 4. Génération du Compte de Résultat

```python
def generer_compte_resultat(grouping_result, mapper):
    """
    Générer le Compte de Résultat SYSCOHADA
    
    Returns:
        dict avec les rubriques du CR
    """
    
    # Filtrer seulement les comptes de résultat
    cr_data = grouping_result[
        grouping_result['nature'] == 'Compte de résultat'
    ].copy()
    
    # Trier par grouping (ordre des comptes 60-89)
    cr_data.sort_values('grouping', inplace=True)
    
    compte_resultat = []
    
    for _, row in cr_data.iterrows():
        compte_resultat.append({
            'grouping': row['grouping'],
            'ref': row['ref'],
            'libelle': row['libelle_groupe'],
            'montant_n': row['Solde N'],
            'montant_n1': row['Solde N-1'],
            'comptes': row['comptes_detailles']
        })
    
    return compte_resultat
```

---

## 🔥 INTÉGRATION DANS VOTRE API EXISTANTE

### Modifier votre endpoint `/mission/make_final/{id_mission}`

```python
from flask import jsonify
from your_mapper import OHADAMapper

# Initialiser le mapper (une seule fois)
mapper = OHADAMapper('path/to/mapping_simple.json')

@app.route('/mission/make_final/<int:id_mission>', methods=['GET'])
def make_final_grouping(id_mission):
    try:
        # 1. Récupérer la balance depuis la DB
        balance_n = get_balance_n(id_mission)
        balance_n1 = get_balance_n1(id_mission)
        
        # 2. Merger les balances
        balance_complete = merge_balances(balance_n, balance_n1)
        
        # 3. Appliquer le grouping OHADA
        grouping_result = grouper_balance(balance_complete, mapper)
        
        # 4. Générer Bilan et CR
        bilan = generer_bilan(grouping_result, mapper)
        compte_resultat = generer_compte_resultat(grouping_result, mapper)
        
        # 5. Retourner le résultat
        return jsonify({
            'success': True,
            'grouping': grouping_result.to_dict('records'),
            'bilan': bilan,
            'compte_resultat': compte_resultat
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

## ⚠️ GESTION DES CAS PARTICULIERS

### 1. Comptes mixtes (Actif/Passif selon le solde)

Les comptes suivants peuvent être Actif OU Passif :
- **Compte 18** : Dettes/Créances participations
- **Compte 40** : Fournisseurs
- **Compte 41** : Clients  
- **Compte 48** : HAO

**Solution** : Le mapping indique la nature principale, mais vous devez vérifier le solde :

```python
def determiner_nature_mixte(numero_compte, solde):
    """Déterminer la vraie nature d'un compte mixte"""
    info = mapper.get_compte_info(numero_compte)
    
    # Si le compte est déjà spécifique (409, 419, etc.)
    if info and info['nature'] in ['Actif', 'Passif']:
        return info['nature']
    
    # Pour les comptes génériques, regarder le solde
    if solde > 0:
        return 'Actif'
    elif solde < 0:
        return 'Passif'
    else:
        return info['nature']  # Nature par défaut
```

### 2. Comptes soustractifs (amortissements, provisions)

Ces comptes diminuent leur groupe :
- **28** : Amortissements
- **29** : Provisions pour dépréciation
- **39** : Dépréciations des stocks
- **49** : Dépréciations des créances

```python
def est_compte_soustractif(numero_compte):
    """Vérifier si un compte est soustractif"""
    prefixe = str(numero_compte)[:2]
    return prefixe in ['28', '29', '39', '49']

# Dans le grouping
if est_compte_soustractif(compte):
    montant = -abs(solde)  # Inverser le signe
else:
    montant = solde
```

---

## 🧪 TESTS À EFFECTUER

### 1. Test de performance

```python
import time

# Charger le mapping
start = time.time()
mapper = OHADAMapper()
print(f"Chargement: {(time.time() - start)*1000:.2f}ms")

# Test de recherche
start = time.time()
for i in range(10000):
    mapper.get_compte_info('101')
print(f"10k recherches: {(time.time() - start)*1000:.2f}ms")
```

### 2. Test de cohérence

```python
# Vérifier que tous les groupings ont des comptes
for grouping_num in range(10, 90):
    comptes = mapper.get_comptes_by_grouping(grouping_num)
    info = mapper.get_grand_groupe_info(grouping_num)
    
    if comptes and not info:
        print(f"❌ Grouping {grouping_num}: comptes sans grand_groupe")
    elif info and not comptes:
        print(f"❌ Grouping {grouping_num}: grand_groupe sans comptes")
```

---

## 📊 COMPARAISON DES DEUX SOLUTIONS

| Critère | Structure Simple | Structure Hiérarchique |
|---------|------------------|------------------------|
| **Taille fichier** | ~150 KB | ~200 KB |
| **Temps de chargement** | ~5ms | ~8ms |
| **Recherche compte** | O(1) - Immédiat | O(n) - Linéaire |
| **Usage mémoire** | Faible | Moyen |
| **Facilité d'usage** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Cas d'usage** | Grouping auto | Affichage complet |

---

## ✅ RECOMMANDATION FINALE

### Pour votre outil d'audit :

1. **Utilisez `mapping_simple.json`** pour :
   - ✅ Grouping automatique des balances
   - ✅ Génération Bilan/CR
   - ✅ API backend

2. **Gardez `mapping_hierarchique.json`** pour :
   - 📊 Export Excel complet
   - 📋 Documentation
   - 🔍 Consultation hiérarchique

3. **Remplacez votre `grouping.json`** actuel par `mapping_simple.json`

---

## 🚀 MIGRATION ÉTAPE PAR ÉTAPE

### Étape 1 : Backup
```bash
cp @/data/grouping.json @/data/grouping.json.backup
```

### Étape 2 : Remplacer
```bash
cp mapping_simple.json @/data/grouping.json
```

### Étape 3 : Adapter le code
- Mettre à jour la structure d'accès aux données
- Utiliser `comptes[numero]` au lieu de chercher dans une liste

### Étape 4 : Tester
- Importer une balance test
- Vérifier le grouping
- Comparer avec l'ancien résultat

### Étape 5 : Déployer
- Déployer sur l'environnement de test
- Valider avec des données réelles
- Déployer en production

---

## 📞 SUPPORT

Si vous rencontrez des problèmes :
1. Vérifier la structure du JSON
2. Tester avec le code d'exemple fourni
3. Comparer avec l'ancien mapping

**Fichiers livrés** :
- ✅ `mapping_simple.json` - Structure optimisée
- ✅ `mapping_hierarchique.json` - Structure complète
- ✅ `Mapping_OHADA_Corrige.xlsx` - Source Excel
- ✅ Ce guide d'intégration
