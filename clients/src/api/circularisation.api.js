// API de la circularisation, sous-lot a (docs/PLAN_circularisation.md) :
// population, sélection manuelle, mode de confirmation, mémo de sélection.
// Toutes les requêtes passent par /api/v1 (jamais /cors). Même pattern que ipe.api.js.
import api from './index'

function messageErreur(error, defaut) {
  const payload = error?.response?.data
  if (payload?.errors) {
    const premier = Object.values(payload.errors).flat()[0]
    if (premier) return typeof premier === 'string' ? premier : JSON.stringify(premier)
  }
  return payload?.error || error?.message || defaut
}

async function appeler(methode, chemin, corps, defaut) {
  try {
    const { data } = await api[methode](chemin, corps)
    if (data?.success) return data.data
    throw new Error(data?.error || defaut)
  } catch (error) {
    throw new Error(messageErreur(error, defaut))
  }
}

const base = (missionId) => `/missions/${missionId}/circularisation`

export const lireCircularisation = (missionId) =>
  appeler('get', base(missionId), undefined, 'Erreur lors de la lecture de la sélection des tiers')

export const constituerPopulation = (missionId, type, utilisateurId) =>
  appeler('post', `${base(missionId)}/${type}/population`, { utilisateur_id: utilisateurId },
    'Erreur lors de la constitution de la population')

export const deciderTiers = (missionId, type, numero, retenu, motif, utilisateurId) =>
  appeler('put', `${base(missionId)}/${type}/tiers`, { numero, retenu, motif, utilisateur_id: utilisateurId },
    'Erreur lors de la décision sur le tiers')

export const definirMode = (missionId, type, mode, motif, utilisateurId) =>
  appeler('put', `${base(missionId)}/${type}/mode`, { mode, motif, utilisateur_id: utilisateurId },
    'Erreur lors du changement de mode de confirmation')

export const lireMemo = (missionId, type) =>
  appeler('get', `${base(missionId)}/${type}/memo`, undefined, 'Erreur lors de la lecture du mémo')

export const soumettreMemo = (missionId, type, utilisateurId) =>
  appeler('post', `${base(missionId)}/${type}/memo/soumettre`, { utilisateur_id: utilisateurId },
    'Erreur lors de la soumission du mémo')

export const validerMemo = (missionId, type, commentaire, utilisateurId) =>
  appeler('post', `${base(missionId)}/${type}/memo/validation`, { commentaire, utilisateur_id: utilisateurId },
    'Erreur lors de la validation du mémo')

export const demanderCorrectionMemo = (missionId, type, commentaire, utilisateurId) =>
  appeler('post', `${base(missionId)}/${type}/memo/demander-correction`, { commentaire, utilisateur_id: utilisateurId },
    'Erreur lors de la demande de correction du mémo')
