// API du verrou IPE (Module 1, CAC-IPE-01). Nouveau périmètre V2 — voir
// docs/PLAN_verrou_IPE.md. Toutes les requêtes passent par /api/v1 (jamais
// /cors), conformément à CLAUDE.md. Même pattern que imports.api.js.
import api from './index'

export async function obtenirEtatIpe(missionId) {
  const { data } = await api.get(`/missions/${missionId}/ipe`)
  if (data?.success) return data.data
  throw new Error(data?.error || "Erreur lors de la récupération de l'état IPE")
}

export async function evaluerIpe(missionId) {
  const { data } = await api.post(`/missions/${missionId}/ipe/evaluer`)
  if (data?.success) return data.data
  throw new Error(data?.error || 'Erreur lors du rapprochement IPE')
}

export async function validerFiabiliteIpe(missionId, validee, commentaire = null) {
  const { data } = await api.post(`/missions/${missionId}/ipe/validation`, {
    validee,
    commentaire,
  })
  if (data?.success) return data.data
  throw new Error(data?.error || 'Erreur lors de la validation de la fiabilité IPE')
}
