// API du journal d'audit (page B, maquette docs/maquettes/6_Journal_audit.html).
// Lecture seule : deux GET, aucune écriture. Toutes les requêtes passent par
// /api/v1 (jamais /cors), conformément à CLAUDE.md. Même pattern que ipe.api.js.
import api from './index'

// Filtres de l'écran -> paramètres de la requête. Le décalage horaire du
// navigateur permet au serveur de lire la période (« Du », « Au ») et l'export
// dans l'heure de l'utilisateur.
function parametres(filtres = {}, page) {
  const p = { decalage: -new Date().getTimezoneOffset() }
  for (const cle of ['module', 'utilisateur', 'du', 'au']) {
    if (filtres[cle]) p[cle] = filtres[cle]
  }
  if (page) p.page = page
  return p
}

function messageErreur(error, defaut) {
  return error?.response?.data?.error || error?.message || defaut
}

export async function lireJournal(missionId, filtres, page = 1) {
  try {
    const { data } = await api.get(`/missions/${missionId}/journal`, { params: parametres(filtres, page) })
    if (data?.success) return data.data
    throw new Error(data?.error || "Erreur lors de la lecture du journal d'audit")
  } catch (error) {
    throw new Error(messageErreur(error, "Erreur lors de la lecture du journal d'audit"))
  }
}

// Classeur .xlsx des entrées filtrées (toutes les pages), téléchargé par le navigateur.
export async function exporterJournal(missionId, filtres) {
  let reponse
  try {
    reponse = await api.get(`/missions/${missionId}/journal/export`, {
      params: parametres(filtres),
      responseType: 'blob',
    })
  } catch (error) {
    // Avec responseType 'blob', le corps d'erreur JSON arrive sous forme de Blob.
    const corps = error?.response?.data
    let message
    if (corps instanceof Blob) {
      try { message = JSON.parse(await corps.text()).error } catch { /* corps non JSON : message générique */ }
    }
    if (message) throw new Error(message)
    throw new Error(messageErreur(error, "Erreur lors de l'export du journal d'audit"))
  }
  const lien = document.createElement('a')
  lien.href = URL.createObjectURL(reponse.data)
  lien.download = `journal_audit_${missionId}.xlsx`
  document.body.appendChild(lien)
  lien.click()
  lien.remove()
  URL.revokeObjectURL(lien.href)
}
