<script setup>
import { computed } from 'vue'
import GroupingTable from './GroupingTable.vue'
import groupingData from '@/data/grouping.json'

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

// 🔹 Extraire les libellés des grands_groupes ayant nature === 'Passif'
const groupesPassifsLibelles = computed(() => {
  const libelles = new Set()
  groupingData.syscohada.grands_groupes.forEach(g => {
    if (g.nature && g.nature.toLowerCase() === 'passif') {
      libelles.add(g.libelle)
    }
  })
  return libelles
})

// 🔹 PASSIF : filtrer par nature depuis grouping.json
const groupings = computed(() =>
  props.grouping.filter(g =>
    groupesPassifsLibelles.value.has(g.libelle)
  ).filter(g => (g.comptes?.length || g.comptes_detaille?.length))
)

const cols = computed(() => [
  { label: 'ref', key: 'ref', align: 'left', hidden: true },
  { label: 'Intitulé', key: 'libelle', align: 'left' },
  { label: props.annee_auditee, key: 'solde_n', align: 'right' },
  { label: parseInt(props.annee_auditee) - 1, key: 'solde_n1', align: 'right' }
])
</script>

<template>
  <GroupingTable title="Grouping Passif" :data="groupings" :columns="cols" :annee_auditee="annee_auditee" expandable />
</template>
