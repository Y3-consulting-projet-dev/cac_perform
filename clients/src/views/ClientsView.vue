<template>
  <div class="p-6 h-full w-full min-h-screen">
    <!-- TITRE -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Liste des clients</h1>
        <p class="text-sm text-gray-500">Tous les clients du cabinet</p>
      </div>

      <!-- BARRE DE RECHERCHE -->
      <div class="flex flex-col md:flex-row gap-3 w-full md:w-auto">
        <input
          v-model="search"
          type="text"
          placeholder="Rechercher par nom..."
          class="p-3 border border-gray-300 rounded-xl w-full md:w-72 focus:outline-none focus:ring-2 focus:ring-blue-ycube"
        />
        <select v-model="sectorFilter"
          class="p-3 border border-gray-300 rounded-xl w-full md:w-60 focus:outline-none focus:ring-2 focus:ring-green-ycube">
          <option value="">Tous secteurs</option>
          <option v-for="sector in sectors" :key="sector" :value="sector">
            {{ sector }}
          </option>
        </select>
      </div>
    </div>

    <!-- TABLEAU CLIENTS -->
    <div class="bg-white rounded-2xl shadow p-4 w-full h-[70vh] overflow-auto">
      <table class="min-w-full w-full">
        <thead>
          <tr class="text-left text-gray-600">
            <th class="py-3 px-4">Entreprise</th>
            <th class="py-3 px-4">Secteur</th>
            <th class="py-3 px-4">Adresse</th>
            <th class="py-3 px-4">N° CC</th>
            <th class="py-3 px-4">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="client in filteredClients" :key="client.id" class="border-t">
            <div class="flex items-center">
              <img :src="client.logo" alt="logo" class="w-10 h-10 rounded-full object-cover" />
              <td class="py-3 px-4 font-semibold text-gray-800">{{ client.name }}</td>
            </div>
            <td class="py-3 px-4">{{ client.sector }}</td>
            <td class="py-3 px-4">{{ client.address }}</td>
            <td class="py-3 px-4">{{ client.cc }}</td>
            <td class="py-3 px-4">
              <button
                @click="openModal(client)"
                class="px-4 py-2 bg-green-ycube text-white rounded-full font-semibold hover:bg-green-ycube-2 transition"
              >
                Voir
              </button>
            </td>
          </tr>

          <tr v-if="filteredClients.length === 0">
            <td colspan="6" class="py-6 text-center text-gray-500">
              Aucun client trouvé
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-white rounded-2xl w-full max-w-3xl p-6 relative">
          
          <!-- CLOSE -->
          <button @click="closeModal"
            class="absolute top-4 right-4 text-gray-500 hover:text-gray-800">
            <i class="fa-solid fa-xmark text-2xl"></i>
          </button>

          <div class="flex flex-col md:flex-row gap-6">
            <!-- Logo -->
            <div class="flex flex-col items-center md:items-start">
              <img :src="selectedClient.logo" alt="logo" class="w-24 h-24 rounded-full object-cover mb-4" />
              <h2 class="text-xl font-bold text-gray-800">{{ selectedClient.name }}</h2>
              <p class="text-sm text-gray-500">{{ selectedClient.sector }}</p>
            </div>

            <!-- INFO -->
            <div class="flex-1">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="text-xs text-gray-500">Adresse</label>
                  <input v-model="selectedClient.address" class="w-full border border-gray-300 rounded-xl p-3" />
                </div>
                <div>
                  <label class="text-xs text-gray-500">N° CC</label>
                  <input v-model="selectedClient.cc" class="w-full border border-gray-300 rounded-xl p-3" />
                </div>
                <div>
                  <label class="text-xs text-gray-500">Capital</label>
                  <input v-model="selectedClient.capital" class="w-full border border-gray-300 rounded-xl p-3" />
                </div>
                <div>
                  <label class="text-xs text-gray-500">Téléphone</label>
                  <input v-model="selectedClient.phone" class="w-full border border-gray-300 rounded-xl p-3" />
                </div>
                <div class="md:col-span-2">
                  <label class="text-xs text-gray-500">Description</label>
                  <textarea v-model="selectedClient.description" rows="3" class="w-full border border-gray-300 rounded-xl p-3"></textarea>
                </div>
              </div>

              <!-- ACTIONS -->
              <div class="flex justify-end gap-3 mt-6">
                <button @click="closeModal"
                  class="px-6 py-2 rounded-full border border-gray-300 font-semibold hover:bg-gray-50">
                  Annuler
                </button>
                <button @click="saveChanges"
                  class="px-6 py-2 rounded-full bg-green-ycube text-white font-semibold hover:bg-green-700">
                  Enregistrer
                </button>
              </div>
            </div>
          </div>

        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const clients = ref([
  {
    id: 1,
    name: "Société Alpha",
    logo: "https://media.licdn.com/dms/image/v2/C4D0BAQGOect4KNRnPA/company-logo_200_200/company-logo_200_200/0/1630549250182/alpha_group_aluminium_logo?e=2147483647&v=beta&t=ferHyawKXFpTuplaZ_H_C3qVcmeia0SlsQAsMpPKbiY",
    sector: "Banque",
    address: "Abidjan, Cocody",
    cc: "CI-0012345",
    capital: "10 000 000 FCFA",
    phone: "+225 01 02 03 04",
    description: "Client premium du cabinet"
  },
  {
    id: 2,
    name: "Boulangerie Du Coin",
    logo: "https://via.placeholder.com/100",
    sector: "Agroalimentaire",
    address: "Abidjan, Treichville",
    cc: "CI-0023456",
    capital: "2 000 000 FCFA",
    phone: "+225 05 06 07 08",
    description: "Client local"
  },
  {
    id: 3,
    name: "NSIA Banque Côte d'Ivoire",
    logo: "data:image/jpeg;base64,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",
    sector: "Banque",
    address: "Abidjan, Treichville",
    cc: "CI-0023456",
    capital: "2 000 000 FCFA",
    phone: "+225 05 06 07 08",
    description: "Client local"
  },
  // ... ajoute ici 18 autres clients fictifs
])

for (let i = 4; i <= 20; i++) {
  clients.value.push({
    id: i,
    name: `Entreprise ${i}`,
    logo: "https://via.placeholder.com/100",
    sector: ["Banque", "Agroalimentaire", "Technologie", "Immobilier", "Santé"][i % 5],
    address: `Adresse ${i}, Abidjan`,
    cc: `CI-00${i}7890`,
    capital: `${i * 1_000_000} FCFA`,
    phone: `+225 07 00 00 0${i}`,
    description: "Description du client"
  })
}

const search = ref("")
const sectorFilter = ref("")
const showModal = ref(false)
const selectedClient = ref({
  id: null,
  name: "",
  logo: "",
  sector: "",
  address: "",
  cc: "",
  capital: "",
  phone: "",
  description: ""
})

const sectors = computed(() => {
  const list = clients.value.map(c => c.sector)
  return [...new Set(list)]
})

const filteredClients = computed(() => {
  return clients.value.filter(client => {
    const matchesName = client.name.toLowerCase().includes(search.value.toLowerCase())
    const matchesSector = sectorFilter.value ? client.sector === sectorFilter.value : true
    return matchesName && matchesSector
  })
})

function openModal(client) {
  selectedClient.value = { ...client }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

function saveChanges() {
  const index = clients.value.findIndex(c => c.id === selectedClient.value.id)
  if (index !== -1) {
    clients.value[index] = { ...selectedClient.value }
  }
  showModal.value = false
}
</script>
