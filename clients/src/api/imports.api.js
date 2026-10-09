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

  const { data } = await axios.post(`${BASE_URL}/missions/${missionId}/balances-auxiliaires`, formData)
  if (data?.success) return data.data
  throw new Error(data?.error || "Erreur lors de l'import de la balance auxiliaire")
}

export async function importerImmobilisations(missionId, fichier, idClient, annee) {
  const formData = new FormData()
  formData.append('fichier', fichier)
  formData.append('id_client', idClient)
  formData.append('annee', String(annee))

  const { data } = await axios.post(`${BASE_URL}/missions/${missionId}/immobilisations`, formData)
  if (data?.success) return data.data
  throw new Error(data?.error || "Erreur lors de l'import du fichier des immobilisations")
}
