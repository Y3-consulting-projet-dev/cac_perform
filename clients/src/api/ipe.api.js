// API du verrou IPE (Module 1, CAC-IPE-01). Nouveau périmètre V2 — voir
// docs/PLAN_verrou_IPE.md. Toutes les requêtes passent par /api/v1 (jamais
// /cors), conformément à CLAUDE.md. Même pattern que imports.api.js.
import api from './index'

// axios rejette (throw) sur tout statut non-2xx : le corps {success, error}
// renvoyé par le backend sur un 400 (commentaire trop court, double clic,
// écart non qualifié...) n'est jamais lu par `if (data?.success)` ci-dessous
// sans ceci — sans quoi l'appelant ne voit que le message générique axios
// ("Request failed with status code 400") au lieu du message clair attendu.
function extraireMessageErreur(error, messageParDefaut) {
  const payload = error?.response?.data
  if (payload?.errors) {
    const premier = Object.values(payload.errors).flat()[0]
    if (premier) return premier
  }
  if (payload?.error) return payload.error
  return error?.message || messageParDefaut
}

export async function obtenirEtatIpe(missionId) {
  try {
    const { data } = await api.get(`/missions/${missionId}/ipe`)
    if (data?.success) return data.data
    throw new Error(data?.error || "Erreur lors de la récupération de l'état IPE")
  } catch (error) {
    throw new Error(extraireMessageErreur(error, "Erreur lors de la récupération de l'état IPE"))
  }
}

export async function evaluerIpe(missionId) {
  try {
    const { data } = await api.post(`/missions/${missionId}/ipe/evaluer`)
    if (data?.success) return data.data
    throw new Error(data?.error || 'Erreur lors du rapprochement IPE')
  } catch (error) {
    throw new Error(extraireMessageErreur(error, 'Erreur lors du rapprochement IPE'))
  }
}

export async function validerFiabiliteIpe(missionId, validee, commentaire = null, utilisateurId = null) {
  try {
    const { data } = await api.post(`/missions/${missionId}/ipe/validation`, {
      validee,
      commentaire,
      utilisateur_id: utilisateurId,
    })
    if (data?.success) return data.data
    throw new Error(data?.error || 'Erreur lors de la validation de la fiabilité IPE')
  } catch (error) {
    throw new Error(extraireMessageErreur(error, 'Erreur lors de la validation de la fiabilité IPE'))
  }
}
