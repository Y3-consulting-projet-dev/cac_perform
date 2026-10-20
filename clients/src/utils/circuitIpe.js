// Points bloquants du circuit de revue IPE, calculés à partir de l'état
// renvoyé par GET /api/v1/missions/<id>/ipe. Partagé par FiabiliteIpeView.vue
// et la barre latérale de GroupingAnalyse.vue (docs/PLAN_ecrans_lot1.md §3.2).
//
// Reflet côté écran de api/src/services/revue_ipe_service.py
// (ecarts_non_qualifies, refus_soumission, refus_validation) : le serveur
// reste la référence et refuse toute action non permise.

export const STATUTS_EDITION_AUDITEUR = ['en_cours', 'en_attente_correction']

export function statutCircuit(etat) {
  return etat?.statut_circuit || 'en_cours'
}

export function qualificationPour(etat, module, numeroCompte) {
  return (etat?.qualifications_ecarts || []).find((q) => q.module === module && q.numero_compte === numeroCompte)
}

// Qualification complète = cause de la liste du serveur (causes_ecart) + commentaire.
export function qualificationComplete(etat, qualification) {
  return !!qualification && (etat?.causes_ecart || []).includes(qualification.cause) && !!(qualification.commentaire || '').trim()
}

// Écarts réels (ligne « ok: false » d'un module en « ecart ») sans qualification
// complète, sous la forme "module:numero_compte".
export function ecartsNonQualifies(etat) {
  const manquants = []
  for (const [cle, module] of Object.entries(etat?.modules || {})) {
    if (module.statut !== 'ecart') continue
    for (const ligne of module.derniere_evaluation?.detail_collectifs || []) {
      if (ligne.ok) continue
      if (!qualificationComplete(etat, qualificationPour(etat, cle, ligne.numero_compte))) {
        manquants.push(`${cle}:${ligne.numero_compte}`)
      }
    }
  }
  return manquants
}

export function demandesCorrectionNonTraitees(etat) {
  return (etat?.remarques || []).filter((r) => r.type === 'demande_correction' && !r.traitee)
}

export function modulesNonEvaluablesSansJustification(etat) {
  return Object.entries(etat?.modules || {})
    .filter(([cle, m]) => m.statut === 'non_evaluable' && !(etat?.justifications_non_evaluables?.[cle]?.commentaire || '').trim())
    .map(([cle]) => cle)
}

// Décompte des points bloquants, pour l'écran et la barre latérale.
export function blocages(etat) {
  return {
    ecarts: ecartsNonQualifies(etat).length,
    justifications: modulesNonEvaluablesSansJustification(etat).length,
    demandes: demandesCorrectionNonTraitees(etat).length,
  }
}

function pluriel(n, singulier, plurielForme) {
  return `${n} ${n > 1 ? plurielForme : singulier}`
}

// « 1 écart à qualifier, 2 justifications à écrire » ; '' si rien ne bloque.
// `avecDemandes` : les demandes de correction ne bloquent que la validation.
export function phraseBlocages(etat, { avecDemandes = false } = {}) {
  const b = blocages(etat)
  const morceaux = []
  if (b.ecarts) morceaux.push(pluriel(b.ecarts, 'écart à qualifier', 'écarts à qualifier'))
  if (b.justifications) morceaux.push(pluriel(b.justifications, 'justification à écrire', 'justifications à écrire'))
  if (avecDemandes && b.demandes) morceaux.push(pluriel(b.demandes, 'demande de correction à traiter', 'demandes de correction à traiter'))
  return morceaux.join(', ')
}
