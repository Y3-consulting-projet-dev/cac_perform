<script setup>
import { ref, onMounted, inject, shallowRef, watch } from 'vue'
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

async function downloadGrouping() {
  if (!grouping.value.length) return

  if (grouping.value[0]?.mat_sign) {
    const response = await axios.get(
      `/mission/download_grouping/${id_mission}`,
      { responseType: 'blob' }
    )

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'grouping.xlsx')
    document.body.appendChild(link)
    link.click()
    window.URL.revokeObjectURL(url)
  } else {
    notif.trigger('Impossible de télécharger car le grouping est incomplet', 'error')
  }
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

            <button class="w-full px-3 py-2 bg-blue-ycube text-white rounded-md shadow-md"
                @click="downloadGrouping">Télécharger le grouping</button>
        </div>

        <!--  -->
        <div class="flex-auto flex flex-col overflow-visible">
            <div class="w-full px-3 py-2 h-full flex flex-col overflow-visible">
                <component
  :is="currentComponent"
  :grouping="grouping"
  :annee_auditee="annee_auditee"
/>

            </div>
        </div>
    </div>
</template>
