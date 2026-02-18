<script setup>
import { ref, inject, onMounted, computed } from 'vue';
import router from "@/router";
import { useNotyf } from '@/composables/useNotyf'


const axios = inject('axios');
const notyf = useNotyf()


const infos = ref({})
const missions = ref([])
const editMode = ref(false)
const props = defineProps(['clientId'])

// Variables pour la suppression de mission
const missionToDelete = ref(null)
const isDeleting = ref(false)
const confirmingDelete = ref(null) // ID de la mission en cours de confirmation
const searchMission = ref("");

onMounted(async() => {
    try {
        console.log("🔍 Chargement des informations du client:", props.clientId)
        const response = (await axios.get(`/client/info_client/${props.clientId}`)).data
        console.log("📊 Réponse complète:", response)
        
        if (response && response.response) {
            infos.value = response.response.info
            missions.value = response.response.missions || []
            console.log("✅ Missions chargées:", missions.value.length)
            console.log("📋 Détails missions:", missions.value)
        } else {
            console.error("❌ Format de réponse inattendu:", response)
            missions.value = []
        }
    } catch (e) {
        console.error("❌ Erreur lors du chargement:", e)
        console.error("📋 Détails:", e.response?.data)
        missions.value = []
    }
})

async function newMission() {
    router.push(`/newMission/${props.clientId}`)
}

async function updateClient() {
    if (!editMode.value) {
        editMode.value = true
        return
    }
    try {
        const payload = { ...infos.value }
        const res = (await axios.put('/client/modifier_client/', payload)).data.response
        notyf.trigger('Client mis à jour', 'success')
        editMode.value = false
    } catch (e) {
        notyf.trigger("Échec de la mise à jour", 'error')
    }
}

const filteredMissions = computed(() => {
  return missions.value.filter(m =>
    m.annee_auditee.toString().includes(searchMission.value) ||
    m.date_debut.includes(searchMission.value) ||
    m.date_fin.includes(searchMission.value)
  );
});


function seeMore(mission, event) {
    if (event) {
        event.stopPropagation()
    }
    if (!mission?._id) {
        console.error("❌ ID de mission manquant")
        notyf.trigger("Erreur: ID de mission manquant", "error")
        return
    }
    console.log("🔍 Navigation vers la mission:", mission._id)
    router.push({
      path: `/grouping-analyse/${mission._id}`,
      query: { annee: mission.annee_auditee }
    })
}

function back() {
    router.push(`/`)
}

// Fonctions pour la suppression de mission
function confirmDeleteMission(mission, event) {
    event.stopPropagation() // Empêcher le clic de se propager
    confirmingDelete.value = mission._id
    missionToDelete.value = mission
}

function cancelDelete() {
    confirmingDelete.value = null
    missionToDelete.value = null
}

async function deleteMission() {
    if (!missionToDelete.value) return
    
    isDeleting.value = true
    try {
        const response = await axios.delete(`/mission/supprimer_mission/${missionToDelete.value._id}`)
        
        if (response.data.success) {
            notyf.trigger('Mission supprimée avec succès', 'success')
            
            // Recharger les missions
            const clientResponse = (await axios.get(`/client/info_client/${props.clientId}`)).data
            if (clientResponse && clientResponse.response) {
                missions.value = clientResponse.response.missions || []
            }
        } else {
            notyf.trigger(response.data.error || 'Erreur lors de la suppression', 'error')
        }
    } catch (e) {
        console.error("❌ Erreur lors de la suppression:", e)
        notyf.trigger(e.response?.data?.error || 'Erreur lors de la suppression de la mission', 'error')
    } finally {
        isDeleting.value = false
        confirmingDelete.value = null
        missionToDelete.value = null
    }
}
</script>

