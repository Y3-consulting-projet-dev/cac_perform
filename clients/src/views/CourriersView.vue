<script setup>
// Courriers de circularisation — sous-lot b (docs/PLAN_circularisation.md),
// maquette 4_Courriers, en quatre étapes affichées une à une (comme le mémo) :
// Modèle (modèle retenu par type ; bibliothèque dans une fenêtre), Coordonnées
// (annuaire du client), Aperçu (lettre du modèle importé, champs surlignés),
// Génération (résumé ; options dans une fenêtre). Génération Word / PDF : en
// attente du choix des bibliothèques (PLAN §5). Aucun envoi réel : l'envoi est
// enregistré dans Suivi des réponses. Le serveur reste juge des règles.
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { lireCourriers, enregistrerCoordonnees, importerModele, urlFichierModele } from '@/api/courriers.api'
import { useNotyf } from '@/composables/useNotyf'
import { formatDateHeureFr } from '@/utils/formatDate'
import FenetreCentree from '@/components/FenetreCentree.vue'

const props = defineProps({ missionId: String })
const emit = defineEmits(['ouvrir-ecran'])
const notyf = useNotyf()

const etat = ref(null)
const erreur = ref('')
const enCours = ref(false)
const etape = ref(0)
const etapesVues = ref(new Set([0]))
const tiersChoisi = ref(null) // { type_tiers, numero } — aperçu
const codeChoisi = ref('C1') // bibliothèque
// Fenêtre ouverte : 'modeles' | 'coordonnees' | 'generation' | null
const fenetre = ref(null)
const tiersEnSaisie = ref(null)
const formulaire = ref({ raison_sociale: '', adresse: '', courriel: '', contact: '' })
const importCode = ref('C1')
const importFichier = ref(null)
const optionsGeneration = ref({ mode: 'lot', tiers: '', formats: ['pdf'], canal: 'courriel' })

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
    etat.value = await lireCourriers(props.missionId)
    erreur.value = ''
  } catch (e) {
    erreur.value = e.message
  }
}

// --- Données dérivées -----------------------------------------------------------

const tousLesTiers = computed(() => (etat.value?.groupes || []).flatMap((g) =>
  g.tiers.map((t) => ({ ...t, type_tiers: g.type_tiers, type_libelle: g.libelle, code_modele: g.code_modele }))))
const modeleActif = (code) => (etat.value?.modeles || []).find((m) => m.code === code)?.actif || null
const nbTiersParCode = (code) => tousLesTiers.value.filter((t) => t.code_modele === code).length
const nomTiers = (t) => t.coordonnees?.raison_sociale || t.libelle
const estChoisi = (t) => tiersChoisi.value && tiersChoisi.value.numero === t.numero && tiersChoisi.value.type_tiers === t.type_tiers
const tiers = computed(() => tousLesTiers.value.find(estChoisi) || null)
const modeleDuTiers = computed(() => (tiers.value ? modeleActif(tiers.value.code_modele) : null))
const modeleBibliotheque = computed(() => (etat.value?.modeles || []).find((m) => m.code === codeChoisi.value) || null)

const nbPrets = computed(() => tousLesTiers.value.filter((t) => t.etat === 'pret').length)
const nbACompleter = computed(() => tousLesTiers.value.length - nbPrets.value)

// Génération : un tiers est bloqué sans modèle de son type, ou sans aucune coordonnée.
function raisonBlocage(t) {
  if (!modeleActif(t.code_modele)) return `Modèle ${t.code_modele} à importer`
  if (t.etat === 'coordonnees_manquantes') return 'Coordonnées manquantes (adresse ou courriel)'
  return null
}
const tiersBloques = computed(() => tousLesTiers.value.map((t) => ({ ...t, raison: raisonBlocage(t) })).filter((t) => t.raison))
const tiersPrets = computed(() => tousLesTiers.value.filter((t) => !raisonBlocage(t)))

// Étapes terminées (cochées).
const modelesComplets = computed(() => tousLesTiers.value.length > 0
  && [...new Set(tousLesTiers.value.map((t) => t.code_modele))].every((code) => modeleActif(code)))
const etapesTerminees = computed(() => [
  modelesComplets.value,
  tousLesTiers.value.length > 0 && nbACompleter.value === 0,
  etapesVues.value.has(2) && modelesComplets.value,
  false, // génération indisponible
])

const ETAPES = ['1 · Modèle', '2 · Coordonnées', '3 · Aperçu', '4 · Génération']
function allerA(i) {
  etape.value = i
  etapesVues.value = new Set([...etapesVues.value, i])
}

