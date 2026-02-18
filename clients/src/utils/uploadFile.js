import axios from 'axios'

export async function uploadFile(
  annee_auditee,
  balances,
  date_debut,
  date_fin,
  date_debut_mandat,
  date_fin_mandat,
  id_client
) {
  const formData = new FormData()

  // 🔹 fichiers
  const validFiles = (balances || []).filter(
    f => f && (f.name || f.size !== undefined)
  )

  validFiles.forEach(file => {
    formData.append('files[]', file)
  })

  // 🔹 champs EXACTS attendus par le backend
  formData.append('annee_auditee', String(annee_auditee)) // ⚠️ forcer string
  formData.append('id_client', id_client)
  formData.append('date_debut', date_debut)
  formData.append('date_fin', date_fin)
  formData.append('date_debut_mandat', date_debut_mandat)
  formData.append('date_fin_mandat', date_fin_mandat)

  const user = (() => {
    try {
      return JSON.parse(sessionStorage.getItem('user') || 'null')
    } catch {
      return null
    }
  })()

  if (user) {
    const nom = `${user.firstname || ''} ${user.lastname || ''}`.trim()
    if (nom) formData.append('responsable_nom', nom)
    if (user.grade) formData.append('responsable_grade', user.grade)
    if (user.role) formData.append('responsable_role', user.role)
    if (user._id) formData.append('responsable_id', user._id)
  }

  // 🧪 DEBUG
  console.log('📦 FormData envoyé :')
  for (let pair of formData.entries()) {
    console.log(pair[0], pair[1])
  }

  try {
    const response = await axios.post(
      'http://localhost:5000/api/v1/missions',
      formData,
      {
        headers: {
          // ❌ NE PAS mettre multipart à la main
          // axios le gère automatiquement
        }
      }
    )

    // ✅ NORMALISATION
    if (response.data?.success === true) {
      return response.data.data
    }

    throw new Error(response.data?.message || 'Erreur inconnue serveur')
  } catch (error) {
    console.error('❌ Erreur upload mission:', error)
    console.error('📨 Réponse serveur:', error?.response?.data)
    throw error
  }
}
