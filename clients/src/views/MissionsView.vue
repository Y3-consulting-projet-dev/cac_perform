<script setup>
import { ref, computed, onMounted, inject, watch } from 'vue'
import router from '@/router'

const axios = inject('axios')

function goToMission(mission) {
  router.push({
    path: `/grouping-analyse/${mission._id}`,
    query: { annee: mission.annee_auditee || '' }
  })
}

function getProgress(mission) {
  if (mission.statut === 'Terminee' || mission.statut === 'Terminée') return 100
  if (mission.statut === 'Suspendue') return 100
  return mission.progress ?? 0
}

const missions = ref([])
const clientsById = ref({})
const searchQuery = ref('')
const itemsPerPage = 25
const currentPage = ref(1)

onMounted(() => {
  loadMissions()
})

const filteredMissions = computed(() => {
  if (!searchQuery.value) return missions.value

  const query = searchQuery.value.toLowerCase()
  return missions.value.filter(m =>
    (m.nom || '').toLowerCase().includes(query) ||
    getClientName(m).toLowerCase().includes(query)
  )
})

const totalPages = computed(() => {
  const total = Math.ceil(filteredMissions.value.length / itemsPerPage)
  return total > 0 ? total : 1
})

const paginatedMissions = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  return filteredMissions.value.slice(start, start + itemsPerPage)
})

function nextPage() {
  if (currentPage.value < totalPages.value) currentPage.value += 1
}

function prevPage() {
  if (currentPage.value > 1) currentPage.value -= 1
}

function newMission() {
  router.push('/newMission')
}

function getMandat(mission) {
  const start = mission.date_debut_mandat || mission.date_debut
  const end = mission.date_fin_mandat || mission.date_fin
  const startYear = start ? start.slice(0, 4) : '-'
  const endYear = end ? end.slice(0, 4) : '-'
  return `${startYear} -> ${endYear}`
}

async function loadMissions() {
  try {
    const [missionsRes, clientsRes] = await Promise.allSettled([
      axios.get('/mission/all_missions'),
      axios.get('/client/afficher_clients/')
    ])

    const missionRows = missionsRes.status === 'fulfilled'
      ? (missionsRes.value.data?.response || [])
      : []
    const clientRows = clientsRes.status === 'fulfilled'
      ? (clientsRes.value.data?.response || [])
      : []

    clientsById.value = clientRows.reduce((acc, client) => {
      if (client?._id) acc[client._id] = client.company_name || ''
      return acc
    }, {})

    missions.value = [...missionRows].sort((a, b) => getMissionCreatedAt(b) - getMissionCreatedAt(a))
    console.log('missions triees:', missions.value)
  } catch (e) {
    console.error('Erreur chargement missions:', e)
    missions.value = []
  }
}

function getClientName(mission) {
  if (mission.company_name) return mission.company_name

  const rawId = mission.id_client
  const clientId = typeof rawId === 'object' ? rawId?._id : rawId

  if (clientId && clientsById.value[clientId]) {
    return clientsById.value[clientId]
  }

  return clientId || '-'
}

function getMissionCreatedAt(mission) {
  const dateFields = [mission.created_at, mission.createdAt, mission.date_creation, mission.updated_at]

  for (const value of dateFields) {
    const ts = Date.parse(value)
    if (!Number.isNaN(ts)) return ts
  }

  const id = String(mission?._id || '')
  if (id.length >= 8) {
    const seconds = parseInt(id.slice(0, 8), 16)
    if (!Number.isNaN(seconds)) return seconds * 1000
  }

  return 0
}

watch(searchQuery, () => {
  currentPage.value = 1
})

watch(totalPages, (value) => {
  if (currentPage.value > value) currentPage.value = value
})
</script>

<template>
  <div class="flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-10">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Missions d'audit</h1>
        <p class="text-sm text-gray-500">Liste complete des missions effectuees</p>
      </div>

      <button
        @click="newMission"
        class="flex items-center gap-2 bg-blue-ycube text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition"
      >
        <i class="fa-solid fa-plus"></i>
        Nouvelle mission
      </button>
    </div>

    <div class="mb-6">
      <div class="flex items-center bg-white px-4 py-2 rounded-lg shadow w-full sm:w-2/3 lg:w-1/3">
        <i class="fa-solid fa-magnifying-glass text-gray-400 mr-3"></i>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Rechercher un client..."
          class="flex-1 focus:outline-none"
        />
      </div>
    </div>

    <div class="bg-white rounded-lg shadow overflow-x-auto">
      <table class="min-w-[900px] w-full table-auto">
        <thead class="bg-gray-100 text-gray-700">
          <tr class="h-12 text-sm">
            <th class="text-left px-4">Client</th>
            <th class="text-left px-4">Mandat</th>
            <th class="text-left px-4">Responsable</th>
            <th class="text-left px-4">Statut</th>
            <th class="text-center px-4">Progression</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="mission in paginatedMissions"
            :key="mission._id"
            @click="goToMission(mission)"
            class="border-b hover:bg-gray-50 transition cursor-pointer"
          >
            <td class="px-4 py-3">{{ getClientName(mission) }}</td>

            <td class="px-4 py-3">{{ getMandat(mission) }}</td>

            <td class="px-4 py-3">
              <p class="font-medium">{{ mission.responsable_nom || '-' }}</p>
              <p class="text-xs text-gray-500">
                {{ mission.responsable_role || '-' }} - {{ mission.responsable_grade || '-' }}
              </p>
            </td>

            <td class="px-4 py-3">
              <span
                class="px-3 py-1 rounded-full text-xs font-semibold"
                :class="{
                  'bg-orange-100 text-orange-700': mission.statut === 'En cours',
                  'bg-green-100 text-green-700': mission.statut === 'Terminee' || mission.statut === 'Terminée',
                  'bg-red-100 text-red-700': mission.statut === 'Suspendue'
                }"
              >
                {{ mission.statut || '-' }}
              </span>
            </td>

            <td class="px-4 py-3">
              <div v-if="mission.statut === 'Terminee' || mission.statut === 'Terminée'" class="h-[2px] w-full bg-green-500 rounded-full"></div>
              <div v-else-if="mission.statut === 'Suspendue'" class="h-[2px] w-full bg-red-500 rounded-full"></div>
              <div v-else class="flex items-center gap-3">
                <div class="flex-1 h-[2px] bg-gray-200 rounded-full overflow-hidden">
                  <div class="h-full bg-orange-400 transition-all" :style="{ width: getProgress(mission) + '%' }"></div>
                </div>
                <span class="text-[11px] font-medium text-gray-600">{{ getProgress(mission) }}%</span>
              </div>
            </td>
          </tr>

          <tr v-if="filteredMissions.length === 0">
            <td colspan="6" class="text-center py-10 text-gray-500">Aucune mission trouvee</td>
          </tr>
        </tbody>
      </table>

      <div v-if="filteredMissions.length > 0" class="flex items-center justify-between p-4">
        <p class="text-sm text-gray-500">
          Page {{ currentPage }} / {{ totalPages }} - {{ filteredMissions.length }} missions
        </p>
        <div class="flex items-center gap-2">
          <button
            class="px-3 py-1 border rounded disabled:opacity-50"
            :disabled="currentPage === 1"
            @click="prevPage"
          >
            Precedent
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
  </div>
</template>
