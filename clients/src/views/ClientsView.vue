<template>
  <div class="p-6 h-full w-full min-h-screen">
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Liste des clients</h1>
        <p class="text-sm text-gray-500">Clients en base de donnees</p>
      </div>

      <div class="flex flex-col md:flex-row gap-3 w-full md:w-auto">
        <button @click="goToNewClient"
          class="px-5 py-3 bg-blue-ycube text-white rounded-xl font-semibold hover:bg-blue-900 transition">
          Nouveau client
        </button>
        <input v-model="search" type="text" placeholder="Rechercher par entreprise..."
          class="p-3 border border-gray-300 rounded-xl w-full md:w-72 focus:outline-none focus:ring-2 focus:ring-blue-ycube" />
        <select v-model="sectorFilter"
          class="p-3 border border-gray-300 rounded-xl w-full md:w-60 focus:outline-none focus:ring-2 focus:ring-green-ycube">
          <option value="">Tous secteurs</option>
          <option v-for="sector in sectors" :key="sector" :value="sector">
            {{ sector }}
          </option>
        </select>
      </div>
    </div>

    <div class="bg-white rounded-2xl shadow p-4 w-full h-[70vh] overflow-auto">
      <div v-if="loading" class="py-10 text-center text-gray-500">Chargement des clients...</div>
      <div v-else-if="errorMsg" class="py-10 text-center text-red-600">{{ errorMsg }}</div>
      <table v-else class="min-w-full w-full">
        <thead>
          <tr class="text-left text-gray-600 border-b">
            <th class="py-3 px-4">Entreprise</th>
            <th class="py-3 px-4">Secteur</th>
            <th class="py-3 px-4">Adresse</th>
            <th class="py-3 px-4">RCCM</th>
            <th class="py-3 px-4">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="client in paginatedClients" :key="client._id" class="border-t">
            <td class="py-3 px-4 font-semibold text-gray-800">{{ client.company_name || '-' }}</td>
            <td class="py-3 px-4">{{ client.sector || '-' }}</td>
            <td class="py-3 px-4">{{ client.address || '-' }}</td>
            <td class="py-3 px-4">{{ client.RCCM || '-' }}</td>
            <td class="py-3 px-4">
              <button @click="openModal(client)"
                class="px-4 py-2 bg-green-ycube text-white rounded-full font-semibold hover:bg-green-ycube-2 transition">
                Voir
              </button>
            </td>
          </tr>

          <tr v-if="filteredClients.length === 0">
            <td colspan="5" class="py-6 text-center text-gray-500">
              Aucun client trouve
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="filteredClients.length > 0" class="flex items-center justify-between px-2 pt-4">
        <p class="text-sm text-gray-500">
          Page {{ currentPage }} / {{ totalPages }} - {{ filteredClients.length }} clients
        </p>
        <div class="flex items-center gap-2">
          <button
            class="px-3 py-1 border rounded disabled:opacity-50"
            :disabled="currentPage === 1"
            @click="prevPage"
          >
            Precedenteeee
          </button>
          <button
            class="px-3 py-1 border rounded disabled:opacity-50"
            :disabled="currentPage === totalPages"
            @click="nextPage"
          >
            Suivant
          </button>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl w-full max-w-3xl p-6 relative max-h-[90vh] overflow-auto">
          <div class="flex justify-end gap-4">

            <button
              class="px-5 py-2 rounded-lg border right-0 border-blue-ycube text-blue-ycube font-semibold hover:bg-blue-ycube hover:text-white transition"
              @click="updateClient">
              {{ editMode ? 'Enregistrer' : 'Modifier client' }}
            </button>
  
            <button v-if="editMode"
              class="px-5 py-2 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition"
              @click="cancelEdit">
              Annuler
            </button>
            <button @click="closeModal" class=" right-4 text-gray-500 hover:text-gray-800">
              <i class="fa-solid fa-xmark text-2xl"></i>
            </button>
          </div>

          <h2 class="text-xl font-bold text-gray-800 mb-6">Details client</h2>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <p class="text-gray-500">Nom du responsable</p>
              <p v-if="!editMode" class="font-semibold text-gray-800">{{ fullResponsibleName(selectedClient) }}</p>
              <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-2">
                <input v-model="selectedClient.civility" class="border p-2 rounded w-full" placeholder="Civilite" />
                <input v-model="selectedClient.responsable_name" class="border p-2 rounded w-full" placeholder="Nom responsable" />
              </div>
            </div>
            <div>
              <p class="text-gray-500">Fonction du responsable</p>
              <p v-if="!editMode" class="font-semibold text-gray-800">{{ selectedClient.responsable_function || '-' }}</p>
              <input v-else v-model="selectedClient.responsable_function" class="border p-2 rounded w-full" />
            </div>
            <div>
              <p class="text-gray-500">Nom de l'entreprise</p>
              <p v-if="!editMode" class="font-semibold text-gray-800">{{ selectedClient.company_name || '-' }}</p>
              <input v-else v-model="selectedClient.company_name" class="border p-2 rounded w-full" />
            </div>
            <div>
              <p class="text-gray-500">Secteur</p>
              <p v-if="!editMode" class="font-semibold text-gray-800">{{ selectedClient.sector || '-' }}</p>
              <input v-else v-model="selectedClient.sector" class="border p-2 rounded w-full" />
            </div>
            <div>
              <p class="text-gray-500">Adresse</p>
              <p v-if="!editMode" class="font-semibold text-gray-800">{{ selectedClient.address || '-' }}</p>
              <input v-else v-model="selectedClient.address" class="border p-2 rounded w-full" />
            </div>
            <div>
              <p class="text-gray-500">RCCM</p>
              <p v-if="!editMode" class="font-semibold text-gray-800">{{ selectedClient.RCCM || '-' }}</p>
              <input v-else v-model="selectedClient.RCCM" class="border p-2 rounded w-full" />
            </div>
            <div>
              <p class="text-gray-500">Forme legale</p>
              <p v-if="!editMode" class="font-semibold text-gray-800">{{ selectedClient.legal_form || '-' }}</p>
              <input v-else v-model="selectedClient.legal_form" class="border p-2 rounded w-full" />
            </div>
            <div>
              <p class="text-gray-500">Date de creation</p>
              <p v-if="!editMode" class="font-semibold text-gray-800">{{ formatDate(selectedClient.creation_date) }}</p>
              <input v-else v-model="selectedClient.creation_date" class="border p-2 rounded w-full" />
            </div>
            <div>
              <p class="text-gray-500">Pays</p>
              <p v-if="!editMode" class="font-semibold text-gray-800">{{ selectedClient.country || '-' }}</p>
              <input v-else v-model="selectedClient.country" class="border p-2 rounded w-full" />
            </div>
          </div>

          <div class="flex justify-between mt-6">
            <button @click="goToClientSpace(selectedClient._id)"
              class="px-6 py-3 rounded-full border text-white bg-green-ycube border-gray-300 font-semibold hover:bg-green-700">
              Voir les missions
            </button>
            <button @click="goToNewMission(selectedClient._id)"
              class="px-6 py-3 rounded-full border text-white bg-blue-ycube border-gray-300 font-semibold hover:bg-blue-700">
              Nouvelle mission
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, watch } from 'vue'
import router from '@/router'
import { useNotyf } from '@/composables/useNotyf'

