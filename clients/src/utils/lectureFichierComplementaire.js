// Présentation lisible (pour un auditeur) du détail d'un fichier
// complémentaire renvoyé par GET /api/v1/missions/<id>/fichiers-complementaires/<id>.
// Mise en forme uniquement : aucun contrôle n'est recalculé ici, tout vient
// de `controles_preliminaires` et `totaux` (controle_preliminaire_service.py,
// fichiers_complementaires_service.py).

const FORMAT_MONTANT = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 })

export function formatMontant(valeur) {
  if (valeur === null || valeur === undefined || valeur === '') return '—'
  const nombre = Number(valeur)
  return Number.isNaN(nombre) ? String(valeur) : FORMAT_MONTANT.format(nombre)
}

// Solde avec son sens : débit - crédit > 0 -> « 1 234 D », < 0 -> « 1 234 C ».
export function formatSens(debit, credit) {
  if ((debit === null || debit === undefined) && (credit === null || credit === undefined)) return '—'
  const net = (Number(debit) || 0) - (Number(credit) || 0)
  if (Math.abs(net) < 0.005) return '0'
  return `${FORMAT_MONTANT.format(Math.abs(net))} ${net > 0 ? 'D' : 'C'}`
}

// Montant unique signé (format simple) : positif = débit, négatif = crédit.
function formatSigne(montant) {
  if (montant === null || montant === undefined) return '—'
  return Number(montant) >= 0 ? formatSens(montant, 0) : formatSens(0, -montant)
}

// Libellés lisibles des données (correspondance des colonnes, détail technique).
export const LIBELLES_DONNEES = {
  code_entite: 'Entité',
  numero_compte: 'Numéro de compte',
  numero: 'Numéro de compte',
  libelle_compte: 'Libellé du compte',
  libelle: 'Libellé du compte',
  montant: 'Montant (signé)',
  solde_ouverture_debit: "Solde d'ouverture — débit",
  solde_ouverture_credit: "Solde d'ouverture — crédit",
  mouvement_debit: 'Mouvements — débit',
  mouvement_credit: 'Mouvements — crédit',
  solde_mouvement_debit: 'Solde des mouvements — débit',
  solde_mouvement_credit: 'Solde des mouvements — crédit',
  solde_final_debit: 'Solde final — débit',
  solde_final_credit: 'Solde final — crédit',
  debit_initial: "Solde d'ouverture — débit",
  credit_initial: "Solde d'ouverture — crédit",
  debit_mvt: 'Mouvements — débit',
  credit_mvt: 'Mouvements — crédit',
  debit_fin: 'Solde final — débit',
  credit_fin: 'Solde final — crédit',
  code_bien: 'Code du bien',
  libelle_bien: 'Désignation du bien',
  categorie: 'Catégorie',
  valeur_brute: 'Valeur brute',
  amortissements_cumules: 'Amortissements cumulés',
  valeur_nette: 'Valeur nette',
}

const LIBELLES_TOTAUX = {
  ouverture: "Solde d'ouverture",
  mouvements: 'Mouvements de la période',
  solde_mouvement: 'Solde des mouvements',
  solde_final: 'Solde final',
  global: 'Total du fichier',
}

const LIBELLES_SOMMES_IMMOBILISATIONS = {
  valeur_brute: 'Valeurs brutes',
  amortissements_cumules: 'Amortissements cumulés',
  valeur_nette: 'Valeurs nettes',
}

const PERIMETRES = {
  toutes_les_lignes: 'tous les comptes',
  comptes_bilan: 'les comptes de bilan (classes 1 à 5)',
  comptes_gestion: 'les comptes de gestion (classes 6 à 8)',
}

export function libellePerimetre(cle) {
  return PERIMETRES[cle] || cle
}

// D'après le CONTENU (valeur brute présente), pas la carte choisie : une
// balance importée par erreur dans la carte immobilisations reste lue comme
// une balance.
export function estImmobilisations(detail) {
  return detail?.totaux?.mode === 'immobilisations'
}

function pluriel(n, singulier, plurielForme) {
  return `${n} ${n > 1 ? plurielForme : singulier}`
}

function listeCourte(elements, max = 5) {
  const liste = elements.filter(Boolean)
  if (liste.length <= max) return liste.join(', ')
  return `${liste.slice(0, max).join(', ')} et ${liste.length - max} autre(s)`
}

