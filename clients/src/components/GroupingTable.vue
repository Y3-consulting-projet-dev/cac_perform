<script setup>
import { ref } from 'vue'

const props = defineProps({
  title: String,
  data: Array,
  columns: Array,
  annee_auditee: {
    type: [String, Number],
    default: ''
  },
  expandable: { type: Boolean, default: false }
})

const expandedRows = ref(new Set())

function toggleRow(index) {
  expandedRows.value.has(index)
    ? expandedRows.value.delete(index)
    : expandedRows.value.add(index)
}

function hasComptes(row) {
  // Vérifier si le groupe a des comptes détaillés (comptes ou comptes_detaille)
  return Array.isArray(row.comptes || row.comptes_detaille)
    && (row.comptes || row.comptes_detaille).length > 0
}
</script>

<template>
  <h3 class="pt-5 pb-2 text-xl font-semibold uppercase">Tableau des clients CAC</h3>

  <div class="overflow-auto rounded-xl shadow bg-white border border-gray-100">
    <table class="min-w-full divide-y divide-gray-200">

      <!-- ================= THEAD ================= -->
      <thead class="bg-gradient-to-r from-blue-ycube via-blue-ycube-1 to-blue-ycube-3">
        <tr>
          <!-- Colonne expand -->
          <th v-if="expandable" class="px-4 py-4 w-12"></th>

          <!-- Colonnes dynamiques -->
          <th
            v-for="col in columns"
            :key="col.key"
            class="px-6 py-4 text-xs font-semibold text-white uppercase tracking-wider"
            :class="col.align === 'right' ? 'text-right' : 'text-left'"
          >
            {{ col.label }}
          </th>
        </tr>
      </thead>

      <!-- ================= TBODY ================= -->
      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-if="!data || data.length === 0">
          <td colspan="100%" class="px-6 py-4 text-center text-gray-500">
            <div class="text-sm">Aucune donnée disponible</div>
            <div class="text-xs mt-1">grouping: {{ data ? 'défini' : 'non défini' }} | Longueur: {{ data?.length || 0 }}</div>
          </td>
        </tr>

        <template v-else v-for="(row, index) in data" :key="index">

          <!-- Ligne principale -->
          <tr
            class="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-300 group"
          >
            <!-- Bouton expand -->
            <td v-if="expandable" class="px-4 py-4 text-center">
              <button
                v-if="hasComptes(row)"
                @click="toggleRow(index)"
                class="p-1 rounded-md hover:bg-blue-100 transition-colors duration-200"
                :title="expandedRows.has(index) ? 'Réduire' : 'Voir le détail'"
              >
                <svg
                  class="w-5 h-5 text-blue-600 transition-transform duration-200"
                  :class="{ 'rotate-90': expandedRows.has(index) }"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M9 5l7 7-7 7" />
                </svg>
              </button>
              <span v-else class="w-5 h-5 inline-block"></span>
            </td>

            <!-- TD dynamiques -->
            <td
              v-for="col in columns"
              :key="col.key"
              class="px-6 py-4 text-sm"
              :class="col.align === 'right'
                ? 'text-right font-mono'
                : 'text-left'"
            >
              {{ row[col.key]?.toLocaleString?.() ?? row[col.key] }}
            </td>
          </tr>

          <!-- ================= LIGNE EXPANDABLE ================= -->
          <tr v-if="expandable && expandedRows.has(index) && hasComptes(row)">
            <td colspan="100%" class="px-6 py-4 bg-gray-50">
              <div class="border-l-4 border-blue-500 pl-4">
                <h4 class="text-sm font-semibold text-gray-900 mb-2">
                  Détail des comptes du groupe {{ row.compte }}
                </h4>

                <!-- Sous-table -->
                <div class="overflow-hidden rounded-lg border border-gray-200 bg-white">
                  <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                      <tr>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Compte
                        </th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Libellé
                        </th>
                        <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          {{ annee_auditee }}
                        </th>
                        <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          {{ parseInt(annee_auditee) - 1 }}
                        </th>
                      </tr>
                    </thead>

                    <tbody class="divide-y divide-gray-200">
                      <tr
                        v-for="(compte, cIndex) in (row.comptes || row.comptes_detaille)"
                        :key="cIndex"
                        class="hover:bg-gray-50 transition"
                      >
                        <td class="px-4 py-3 text-sm font-mono">
                          {{ compte.numero_compte }}
                        </td>
                        <td class="px-4 py-3 text-sm">
                          {{ compte.libelle }}
                        </td>
                        <td class="px-4 py-3 text-sm font-mono text-right">
                          {{ (compte.solde_n || 0).toLocaleString() }}
                        </td>
                        <td class="px-4 py-3 text-sm font-mono text-right">
                          {{ (compte.solde_n1 || 0).toLocaleString() }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </td>
          </tr>

        </template>
      </tbody>
    </table>
  </div>
</template>
