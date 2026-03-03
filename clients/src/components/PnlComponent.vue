<script setup>
import { computed, onMounted } from 'vue'

const props = defineProps(['efiPnl', 'annee_auditee'])
const isSignificant = true

const GROUP_REFS = new Set([
  'XA','XB','XC','XD','XE','XF','XG','XH','XI',
])

// Ordre officiel SYSCOHADA Compte de Résultat (page 1050)
const SYSCOHADA_ORDER_PNL = [
  'TA','RA','RB',
  'XA',
  'TB','TC','TD',
  'XB',
  'TE','TF','TG','TH','TI',
  'RC','RD','RE','RF','RG','RH','RI','RJ',
  'XC',
  'RK',
  'XD',
  'TJ','RL',
  'XE',
  'TK','TL','TM','RM','RN',
  'XF',
  'XG',
  'TN','TO','RO','RP',
  'XH',
  'RQ','RS',
  'XI',
]

const rows = computed(() => {
  const byRef = {}
  for (const row of (props.efiPnl || [])) {
    if (row?.ref) byRef[row.ref] = row
  }
  const result = []
  for (const ref of SYSCOHADA_ORDER_PNL) {
    if (byRef[ref]) result.push({ ...byRef[ref], _isGroup: GROUP_REFS.has(ref) })
  }
  for (const row of (props.efiPnl || [])) {
    if (row?.ref && !SYSCOHADA_ORDER_PNL.includes(row.ref))
      result.push({ ...row, _isGroup: GROUP_REFS.has(row.ref) })
  }
  return result
})

function formatAmount(value) {
  if (value === null || value === undefined || value === '') return ''
  const n = Number(typeof value === 'string' ? value.replace(/\s+/g,'').replace(/,/g,'.') : value)
  if (Number.isNaN(n)) return value
  return n.toLocaleString('fr-FR', { maximumFractionDigits: 0 })
}
function getVariation(row)        { return (row.net_solde_n||0) - (row.net_solde_n1||0) }
function getVariationPercent(row) { if (!row.net_solde_n1) return 0; return (getVariation(row)/Math.abs(row.net_solde_n1))*100 }
function isMaterial(row)          { return Math.abs(getVariationPercent(row)) >= 10 }
function isQualitative(row)       { return Math.abs(getVariationPercent(row)) >= 20 }
function isMatSign(row)           { return isMaterial(row) && isQualitative(row) }

onMounted(() => {
  console.log('📊 PnlComponent - efiPnl:', props.efiPnl)
  console.log('  - Longueur:', props.efiPnl?.length)
})
</script>

<template>
  <h3 class="pt-5 pb-1 pl-0 text-xl font-semibold uppercase tracking-wider">Compte de résultat</h3>
  <div class="rounded-xl shadow-xl bg-white border border-gray-100 overflow-x-auto overflow-y-visible">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gradient-to-r from-blue-ycube to-blue-ycube-3">
        <tr>
          <th colspan="2"></th>
          <th colspan="2" class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">EXERCICE DU</th>
          <th colspan="5"></th>
        </tr>
        <tr>
          <th colspan="2"></th>
          <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">31/12/{{ props.annee_auditee }}</th>
          <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">31/12/{{ parseInt(props.annee_auditee) - 1 }}</th>
          <th colspan="5"></th>
        </tr>
        <tr>
          <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">REF</th>
          <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Intitulé</th>
          <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">NET</th>
          <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">NET N-1</th>
          <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Variation</th>
          <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Variation %</th>
          <th v-if="isSignificant" class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Quantitatif</th>
          <th v-if="isSignificant" class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Qualitatif</th>
          <th v-if="isSignificant" class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Significativité</th>
        </tr>
      </thead>

      <tbody class="bg-white divide-y divide-gray-100">
        <tr v-if="!rows.length">
          <td colspan="11" class="px-6 py-8 text-center text-gray-400 text-sm">
            Aucune donnée disponible | efiPnl: {{ props.efiPnl ? 'défini' : 'non défini' }} | Longueur: {{ props.efiPnl?.length || 0 }}
          </td>
        </tr>

        <tr
          v-for="(data, index) in rows"
          :key="`pnl-${index}-${data.ref}`"
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
              :class="data._isGroup ? 'text-blue-900 font-bold uppercase' : 'text-gray-800 pl-10'">
            {{ data.libelle }}
          </td>
          <td class="px-6 py-3 text-right font-mono text-sm font-semibold"
              :class="data._isGroup ? 'text-blue-900' : 'text-gray-900'">
            {{ formatAmount(data.net_solde_n) }}
          </td>
          <td class="px-6 py-3 text-right font-mono text-sm"
              :class="data._isGroup ? 'text-blue-900' : 'text-gray-600'">
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
          <td v-if="isSignificant" class="px-6 py-3 text-center text-sm">
            <span v-if="!data._isGroup" :class="isMaterial(data) ? 'text-amber-600 font-semibold' : 'text-gray-400'">
              {{ isMaterial(data) ? 'Oui' : 'Non' }}
            </span>
          </td>
          <td v-if="isSignificant" class="px-6 py-3 text-center text-sm">
            <span v-if="!data._isGroup" :class="isQualitative(data) ? 'text-amber-600 font-semibold' : 'text-gray-400'">
              {{ isQualitative(data) ? 'Oui' : 'Non' }}
            </span>
          </td>
          <td v-if="isSignificant" class="px-6 py-3 text-center text-sm font-semibold">
            <span v-if="!data._isGroup" :class="isMatSign(data) ? 'text-red-600' : 'text-emerald-600'">
              {{ isMatSign(data) ? 'Significatif' : 'Non significatif' }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>