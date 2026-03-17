<script setup>
import { computed, onMounted } from 'vue'

const props = defineProps(['efiActif', 'annee_auditee'])

// Refs qui sont des sous-totaux/totaux (s'affichent après leurs éléments)
const GROUP_REFS = new Set([
  'AD','AI','AQ','AZ','BG','BK','BT','BZ',
])

// Ordre officiel SYSCOHADA du bilan actif (page 1049)
const ACTIF_ORDER = [
  'AD','AE','AF','AG','AH',          
  'AI','AJ','AK','AL','AM','AN',
  'AP', 
  'AQ','AR','AS',                     
  'AZ',                               
  'BA','BB','BG','BH','BI','BJ','BK',                     
  'BQ','BR','BS','BT',              
  'BZ','BU',                                                    
]

function buildOrderedRows(rows) {
  const byRef = {}
  for (const row of rows) { if (row?.ref) byRef[row.ref] = row }

  const result = []
  const seen = new Set()

  for (const ref of ACTIF_ORDER) {
    const row = byRef[ref]
    if (row && !seen.has(ref)) {
      seen.add(ref)
      result.push({ ...row, _isGroup: GROUP_REFS.has(ref) })
    }
  }
  // Orphelins éventuels
  for (const row of rows) {
    if (row?.ref && !seen.has(row.ref)) {
      result.push({ ...row, _isGroup: GROUP_REFS.has(row.ref) })
    }
  }
  return result
}

const rows = computed(() => buildOrderedRows(props.efiActif || []))

function formatAmount(value) {
  if (value === null || value === undefined || value === '') return ''
  const n = Number(typeof value === 'string' ? value.replace(/\s+/g,'').replace(/,/g,'.') : value)
  if (Number.isNaN(n)) return value
  return n.toLocaleString('fr-FR', { maximumFractionDigits: 0 })
}
function getVariation(row)        { return (row.net_solde_n||0) - (row.net_solde_n1||0) }
function getVariationPercent(row) { if (!row.net_solde_n1) return 0; return (getVariation(row)/Math.abs(row.net_solde_n1))*100 }

onMounted(() => console.log('📊 ActifComponent - efiActif:', props.efiActif))
</script>

<template>
  <h3 class="pt-5 pb-1 pl-0 text-xl font-semibold uppercase tracking-wider">Bilan Actif</h3>
  <div class="rounded-xl shadow-xl bg-white border border-gray-100 overflow-auto">
    <table class="min-w-full divide-y divide-gray-200">

      <thead class="bg-gradient-to-r from-blue-ycube to-blue-ycube-3">
        <tr>
          <th colspan="4"></th>
          <th colspan="2" class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">EXERCICE DU</th>
          <th colspan="5"></th>
        </tr>
        <tr>
          <th colspan="4"></th>
          <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">31/12/{{ props.annee_auditee }}</th>
          <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">31/12/{{ parseInt(props.annee_auditee) - 1 }}</th>
          <th colspan="5"></th>
        </tr>
        <tr>
          <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">REF</th>
          <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Intitulé</th>
          <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">BRUT</th>
          <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">AMORT et DEPREC</th>
          <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">NET</th>
          <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">NET N-1</th>
          <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Variation</th>
          <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Variation %</th>
        </tr>
      </thead>

      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-if="!rows.length">
          <td colspan="11" class="px-6 py-8 text-center text-gray-400 text-sm">Aucune donnée disponible</td>
        </tr>

        <tr
          v-for="(data, index) in rows"
          :key="`actif-${index}-${data.ref}`"
          :class="[
            data._isGroup
              ? 'bg-gradient-to-r from-blue-100 to-indigo-100 border-t-2 border-blue-400 font-semibold'
              : 'hover:bg-blue-50 transition-colors duration-150',
          ]"
        >
          <td class="px-6 py-3 whitespace-nowrap font-mono text-sm font-bold"
              :class="data._isGroup ? 'text-blue-900' : 'text-gray-700'">
            {{ data.ref }}
          </td>
          <td class="px-6 py-3 text-sm"
              :class="data._isGroup ? 'text-blue-900 font-semibold' : 'text-gray-800'">
            {{ data.libelle }}
          </td>
          <td class="px-6 py-3 text-right font-mono text-sm"
              :class="data._isGroup ? 'text-blue-900 font-semibold' : 'text-gray-700'">
            {{ formatAmount(data.brut_solde_n) }}
          </td>
          <td class="px-6 py-3 text-right font-mono text-sm"
              :class="data._isGroup ? 'text-blue-900 font-semibold' : 'text-gray-700'">
            {{ formatAmount(data.amor_solde_n) }}
          </td>
          <td class="px-6 py-3 text-right font-mono text-sm font-semibold"
              :class="data._isGroup ? 'text-blue-900' : 'text-gray-900'">
            {{ formatAmount(data.net_solde_n) }}
          </td>
          <td class="px-6 py-3 text-right font-mono text-sm"
              :class="data._isGroup ? 'text-blue-700' : 'text-gray-600'">
            {{ formatAmount(data.net_solde_n1) }}
          </td>
          <td class="px-6 py-3 text-right font-mono text-sm font-semibold"
              :class="getVariation(data) >= 0 ? 'text-emerald-600' : 'text-red-500'">
            {{ formatAmount(getVariation(data)) }}
          </td>
          <td class="px-6 py-3 text-right font-mono text-sm"
              :class="getVariationPercent(data) >= 0 ? 'text-emerald-600' : 'text-red-500'">
            {{ getVariationPercent(data).toFixed(2) }} %
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>