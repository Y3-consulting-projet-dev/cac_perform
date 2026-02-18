import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin } from '@/api/auth.api'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(sessionStorage.getItem('token') || '')
  const user = ref(JSON.parse(sessionStorage.getItem('user')) || null)

  const isLoading = ref(false)
  const isAuthenticated = computed(() => !!token.value)

  async function login(credentials) {
    isLoading.value = true
    try {
      const userData = await apiLogin(credentials)

      token.value = sessionStorage.getItem('token')
      user.value = userData

      isLoading.value = false
      return true
    } catch (error) {
      console.error('Erreur de connexion:', error)
      isLoading.value = false
      return false
    }
  }

  const initialize = async () => {
    try {
      const savedToken = sessionStorage.getItem('token')
      const savedUser = sessionStorage.getItem('user')

      if (savedToken && savedUser) {
        token.value = savedToken
        user.value = JSON.parse(savedUser)
      }
    } catch (error) {
      console.error('Erreur lors de l\'initialisation:', error)
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null

    sessionStorage.removeItem('token')
    sessionStorage.removeItem('user')
    delete axios.defaults.headers.common['Authorization']
  }

  function updateUser(userData) {
    user.value = userData
    sessionStorage.setItem('user', JSON.stringify(userData))
  }

  return {
    token,
    user,
    isAuthenticated,
    isLoading,
    initialize,
    login,
    logout,
    updateUser,
  }
})
