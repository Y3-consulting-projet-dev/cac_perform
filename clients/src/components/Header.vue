<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import router from '@/router';

const userProfile = ref({
  nom: '',
  email: '',
  role: '',
  avatar: '👤'
})

onMounted(async () => {
  const storedUser = sessionStorage.getItem('user')

  if (storedUser) {
    const user = JSON.parse(storedUser)

    userProfile.value.nom = `${user.firstname} ${user.lastname}`
    userProfile.value.role = user.role
    userProfile.value.email = user.email
  }

  // Ajout d'un listener global pour fermer les menus au clic en dehors
  window.addEventListener('click', handleOutsideClick)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', handleOutsideClick)
})

const notifications = ref([
  { id: 1, message: 'Nouvelle mission assignée', date: '2 min', lu: false },
  { id: 2, message: 'Rapport de synthèse généré', date: '1 heure', lu: false },
  { id: 3, message: 'Client CAC-001 mis à jour', date: '3 heures', lu: true }
])

const showNotifications = ref(false)
const showProfileMenu = ref(false)

const unreadCount = notifications.value.filter(n => !n.lu).length

function toggleNotifications(event) {
  event.stopPropagation()
  showNotifications.value = !showNotifications.value
  showProfileMenu.value = false
}

function toggleProfileMenu(event) {
  event.stopPropagation()
  showProfileMenu.value = !showProfileMenu.value
  showNotifications.value = false
}

function handleOutsideClick() {
  showNotifications.value = false
  showProfileMenu.value = false
}

function logout() {
  sessionStorage.removeItem('token')
  sessionStorage.removeItem('user')
  router.push('/connexion')
}

function profile() {
  showProfileMenu.value = false
  router.push('/profile')
}

function markAsRead(notificationId) {
  const notification = notifications.value.find(n => n.id === notificationId)
  if (notification) {
    notification.lu = true
  }
}

function markAllAsRead() {
  notifications.value.forEach(n => n.lu = true)
}
</script>

<template>
  <header class="flex justify-between items-center bg-blanc3 px-6 py-4 rounded-lg shadow-sm">
    <!-- Logo -->
     <button @click="router.push('/')">
       <img src="../assets/logo_y3.png" alt="Logo" class="h-14" />
     </button>

    <!-- Profil et Notifications -->
    <div class="profil flex items-center gap-6">

      <!-- Notifications -->
      <div class="relative">
        <button @click="toggleNotifications" class="relative focus:outline-none hover:text-orange-600 transition">
          <i class="fa-solid fa-bell text-2xl text-orange-500"></i>
          <span v-if="unreadCount > 0"
            class="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
            {{ unreadCount }}
          </span>
        </button>

        <!-- Popup Notifications -->
        <Teleport to="body">
          <div v-if="showNotifications"
            class="fixed top-20 right-12 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
            <div class="p-4 border-b border-gray-100">
              <h3 class="font-semibold text-gray-800">Notifications ({{ unreadCount }})</h3>
              <button @click="showNotifications = false" class="absolute top-2 right-2 text-gray-400 hover:text-gray-600">
                <i class="fa-solid fa-times text-lg"></i>
              </button>
            </div>

            <div class="max-h-96 overflow-y-auto">
              <div v-for="notification in notifications" :key="notification.id"
                class="p-3 border-b border-gray-50 hover:bg-gray-50 cursor-pointer transition flex justify-between items-start"
                :class="{ 'bg-blue-50': !notification.lu }" @click="markAsRead(notification.id)">
                <div class="flex-1">
                  <p class="text-sm" :class="{ 'font-semibold': !notification.lu }">
                    {{ notification.message }}
                  </p>
                  <p class="text-xs text-gray-500 mt-1">{{ notification.date }}</p>
                </div>
                <span v-if="!notification.lu" class="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 ml-2 mt-1"></span>
              </div>

              <div v-if="notifications.length === 0" class="p-8 text-center text-gray-500">
                Aucune notification
              </div>
            </div>

            <div class="p-3 border-t border-gray-100 bg-gray-50">
              <button @click="markAllAsRead"
                class="w-full text-sm text-center text-blue-600 hover:text-blue-700 font-medium">
                Marquer tout comme lu
              </button>
            </div>
          </div>
        </Teleport>
      </div>

      <!-- Divider -->
      <div class="w-px h-8 bg-gray-300"></div>

      <!-- Profil Menu -->
      <div class="relative">
        <button @click="toggleProfileMenu"
          class="flex items-center gap-3 hover:bg-gray-100 px-3 py-2 rounded-lg transition focus:outline-none">
          <div
            class="w-10 h-10 bg-blue-ycube rounded-full flex items-center justify-center text-white text-lg font-semibold">
            {{ userProfile.nom.charAt(0) }}
          </div>
          <div class="text-left">
            <p class="text-sm font-semibold text-gray-800">{{ userProfile.nom }}</p>
            <p class="text-xs text-gray-500">{{ userProfile.role }}</p>
          </div>
          <i class="fa-solid fa-chevron-down text-xs text-gray-500"></i>
        </button>

        <!-- Profile Dropdown Menu -->
        <Teleport to="body">
          <div v-if="showProfileMenu"
            class="fixed top-20 right-4 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
            <div class="p-4 border-b border-gray-100 flex justify-between items-start">
              <div>
                <p class="text-sm font-semibold text-gray-800">{{ userProfile.nom }}</p>
                <p class="text-xs text-gray-500">{{ userProfile.email }}</p>
              </div>
              <button @click="showProfileMenu = false" class="text-gray-400 hover:text-gray-600">
                <i class="fa-solid fa-times"></i>
              </button>
            </div>

            <div class="p-3 space-y-2">
              <button @click="profile"
                class="w-full text-left text-sm text-gray-700 hover:bg-gray-100 px-3 py-2 rounded transition flex items-center gap-2">
                <i class="fa-solid fa-user text-gray-500"></i>
                Mon profil
              </button>
              <button
                @click="showProfileMenu = false"
                class="w-full text-left text-sm text-gray-700 hover:bg-gray-100 px-3 py-2 rounded transition flex items-center gap-2">
                <i class="fa-solid fa-cog text-gray-500"></i>
                Paramètres
              </button>
              <button
                @click="showProfileMenu = false"
                class="w-full text-left text-sm text-gray-700 hover:bg-gray-100 px-3 py-2 rounded transition flex items-center gap-2">
                <i class="fa-solid fa-question-circle text-gray-500"></i>
                Aide
              </button>
            </div>

            <div class="p-3 border-t border-gray-100">
              <button
                @click="logout"
                class="w-full text-left text-sm text-red-600 hover:bg-red-50 px-3 py-2 rounded transition flex items-center gap-2 font-medium">
                <i class="fa-solid fa-sign-out-alt"></i>
                Déconnexion
              </button>
            </div>
          </div>
        </Teleport>
      </div>

    </div>
  </header>
</template>

<style scoped>
.profil {
  min-width: 300px;
}
</style>
