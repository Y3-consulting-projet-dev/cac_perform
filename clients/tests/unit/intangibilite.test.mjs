// Tests de la présentation des textes du contrôle d'intangibilité
// (src/utils/intangibilite.js). Lancement : npm run test:unit.
import { test } from 'node:test'
import assert from 'node:assert/strict'

import { conclusionCourte, montantsEnFrancais } from '../../src/utils/intangibilite.js'

const ESPACE = ' ' // séparateur des milliers de Intl fr-FR

test('conclusion courte : partie avant « - »', () => {
  assert.equal(conclusionCourte('Écart significatif détecté - Nécessite une justification'), 'Écart significatif détecté')
  assert.equal(conclusionCourte('Compte supprimé ou reclassé - Vérifier la légitimité'), 'Compte supprimé ou reclassé')
  assert.equal(conclusionCourte('Sans tiret'), 'Sans tiret')
  assert.equal(conclusionCourte(null), '')
})

test('montants du texte V1 au format français, N-1 intact', () => {
  assert.equal(montantsEnFrancais("Écart de 53898096.0 entre l'ouverture de l'exercice N (334911894.0) et la clôture de l'exercice N-1"),
    `Écart de 53${ESPACE}898${ESPACE}096 entre l'ouverture de l'exercice N (334${ESPACE}911${ESPACE}894) et la clôture de l'exercice N-1`)
  assert.equal(montantsEnFrancais("un solde d'ouverture de -10000.0, mais"), `un solde d'ouverture de -10${ESPACE}000, mais`)
  assert.equal(montantsEnFrancais('un solde de clôture de 0.0, mais'), 'un solde de clôture de 0, mais')
})