// --- Sélecteur du tiers (aperçu) : liste déroulante avec recherche ---------------
const selecteur = ref(null)
const champRecherche = ref(null)
const selecteurOuvert = ref(false)
const recherche = ref('')
const indexSurvol = ref(0)
const indexTiers = computed(() => tousLesTiers.value.findIndex(estChoisi))
const tiersFiltres = computed(() => {
  const q = recherche.value.trim().toLowerCase()
  if (!q) return tousLesTiers.value
  return tousLesTiers.value.filter((t) =>
    [nomTiers(t), t.numero, ETATS[t.etat].libelle].some((v) => String(v || '').toLowerCase().includes(q)))
})
watch(tiersFiltres, () => { indexSurvol.value = 0 })

function choisir(t) {
  tiersChoisi.value = { type_tiers: t.type_tiers, numero: t.numero }
  fermerSelecteur()
}
function decaler(pas) {
  const t = tousLesTiers.value[indexTiers.value + pas]
  if (t) tiersChoisi.value = { type_tiers: t.type_tiers, numero: t.numero }
}
function surClicDocument(e) {
  if (selecteur.value && !selecteur.value.contains(e.target)) fermerSelecteur()
}
async function basculerSelecteur() {
  if (selecteurOuvert.value) return fermerSelecteur()
  recherche.value = ''
  indexSurvol.value = Math.max(0, indexTiers.value)
  selecteurOuvert.value = true
  document.addEventListener('mousedown', surClicDocument)
  await nextTick()
  champRecherche.value?.focus()
}
function fermerSelecteur() {
  selecteurOuvert.value = false
  document.removeEventListener('mousedown', surClicDocument)
}
function surToucheRecherche(e) {
  const n = tiersFiltres.value.length
  if (e.key === 'ArrowDown') { e.preventDefault(); indexSurvol.value = n ? (indexSurvol.value + 1) % n : 0 }
  else if (e.key === 'ArrowUp') { e.preventDefault(); indexSurvol.value = n ? (indexSurvol.value - 1 + n) % n : 0 }
  else if (e.key === 'Enter') { e.preventDefault(); if (tiersFiltres.value[indexSurvol.value]) choisir(tiersFiltres.value[indexSurvol.value]) }
  else if (e.key === 'Escape') { e.preventDefault(); fermerSelecteur() }
}
onBeforeUnmount(() => document.removeEventListener('mousedown', surClicDocument))

// Premier tiers choisi par défaut pour l'aperçu.
watch(tousLesTiers, (liste) => {
  if (!tiers.value && liste.length) tiersChoisi.value = { type_tiers: liste[0].type_tiers, numero: liste[0].numero }
})

// --- Fenêtres ------------------------------------------------------------------

function ouvrirModeles(code) {
  codeChoisi.value = code || codeChoisi.value
  importCode.value = codeChoisi.value
  importFichier.value = null
  fenetre.value = 'modeles'
}

function ouvrirCoordonnees(t) {
  tiersEnSaisie.value = t
  const c = t.coordonnees || {}
  formulaire.value = { raison_sociale: c.raison_sociale || t.libelle || '', adresse: c.adresse || '', courriel: c.courriel || '', contact: c.contact || '' }
  fenetre.value = 'coordonnees'
}

function ouvrirGeneration() {
  optionsGeneration.value = { mode: 'lot', tiers: tiersPrets.value[0] ? `${tiersPrets.value[0].type_tiers}|${tiersPrets.value[0].numero}` : '', formats: ['pdf'], canal: 'courriel' }
  fenetre.value = 'generation'
}

const fermer = () => { fenetre.value = null }

async function enregistrer() {
  enCours.value = true
  try {
    etat.value = await enregistrerCoordonnees(props.missionId, tiersEnSaisie.value.type_tiers, tiersEnSaisie.value.numero, formulaire.value, utilisateurConnecte())
    fenetre.value = null
    notyf.trigger('Coordonnées enregistrées', 'success')
  } catch (e) {
    notyf.trigger(e.message, 'error')
  } finally {
    enCours.value = false
  }
}

async function importer() {
  enCours.value = true
  try {
    etat.value = await importerModele(props.missionId, importCode.value, importFichier.value, utilisateurConnecte())
    codeChoisi.value = importCode.value
    importFichier.value = null
    notyf.trigger('Modèle importé', 'success')
  } catch (e) {
    notyf.trigger(e.message, 'error')
  } finally {
    enCours.value = false
  }
}

