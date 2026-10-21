<script setup>
// Journal d'audit (page B) : LECTURE SEULE de l'historique déjà enregistré
// (imports, retraits, remplacements de balance, rapprochements, circuit de
// revue, remarques, décisions sur les sous-totaux) — assemblé côté serveur par
// api/src/services/journal_audit_service.py. Aucune modification ni
// suppression possible depuis cet écran.
import { onMounted, reactive, ref, watch } from 'vue'
import { lireJournal, exporterJournal } from '@/api/journal.api'
import { useNotyf } from '@/composables/useNotyf'

const props = defineProps({ missionId: String })
const notyf = useNotyf()

const filtres = reactive({ module: '', utilisateur: '', du: '', au: '' })
const journal = ref(null)
const chargement = ref(false)
const erreur = ref('')
const exportEnCours = ref(false)

async function charger(page = 1) {
  chargement.value = true
  erreur.value = ''
  try {
    journal.value = await lireJournal(props.missionId, filtres, page)
  } catch (e) {
    erreur.value = e.message
  } finally {
    chargement.value = false
  }
}

async function exporter() {
  exportEnCours.value = true
  try {
    await exporterJournal(props.missionId, filtres)
  } catch (e) {
    notyf.trigger(e.message, 'error')
  } finally {
    exportEnCours.value = false
  }
}

// Les filtres s'appliquent dès qu'ils changent (pas de bouton « Appliquer » sur la maquette).
watch(filtres, () => charger(1))
onMounted(() => charger(1))

function formaterDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

const CHAMP = 'h-11 text-[15px] px-2.5 border border-gray-300 rounded-[10px] bg-white text-gray-800 font-normal focus:outline-none focus:ring-2 focus:ring-blue-ycube'
</script>

<template>
  <!-- Disposition de la maquette docs/maquettes/6_Journal_audit.html ; couleurs et police de la charte
       (CLAUDE.md, section charte d'interface). -->
  <div class="h-full w-full overflow-y-auto bg-[#f5f7fa] text-gray-800">
    <div class="p-7 flex flex-col gap-5">

      <!-- En-tête -->
      <section class="bg-white rounded-[14px] shadow px-7 py-6 flex flex-col gap-1.5 text-center">
        <h1 class="m-0 text-[26px] font-bold text-blue-ycube">Journal d'audit</h1>
        <p class="m-0 text-gray-500">Toutes les actions de la mission, horodatées. Aucune entrée ne peut être modifiée ni supprimée.</p>
      </section>

      <!-- Filtres et export -->
      <section class="bg-white rounded-[14px] shadow px-6 py-5 flex gap-3 flex-wrap items-end">
        <label class="flex flex-col gap-1.5 text-sm font-semibold flex-[1_1_180px]">Module
          <select v-model="filtres.module" :class="CHAMP">
            <option value="">Tous</option>
            <option v-for="m in journal?.modules || []" :key="m" :value="m">{{ m }}</option>
          </select>
        </label>
        <label class="flex flex-col gap-1.5 text-sm font-semibold flex-[1_1_180px]">Utilisateur
          <select v-model="filtres.utilisateur" :class="CHAMP">
            <option value="">Tous</option>
            <option v-for="u in journal?.utilisateurs || []" :key="u.valeur" :value="u.valeur">{{ u.libelle }}</option>
          </select>
        </label>
        <label class="flex flex-col gap-1.5 text-sm font-semibold flex-[1_1_160px]">Du
          <input v-model="filtres.du" type="date" :max="filtres.au || undefined" :class="CHAMP" />
        </label>
        <label class="flex flex-col gap-1.5 text-sm font-semibold flex-[1_1_160px]">Au
          <input v-model="filtres.au" type="date" :min="filtres.du || undefined" :class="CHAMP" />
        </label>
        <button
          type="button"
          class="h-11 px-5 rounded-[10px] border border-blue-ycube bg-white text-blue-ycube text-[13px] font-bold hover:bg-blue-ycube hover:text-white transition disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="exportEnCours || !journal?.nb_entrees"
          @click="exporter"
        >
          {{ exportEnCours ? 'Export…' : 'Exporter (Excel)' }}
        </button>
      </section>

      <!-- Entrées -->
      <section class="bg-white rounded-[14px] shadow px-7 py-6 flex flex-col gap-3.5">
        <p v-if="erreur" class="m-0 px-4 py-3 rounded-[10px] bg-red-100 text-red-700 text-sm">{{ erreur }}</p>

        <div class="overflow-x-auto">
          <table class="min-w-full text-[15px] border-collapse">
            <thead class="bg-blue-ycube text-white text-left">
              <tr>
                <th class="px-4 py-3.5">Date</th>
                <th class="px-4 py-3.5">Utilisateur</th>
                <th class="px-4 py-3.5">Module</th>
                <th class="px-4 py-3.5">Action</th>
                <th class="px-4 py-3.5">Détail</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(e, i) in journal?.entrees || []"
                :key="i"
                class="border-b border-gray-200 last:border-b-0 hover:bg-gray-50 align-top"
              >
                <td class="px-4 py-3 whitespace-nowrap">{{ formaterDate(e.horodatage) }}</td>
                <td class="px-4 py-3 whitespace-nowrap" :class="e.utilisateur ? '' : 'text-orange-700 font-semibold'">
                  {{ e.utilisateur || 'Non identifié' }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap">{{ e.module }}</td>
                <td class="px-4 py-3">{{ e.action }}</td>
                <td class="px-4 py-3 text-gray-700 break-words">{{ e.detail || '—' }}</td>
              </tr>
              <tr v-if="journal && !journal.entrees.length">
                <td colspan="5" class="px-4 py-6 text-center text-gray-500">
                  {{ filtres.module || filtres.utilisateur || filtres.du || filtres.au
                    ? 'Aucune entrée pour ces filtres.'
                    : 'Aucune action enregistrée pour cette mission.' }}
                </td>
              </tr>
              <tr v-if="!journal && chargement">
                <td colspan="5" class="px-4 py-6 text-center text-gray-500">Chargement…</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="journal" class="flex justify-between items-center gap-3 flex-wrap text-sm text-gray-500">
          <span>Page {{ journal.page }} sur {{ journal.nb_pages }}</span>
          <div class="flex gap-2">
            <button
              type="button"
              class="h-11 px-4 rounded-[10px] border border-gray-300 bg-white text-[13px] font-semibold text-gray-800 hover:bg-gray-100 transition disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="chargement || journal.page <= 1"
              @click="charger(journal.page - 1)"
            >
              Précédent
            </button>
            <button
              type="button"
              class="h-11 px-4 rounded-[10px] border border-gray-300 bg-white text-[13px] font-semibold text-gray-800 hover:bg-gray-100 transition disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="chargement || journal.page >= journal.nb_pages"
              @click="charger(journal.page + 1)"
            >
              Suivant
            </button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
