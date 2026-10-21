// API des paramètres communs (page C, maquette docs/maquettes/7_Parametres.html).
// Consultation seule : un GET, aucune écriture tant qu'il n'y a pas
// d'authentification. Même pattern que journal.api.js.
import api from './index'

export async function lireParametres() {
  try {
    const { data } = await api.get('/parametres')
    if (data?.success) return data.data
    throw new Error(data?.error || 'Erreur lors de la lecture des paramètres')
  } catch (error) {
    throw new Error(error?.response?.data?.error || error?.message || 'Erreur lors de la lecture des paramètres')
  }
}