// Options de génération indisponibles, chacune avec sa raison (PLAN_circularisation §5).
const RAISON_FORMATS = 'Bibliothèques de génération Word / PDF à valider avec la personne qui gère le serveur.'
const RAISON_ENVOI = 'Aucun envoi réel par l’outil : envoyez depuis votre messagerie ou par courrier, puis enregistrez l’envoi dans Suivi des réponses.'

// --- Affichage -----------------------------------------------------------------

const ETATS = {
  pret: { libelle: 'Prêt', classe: 'bg-green-100 text-green-700' },
  courriel_manquant: { libelle: 'Courriel manquant', classe: 'bg-orange-100 text-orange-700' },
  coordonnees_manquantes: { libelle: 'Coordonnées manquantes', classe: 'bg-orange-100 text-orange-700' },
}

function formatValeur(nom, valeur) {
  if (valeur === null || valeur === undefined || valeur === '') return null
  if (nom === 'solde') {
    const entier = Math.round(valeur)
    const formate = new Intl.NumberFormat('fr-FR').format(Math.abs(entier))
    return entier === 0 ? formate : `${formate} ${entier < 0 ? 'C' : 'D'}`
  }
  return String(valeur)
}

// Aperçu : chaque paragraphe du modèle découpé en texte et champs {{ … }} ;
// champ connu et alimenté -> valeur surlignée ; sinon -> [champ] surligné en orange.
const CHAMP_FUSION = /\{\{\s*([A-Za-z_][\w.]*)\s*\}\}/g
function morceaux(paragraphe) {
  const resultat = []
  let dernier = 0
  for (const m of paragraphe.matchAll(CHAMP_FUSION)) {
    if (m.index > dernier) resultat.push({ texte: paragraphe.slice(dernier, m.index) })
    const valeur = formatValeur(m[1], tiers.value?.valeurs?.[m[1]])
    resultat.push(valeur === null ? { manquant: `[${m[1]}]` } : { valeur })
    dernier = m.index + m[0].length
  }
  if (dernier < paragraphe.length) resultat.push({ texte: paragraphe.slice(dernier) })
  return resultat
}

onMounted(charger)

const CARTE = 'bg-white rounded-[14px] shadow'
const TITRE = 'm-0 text-[17px] font-bold tracking-[0.3px] uppercase text-blue-ycube'
const CHAMP = 'h-11 px-3 text-[15px] font-normal border border-gray-300 rounded-[10px] bg-white focus:outline-none focus:ring-2 focus:ring-blue-ycube'
const BOUTON_PRIMAIRE = 'h-11 px-5 rounded-[10px] bg-blue-ycube text-white font-bold hover:bg-blue-900 transition disabled:opacity-50 disabled:cursor-not-allowed'
const BOUTON_SECONDAIRE = 'h-11 px-5 rounded-[10px] border border-blue-ycube bg-white text-blue-ycube font-bold hover:bg-blue-ycube hover:text-white transition disabled:opacity-50 disabled:cursor-not-allowed'
const BOUTON_ANNULER = 'h-11 px-5 rounded-[10px] border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition'
const BOUTON_LIGNE = 'h-9 px-3 rounded-lg border border-blue-ycube bg-white text-blue-ycube text-sm font-bold hover:bg-blue-ycube hover:text-white transition whitespace-nowrap'
// Syntaxe des champs (docxtpl) : écrite ici, une interpolation Vue ne peut pas contenir « }} ».
const champ = (nom) => '{{ ' + nom + ' }}'
const champsReconnus = computed(() => Object.keys(etat.value?.champs_disponibles || {}).map(champ).join(', '))
</script>

