<script setup>
import { ref, inject, onMounted } from 'vue';
import router from '@/router';
import { useRoute } from 'vue-router';

const axios = inject('axios');
// DATA
const listClients = ref([])
const lastTenClients = ref([])
const totalMissions = ref(0)
const searchQuery = ref("")

const showDeleteModal = ref(false)
const clientToDelete = ref(null)
const isDeleting = ref(false)
const route = useRoute()

const userProfile = ref({
  nom: '',
  role: ''
})

onMounted(async () => {
  const storedUser = sessionStorage.getItem('user')

  if (storedUser) {
    const user = JSON.parse(storedUser)

    userProfile.value.nom = `${user.firstname} ${user.lastname}`
    userProfile.value.role = user.role
  }

  await loadClients()
  await loadMissions()
})
const unreadNotifications = ref(3)


async function loadClients() {
  try {
    const response = await axios.get('/client/afficher_clients/')
    listClients.value = response.data.response

    lastTenClients.value = [...listClients.value]
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .slice(0, 10)

  } catch (error) {
    console.error(error)
  }
}

async function loadMissions() {
  try {
    const response = await axios.get('/mission/afficher_missions/')
    totalMissions.value = response.data.response.length
  } catch (error) {
    console.error(error)
  }
}

function redirectClientSpace(id) {
  router.push(`/client/${id}`)
}

function newClient() {
  router.push(`/newClient`)
}

function logout() {
  sessionStorage.removeItem('token')
  sessionStorage.removeItem('user')
  router.push('/connexion')
}


function isActive(path) {
  return route.path === path
}

// Suppression
function confirmDeleteClient(client, event) {
  event.stopPropagation()
  clientToDelete.value = client
  showDeleteModal.value = true
}

// ====== DONNÉES STATIQUES (TEMPORAIRES) ======
const currentMission = ref({
  id: 'mission-demo-001',
  nom: 'Audit financier 2024',
  entreprise: 'NSIA Banque Guinée',
  annee: 2024,
  progression: 45, // %
  etape: 'Contrôle de cohérence'
})

async function deleteClient() {
  if (!clientToDelete.value) return

  isDeleting.value = true
  try {
    const response = await axios.delete(`/client/supprimer_client/${clientToDelete.value._id}`)

    if (response.data.response === 'success') {
      listClients.value = listClients.value.filter(c => c._id !== clientToDelete.value._id)
      alert(`Client supprimé avec succès`)
    }

  } catch (error) {
    console.error(error)
  } finally {
    isDeleting.value = false
    showDeleteModal.value = false
    clientToDelete.value = null
  }
}
</script>

<template>
  <div class="flex w-full overflow-hidden">

    <!-- SIDEBAR GAUCHE -->
    <!-- SIDEBAR GAUCHE -->
<aside class="w-72 shrink-0 bg-blue-ycube text-white flex flex-col px-6 py-8">

  <!-- Logo -->
  <div class="flex items-center gap-3 mb-10">
    <img src="../assets/logo.png" alt="Logo" class="h-12" />
    <h2 class="text-lg font-bold tracking-wide">CAC PERFORM</h2>
  </div>

  <!-- Menu -->
  <nav class="flex flex-col gap-4 text-white">

    <!-- Tableau de bord -->
    <button
      @click="router.push('/')"
      :class="[
        'flex items-center gap-3 px-3 py-2 rounded-lg transition',
        isActive('/') 
          ? 'bg-white text-blue-ycube font-semibold shadow-md' 
          : 'hover:bg-blue-700'
      ]"
    >
      <i :class="[
        'fa-solid fa-chart-pie text-lg',
        isActive('/') ? 'text-blue-ycube' : 'text-white'
      ]"></i>
      Tableau de bord
    </button>

    <!-- Clients -->
    <button
      @click="router.push('/clients')"
      :class="[
        'flex items-center gap-3 px-3 py-2 rounded-lg transition',
        isActive('/clients') 
          ? 'bg-white text-blue-ycube font-semibold shadow-md' 
          : 'hover:bg-green-ycube-2'
      ]"
    >
      <i :class="[
        'fa-solid fa-users text-lg',
        isActive('/clients') ? 'text-blue-ycube' : 'text-white'
      ]"></i>
      Clients
    </button>

    <!-- Missions -->
    <button
      @click="router.push('/missions')"
      :class="[
        'flex items-center gap-3 px-3 py-2 rounded-lg transition',
        isActive('/missions') 
          ? 'bg-white text-blue-ycube font-semibold shadow-md' 
          : 'hover:bg-green-ycube-2'
      ]"
    >
      <i :class="[
        'fa-solid fa-clipboard-check text-lg',
        isActive('/missions') ? 'text-blue-ycube' : 'text-white'
      ]"></i>
      Missions d’audit
    </button>

  </nav>

  <!-- Profil / Notifications -->
  <div class="mt-auto flex flex-col gap-6 pt-10 border-t border-white/30">

    <!-- Notifications -->
    <div class="flex items-center gap-4 cursor-pointer hover:text-gray-200 transition">
      <i class="fa-solid fa-bell text-orange-400 text-xl"></i>
      <span class="text-sm">Notifications ({{ unreadNotifications }})</span>
    </div>

    <!-- Profil utilisateur -->
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center text-white text-lg font-semibold">
        {{ userProfile.nom.charAt(0) }}
      </div>
      <div>
        <p class="font-semibold">{{ userProfile.nom }}</p>
        <p class="text-xs text-gray-200">{{ userProfile.role }}</p>
      </div>
    </div>

    <!-- Déconnexion -->
    <button @click="logout"
      class="flex items-center gap-2 text-gray-200 hover:text-red-300 transition">
      <i class="fa-solid fa-right-from-bracket"></i>
      Déconnexion
    </button>

  </div>

