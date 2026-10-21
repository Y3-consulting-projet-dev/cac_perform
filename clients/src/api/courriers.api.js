// API des courriers de circularisation, sous-lot b (docs/PLAN_circularisation.md) :
// annuaire des coordonnées, bibliothèque de modèles Word. /api/v1 uniquement.
// L'import d'un modèle (multipart) passe par axios « brut », comme
// imports.api.js : l'en-tête JSON de l'instance partagée casserait la frontière.
import axios from 'axios'
import api from './index'

const BASE_URL = 'http://localhost:5000/api/v1'

function messageErreur(error, defaut) {
  return error?.response?.data?.error || error?.message || defaut
}

const base = (missionId) => `/missions/${missionId}/courriers`

export async function lireCourriers(missionId) {
  try {
    const { data } = await api.get(base(missionId))
    if (data?.success) return data.data
    throw new Error(data?.error || 'Erreur lors de la lecture des courriers')
  } catch (error) {
    throw new Error(messageErreur(error, 'Erreur lors de la lecture des courriers'))
  }
}

export async function enregistrerCoordonnees(missionId, typeTiers, numero, coordonnees, utilisateurId) {
  try {
    const { data } = await api.put(`${base(missionId)}/coordonnees`, {
      type_tiers: typeTiers, numero, ...coordonnees, utilisateur_id: utilisateurId,
    })
    if (data?.success) return data.data
    throw new Error(data?.error || "Erreur lors de l'enregistrement des coordonnées")
  } catch (error) {
    throw new Error(messageErreur(error, "Erreur lors de l'enregistrement des coordonnées"))
  }
}

export async function importerModele(missionId, code, fichier, utilisateurId) {
  const formulaire = new FormData()
  formulaire.append('code', code)
  formulaire.append('fichier', fichier)
  if (utilisateurId) formulaire.append('utilisateur_id', utilisateurId)
  try {
    const { data } = await axios.post(`${BASE_URL}${base(missionId)}/modeles`, formulaire)
    if (data?.success) return data.data
    throw new Error(data?.error || "Erreur lors de l'import du modèle")
  } catch (error) {
    throw new Error(messageErreur(error, "Erreur lors de l'import du modèle"))
  }
}

export const urlFichierModele = (missionId, modeleId) => `${BASE_URL}${base(missionId)}/modeles/${modeleId}/fichier`
