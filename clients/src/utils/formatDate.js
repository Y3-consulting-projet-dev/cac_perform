// Date + heure au format français, sans secondes : « 13/10/2026 16:41 ».
//
// Les dates d'import sont enregistrées par le backend en UTC sans fuseau
// (datetime.utcnow().isoformat(), ex. « 2026-10-13T14:41:07.123456 ») :
// sans « Z », le navigateur les lirait comme une heure locale. On ajoute donc
// « Z » quand aucun fuseau n'est indiqué, pour afficher l'heure locale réelle.
export function formatDateHeureFr(valeur) {
  if (!valeur) return '—'
  let texte = String(valeur)
  if (/^\d{4}-\d{2}-\d{2}T[\d:.]+$/.test(texte)) texte += 'Z'
  const date = new Date(texte)
  if (Number.isNaN(date.getTime())) return String(valeur)
  return date.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
