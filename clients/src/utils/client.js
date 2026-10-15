// Champs client facultatifs ajoutés en V2 : N°CC (compte contribuable) et
// capital social (FCFA). Partagé par NewClient.vue, ClientSpace.vue et
// ClientsView.vue.

// TODO(décision) : format officiel du N°CC à confirmer. Format indicatif
// (7 chiffres puis une lettre, ex. « 1512345 A ») : simple avertissement,
// jamais un blocage.
const FORMAT_NUMERO_CC = /^\d{7}\s?[A-Za-z]$/

export function avertissementNumeroCc(valeur) {
  const texte = String(valeur || '').trim()
  if (!texte || FORMAT_NUMERO_CC.test(texte)) return ''
  return 'Format inhabituel : un N°CC compte en général 7 chiffres et une lettre (ex. 1512345 A). Vous pouvez enregistrer quand même.'
}

// « 100 000 000 FCFA » ; tiret si non renseigné.
export function formatCapital(valeur) {
  if (valeur === null || valeur === undefined || valeur === '') return '-'
  const nombre = Number(String(valeur).replace(/[\s  ]/g, ''))
  if (Number.isNaN(nombre)) return String(valeur)
  return `${new Intl.NumberFormat('fr-FR').format(nombre)} FCFA`
}
