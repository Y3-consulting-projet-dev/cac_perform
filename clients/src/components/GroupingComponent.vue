<script setup>
import { ref, onMounted, inject, shallowRef, watch, computed } from 'vue'
import GroupingInitial from './GroupingInitial.vue'
import GroupingActif from './GroupingActif.vue'
import GroupingPassif from './GroupingPassif.vue'
import GroupingPnl from './GroupingPnl.vue'
import { useNotyf } from '@/composables/useNotyf'

const notif = useNotyf()
const axios = inject('axios')

const props = defineProps ({
  data: {
    type: [Object, Array],
    default: () => ({})
  },
  annee_auditee: {
    type: [String, Number],
    default: null
  }
})



const activeTab = ref('init')
const currentComponent = shallowRef(GroupingInitial)

// ✅ SOURCE UNIQUE
const grouping = ref([])
const selectedGroupIds = ref([])
const selectionMode = ref(false)

// Recuperer l'id mission
const id_mission = window.location.pathname.split('/')[2]

function syncGrouping(nextGrouping) {
  if (!Array.isArray(nextGrouping)) {
    console.warn('❌ GroupingComponent sans données valides', props.data)
    return
  }
  grouping.value = nextGrouping
  if (!activeTab.value) showComp('init')
}

onMounted(() => {
  syncGrouping(props.data?.grouping)
})

watch(
  () => props.data?.grouping,
  (next) => {
    if (next) syncGrouping(next)
  },
  { deep: false }
)



function showComp(type) {
  activeTab.value = type

  if (type === 'init') currentComponent.value = GroupingInitial
  if (type === 'actif') currentComponent.value = GroupingActif
  if (type === 'passif') currentComponent.value = GroupingPassif
  if (type === 'pnl') currentComponent.value = GroupingPnl
}



const selectableGroups = computed(() => {
  return (grouping.value || [])
    .filter((g) => Array.isArray(g?.comptes || g?.comptes_detaille) && (g.comptes || g.comptes_detaille).length > 0)
    .map((g) => ({
      id: String(g.ref || g.libelle || g.compte || '').trim(),
      label: g.libelle || g.ref || g.compte || ''
    }))
    .filter((g) => g.id)
})

function selectAllGroups() {
  selectedGroupIds.value = selectableGroups.value.map((g) => g.id)
}

function clearGroupSelection() {
  selectedGroupIds.value = []
}

async function downloadGrouping() {
  if (!grouping.value.length) return

  if (selectionMode.value && !selectedGroupIds.value.length) {
    notif.trigger('Veuillez selectionner au moins un groupe.', 'warning')
    return
  }

  if (!grouping.value[0]?.mat_sign) {
    notif.trigger('Grouping incomplet: téléchargement forcé.', 'warning')
  }

  const refsParam = selectedGroupIds.value.length
    ? `?refs=${encodeURIComponent(selectedGroupIds.value.join(','))}`
    : ''
  const response = await axios.get(
    `/mission/download_grouping/${id_mission}${refsParam}`,
    { responseType: 'blob' }
  )

  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', 'grouping.xlsx')
  document.body.appendChild(link)
  link.click()
  window.URL.revokeObjectURL(url)
}

</script>


<template>
    <div class="h-full w-full flex flex-col space-y-2 overflow-auto">
        <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <button @click="showComp('init')" :class="[
                'w-full px-3 py-2 text-white rounded-md shadow-md transition-all duration-300',
                activeTab === 'init' ? 'bg-green-ycube' : 'bg-blue-ycube'
            ]">
                Grouping Initial
            </button>

            <button @click="showComp('actif')" :class="[
                'w-full px-3 py-2 text-white rounded-md shadow-md transition-all duration-300',
                activeTab === 'actif' ? 'bg-green-ycube' : 'bg-blue-ycube'
            ]">
                Actifs
            </button>

            <button @click="showComp('passif')" :class="[
                'w-full px-3 py-2 text-white rounded-md shadow-md transition-all duration-300',
                activeTab === 'passif' ? 'bg-green-ycube' : 'bg-blue-ycube'
            ]">
                Passifs
            </button>

            <button @click="showComp('pnl')" :class="[
                'w-full px-3 py-2 text-white rounded-md shadow-md transition-all duration-300',
                activeTab === 'pnl' ? 'bg-green-ycube' : 'bg-blue-ycube'
            ]">
                Compte de résultat
            </button>

            <button v-if="!selectionMode" class="w-full px-3 py-2 bg-blue-ycube text-white rounded-md shadow-md"
                @click="selectionMode = true">Télécharger</button>

            <template v-else>
                <button class="w-full px-3 py-2 bg-gray-100 text-gray-700 rounded-md shadow-md"
                    @click="selectAllGroups">Tout sélectionner</button>

                <button class="w-full px-3 py-2 bg-green-ycube text-white rounded-md shadow-md"
                    :disabled="!selectedGroupIds.length"
                    @click="downloadGrouping">Télécharger</button>

                <button class="w-full px-3 py-2 bg-gray-200 text-gray-700 rounded-md shadow-md"
                    @click="selectionMode = false; clearGroupSelection()">Annuler</button>
            </template>
        </div>

        <!--  -->
        <div class="flex-auto flex flex-col overflow-visible">
            <div class="w-full px-3 py-2 h-full flex flex-col overflow-visible">
                <component
  :is="currentComponent"
  :grouping="grouping"
  :annee_auditee="annee_auditee"
  :selection-enabled="selectionMode"
  :selected-ids="selectedGroupIds"
  @update:selected-ids="selectedGroupIds = $event"
/>

            </div>
        </div>
    </div>
</template>
