<script setup>
// Sélection des tiers à circulariser — sous-lot a (docs/PLAN_circularisation.md) :
// population depuis les balances auxiliaires actives, sélection MANUELLE avec
// motif, mode de confirmation, accès au mémo. La sélection par seuils et
// l'échantillonnage MUS (sous-lot d) attendent CAC-SEUILS-01 et ECH-01.
// Le serveur reste juge de toutes les règles (circularisation_service).
import { computed, onMounted, ref } from 'vue'
import {
  lireCircularisation, constituerPopulation, deciderTiers, definirMode,
} from '@/api/circularisation.api'
import { useNotyf } from '@/composables/useNotyf'
import { formatDateHeureFr } from '@/utils/formatDate'
import MemoSelectionView from '@/views/MemoSelectionView.vue'

const props = defineProps({ missionId: String })
const emit = defineEmits(['ouvrir-ecran'])
const notyf = useNotyf()

const etat = ref(null)
const erreur = ref('')
const typeActif = ref('fournisseurs')
const filtre = ref('tous')
const enCours = ref(false)
const memoOuvert = ref(false)
// Fenêtre de motif : { titre, action(motif) } — retenir/exclure un tiers, confirmation négative.
const fenetreMotif = ref(null)
const motif = ref('')

// Même convention que FiabiliteIpeView : aucune authentification, l'utilisateur
// est celui enregistré par l'écran de connexion.
function utilisateurConnecte() {
  try {
    const utilisateur = JSON.parse(sessionStorage.getItem('user') || 'null')
    if (!utilisateur) return null
    const nom = `${utilisateur.firstname || ''} ${utilisateur.lastname || ''}`.trim()
    return nom || utilisateur._id || null
  } catch {
    return null
  }
}

async function charger() {
  try {
    etat.value = await lireCircularisation(props.missionId)
    erreur.value = ''
  } catch (e) {
    erreur.value = e.message
  }
}

const type = computed(() => etat.value?.types.find((t) => t.cle === typeActif.value) || null)
const selection = computed(() => type.value?.selection || null)
const modifiable = computed(() => ['en_cours', 'en_attente_correction'].includes(selection.value?.statut))
const longueurMin = computed(() => etat.value?.longueur_min_motif || 15)

const tiersAffiches = computed(() => {
  const tiers = selection.value?.tiers || []
  if (filtre.value === 'retenus') return tiers.filter((t) => t.retenu)
  if (filtre.value === 'non_retenus') return tiers.filter((t) => !t.retenu)
  return tiers
})

function remplacerType(nouveau) {
  const i = etat.value.types.findIndex((t) => t.cle === nouveau.cle)
  if (i >= 0) etat.value.types[i] = nouveau
}

async function executer(action, succes) {
  enCours.value = true
  try {
    remplacerType(await action())
    if (succes) notyf.trigger(succes, 'success')
    return true
  } catch (e) {
    notyf.trigger(e.message, 'error')
    return false
  } finally {
    enCours.value = false
  }
}

function constituer() {
  return executer(() => constituerPopulation(props.missionId, typeActif.value, utilisateurConnecte()), 'Population constituée')
}

function ouvrirMotif(titre, action) {
  motif.value = ''
  fenetreMotif.value = { titre, action }
}

async function confirmerMotif() {
  const ok = await executer(() => fenetreMotif.value.action(motif.value.trim()))
  if (ok) fenetreMotif.value = null
}

function basculerTiers(tiers) {
  const retenir = !tiers.retenu
  ouvrirMotif(`${retenir ? 'Retenir' : 'Exclure'} le tiers ${tiers.numero} · ${tiers.libelle}`,
    (m) => deciderTiers(props.missionId, typeActif.value, tiers.numero, retenir, m, utilisateurConnecte()))
}

function changerMode(mode) {
  if (mode === selection.value?.mode?.valeur) return
  if (mode === 'negatif') {
    ouvrirMotif('Confirmation négative · motif de la décision',
      (m) => definirMode(props.missionId, typeActif.value, 'negatif', m, utilisateurConnecte()))
  } else {
    executer(() => definirMode(props.missionId, typeActif.value, 'positif', null, utilisateurConnecte()), 'Mode positif rétabli')
  }
}