<template>
  <div class="flex flex-col w-full overflow-hidden">

    <!-- HEADER -->
    <div class="bg-white shadow-sm px-6 py-4 flex items-center justify-between">
      
      <button
        @click="back"
        class="text-blue-ycube font-semibold hover:underline flex items-center gap-2"
      >
        <i class="fa-solid fa-arrow-left"></i> Retour
      </button>

      <div class="text-center">
        <h1 class="text-xl font-bold text-blue-ycube">{{ infos.nom }}</h1>
        <p class="text-sm text-gray-500">{{ infos.activite }}</p>
      </div>

      <div class="flex gap-3">
        <button
          class="px-5 py-2 rounded-lg border border-blue-ycube text-blue-ycube font-semibold hover:bg-blue-ycube hover:text-white transition"
          @click="updateClient"
        >
          {{ editMode ? 'Enregistrer' : 'Modifier client' }}
        </button>

        <button
          class="px-5 py-2 rounded-lg bg-green-ycube-2 text-white font-semibold hover:bg-green-ycube transition"
          @click="newMission"
        >
          Nouvelle mission
        </button>
      </div>

    </div>


    <!-- CONTENU + INFOS CLIENT -->
    <div class="p-6 overflow-y-auto flex flex-col gap-8">

      <!-- Informations du client -->
      <div class="bg-white shadow rounded-xl p-6 grid grid-cols-2 gap-6">

        <div>
          <label class="text-gray-500 text-sm">Client</label>
          <p v-if="!editMode" class="font-semibold text-blue-ycube">{{ infos.nom }}</p>
          <input v-else v-model="infos.nom" class="border p-2 rounded w-full" />
        </div>

        <div>
          <label class="text-gray-500 text-sm">Forme juridique</label>
          <p v-if="!editMode" class="font-semibold text-blue-ycube">{{ infos.forme_juridique }}</p>
          <input v-else v-model="infos.forme_juridique" class="border p-2 rounded w-full" />
        </div>

        <div>
          <label class="text-gray-500 text-sm">Activité</label>
          <p v-if="!editMode" class="font-semibold text-blue-ycube">{{ infos.activite }}</p>
          <input v-else v-model="infos.activite" class="border p-2 rounded w-full" />
        </div>

        <div>
          <label class="text-gray-500 text-sm">N°CC</label>
          <p v-if="!editMode" class="font-semibold text-blue-ycube">{{ infos.n_cc }}</p>
          <input v-else v-model="infos.n_cc" class="border p-2 rounded w-full" />
        </div>

        <div>
          <label class="text-gray-500 text-sm">Adresse</label>
          <p v-if="!editMode" class="font-semibold text-blue-ycube">{{ infos.adresse }}</p>
          <input v-else v-model="infos.adresse" class="border p-2 rounded w-full" />
        </div>

        <div>
          <label class="text-gray-500 text-sm">Capital</label>
          <p v-if="!editMode" class="font-semibold text-blue-ycube">{{ infos.capital }}</p>
          <input v-else v-model="infos.capital" class="border p-2 rounded w-full" />
        </div>

        <div>
          <label class="text-gray-500 text-sm">Siège social</label>
          <p v-if="!editMode" class="font-semibold text-blue-ycube">{{ infos.siege_social }}</p>
          <input v-else v-model="infos.siege_social" class="border p-2 rounded w-full" />
        </div>

        <div>
          <label class="text-gray-500 text-sm">Référentiel comptable</label>
          <p v-if="!editMode" class="font-semibold text-blue-ycube">{{ infos.referentiel }}</p>
          <input v-else v-model="infos.referentiel" class="border p-2 rounded w-full" />
        </div>

      </div>


      <!-- RECHERCHE -->
      <div class="flex justify-end">
        <div class="flex items-center bg-white px-4 py-2 w-1/3 rounded-lg shadow">
          <i class="fa-solid fa-magnifying-glass text-gray-500 mr-3"></i>
          <input
            v-model="searchMission"
            type="text"
            placeholder="Rechercher une mission..."
            class="flex-1 bg-transparent focus:outline-none"
          />
        </div>
      </div>


      <!-- TABLEAU DES MISSIONS -->
      <div class="bg-white shadow rounded-xl p-6">

        <h3 class="text-xl font-semibold mb-4 text-blue-ycube">
          Tableau des missions
        </h3>

        <table class="min-w-full text-sm">
          <thead class="bg-blue-ycube text-white h-12 text-left">
            <tr>
              <th class="px-3">#</th>
              <th class="px-3">Année auditée</th>
              <th class="px-3">Date début</th>
              <th class="px-3">Date fin</th>
              <th class="px-3 text-center">Actions</th>
            </tr>
          </thead>

          <tbody>

            <tr v-if="filteredMissions.length === 0" class="h-12">
              <td colspan="5" class="text-center text-gray-500 py-4">
                Aucune mission trouvée.
              </td>
            </tr>

            <tr
              v-for="(mission, index) in filteredMissions"
              :key="mission._id"
              class="h-12 border-b hover:bg-gray-50 cursor-pointer"
            >
              <td class="px-3">{{ index + 1 }}</td>
              <td class="px-3">{{ mission.annee_auditee }}</td>
              <td class="px-3">{{ mission.date_debut }}</td>
              <td class="px-3">{{ mission.date_fin }}</td>

              <td class="px-3">
                <div class="flex justify-center gap-2">

                  <button
                    class="px-4 py-1 bg-blue-ycube text-white rounded hover:bg-blue-700 text-xs"
                    @click.stop="seeMore(mission)"
                  >
                    Voir
                  </button>

                  <button
                    class="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-xs"
                    @click.stop="confirmDeleteMission(mission)"
                  >
                    🗑️
                  </button>

                </div>
              </td>

            </tr>

          </tbody>
        </table>

      </div>

    </div>

  </div>
</template>
