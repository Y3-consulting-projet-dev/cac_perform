<script setup>
import { onMounted } from 'vue';

const props = defineProps(['efiPnl', 'annee_auditee'])

const isSignificant = true

function formatAmount(value) {
  if (value === null || value === undefined || value === '') return ''
  const normalized = typeof value === 'string' ? value.replace(/\s+/g, '').replace(/,/g, '.') : value
  const num = Number(normalized)
  if (Number.isNaN(num)) return value
  const opts = Number.isInteger(num)
    ? { maximumFractionDigits: 0 }
    : { minimumFractionDigits: 2, maximumFractionDigits: 2 }
  return num.toLocaleString('fr-FR', opts)
}

function getVariation(row) {
  return (row.net_solde_n || 0) - (row.net_solde_n1 || 0)
}

function getVariationPercent(row) {
  if (!row.net_solde_n1) return 0
  return (getVariation(row) / Math.abs(row.net_solde_n1)) * 100
}

function isMaterial(row) {
  return Math.abs(getVariationPercent(row)) >= 10
}

function isQualitative(row) {
  return Math.abs(getVariationPercent(row)) >= 20
}

function isMatSign(row) {
  return isMaterial(row) && isQualitative(row)
}

function isTotalRef(ref) {
  return typeof ref === 'string' && ref.endsWith('Z')
}

onMounted(() => {
  console.log('📊 PnlComponent - Données reçues:');
  console.log('  - efiPnl:', props.efiPnl);
  console.log('  - annee_auditee:', props.annee_auditee);
  console.log('  - Longueur:', props.efiPnl?.length);
})
</script>

<template>
    <!-- Tableau grouping principal -->
    <h3 class="pt-5 pb-1 pl-0 text-xl font-semibold uppercase tracking-wider">Compte de résultat</h3>
    <div class="rounded-xl shadow-xl bg-white border border-gray-100 overflow-x-auto overflow-y-visible">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gradient-to-r from-blue-ycube to-blue-ycube-3">
              <tr>
                <th colspan="4"></th>
                <th colspan="2" class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">
                  EXERCICE DU
                </th>
                <th colspan="5"></th>
              </tr>
              <tr>
                <th colspan="4"></th>
                <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">
                  31/12/{{ props.annee_auditee }}
                </th>
                <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">
                  31/12/{{ parseInt(props.annee_auditee) - 1 }}
                </th>
                <th colspan="5"></th>
              </tr>
              <tr>
                <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">REF</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Intitulé</th>
                <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">BRUT</th>
                <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">AMORT et DEPREC</th>
                <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">NET</th>
                <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">NET</th>
                <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Variation</th>
                <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Variation %</th>
                <th v-if="isSignificant" class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Quantitatif</th>
                <th v-if="isSignificant" class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Qualitatif</th>
                <th v-if="isSignificant" class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Significativité</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                <tr v-if="!props.efiPnl || props.efiPnl.length === 0">
                  <td colspan="11" class="px-6 py-4 text-center text-gray-500">
                    <div class="text-sm">Aucune donnée disponible</div>
                    <div class="text-xs mt-1">efiPnl: {{ props.efiPnl ? 'défini' : 'non défini' }} | Longueur: {{ props.efiPnl?.length || 0 }}</div>
                  </td>
                </tr>
                <tr v-for="data,index in props.efiPnl" :key="`pnl-${index}-${data.ref}`" 
                    :class="[
                      isTotalRef(data.ref)
                        ? 'bg-gradient-to-r from-blue-100 to-indigo-100 border-t-2 border-blue-500 font-bold'
                        : 'hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50',
                      'transition-all duration-300 group transform hover:scale-[1.01] hover:shadow-md'
                    ]">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div :class="[
                          'text-sm font-mono',
                          isTotalRef(data.ref) ? 'font-extrabold text-blue-900' : 'font-bold text-gray-900 group-hover:text-blue-700'
                        ]">{{ data.ref }}</div>
                    </td>
                    <td class="px-6 py-4">
                        <div :class="[
                          'text-sm max-w-xs truncate',
                          isTotalRef(data.ref) ? 'font-bold text-blue-900' : 'text-gray-900 group-hover:text-blue-700'
                        ]" :title="data.libelle">{{ data.libelle }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div class="text-sm font-mono font-semibold text-gray-900 group-hover:text-blue-700">
                        {{ formatAmount(data.brut_solde_n) }}
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div class="text-sm font-mono font-semibold text-gray-900 group-hover:text-blue-700">
                        {{ formatAmount(data.amor_solde_n) }}
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div class="text-sm font-mono font-semibold text-gray-900 group-hover:text-blue-700">
                        {{ formatAmount(data.net_solde_n) }}
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div class="text-sm font-mono text-gray-900 group-hover:text-blue-700">
                        {{ formatAmount(data.net_solde_n1) }}
                      </div>
                    </td>
                    <td class="px-6 py-4 text-right font-mono font-semibold"
                      :class="getVariation(data) >= 0 ? 'text-emerald-600' : 'text-red-600'">
                      {{ formatAmount(getVariation(data)) }}
                    </td>
                    <td class="px-6 py-4 text-right font-mono"
                      :class="getVariationPercent(data) >= 0 ? 'text-emerald-600' : 'text-red-600'">
                      {{ getVariationPercent(data).toFixed(2) }} %
                    </td>
                    <td v-if="isSignificant" class="px-6 py-4 text-center">
                      {{ isMaterial(data) ? 'Oui' : 'Non' }}
                    </td>
                    <td v-if="isSignificant" class="px-6 py-4 text-center">
                      {{ isQualitative(data) ? 'Oui' : 'Non' }}
                    </td>
                    <td v-if="isSignificant" class="px-6 py-4 text-center font-semibold"
                      :class="isMatSign(data) ? 'text-red-600' : 'text-emerald-600'">
                      {{ isMatSign(data) ? 'Significatif' : 'Non significatif' }}
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>
