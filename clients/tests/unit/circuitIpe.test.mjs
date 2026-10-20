// Tests du calcul partagé des points bloquants du circuit de revue IPE
// (src/utils/circuitIpe.js). Lancement : npm run test:unit (node --test, sans dépendance).
import { test } from 'node:test'
import assert from 'node:assert/strict'

import * as circuit from '../../src/utils/circuitIpe.js'

const CAUSES = ['Cut-off', "Erreur d'imputation", 'En cours de justification', 'Partie liée']

function etatFictif(extra = {}) {
  return {
    statut_circuit: 'en_cours',
    causes_ecart: CAUSES,
    modules: {
      ipe_1_clients: { statut: 'ok', derniere_evaluation: { detail_collectifs: [{ numero_compte: '41', ok: true }] } },
      ipe_2_fournisseurs: {
        statut: 'ecart',
        derniere_evaluation: { detail_collectifs: [{ numero_compte: '401', ok: false }, { numero_compte: '408', ok: true }] },
      },
      ipe_3_immobilisations: { statut: 'non_evaluable', derniere_evaluation: { detail_collectifs: [] } },
    },
    qualifications_ecarts: [],
    justifications_non_evaluables: {},
    remarques: [],
    ...extra,
  }
}

test('un écart réel non qualifié et un module non évaluable non justifié bloquent', () => {
  const etat = etatFictif()
  assert.deepEqual(circuit.ecartsNonQualifies(etat), ['ipe_2_fournisseurs:401'])
  assert.deepEqual(circuit.modulesNonEvaluablesSansJustification(etat), ['ipe_3_immobilisations'])
  assert.equal(circuit.phraseBlocages(etat), '1 écart à qualifier, 1 justification à écrire')
})

test('une qualification exige une cause de la liste du serveur ET un commentaire', () => {
  const sansCommentaire = etatFictif({ qualifications_ecarts: [{ module: 'ipe_2_fournisseurs', numero_compte: '401', cause: 'Cut-off', commentaire: ' ' }] })
  assert.equal(circuit.ecartsNonQualifies(sansCommentaire).length, 1)
  const causeInconnue = etatFictif({ qualifications_ecarts: [{ module: 'ipe_2_fournisseurs', numero_compte: '401', cause: 'Autre', commentaire: 'Explication suffisante' }] })
  assert.equal(circuit.ecartsNonQualifies(causeInconnue).length, 1)
  const complete = etatFictif({ qualifications_ecarts: [{ module: 'ipe_2_fournisseurs', numero_compte: '401', cause: 'Cut-off', commentaire: 'Factures de décembre reçues en janvier' }] })
  assert.deepEqual(circuit.ecartsNonQualifies(complete), [])
})

test('rien ne bloque : phrase vide', () => {
  const etat = etatFictif({
    qualifications_ecarts: [{ module: 'ipe_2_fournisseurs', numero_compte: '401', cause: 'Cut-off', commentaire: 'Factures de décembre reçues en janvier' }],
    justifications_non_evaluables: { ipe_3_immobilisations: { commentaire: "Pas de registre des immobilisations fourni par l'entité" } },
  })
  assert.equal(circuit.phraseBlocages(etat), '')
  assert.deepEqual(circuit.blocages(etat), { ecarts: 0, justifications: 0, demandes: 0 })
})

test('les demandes de correction ne comptent que si demandé (elles bloquent la validation, pas la soumission)', () => {
  const etat = etatFictif({ remarques: [
    { type: 'demande_correction', traitee: false },
    { type: 'demande_correction', traitee: false },
    { type: 'demande_correction', traitee: true },
    { type: 'information', traitee: false },
  ] })
  assert.equal(circuit.blocages(etat).demandes, 2)
  assert.ok(!circuit.phraseBlocages(etat).includes('demande'))
  assert.ok(circuit.phraseBlocages(etat, { avecDemandes: true }).endsWith('2 demandes de correction à traiter'))
})

test('état absent ou incomplet : aucun blocage, statut par défaut « en cours »', () => {
  assert.equal(circuit.statutCircuit(null), 'en_cours')
  assert.equal(circuit.phraseBlocages(undefined), '')
})