</aside>



    <!-- CONTENU DASHBOARD -->
    <main class="flex-1 overflow-y-auto p-6 lg:p-10 flex flex-col gap-10">

      <!-- BARRE DE RECHERCHE -->
      <div class="flex justify-end">
        <div class="flex items-center bg-white px-4 py-2 w-full sm:w-2/3 lg:w-1/3 rounded-lg shadow">
          <i class="fa-solid fa-magnifying-glass text-gray-500 mr-3"></i>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Rechercher un client..."
            class="flex-1 bg-transparent focus:outline-none"
          />
        </div>
      </div>

      <!-- CARDS (stats) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 lg:gap-8">

        <div class="bg-white rounded-lg shadow p-6 text-center">
          <p class="text-4xl font-bold text-blue-ycube">{{ listClients.length }}</p>
          <p class="text-gray-600 mt-2">Clients enregistrés</p>
        </div>

        <div class="bg-white rounded-lg shadow p-6 text-center">
          <p class="text-4xl font-bold text-green-ycube">{{ totalMissions }}</p>
          <p class="text-gray-600 mt-2">Missions d’audit réalisées</p>
        </div>

      </div>

      <!-- CARD : MISSION EN COURS -->
<div class="bg-white rounded-xl shadow p-6">

  <!-- Header -->
  <div class="flex justify-between items-start mb-4">
    <div>
      <h3 class="text-lg font-semibold text-gray-800">Mission en cours</h3>
      <p class="text-sm text-gray-500">
        {{ currentMission.entreprise }} — {{ currentMission.annee }}
      </p>
    </div>

    <span class="px-3 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-700">
      En cours
    </span>
  </div>

  <!-- Nom + étape -->
  <p class="text-sm text-gray-700 mb-2">
    Mission :
    <span class="font-semibold text-blue-ycube">
      {{ currentMission.nom }}
    </span>
  </p>

  <p class="text-sm text-gray-700 mb-3">
    Étape actuelle :
    <span class="font-semibold text-green-ycube">
      {{ currentMission.etape }}
    </span>
  </p>

  <!-- Barre de progression -->
  <div class="w-full bg-gray-200 rounded-full h-3 mb-4">
    <div
      class="bg-blue-ycube h-3 rounded-full transition-all duration-500"
      :style="{ width: currentMission.progression + '%' }"
    ></div>
  </div>

  <div class="flex justify-between items-center">
    <span class="text-sm text-gray-600">
      Progression : <strong>{{ currentMission.progression }}%</strong>
    </span>

    <button
      class="px-4 py-2 bg-blue-ycube text-white rounded-md text-sm font-semibold hover:bg-blue-700 transition"
    >
      Reprendre la mission →
    </button>
  </div>

</div>


      <!-- TABLEAU 10 DERNIERS CLIENTS -->
      <div class="bg-white rounded-lg shadow p-6">
        <h3 class="text-xl font-semibold mb-4">Derniers clients enregistrés</h3>

        <table class="w-full table-auto border-collapse">
          <thead class="bg-gray-100 text-gray-700">
            <tr class="h-12">
              <th class="text-left pl-3">Client</th>
              <th class="text-left pl-3">Activité</th>
              <th class="text-left pl-3">Adresse</th>
              <th class="text-left pl-3">Référentiel</th>
              <th class="text-left pl-3">Dernière mission</th>
              <th class="text-center">Actions</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="client in lastTenClients"
                :key="client._id"
                class="h-12 border-b hover:bg-gray-50 cursor-pointer"
                @click="redirectClientSpace(client._id)">

              <td class="pl-3">{{ client.nom }}</td>
              <td class="pl-3">{{ client.activite }}</td>
              <td class="pl-3">{{ client.adresse }}</td>
              <td class="pl-3">{{ client.referentiel }}</td>
              <td class="pl-3">{{ client.date_mission }}</td>

              <td class="text-center">
                <button 
                  @click.stop="confirmDeleteClient(client, $event)"
                  class="bg-red-500 text-white px-2 py-1 rounded text-xs">
                  🗑️
                </button>
              </td>

            </tr>
          </tbody>

        </table>
      </div>

    </main>


    <!-- MODAL SUPPRESSION -->
    <div v-if="showDeleteModal"
         class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">

      <div class="bg-white p-6 rounded-lg shadow-xl max-w-md w-full">
        <h3 class="text-lg font-semibold mb-4">Supprimer le client ?</h3>

        <p class="text-sm text-gray-600 mb-6">
          Voulez-vous vraiment supprimer <strong>{{ clientToDelete?.nom }}</strong> ?
        </p>

        <div class="flex justify-end gap-3">
          <button @click="cancelDelete"
                  class="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300">
            Annuler
          </button>

          <button @click="deleteClient"
                  class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                  :disabled="isDeleting">
            Supprimer
          </button>
        </div>
      </div>

    </div>

  </div>
</template>