// Contrôles en liste : { cle, libelle, statut: 'ok'|'alerte'|'non_applicable', aVerifier }.
export function controlesLisibles(detail) {
  const cp = detail?.controles_preliminaires || {}
  const immo = estImmobilisations(detail)
  const controles = []

  if (cp.integrite) {
    controles.push({
      cle: 'integrite',
      libelle: cp.integrite.ok ? 'Fichier lisible' : 'Fichier mal lu',
      statut: cp.integrite.ok ? 'ok' : 'alerte',
      aVerifier: cp.integrite.ok ? '' :
        `Le fichier n'a pas pu être lu correctement (${listeCourte(cp.integrite.erreurs || [])}). Vérifiez qu'il s'agit d'un classeur Excel (.xlsx) non protégé, puis réimportez-le.`,
    })
  }

  if (cp.doublons) {
    const doublons = cp.doublons.doublons || []
    controles.push({
      cle: 'doublons',
      libelle: cp.doublons.ok ? 'Aucun doublon' : 'Doublons détectés',
      statut: cp.doublons.ok ? 'ok' : 'alerte',
      aVerifier: cp.doublons.ok ? '' :
        `${pluriel(doublons.length, immo ? 'bien apparaît' : 'compte apparaît', immo ? 'biens apparaissent' : 'comptes apparaissent')} plusieurs fois : ${listeCourte(doublons)}. Vérifiez que le fichier n'a pas été exporté deux fois ou assemblé à partir de plusieurs extraits.`,
    })
  }

  const bt = cp.bouclage_total
  if (bt) {
    const enEcart = (bt.resultats || []).filter((r) => !r.ok)
    controles.push({
      cle: 'bouclage_total',
      libelle: enEcart.length ? 'Les totaux du fichier ne sont pas retrouvés' : 'Les totaux du fichier sont retrouvés',
      statut: !bt.nb_lignes_de_total_detectees ? 'non_applicable' : (enEcart.length ? 'alerte' : 'ok'),
      aVerifier: !bt.nb_lignes_de_total_detectees
        ? 'Le fichier ne contient pas de ligne de total : rien à comparer.'
        : (enEcart.length
          ? `${pluriel(enEcart.length, 'ligne de total ne correspond', 'lignes de total ne correspondent')} pas à la somme des comptes importés (${listeCourte(enEcart.map((r) => `ligne ${r.ligne_excel}${r.libelle ? ' « ' + r.libelle + ' »' : ''}`))}). Vérifiez qu'aucun compte ne manque dans le fichier et qu'aucune ligne n'a été ajoutée ou modifiée à la main.`
          : ''),
    })
  }

  if (cp.sous_totaux) {
    const st = cp.sous_totaux
    controles.push({
      cle: 'sous_totaux',
      libelle: st.nb ? 'Lignes de sous-total écartées' : 'Aucune ligne de sous-total',
      statut: 'ok',
      aVerifier: st.nb
        ? `${pluriel(st.nb, 'ligne résume', 'lignes résument')} d'autres comptes du fichier et ${st.nb > 1 ? 'ont été écartées' : 'a été écartée'} pour ne pas les compter deux fois : ${listeCourte(st.lignes.map((l) => l.numero_compte))}.`
        : '',
    })
  }

  const bl = cp.bouclage_ligne
  if (bl) {
    const enEcart = bl.lignes_en_ecart || []
    controles.push({
      cle: 'bouclage_ligne',
      libelle: bl.applicable && enEcart.length
        ? 'Certains comptes sont incohérents (ouverture + mouvements ≠ solde final)'
        : 'Chaque compte est cohérent (ouverture + mouvements = solde final)',
      statut: !bl.applicable ? 'non_applicable' : (enEcart.length ? 'alerte' : 'ok'),
      aVerifier: !bl.applicable
        ? "Non vérifiable : le fichier ne détaille pas l'ouverture, les mouvements et le solde final en débit et crédit."
        : (enEcart.length
          ? `${pluriel(enEcart.length, 'compte a', 'comptes ont')} un solde final différent de « ouverture + mouvements » : ${listeCourte(enEcart.map((e) => `${e.numero_compte} (écart ${formatMontant(e.ecart)})`))}. Vérifiez ces comptes dans le logiciel comptable.`
          : ''),
    })
  }

  return controles
}

export function nombreAlertes(detail) {
  return controlesLisibles(detail).filter((c) => c.statut === 'alerte').length
}

// Phrase de synthèse : « 11 comptes importés, 3 lignes de total écartées, tous les contrôles sont OK. »
export function phraseSynthese(detail) {
  const cp = detail?.controles_preliminaires || {}
  const nbLignes = (detail?.lignes || []).length
  const nbEcartees = cp.lignes_ecartees?.nb || 0
  const nbTotaux = cp.bouclage_total?.nb_lignes_de_total_detectees || 0
  const nbSousTotaux = cp.sous_totaux?.nb || 0
  const nbAutres = Math.max(nbEcartees - nbTotaux - nbSousTotaux, 0)
  const alertes = nombreAlertes(detail)

  const morceaux = [pluriel(nbLignes, estImmobilisations(detail) ? 'bien importé' : 'compte importé',
    estImmobilisations(detail) ? 'biens importés' : 'comptes importés')]
  if (nbSousTotaux) morceaux.push(pluriel(nbSousTotaux, 'ligne de sous-total écartée', 'lignes de sous-total écartées'))
  if (nbTotaux) morceaux.push(pluriel(nbTotaux, 'ligne de total écartée', 'lignes de total écartées'))
  if (nbAutres) morceaux.push(pluriel(nbAutres, 'autre ligne sans numéro écartée', 'autres lignes sans numéro écartées'))
  if (!detail?.controles_preliminaires) {
    // Balance de l'import d'origine (V1) : aucun contrôle n'a été enregistré.
    morceaux.push("import d'origine, aucun contrôle enregistré")
  } else {
    morceaux.push(alertes ? `${pluriel(alertes, 'alerte', 'alertes')} à vérifier` : 'tous les contrôles sont OK')
  }
  return `${morceaux.join(', ')}.`
}