function formatMontant(valeur) {
  if (valeur === null || valeur === undefined) return '—'
  const entier = Math.round(valeur)
  const formate = new Intl.NumberFormat('fr-FR').format(Math.abs(entier))
  return entier === 0 ? formate : `${formate} ${entier < 0 ? 'C' : 'D'}`
}
const formatEntier = (v) => (v === null || v === undefined ? '—' : new Intl.NumberFormat('fr-FR').format(Math.round(v)))
const formatTaux = (v) => (v === null || v === undefined ? '—' : `${v.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} %`)

// Prérequis IPE (maquette : « Rapprochement en cours, non validé… »).
const prerequisIpe = computed(() => {
  const statut = etat.value?.ipe?.statut_affiche
  if (statut === 'valide') return { texte: 'Fiabilité IPE validée : la population peut être utilisée.' }
  if (statut === 'anterieure_au_verrou') return { texte: 'Mission antérieure au verrou IPE : le rapprochement reste informatif.' }
  const libelles = { non_commence: 'non commencé', en_cours: 'en cours', soumis_pour_revue: 'soumis pour revue', en_attente_correction: 'en attente de correction' }
  return {
    texte: `Rapprochement ${libelles[statut] || 'non commencé'}, non validé. La population ne doit être utilisée qu'après validation de la fiabilité.`,
  }
})

const STATUTS_SELECTION = {
  en_cours: { libelle: 'En cours', classe: 'bg-orange-100 text-orange-700' },
  soumis_pour_revue: { libelle: 'Mémo soumis pour revue', classe: 'bg-orange-100 text-orange-700' },
  en_attente_correction: { libelle: 'Correction demandée', classe: 'bg-orange-100 text-orange-700' },
  valide: { libelle: 'Mémo validé', classe: 'bg-green-100 text-green-700' },
}

function etiquetteOnglet(t) {
  if (t.indisponible) return `${t.libelle} · ${t.etiquette}`
  const nb = t.selection?.indicateurs?.nb_tiers ?? t.fichier_actif?.nb_lignes
  return nb === undefined || nb === null ? `${t.libelle} · aucun fichier` : `${t.libelle} · ${nb}`
}

onMounted(charger)

const CARTE = 'bg-white rounded-[14px] shadow'
const FIELDSET = 'm-0 border border-gray-200 rounded-xl px-4 py-3.5 flex flex-col gap-2.5'
const RADIO = 'flex gap-2.5 items-start text-[15px]'
</script>

