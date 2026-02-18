<script setup>
import { computed } from 'vue'
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


/* 🔹 ACTIF : classes 2,3,4,5 */
const groupings = computed(() =>
  props.grouping.filter(g =>
    ['2', '3', '4', '5'].includes(g.compte?.toString().charAt(0))
  ).filter(g => (g.comptes?.length || g.comptes_detaille?.length))
)


const cols = computed(() => [
  { label: '#', key: 'compte', align: 'left' },
  { label: 'Intitulé', key: 'libelle', align: 'left' },
  { label: props.annee_auditee, key: 'solde_n', align: 'right' },
  { label: parseInt(props.annee_auditee) - 1, key: 'solde_n1', align: 'right' }
])
</script>

<template>
  <GroupingTable
    title="Grouping Actif"
    :data="groupings"
    :columns="cols"
    :annee_auditee="annee_auditee"
    expandable
  />
</template>
