<script setup>
import { ref, inject, onMounted, computed } from 'vue'
import GroupingTable from './GroupingTable.vue'

const props = defineProps({
  grouping: {
    type: Array,
    default: () => []
  },
  annee_auditee: {
    type: [String, Number],
    required: true
  }
})

const axios = inject('axios')
const groupings = ref([])
const id_mission = window.location.pathname.split('/')[2]

const groupingInitialCols = computed(() => {
  const annee = parseInt(props.annee_auditee)

  return [
    {label: 'ref', key: 'ref', align: 'left', hidden: true},

    { label: 'Intitulé', key: 'libelle', align: 'left' },
    {
      label: isNaN(annee) ? 'N' : annee,
      key: 'solde_n',
      align: 'right'
    },
    {
      label: isNaN(annee) ? 'N-1' : annee - 1,
      key: 'solde_n1',
      align: 'right'
    }
  ]
})

function hasComptes(row) {
  const comptes = row?.comptes || row?.comptes_detaille
  return Array.isArray(comptes) && comptes.length > 0
}

onMounted(async () => {
  groupings.value = props.grouping.filter(hasComptes)
  console.log('📊 GroupingInitial - Données reçues:', groupings.value)
  await showSignificantGrouping()
})

async function showSignificantGrouping() {
  const result = await axios.get(`/mission/make_final/${id_mission}`)

  const grouping = result.data?.grouping || []

  console.log('📊 Grouping FINAL reçu:', grouping)

  // 👉 Afficher TOUJOURS le grouping
  groupings.value = grouping.filter(hasComptes)

  // Optionnel : log métier
  if (grouping.length && grouping[0].mat_sign) {
    console.log('✅ Grouping significatif détecté')
  }
}

</script>

<template>
  <!-- Tableau grouping principal -->
  <GroupingTable
    title="Grouping initial"
    :data="groupings"
    :columns="groupingInitialCols"
    :annee_auditee="annee_auditee"
    expandable
  />
</template>
