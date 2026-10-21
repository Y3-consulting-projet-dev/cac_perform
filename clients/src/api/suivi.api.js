// API du suivi des réponses, sous-lot c (docs/PLAN_circularisation.md). /api/v1
// uniquement. Aucun envoi réel : on enregistre ce que l'auditeur a fait.
// Réponse, analyse d'écart, procédure alternative : multipart (pièce jointe
// facultative) via axios « brut », comme imports.api.js.
import axios from 'axios'
import api from './index'

const BASE_URL = 'http://localhost:5000/api/v1'
const base = (missionId) => `/missions/${missionId}/suivi`

function messageErreur(error, defaut) {
  return error?.response?.data?.error || error?.message || defaut
}

async function appeler(requete, defaut) {
  try {
    const { data } = await requete()
    if (data?.success) return data.data
    throw new Error(data?.error || defaut)
  } catch (error) {
    throw new Error(messageErreur(error, defaut))
  }
}

function formulaire(champs, fichier) {
  const f = new FormData()
  for (const [cle, valeur] of Object.entries(champs)) {
    if (valeur !== null && valeur !== undefined && valeur !== '') f.append(cle, valeur)
  }
  if (fichier) f.append('fichier', fichier)
  return f
}

export const lireSuivi = (missionId) =>
  appeler(() => api.get(base(missionId)), 'Erreur lors de la lecture du suivi des réponses')

export const enregistrerEnvoi = (missionId, champs) =>
  appeler(() => api.post(`${base(missionId)}/envois`, champs), "Erreur lors de l'enregistrement de l'envoi")

export const enregistrerRelance = (missionId, envoiId, champs) =>
  appeler(() => api.post(`${base(missionId)}/${envoiId}/relances`, champs), "Erreur lors de l'enregistrement de la relance")

export const enregistrerReponse = (missionId, envoiId, champs, fichier) =>
  appeler(() => axios.post(`${BASE_URL}${base(missionId)}/${envoiId}/reponse`, formulaire(champs, fichier)),
    "Erreur lors de l'enregistrement de la réponse")

export const analyserEcart = (missionId, envoiId, champs, fichier) =>
  appeler(() => axios.post(`${BASE_URL}${base(missionId)}/${envoiId}/analyse-ecart`, formulaire(champs, fichier)),
    "Erreur lors de l'enregistrement de l'analyse")

export const documenterProcedure = (missionId, envoiId, champs, fichier) =>
  appeler(() => axios.post(`${BASE_URL}${base(missionId)}/${envoiId}/procedure-alternative`, formulaire(champs, fichier)),
    "Erreur lors de l'enregistrement de la procédure")

export const urlPiece = (missionId, fichierId) => `${BASE_URL}${base(missionId)}/pieces/${fichierId}`