<template>
  <!-- Disposition de la maquette docs/maquettes/4_Courriers.html, en étapes affichées une à une ;
       couleurs et police de la charte. -->
  <div class="h-full w-full overflow-y-auto bg-[#f5f7fa] text-gray-800">
    <div class="p-7 flex flex-col gap-5">

      <section :class="[CARTE, 'px-7 py-6 flex flex-col gap-1.5 text-center']">
        <h1 class="m-0 text-[26px] font-bold text-blue-ycube">Courriers de circularisation</h1>
        <p class="m-0 text-gray-500">Fusion des modèles avec les tiers retenus, génération et envoi · CIR-01</p>
      </section>

      <!-- Navigation par étapes : l'étape en cours en bleu, les étapes terminées cochées -->
      <nav aria-label="Étapes des courriers">
        <ol class="list-none m-0 p-0 grid grid-cols-2 xl:grid-cols-4 gap-2">
          <li v-for="(e, i) in ETAPES" :key="e">
            <button type="button" :aria-current="i === etape ? 'step' : undefined"
                    :class="['w-full px-3.5 py-3 rounded-[10px] text-sm text-left flex items-center gap-2 transition',
                             i === etape ? 'bg-blue-ycube text-white font-bold'
                               : 'bg-white text-gray-700 font-semibold border border-gray-200 hover:bg-gray-50']"
                    @click="allerA(i)">
              <i v-if="etapesTerminees[i]" :class="['fa-solid fa-circle-check', i === etape ? 'text-white' : 'text-green-700']" aria-hidden="true"></i>{{ e }}
            </button>
          </li>
        </ol>
      </nav>

      <p v-if="erreur" class="m-0 px-4 py-3 rounded-[10px] bg-red-100 text-red-700 text-sm">{{ erreur }}</p>

      <template v-if="etat">
        <p v-if="!tousLesTiers.length" class="m-0 px-4 py-3 rounded-[10px] bg-gray-100 text-gray-700 text-sm">
          Aucun tiers retenu.
          <button type="button" class="font-semibold text-blue-ycube underline" @click="emit('ouvrir-ecran', 'selection_tiers')">Faire la sélection des tiers</button>
        </p>

        <!-- 1 · Modèle : modèle retenu par type de tiers -->
        <section v-if="etape === 0" :class="[CARTE, 'px-7 py-6 flex flex-col gap-3.5']">
          <div class="flex justify-between items-center gap-3 flex-wrap">
            <h2 :class="TITRE">Modèle retenu par type de tiers</h2>
            <button type="button" :class="BOUTON_SECONDAIRE" @click="ouvrirModeles()">Gérer les modèles</button>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-[15px] border-collapse">
              <thead class="bg-blue-ycube text-white text-left">
                <tr>
                  <th class="px-4 py-3.5">Modèle</th>
                  <th class="px-4 py-3.5">Fichier</th>
                  <th class="px-4 py-3.5">Version</th>
                  <th class="px-4 py-3.5">Tiers retenus</th>
                  <th class="px-4 py-3.5">État</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="m in etat.modeles" :key="m.code" class="border-b border-gray-200 last:border-b-0 hover:bg-gray-50">
                  <td class="px-4 py-3 font-semibold">{{ m.code }} · {{ m.libelle }}</td>
                  <td class="px-4 py-3">{{ m.actif?.nom_fichier || '—' }}</td>
                  <td class="px-4 py-3 whitespace-nowrap">
                    <template v-if="m.actif">v{{ m.actif.version }} · {{ formatDateHeureFr(m.actif.importe_le) }}</template>
                    <template v-else>—</template>
                  </td>
                  <td class="px-4 py-3">{{ nbTiersParCode(m.code) }}</td>
                  <td class="px-4 py-3 whitespace-nowrap">
                    <span v-if="m.actif && m.actif.champs_inconnus.length" class="px-3 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-700"
                          :title="`Champs non alimentés : ${m.actif.champs_inconnus.join(', ')}`">Champs à compléter</span>
                    <span v-else-if="m.actif" class="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700">Prêt</span>
                    <span v-else-if="nbTiersParCode(m.code)" class="px-3 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-700">À importer</span>
                    <span v-else class="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700">Non utilisé</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <span class="text-[13px] text-gray-500">Modèles versionnés. Modification réservée aux profils seniors et au-delà.</span>
        </section>

        <!-- 2 · Coordonnées : tiers retenus et leur état -->
        <section v-if="etape === 1" :class="[CARTE, 'px-7 py-6 flex flex-col gap-3.5']">
          <div class="flex justify-between items-center gap-3 flex-wrap">
            <h2 :class="TITRE">Coordonnées des tiers retenus</h2>
            <div class="flex gap-2 flex-wrap text-sm">
              <span class="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700">{{ nbPrets }} prêt{{ nbPrets > 1 ? 's' : '' }}</span>
              <span :class="['px-3 py-1 rounded-full text-xs font-semibold', nbACompleter ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-700']">
                {{ nbACompleter }} à compléter
              </span>
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-[15px] border-collapse">
              <thead class="bg-blue-ycube text-white text-left">
                <tr>
                  <th class="px-4 py-3.5">Tiers</th>
                  <th class="px-4 py-3.5">Courriel</th>
                  <th class="px-4 py-3.5">Adresse postale</th>
                  <th class="px-4 py-3.5">État</th>
                  <th class="px-4 py-3.5"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="t in tousLesTiers" :key="t.type_tiers + t.numero" class="border-b border-gray-200 last:border-b-0 hover:bg-gray-50 align-top">
                  <td class="px-4 py-3"><strong>{{ nomTiers(t) }}</strong><br />
                    <span class="text-[13px] text-gray-500">{{ t.numero }} · {{ t.type_libelle.toLowerCase() }}</span></td>
                  <td class="px-4 py-3">{{ t.coordonnees?.courriel || '—' }}</td>
                  <td class="px-4 py-3 whitespace-pre-line">{{ t.coordonnees?.adresse || '—' }}</td>
                  <td class="px-4 py-3 whitespace-nowrap">
                    <span :class="['px-3 py-1 rounded-full text-xs font-semibold', ETATS[t.etat].classe]">{{ ETATS[t.etat].libelle }}</span>
                  </td>
                  <td class="px-4 py-3 text-right">
                    <button type="button" :class="BOUTON_LIGNE" @click="ouvrirCoordonnees(t)">Compléter</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <span class="text-[13px] text-gray-500">Annuaire du client, réutilisé d'une mission à l'autre. Sans courriel, l'envoi se fait par courrier postal.</span>
        </section>

        <!-- 3 · Aperçu : barre de choix du tiers sur toute la largeur, puis la lettre en pleine largeur -->
        <template v-if="etape === 2 && tousLesTiers.length">
          <section aria-label="Choix du tiers" :class="[CARTE, 'px-6 py-4 flex items-center gap-3 flex-wrap']">
            <!-- Sélecteur du tiers : liste déroulante avec recherche -->
            <div ref="selecteur" class="relative flex-[1_1_320px] min-w-0">
              <button type="button" aria-haspopup="listbox" :aria-expanded="selecteurOuvert"
                      class="w-full h-11 px-3 rounded-[10px] border border-gray-300 bg-white flex items-center gap-2 text-left hover:bg-gray-50 transition focus:outline-none focus:ring-2 focus:ring-blue-ycube"
                      @click="basculerSelecteur">
                <template v-if="tiers">
                  <span class="font-semibold truncate">{{ nomTiers(tiers) }}</span>
                  <span class="text-[13px] text-gray-500 shrink-0">{{ tiers.numero }}</span>
                  <span :class="['ml-auto shrink-0 px-2.5 py-0.5 rounded-full text-xs font-semibold', ETATS[tiers.etat].classe]">{{ ETATS[tiers.etat].libelle }}</span>
                </template>
                <i class="fa-solid fa-chevron-down text-gray-500 text-xs shrink-0" :class="tiers ? '' : 'ml-auto'" aria-hidden="true"></i>
              </button>
              <div v-if="selecteurOuvert" class="absolute z-40 mt-1 w-full bg-white rounded-[10px] shadow border border-gray-200 p-2 flex flex-col gap-2">
                <input ref="champRecherche" v-model="recherche" type="search" placeholder="Rechercher un tiers (nom, compte, état)"
                       aria-label="Rechercher un tiers" :class="[CHAMP, 'w-full']" @keydown="surToucheRecherche" />
                <ul role="listbox" aria-label="Tiers retenus" class="list-none m-0 p-0 max-h-72 overflow-y-auto">
                  <li v-for="(t, i) in tiersFiltres" :key="t.type_tiers + t.numero" role="option" :aria-selected="estChoisi(t)"
                      :class="['px-3 py-2 rounded-lg flex items-center gap-2 cursor-pointer',
                               i === indexSurvol ? 'bg-gray-100' : '', estChoisi(t) ? 'font-semibold' : '']"
                      @mouseenter="indexSurvol = i" @mousedown.prevent="choisir(t)">
                    <span class="truncate">{{ nomTiers(t) }}</span>
                    <span class="text-[13px] text-gray-500 shrink-0">{{ t.numero }}</span>
                    <span :class="['ml-auto shrink-0 px-2.5 py-0.5 rounded-full text-xs font-semibold', ETATS[t.etat].classe]">{{ ETATS[t.etat].libelle }}</span>
                  </li>
                  <li v-if="!tiersFiltres.length" class="px-3 py-2 text-sm text-gray-500">Aucun tiers ne correspond.</li>
                </ul>
              </div>
            </div>
            <div class="flex gap-2 flex-wrap">
              <button type="button" :class="BOUTON_LIGNE" :disabled="indexTiers <= 0" @click="decaler(-1)">Tiers précédent</button>
              <button type="button" :class="BOUTON_LIGNE" :disabled="indexTiers >= tousLesTiers.length - 1" @click="decaler(1)">Tiers suivant</button>
            </div>
            <span class="text-sm text-gray-700 whitespace-nowrap"><strong>{{ nbPrets }}</strong> prêt{{ nbPrets > 1 ? 's' : '' }} sur {{ tousLesTiers.length }}</span>
            <button v-if="tiers && tiers.etat !== 'pret'" type="button" :class="BOUTON_LIGNE" @click="ouvrirCoordonnees(tiers)">Compléter</button>
          </section>

          <!-- Aperçu de la lettre : toute la largeur de la zone principale -->
          <section v-if="tiers" :class="[CARTE, '@container px-7 py-6 flex flex-col gap-3.5']">
            <div class="flex justify-between items-center gap-3 flex-wrap">
              <h2 class="m-0 text-[15px] font-bold tracking-[0.3px] uppercase text-blue-ycube">Aperçu · {{ nomTiers(tiers) }}</h2>
              <span class="text-[13px] text-gray-500">Les champs fusionnés sont surlignés</span>
            </div>
            <article v-if="modeleDuTiers?.paragraphes?.length"
                     class="w-full border border-gray-200 rounded-lg px-6 py-8 @3xl:px-14 @3xl:py-12 flex flex-col gap-4 text-base leading-[1.7]">
              <p v-for="(p, i) in modeleDuTiers.paragraphes" :key="i" class="m-0 whitespace-pre-line min-h-[1em]">
                <template v-for="(m, j) in morceaux(p)" :key="j">
                  <mark v-if="m.valeur" class="bg-blue-ycube/10 text-gray-800 px-1 rounded">{{ m.valeur }}</mark>
                  <mark v-else-if="m.manquant" class="bg-orange-100 text-orange-700 px-1 rounded">{{ m.manquant }}</mark>
                  <template v-else>{{ m.texte }}</template>
                </template>
              </p>
            </article>
            <div v-else class="border border-dashed border-gray-300 rounded-lg p-4 text-gray-500 text-sm">
              Importez le modèle {{ tiers.code_modele }} ({{ tiers.type_libelle.toLowerCase() }}) pour voir l'aperçu du courrier.
              <button type="button" class="font-semibold text-blue-ycube underline" @click="ouvrirModeles(tiers.code_modele)">Gérer les modèles</button>
            </div>
          </section>
        </template>

        <!-- 4 · Génération : résumé, puis options dans une fenêtre -->
        <section v-if="etape === 3" :class="[CARTE, 'px-7 py-6 flex flex-col gap-3.5']">
          <h2 :class="TITRE">Génération</h2>
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-3">
            <div class="px-5 py-4 rounded-[10px] bg-gray-50">
              <div class="text-[13px] text-gray-500">Courriers prêts</div>
              <div class="text-2xl font-extrabold text-green-700">{{ tiersPrets.length }}</div>
            </div>
            <div class="px-5 py-4 rounded-[10px] bg-gray-50">
              <div class="text-[13px] text-gray-500">Tiers bloqués</div>
              <div :class="['text-2xl font-extrabold', tiersBloques.length ? 'text-orange-700' : 'text-gray-700']">{{ tiersBloques.length }}</div>
            </div>
          </div>
          <table v-if="tiersBloques.length" class="min-w-full text-[15px] border-collapse">
            <thead class="bg-blue-ycube text-white text-left">
              <tr><th class="px-4 py-3.5">Tiers bloqué</th><th class="px-4 py-3.5">Raison</th></tr>
            </thead>
            <tbody>
              <tr v-for="t in tiersBloques" :key="t.type_tiers + t.numero" class="border-b border-gray-200 last:border-b-0">
                <td class="px-4 py-3"><strong>{{ nomTiers(t) }}</strong> <span class="text-[13px] text-gray-500">{{ t.numero }}</span></td>
                <td class="px-4 py-3 text-orange-700">{{ t.raison }}</td>
              </tr>
            </tbody>
          </table>
          <div class="flex justify-end">
            <button type="button" :class="BOUTON_PRIMAIRE" :disabled="!tousLesTiers.length" @click="ouvrirGeneration">Générer</button>
          </div>
        </section>

        <!-- Précédent / Suivant -->
        <div class="flex justify-between gap-3">
          <button type="button" :class="BOUTON_ANNULER" :disabled="etape === 0" :style="etape === 0 ? 'visibility:hidden' : ''"
                  @click="allerA(etape - 1)">Précédent</button>
          <button type="button" :class="BOUTON_PRIMAIRE" :disabled="etape === ETAPES.length - 1"
                  :style="etape === ETAPES.length - 1 ? 'visibility:hidden' : ''" @click="allerA(etape + 1)">Suivant</button>
        </div>
      </template>
    </div>

    <!-- Bibliothèque des modèles : import, versions, champs détectés -->
    <FenetreCentree v-if="fenetre === 'modeles'" titre="Bibliothèque des modèles"
                    sous-titre="Modèles versionnés, communs au cabinet" @fermer="fermer">
      <div class="grid grid-cols-2 xl:grid-cols-5 gap-2.5">
        <button v-for="m in etat.modeles" :key="m.code" type="button"
                :class="['rounded-xl p-3 flex flex-col gap-1 text-left transition',
                         m.code === codeChoisi ? 'border-2 border-blue-ycube bg-blue-ycube/10' : 'border border-gray-200 hover:bg-gray-50']"
                @click="codeChoisi = m.code; importCode = m.code">
          <strong class="text-sm">{{ m.code }} · {{ m.libelle }}</strong>
          <span class="text-xs text-gray-500">{{ m.actif ? `v${m.actif.version}` : 'À importer' }}</span>
        </button>
      </div>
      <div v-if="modeleBibliotheque" class="flex flex-col gap-1.5 text-sm">
        <template v-if="modeleBibliotheque.actif">
          <span>
            <strong>{{ modeleBibliotheque.code }} · {{ modeleBibliotheque.libelle }}</strong> — {{ modeleBibliotheque.actif.nom_fichier }},
            version {{ modeleBibliotheque.actif.version }}, importée par {{ modeleBibliotheque.actif.importe_par }}
            le {{ formatDateHeureFr(modeleBibliotheque.actif.importe_le) }} ·
            <a :href="urlFichierModele(missionId, modeleBibliotheque.actif._id)" class="font-semibold text-blue-ycube underline">Télécharger</a>
          </span>
          <span>
            Champs détectés :
            <span v-if="!modeleBibliotheque.actif.champs.length" class="text-gray-500">aucun.</span>
            <span v-for="c in modeleBibliotheque.actif.champs" :key="c"
                  :class="['inline-block mr-1.5 mb-1 px-2.5 py-0.5 rounded-full text-xs font-semibold',
                           modeleBibliotheque.actif.champs_inconnus.includes(c) ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-700']">{{ c }}</span>
          </span>
          <span v-if="modeleBibliotheque.actif.champs_inconnus.length" class="text-orange-700">
            Champ(s) que l'outil ne sait pas alimenter : {{ modeleBibliotheque.actif.champs_inconnus.join(', ') }}.
          </span>
        </template>
        <span v-else class="text-gray-500">Aucun modèle {{ modeleBibliotheque.code }} importé.</span>
      </div>
      <div class="border-t border-gray-200 pt-4 flex flex-col gap-3">
        <strong class="text-sm text-blue-ycube">Importer un modèle Word</strong>
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-3">
          <label class="flex flex-col gap-1.5 text-sm font-semibold">Modèle
            <select v-model="importCode" :class="CHAMP">
              <option v-for="m in etat.modeles" :key="m.code" :value="m.code">
                {{ m.code }} · {{ m.libelle }}{{ m.actif ? ` (remplace la version ${m.actif.version})` : '' }}
              </option>
            </select>
          </label>
          <label class="flex flex-col gap-1.5 text-sm font-semibold">Fichier Word (.docx)
            <input type="file" accept=".docx" class="text-sm font-normal py-2.5" @change="(e) => (importFichier = e.target.files[0] || null)" />
          </label>
        </div>
        <span class="text-[13px] text-gray-500">
          Les champs à remplir s'écrivent {{ champ('nom_du_champ') }} dans le modèle. Champs reconnus : {{ champsReconnus }}.
        </span>
        <div class="flex justify-end gap-3">
          <button type="button" :class="BOUTON_ANNULER" @click="fermer">Fermer</button>
          <button type="button" :class="BOUTON_PRIMAIRE" :disabled="enCours || !importFichier" @click="importer">Importer</button>
        </div>
      </div>
    </FenetreCentree>

    <!-- Coordonnées d'un tiers (annuaire du client) -->
    <FenetreCentree v-if="fenetre === 'coordonnees' && tiersEnSaisie" :titre="`Coordonnées · ${tiersEnSaisie.numero}`"
                    :sous-titre="tiersEnSaisie.libelle" largeur="max-w-xl" @fermer="fermer">
      <form class="flex flex-col gap-4" @submit.prevent="enregistrer">
        <label class="flex flex-col gap-1.5 text-sm font-semibold">Raison sociale
          <input v-model="formulaire.raison_sociale" :class="CHAMP" />
        </label>
        <label class="flex flex-col gap-1.5 text-sm font-semibold">Adresse postale
          <textarea v-model="formulaire.adresse" rows="2" :class="[CHAMP, 'h-auto py-2']"></textarea>
        </label>
        <label class="flex flex-col gap-1.5 text-sm font-semibold">Courriel
          <input v-model="formulaire.courriel" type="email" :class="CHAMP" placeholder="compta@tiers.ci" />
        </label>
        <label class="flex flex-col gap-1.5 text-sm font-semibold">Contact
          <input v-model="formulaire.contact" :class="CHAMP" placeholder="Service comptable, nom…" />
        </label>
        <span class="text-[13px] text-gray-500">
          Annuaire du client, réutilisé d'une mission à l'autre.
          <template v-if="tiersEnSaisie.coordonnees">Version {{ tiersEnSaisie.coordonnees.version }}, par {{ tiersEnSaisie.coordonnees.modifie_par }}
            le {{ formatDateHeureFr(tiersEnSaisie.coordonnees.modifie_le) }}.</template>
        </span>
        <div class="flex justify-end gap-3">
          <button type="button" :class="BOUTON_ANNULER" @click="fermer">Annuler</button>
          <button type="submit" :class="BOUTON_PRIMAIRE" :disabled="enCours">Enregistrer les coordonnées</button>
        </div>
      </form>
    </FenetreCentree>

    <!-- Génération : options et confirmation (indisponible : aucune bibliothèque, aucun envoi réel) -->
    <FenetreCentree v-if="fenetre === 'generation'" titre="Générer les courriers"
                    :sous-titre="`${tiersPrets.length} courrier${tiersPrets.length > 1 ? 's' : ''} prêt${tiersPrets.length > 1 ? 's' : ''}`"
                    largeur="max-w-xl" @fermer="fermer">
      <fieldset class="m-0 border border-gray-200 rounded-xl px-4 py-3.5 flex flex-col gap-2.5">
        <legend class="px-1 text-[15px] font-semibold">Génération</legend>
        <label class="flex gap-2.5 items-center text-[15px]">
          <input v-model="optionsGeneration.mode" type="radio" value="lot" class="w-[18px] h-[18px] accent-blue-ycube" /> En lot (tous les tiers prêts)
        </label>
        <label class="flex gap-2.5 items-center text-[15px]">
          <input v-model="optionsGeneration.mode" type="radio" value="unitaire" class="w-[18px] h-[18px] accent-blue-ycube" /> Un seul tiers
        </label>
        <select v-if="optionsGeneration.mode === 'unitaire'" v-model="optionsGeneration.tiers" :class="CHAMP">
          <option v-for="t in tiersPrets" :key="t.type_tiers + t.numero" :value="`${t.type_tiers}|${t.numero}`">{{ t.numero }} · {{ nomTiers(t) }}</option>
        </select>
      </fieldset>
      <fieldset class="m-0 border border-gray-200 rounded-xl px-4 py-3.5 flex flex-col gap-2.5" disabled>
        <legend class="px-1 text-[15px] font-semibold text-gray-400">Formats</legend>
        <label class="flex gap-2.5 items-center text-[15px] text-gray-400"><input type="checkbox" checked class="w-[18px] h-[18px]" /> PDF (envoi et archivage)</label>
        <label class="flex gap-2.5 items-center text-[15px] text-gray-400"><input type="checkbox" class="w-[18px] h-[18px]" /> Word (retouche manuelle)</label>
        <span class="text-[13px] text-gray-500">{{ RAISON_FORMATS }}</span>
      </fieldset>
      <fieldset class="m-0 border border-gray-200 rounded-xl px-4 py-3.5 flex flex-col gap-2.5" disabled>
        <legend class="px-1 text-[15px] font-semibold text-gray-400">Envoi</legend>
        <label class="flex gap-2.5 items-center text-[15px] text-gray-400"><input type="radio" checked class="w-[18px] h-[18px]" /> Courriel</label>
        <label class="flex gap-2.5 items-center text-[15px] text-gray-400"><input type="radio" class="w-[18px] h-[18px]" /> Courrier postal (impression)</label>
        <span class="text-[13px] text-gray-500">{{ RAISON_ENVOI }}</span>
      </fieldset>
      <p class="m-0 px-3.5 py-3 rounded-[10px] bg-orange-100 text-orange-700 text-sm">
        Génération indisponible : {{ RAISON_FORMATS }}
      </p>
      <div class="flex justify-end gap-3">
        <button type="button" :class="BOUTON_ANNULER" @click="fermer">Annuler</button>
        <button type="button" :class="BOUTON_PRIMAIRE" disabled>Confirmer la génération</button>
      </div>
    </FenetreCentree>
  </div>
</template>