const axios = inject('axios')
const notyf = useNotyf()

const clients = ref([])
const loading = ref(false)
const errorMsg = ref('')

const search = ref('')
const sectorFilter = ref('')
const showModal = ref(false)
const selectedClient = ref({})
const originalSelectedClient = ref({})

const editMode = ref(false)
const itemsPerPage = 25
const currentPage = ref(1)

function normalizeClient(raw) {
  return {
    _id: raw._id || '',
    civility: raw.civility || '',
    responsable_name: raw.responsable_name || '',
    responsable_function: raw.responsable_function || '',
    company_name: raw.company_name || '',
    sector: raw.sector || '',
    address: raw.address || '',
    RCCM: raw.RCCM || '',
    legal_form: raw.legal_form || '',
    creation_date: raw.creation_date || '',
    country: raw.country || ''
  }
}

async function loadClients() {
  loading.value = true
  errorMsg.value = ''

  try {
    const { data } = await axios.get('/client/afficher_clients/')
    const apiClients = Array.isArray(data?.response) ? data.response : []
    clients.value = apiClients.map(normalizeClient)
  } catch (error) {
    console.error(error)
    errorMsg.value = error?.response?.data?.message || 'Erreur lors du chargement des clients.'
  } finally {
    loading.value = false
  }
}

const sectors = computed(() => {
  const list = clients.value.map(c => c.sector).filter(Boolean)
  return [...new Set(list)]
})

const filteredClients = computed(() => {
  const keyword = search.value.trim().toLowerCase()
  return clients.value.filter(client => {
    const matchesName = (client.company_name || '').toLowerCase().includes(keyword)
    const matchesSector = sectorFilter.value ? client.sector === sectorFilter.value : true
    return matchesName && matchesSector
  })
})

const totalPages = computed(() => {
  const total = Math.ceil(filteredClients.value.length / itemsPerPage)
  return total > 0 ? total : 1
})

const paginatedClients = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  return filteredClients.value.slice(start, start + itemsPerPage)
})

function nextPage() {
  if (currentPage.value < totalPages.value) currentPage.value += 1
}

function prevPage() {
  if (currentPage.value > 1) currentPage.value -= 1
}

function openModal(client) {
  selectedClient.value = { ...client }
  originalSelectedClient.value = { ...client }
  editMode.value = false
  showModal.value = true
}

function closeModal() {
  editMode.value = false
  showModal.value = false
}

function goToNewClient() {
  router.push('/newClient')
}

function goToNewMission(_id) {
  if (!_id) return
  router.push(`/newMission/${_id}`)
}

function goToClientSpace(_id) {
  router.push(`/client/${_id}`)
}

function fullResponsibleName(client) {
  const civ = (client?.civility || '').trim()
  const nom = (client?.responsable_name || '').trim()
  const full = [civ, nom].filter(Boolean).join(' ')
  return full || '-'
}

function formatDate(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('fr-FR')
}

async function updateClient() {
  if (!editMode.value) {
    originalSelectedClient.value = { ...selectedClient.value }
    editMode.value = true
    return
  }
  try {
    const payload = { ...selectedClient.value }
    await axios.put('/client/modifier_client/', payload)
    const index = clients.value.findIndex(c => c._id === selectedClient.value._id)
    if (index !== -1) {
      clients.value[index] = normalizeClient(selectedClient.value)
    }
    originalSelectedClient.value = { ...selectedClient.value }
    notyf.trigger('Client mis à jour', 'success')
    editMode.value = false
  } catch (e) {
    notyf.trigger("Echec de la mise à jour", 'error')
  }
}


function cancelEdit() {
  selectedClient.value = { ...originalSelectedClient.value }
  editMode.value = false
}

watch([search, sectorFilter], () => {
  currentPage.value = 1
})

watch(totalPages, (value) => {
  if (currentPage.value > value) currentPage.value = value
})

onMounted(loadClients)
</script>
