// API refonte de l'import (balances, mapping, fichiers auxiliaires/immobilisations).
// Nouveau périmètre V2 — voir docs/PLAN_import_refonte.md.
//
// Toutes les requêtes passent par /api/v1 (jamais /cors), conformément à
// CLAUDE.md. Les appels avec fichier (multipart) utilisent axios « brut »
// plutôt que l'instance partagée `api` (voir clients/src/api/index.js) : son
// en-tête par défaut Content-Type: application/json empêcherait axios de
// générer correctement la frontière multipart — même pattern que
// clients/src/utils/uploadFile.js pour l'import de balance existant.
import axios from 'axios'
import api from './index'

const BASE_URL = 'http://localhost:5000/api/v1'

// axios lève une exception sur un 4xx/5xx : on remonte le message du backend
// ({ success: false, error }) plutôt que « Request failed with status code 400 ».
function messageErreur(e, defaut) {
  return e?.response?.data?.error || (e?.response ? `${defaut} (HTTP ${e.response.status})` : `${defaut} : ${e?.message || 'serveur injoignable'}`)
}

// Informations de la mission (id_client, annee_auditee...) via /api/v1 —
// remplace la lecture de /cors/mission/affichage_infos_mission, dont la
// réponse n'a pas de clé `response` (l'écran restait sans mission chargée).
export async function obtenirMission(missionId) {
  let data
  try {
    ({ data } = await api.get(`/missions/${missionId}`))
  } catch (e) {
    throw new Error(messageErreur(e, 'Mission non chargée'))
  }
  if (data?.success && data.data) return data.data
  throw new Error(data?.error || 'Mission non chargée : réponse inattendue du serveur')
}

export async function apercuMapping(fichier) {
  const formData = new FormData()
  formData.append('fichier', fichier)

  const { data } = await axios.post(`${BASE_URL}/imports/apercu`, formData)
  if (data?.success) return data.data
  throw new Error(data?.error || "Erreur lors de l'analyse du fichier")
}

export async function enregistrerMapping(idClient, logicielComptable, mapping) {
  const { data } = await api.post('/imports/mapping', {
    id_client: idClient,
    logiciel_comptable: logicielComptable,
    mapping,
  })
  if (data?.success) return data.data
  throw new Error(data?.error || "Erreur lors de l'enregistrement du mapping")
}

export async function recupererMapping(idClient, logicielComptable) {
  const { data } = await api.get('/imports/mapping', {
    params: { id_client: idClient, logiciel_comptable: logicielComptable },
  })
  if (data?.success) return data.data
  throw new Error(data?.error || "Erreur lors de la récupération du mapping")
}

export async function controlesPreliminaires(fichier) {
  const formData = new FormData()
  formData.append('fichier', fichier)

  const { data } = await axios.post(`${BASE_URL}/imports/controles-preliminaires`, formData)
  if (data?.success) return data.data
  throw new Error(data?.error || 'Erreur lors des contrôles préliminaires')
}

export async function importerBalanceAuxiliaire(missionId, fichier, typeAuxiliaire, idClient, annee) {
  const formData = new FormData()
  formData.append('fichier', fichier)
  formData.append('type_auxiliaire', typeAuxiliaire)
  formData.append('id_client', idClient)
  formData.append('annee', String(annee))

  let data
  try {
    ({ data } = await axios.post(`${BASE_URL}/missions/${missionId}/balances-auxiliaires`, formData))
  } catch (e) {
    throw new Error(messageErreur(e, "Erreur lors de l'import de la balance auxiliaire"))
  }
  if (data?.success) return data.data
  throw new Error(data?.error || "Erreur lors de l'import de la balance auxiliaire")
}

export async function importerImmobilisations(missionId, fichier, idClient, annee) {
  const formData = new FormData()
  formData.append('fichier', fichier)
  formData.append('id_client', idClient)
  formData.append('annee', String(annee))

  let data
  try {
    ({ data } = await axios.post(`${BASE_URL}/missions/${missionId}/immobilisations`, formData))
  } catch (e) {
    throw new Error(messageErreur(e, "Erreur lors de l'import du fichier des immobilisations"))
  }
  if (data?.success) return data.data
  throw new Error(data?.error || "Erreur lors de l'import du fichier des immobilisations")
}

// --- Consultation des fichiers complémentaires (lecture seule) ---
// Écran de données, pas une étape d'audit : aucun rapprochement IPE ici.

export async function listerFichiersComplementaires(missionId) {
  const { data } = await api.get(`/missions/${missionId}/fichiers-complementaires`)
  if (data?.success) return data.data
  throw new Error(data?.error || 'Erreur lors de la récupération des fichiers complémentaires')
}

// Versions active + archivées d'un type de fichier (la plus récente d'abord).
export async function historiqueFichiersComplementaires(missionId, typeFichier) {
  const { data } = await api.get(`/missions/${missionId}/fichiers-complementaires/${typeFichier}/historique`)
  if (data?.success) return data.data
  throw new Error(data?.error || "Erreur lors de la récupération de l'historique")
}

export async function detailFichierComplementaire(missionId, fichierId) {
  const { data } = await api.get(`/missions/${missionId}/fichiers-complementaires/${fichierId}`)
  if (data?.success) return data.data
  throw new Error(data?.error || 'Erreur lors de la récupération du détail du fichier')
}
