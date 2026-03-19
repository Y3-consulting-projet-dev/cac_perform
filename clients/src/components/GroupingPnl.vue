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
  },
  selectionEnabled: { type: Boolean, default: false },
  selectedIds: { type: Array, default: () => [] }
})


/* 🔹 PnL : classes 6 et 7 */
const groupings = computed(() =>
  props.grouping.filter(g => g.section === 'pnl')
)


const cols = computed(() => [
  { label: 'Intitulé', key: 'libelle', align: 'left' },
  { label: props.annee_auditee, key: 'solde_n', align: 'right' },
  { label: parseInt(props.annee_auditee) - 1, key: 'solde_n1', align: 'right' }
])
</script>

<template>
  <GroupingTable
    title="Grouping Pnl"
    :data="groupings"
    :columns="cols"
    :annee_auditee="annee_auditee"
    :selectable="selectionEnabled"
    :selected-ids="selectedIds"
    @update:selected-ids="emit('update:selectedIds', $event)"
    expandable
  />
</template>
