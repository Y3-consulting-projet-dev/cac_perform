import api from './index'

export async function login(credentials) {
  const { data } = await api.post('/users/login', credentials)

  const token = data.token || data.access_token
  if (!token) throw new Error('Token manquant')

  const user = {
    ...data.user,
  }

  sessionStorage.setItem('token', token)
  sessionStorage.setItem('user', JSON.stringify(user))

  return user
}

export function register(payload) {
  return api.post('/users/register', payload)
}

export function getCurrentUser() {
  const user = sessionStorage.getItem('user')
  return user ? JSON.parse(user) : null
}

export function getUserProfile() {
  const user = getCurrentUser()
  if (!user?._id) throw new Error('Utilisateur non authentifié')
  return api.get(`/users/${user._id}/profile`)
}

export function updateUserProfile(payload) {
  const user = getCurrentUser()
  if (!user?._id) throw new Error('Utilisateur non authentifié')
  return api.put(`/users/${user._id}/profile`, payload)
}

export function changeUserPassword(payload) {
  const user = getCurrentUser()
  if (!user?._id) throw new Error('Utilisateur non authentifié')
  return api.put(`/users/${user._id}/password`, payload)
}