<template>
  <MemoSelectionView
    v-if="memoOuvert"
    :mission-id="missionId"
    :type="typeActif"
    @retour="memoOuvert = false; charger()"
    @ouvrir-ecran="(e) => emit('ouvrir-ecran', e)"
  />

  <!-- Disposition de la maquette docs/maquettes/2_Selection_tiers.html ; couleurs et police de la charte. -->
  <div v-else class="h-full w-full overflow-y-auto bg-[#f5f7fa] text-gray-800">
    <div class="p-7 flex flex-col gap-5">

      <!-- En-tête -->
      <section :class="[CARTE, 'px-7 py-6 flex flex-col gap-1.5 text-center']">
        <h1 class="m-0 text-[26px] font-bold text-blue-ycube">Sélection des tiers à circulariser</h1>
        <p class="m-0 text-gray-500">
          <template v-if="etat?.mission?.entite">{{ etat.mission.entite }} · </template>
          <template v-if="etat?.mission?.exercice">exercice {{ etat.mission.exercice }} · </template>
          CIR-01, à partir des seuils de SEUILS-01 et de l'échantillonnage ECH-01
        </p>
      </section>

      <p v-if="erreur" class="m-0 px-4 py-3 rounded-[10px] bg-red-100 text-red-700 text-sm">{{ erreur }}</p>

      <template v-if="etat">
        <!-- Prérequis IPE et seuils de l'étape 5 -->
        <section class="grid grid-cols-1 xl:grid-cols-2 gap-5">
          <div :class="[CARTE, 'px-6 py-5 flex flex-col gap-2']">
            <h2 class="m-0 text-[15px] font-bold tracking-[0.3px] uppercase text-blue-ycube">Prérequis · Fiabilité IPE</h2>
            <p class="m-0 text-sm text-gray-800">{{ prerequisIpe.texte }}</p>
            <button type="button" class="self-start text-sm font-semibold text-blue-ycube underline" @click="emit('ouvrir-ecran', 'fiabilite_ipe')">
              Ouvrir Fiabilité IPE
            </button>
          </div>
          <div :class="[CARTE, 'px-6 py-5 flex flex-col gap-2.5']"
               :title="`${etat.seuils.disponible ? `Benchmark retenu : ${etat.seuils.benchmark}` : 'Aucun benchmark retenu à l’étape 5'} · ${etat.seuils.correspondance}`">
            <h2 class="m-0 text-[15px] font-bold tracking-[0.3px] uppercase text-blue-ycube">Seuils retenus · Étape 5</h2>
            <div class="grid grid-cols-3 gap-2.5">
              <div v-for="s in etat.seuils.valeurs" :key="s.cle" class="px-3 py-2.5 rounded-[10px] bg-gray-50">
                <div class="text-[13px] text-gray-500">{{ s.libelle }}</div>
                <div class="font-extrabold text-[17px]">{{ etat.seuils.disponible ? formatEntier(s.valeur) : 'Non calculé' }}</div>
              </div>
            </div>
          </div>
        </section>

        <!-- Population -->
        <section :class="[CARTE, 'px-7 py-6 flex flex-col gap-[18px]']">
          <h2 class="m-0 text-[17px] font-bold tracking-[0.3px] uppercase text-blue-ycube">Population</h2>
          <div role="tablist" aria-label="Types de tiers" class="flex gap-2 flex-wrap">
            <button
              v-for="t in etat.types"
              :key="t.cle"
              type="button"
              role="tab"
              :aria-selected="t.cle === typeActif"
              class="h-11 px-4 rounded-[10px] text-[15px] transition"
              :class="t.cle === typeActif ? 'bg-blue-ycube text-white font-bold' : 'border border-gray-300 bg-white font-semibold text-gray-800 hover:bg-gray-100'"
              @click="typeActif = t.cle; filtre = 'tous'"
            >
              {{ etiquetteOnglet(t) }}
            </button>
          </div>

          <p v-if="type?.indisponible" class="m-0 px-4 py-3 rounded-[10px] bg-gray-100 text-gray-700 text-sm">
            {{ type.libelle }} : {{ type.indisponible }}.
          </p>

          <template v-else-if="type">
            <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
              <fieldset :class="FIELDSET">
                <legend class="px-1 text-[15px] font-semibold">Méthode</legend>
                <label :class="[RADIO, 'text-gray-400 cursor-not-allowed']" title="Sous-lot d : en attente de CAC-SEUILS-01 et ECH-01">
                  <input type="radio" disabled class="w-[18px] h-[18px] mt-0.5" />
                  Seuils SS/SP/TS et échantillonnage MUS (ECH-01) · à venir
                </label>
                <label :class="RADIO">
                  <input type="radio" checked disabled class="w-[18px] h-[18px] mt-0.5 accent-blue-ycube" />
                  Sélection manuelle uniquement
                </label>
              </fieldset>
              <fieldset :class="FIELDSET">
                <legend class="px-1 text-[15px] font-semibold">Tirage reproductible</legend>
                <label class="flex flex-col gap-1.5 text-sm font-semibold text-gray-400">Graine du tirage
                  <input type="text" disabled value="Sélection automatique à venir"
                         class="h-11 px-3 text-[15px] font-normal border border-gray-300 rounded-[10px] bg-gray-50" />
                </label>
                <span class="text-[13px] text-gray-500">Enregistrée au journal : le tirage peut être rejoué à l'identique.</span>
              </fieldset>
              <fieldset :class="FIELDSET">
                <legend class="px-1 text-[15px] font-semibold">Mode de confirmation</legend>
                <label :class="RADIO">
                  <input type="radio" name="mode" class="w-[18px] h-[18px] mt-0.5 accent-blue-ycube"
                         :checked="(selection?.mode?.valeur || 'positif') === 'positif'"
                         :disabled="!modifiable || enCours" @change="changerMode('positif')" />
                  Positive (par défaut)
                </label>
                <label :class="RADIO">
                  <input type="radio" name="mode" class="w-[18px] h-[18px] mt-0.5 accent-blue-ycube"
                         :checked="selection?.mode?.valeur === 'negatif'"
                         :disabled="!modifiable || enCours" @change="changerMode('negatif')" />
                  <span>Négative · décision du Manager, motif obligatoire
                    <span v-if="selection?.mode?.valeur === 'negatif'" class="block text-[13px] text-gray-500">
                      « {{ selection.mode.motif }} » · {{ selection.mode.utilisateur_id }} · {{ formatDateHeureFr(selection.mode.horodatage) }}
                    </span>
                  </span>
                </label>
              </fieldset>
            </div>

            <p v-if="selection?.a_refaire" class="m-0 px-4 py-3 rounded-[10px] bg-orange-100 text-orange-700 text-sm">
              {{ selection.a_refaire }}
            </p>
            <p v-if="!type.fichier_actif" class="m-0 px-4 py-3 rounded-[10px] bg-gray-100 text-gray-700 text-sm">
              Aucune balance auxiliaire {{ type.libelle.toLowerCase() }} active : importez-la dans Fichiers complémentaires.
            </p>

            <div class="flex gap-3 flex-wrap items-center">
              <button
                type="button"
                class="h-[46px] px-[22px] rounded-[10px] bg-blue-ycube text-white text-[15px] font-bold hover:bg-blue-900 transition disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="enCours || !type.fichier_actif || selection?.statut === 'soumis_pour_revue'"
                @click="constituer"
              >
                {{ selection ? 'Lancer à nouveau la sélection' : 'Lancer la sélection' }}
              </button>
              <button
                type="button"
                disabled
                title="Tiers hors population : à confirmer par CAC-CIR-01"
                class="h-[46px] px-[22px] rounded-[10px] border border-blue-ycube bg-white text-blue-ycube text-[15px] font-bold opacity-50 cursor-not-allowed"
              >
                Ajouter un tiers manuellement
              </button>
              <span v-if="selection" class="text-[13px] text-gray-500">
                Population photographiée le {{ formatDateHeureFr(selection.cree_le) }} par {{ selection.cree_par || 'Non identifié' }}
                · {{ selection.population.source.nom_fichier }} v{{ selection.population.source.version }}
                · sélection version {{ selection.version }}
              </span>
            </div>
          </template>
        </section>

        <template v-if="selection">
          <!-- Indicateurs -->
          <section class="grid grid-cols-2 xl:grid-cols-4 gap-4">
            <div :class="[CARTE, 'px-5 py-[18px]']">
              <div class="text-[13px] text-gray-500">Tiers sélectionnés</div>
              <div class="text-2xl font-extrabold text-blue-ycube">{{ selection.indicateurs.nb_retenus }} / {{ selection.indicateurs.nb_tiers }}</div>
              <div class="text-[13px] text-gray-500">Taux de sélection {{ formatTaux(selection.indicateurs.taux_selection) }}</div>
            </div>
            <div :class="[CARTE, 'px-5 py-[18px]']">
              <div class="text-[13px] text-gray-500">Valeur de la population</div>
              <div class="text-2xl font-extrabold text-blue-ycube">{{ formatEntier(selection.indicateurs.valeur_population) }}</div>
              <div class="text-[13px] text-gray-500" title="Soldes pris en valeur absolue (convention provisoire, CAC-CIR-01 à confirmer)">Somme des soldes</div>
            </div>
            <div :class="[CARTE, 'px-5 py-[18px]']">
              <div class="text-[13px] text-gray-500">Valeur couverte</div>
              <div class="text-2xl font-extrabold text-blue-ycube">{{ formatEntier(selection.indicateurs.valeur_couverte) }}</div>
              <div class="text-[13px] text-gray-500">Taux de couverture {{ formatTaux(selection.indicateurs.taux_couverture) }}</div>
            </div>
            <div :class="[CARTE, 'px-5 py-[18px]']">
              <div class="text-[13px] text-gray-500">Solde moyen sélectionné</div>
              <div class="text-2xl font-extrabold text-blue-ycube">{{ formatEntier(selection.indicateurs.solde_moyen_retenu) }}</div>
              <div class="text-[13px] text-gray-500">Valeur couverte / sélectionnés</div>
            </div>
          </section>

          <!-- Tiers -->
          <section :class="[CARTE, 'px-7 py-6 flex flex-col gap-3.5']">
            <div class="flex justify-between items-center gap-3 flex-wrap">
              <div class="flex items-center gap-3">
                <h2 class="m-0 text-[17px] font-bold tracking-[0.3px] uppercase text-blue-ycube">Tiers · {{ type.libelle }}</h2>
                <span :class="['px-3 py-1 rounded-full text-xs font-semibold', STATUTS_SELECTION[selection.statut]?.classe]">
                  {{ STATUTS_SELECTION[selection.statut]?.libelle }}
                </span>
              </div>
              <label class="flex items-center gap-2 text-sm">Afficher
                <select v-model="filtre" class="h-10 px-2.5 text-sm border border-gray-300 rounded-[10px] bg-white">
                  <option value="tous">Tous</option>
                  <option value="retenus">Sélectionnés</option>
                  <option value="non_retenus">Non sélectionnés</option>
                </select>
              </label>
            </div>
            <div class="overflow-x-auto">
              <table class="min-w-full text-[15px] border-collapse">
                <thead class="bg-blue-ycube text-white text-left">
                  <tr>
                    <th class="px-4 py-3.5">Retenu</th>
                    <th class="px-4 py-3.5">Compte</th>
                    <th class="px-4 py-3.5">Libellé</th>
                    <th class="px-4 py-3.5 text-right">Solde final</th>
                    <th class="px-4 py-3.5">Origine</th>
                    <th class="px-4 py-3.5">Motif</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="t in tiersAffiches" :key="t.numero" class="border-b border-gray-200 last:border-b-0 hover:bg-gray-50 align-top">
                    <td class="px-4 py-3">
                      <input type="checkbox" :checked="t.retenu" :disabled="!modifiable || enCours"
                             :aria-label="`Retenir ${t.numero}`" class="w-[18px] h-[18px] accent-blue-ycube cursor-pointer disabled:cursor-not-allowed"
                             @click.prevent="basculerTiers(t)" />
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap">{{ t.numero }}</td>
                    <td class="px-4 py-3">{{ t.libelle }}</td>
                    <td class="px-4 py-3 text-right whitespace-nowrap">{{ formatMontant(t.solde) }}</td>
                    <td class="px-4 py-3 whitespace-nowrap">
                      <span v-if="t.origine === 'ajout_manuel'" class="px-2.5 py-0.5 rounded-full text-[13px] font-bold bg-orange-100 text-orange-700">Ajout manuel</span>
                      <span v-else-if="t.origine === 'exclusion_manuelle'" class="px-2.5 py-0.5 rounded-full text-[13px] font-bold bg-gray-100 text-gray-700">Exclusion manuelle</span>
                      <span v-else class="text-gray-500">Non retenu</span>
                    </td>
                    <td class="px-4 py-3" :class="t.motif ? 'text-gray-800' : 'text-gray-500'"
                        :title="t.motif ? `${t.utilisateur_id} · ${formatDateHeureFr(t.horodatage)}` : ''">
                      {{ t.motif || '—' }}
                    </td>
                  </tr>
                  <tr v-if="!tiersAffiches.length">
                    <td colspan="6" class="px-4 py-6 text-center text-gray-500">Aucun tiers pour ce filtre.</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="flex justify-end">
              <button type="button"
                      class="h-[46px] px-[22px] rounded-[10px] bg-green-ycube-2 text-white text-[15px] font-bold hover:bg-green-ycube transition"
                      @click="memoOuvert = true">
                Générer le mémo de sélection
              </button>
            </div>
          </section>
        </template>
      </template>
    </div>

    <!-- Fenêtre de motif (charte : modale de ClientsView) -->
    <div v-if="fenetreMotif" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-xl border-[22px] border-white p-0.5 relative max-h-[90vh] overflow-auto flex flex-col gap-4">
        <h3 class="m-0 text-lg font-bold text-blue-ycube">{{ fenetreMotif.titre }}</h3>
        <label class="flex flex-col gap-1.5 text-sm font-semibold">Motif
          <textarea v-model="motif" rows="3" :placeholder="`Au moins ${longueurMin} caractères`"
                    class="px-3 py-2 text-[15px] font-normal border border-gray-300 rounded-[10px] focus:outline-none focus:ring-2 focus:ring-blue-ycube"></textarea>
          <span class="text-xs font-normal text-gray-500">{{ motif.trim().length }} / {{ longueurMin }} caractères minimum</span>
        </label>
        <div class="flex justify-end gap-3">
          <button type="button" class="px-5 py-2 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition"
                  @click="fenetreMotif = null">Annuler</button>
          <button type="button"
                  class="px-5 py-2 rounded-lg bg-blue-ycube text-white font-semibold hover:bg-blue-900 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="enCours || motif.trim().length < longueurMin" @click="confirmerMotif">Confirmer</button>
        </div>
      </div>
    </div>
  </div>
</template>