// Totaux : lignes { libelle, debit, credit } (balances) ou { libelle, montant } (immobilisations).
export function totauxLisibles(detail) {
  const t = detail?.totaux || {}
  if (t.mode === 'immobilisations') {
    return {
      mode: 'montants',
      lignes: Object.entries(t.sommes || {}).map(([cle, v]) => ({ libelle: LIBELLES_SOMMES_IMMOBILISATIONS[cle] || cle, montant: formatMontant(v) })),
    }
  }
  const ordre = ['ouverture', 'mouvements', 'solde_mouvement', 'solde_final', 'global']
  const lignes = ordre.filter((cle) => t.totaux?.[cle]).map((cle) => ({
    libelle: LIBELLES_TOTAUX[cle],
    debit: formatMontant(t.totaux[cle].debit),
    credit: formatMontant(t.totaux[cle].credit),
  }))
  return { mode: 'debit_credit', lignes, montantSigne: t.mode === 'montant_signe' }
}

// Colonnes du tableau des comptes selon les données présentes dans le fichier.
export function colonnesComptes(detail) {
  const premiere = detail?.lignes?.[0] || {}
  const a = (cle) => cle in premiere
  const paire = (prefixe) => a(`${prefixe}_debit`) || a(`${prefixe}_credit`)

  if (estImmobilisations(detail)) {
    return [
      a('code_bien') && { titre: 'Code', valeur: (l) => l.code_bien ?? '—' },
      { titre: 'Désignation', valeur: (l) => l.libelle_bien ?? l.libelle ?? '—', large: true },
      (a('numero_compte') || a('categorie')) && { titre: 'Compte', valeur: (l) => l.numero_compte ?? l.categorie ?? '—' },
      { titre: 'Valeur brute', valeur: (l) => formatMontant(l.valeur_brute), montant: true },
      { titre: 'Amortissements', valeur: (l) => formatMontant(l.amortissements_cumules), montant: true },
      a('valeur_nette') && { titre: 'Valeur nette', valeur: (l) => formatMontant(l.valeur_nette), montant: true },
    ].filter(Boolean)
  }

  // Forme des balances générales (import V1 et import V2 de la balance générale).
  if (a('debit_initial') || a('debit_fin')) {
    return [
      { titre: 'Compte', valeur: (l) => l.numero_compte ?? '—' },
      { titre: 'Libellé', valeur: (l) => l.libelle || '—', large: true },
      { titre: "Solde d'ouverture", valeur: (l) => formatSens(l.debit_initial, l.credit_initial), montant: true },
      {
        titre: 'Mouvements',
        valeur: (l) => formatSens(l.debit_mvt, l.credit_mvt),
        infobulle: (l) => `Débit ${formatMontant(l.debit_mvt)} — Crédit ${formatMontant(l.credit_mvt)}`,
        montant: true,
      },
      { titre: 'Solde final', valeur: (l) => formatSens(l.debit_fin, l.credit_fin), montant: true },
    ]
  }

  const finale = paire('solde_final') ? 'solde_final' : (paire('solde_mouvement') ? 'solde_mouvement' : null)
  return [
    a('code_entite') && { titre: 'Entité', valeur: (l) => l.code_entite ?? '—' },
    { titre: 'Compte', valeur: (l) => l.numero_compte ?? l.numero ?? '—' },
    { titre: 'Libellé', valeur: (l) => l.libelle_compte ?? l.libelle ?? '—', large: true },
    paire('solde_ouverture') && { titre: "Solde d'ouverture", valeur: (l) => formatSens(l.solde_ouverture_debit, l.solde_ouverture_credit), montant: true },
    paire('mouvement') && {
      titre: 'Mouvements',
      valeur: (l) => formatSens(l.mouvement_debit, l.mouvement_credit),
      infobulle: (l) => `Débit ${formatMontant(l.mouvement_debit)} — Crédit ${formatMontant(l.mouvement_credit)}`,
      montant: true,
    },
    finale && { titre: 'Solde final', valeur: (l) => formatSens(l[`${finale}_debit`], l[`${finale}_credit`]), montant: true },
    a('montant') && { titre: 'Solde', valeur: (l) => formatSigne(l.montant), montant: true },
  ].filter(Boolean)
}
