<script setup>
// Courriers de circularisation — sous-lot b (docs/PLAN_circularisation.md),
// maquette 4_Courriers : bibliothèque de modèles Word versionnés, tiers
// retenus avec leur état, aperçu du courrier (texte du modèle importé, champs
// fusionnés surlignés), coordonnées des tiers (annuaire du client, fenêtre
// centrée). Génération Word / PDF : en attente du choix des bibliothèques
// (PLAN §5). Envoi : écran Suivi des réponses. Le serveur reste juge des règles.
import { computed, onMounted, ref, watch } from 'vue'
import { lireCourriers, enregistrerCoordonnees, importerModele, urlFichierModele } from '@/api/courriers.api'
import { useNotyf } from '@/composables/useNotyf'
import { formatDateHeureFr } from '@/utils/formatDate'

const props = defineProps({ missionId: String })
const emit = defineEmits(['ouvrir-ecran'])
const notyf = useNotyf()

const etat = ref(null)
const erreur = ref('')
const enCours = ref(false)
const tiersChoisi = ref(null) // { type_tiers, numero }
const codeChoisi = ref(null)
const formulaire = ref({ raison_sociale: '', adresse: '', courriel: '', contact: '' })
const fenetreCoordonnees = ref(false)
const fenetreImport = ref(false)
const importCode = ref('C1')
const importFichier = ref(null)

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

const tousLesTiers = computed(() => (etat.value?.groupes || []).flatMap((g) =>
  g.tiers.map((t) => ({ ...t, type_tiers: g.type_tiers, type_libelle: g.libelle, code_modele: g.code_modele }))))
const tiers = computed(() => tousLesTiers.value.find((t) =>
  t.type_tiers === tiersChoisi.value?.type_tiers && t.numero === tiersChoisi.value?.numero) || null)
const estChoisi = (t) => tiers.value && tiers.value.numero === t.numero && tiers.value.type_tiers === t.type_tiers
const modele = computed(() => (etat.value?.modeles || []).find((m) => m.code === codeChoisi.value) || null)
const modeleDuTiers = computed(() => (etat.value?.modeles || []).find((m) => m.code === tiers.value?.code_modele)?.actif || null)
const sansCourriel = computed(() => tousLesTiers.value.filter((t) => t.etat !== 'pret').length)
// Étape affichée (maquette) : 2 · Prévisualisation dès qu'un aperçu existe ; 3 et 4 à venir.
const etapeActive = computed(() => (tiers.value && modeleDuTiers.value ? 1 : 0))

// Premier tiers choisi par défaut ; le modèle suit le type du tiers choisi.
watch(tousLesTiers, (liste) => {
  if (!tiers.value && liste.length) tiersChoisi.value = { type_tiers: liste[0].type_tiers, numero: liste[0].numero }
})
watch(tiers, (t) => { if (t) codeChoisi.value = t.code_modele })

function ouvrirCoordonnees() {
  const c = tiers.value.coordonnees || {}
  formulaire.value = { raison_sociale: c.raison_sociale || tiers.value.libelle || '', adresse: c.adresse || '', courriel: c.courriel || '', contact: c.contact || '' }
  fenetreCoordonnees.value = true
}

async function enregistrer() {
  enCours.value = true
  try {
    etat.value = await enregistrerCoordonnees(props.missionId, tiers.value.type_tiers, tiers.value.numero, formulaire.value, utilisateurConnecte())
    fenetreCoordonnees.value = false
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
    fenetreImport.value = false
    notyf.trigger('Modèle importé', 'success')
  } catch (e) {
    notyf.trigger(e.message, 'error')
  } finally {
    enCours.value = false
  }
}

function ouvrirImport() {
  importCode.value = codeChoisi.value || 'C1'
  importFichier.value = null
  fenetreImport.value = true
}

const ETATS = {
  pret: { libelle: 'Prêt', classe: 'text-green-700' },
  courriel_manquant: { libelle: 'Courriel manquant', classe: 'text-orange-700' },
  coordonnees_manquantes: { libelle: 'Coordonnées manquantes', classe: 'text-orange-700' },
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
const ETAPES = ['1 · Modèle', '2 · Prévisualisation', '3 · Génération', '4 · Envoi']
// Syntaxe des champs (docxtpl) : écrite ici, une interpolation Vue ne peut pas contenir « }} ».
const champ = (nom) => '{{ ' + nom + ' }}'
const champsReconnus = computed(() => Object.keys(etat.value?.champs_disponibles || {}).map(champ).join(', '))
</script>

<template>
  <!-- Disposition de la maquette docs/maquettes/4_Courriers.html ; couleurs et police de la charte. -->
  <div class="h-full w-full overflow-y-auto bg-[#f5f7fa] text-gray-800">
    <div class="p-7 flex flex-col gap-5">

      <section :class="[CARTE, 'px-7 py-6 flex flex-col gap-1.5 text-center']">
        <h1 class="m-0 text-[26px] font-bold text-blue-ycube">Courriers de circularisation</h1>
        <p class="m-0 text-gray-500">Fusion des modèles avec les tiers retenus, génération et envoi · CIR-01</p>
      </section>

      <!-- Étapes (maquette) : 3 · Génération en attente des bibliothèques, 4 · Envoi dans Suivi des réponses -->
      <ol class="list-none m-0 p-0 grid grid-cols-2 xl:grid-cols-4 gap-2">
        <li v-for="(e, i) in ETAPES" :key="e"
            :title="i === 2 ? 'Génération Word / PDF : en attente du choix des bibliothèques' : i === 3 ? 'Envoi : écran Suivi des réponses' : ''"
            :class="['px-3.5 py-3 rounded-[10px] text-sm', i === etapeActive ? 'bg-blue-ycube text-white font-bold' : 'bg-white text-gray-700 font-semibold border border-gray-200']">
          {{ e }}
        </li>
      </ol>

      <p v-if="erreur" class="m-0 px-4 py-3 rounded-[10px] bg-red-100 text-red-700 text-sm">{{ erreur }}</p>

      <template v-if="etat">
        <!-- Bibliothèque des modèles -->
        <section :class="[CARTE, 'px-7 py-6 flex flex-col gap-3.5']">
          <div class="flex justify-between items-center gap-3 flex-wrap">
            <h2 :class="TITRE">Bibliothèque des modèles</h2>
            <button type="button"
                    class="h-11 px-[18px] rounded-[10px] border border-blue-ycube bg-white text-blue-ycube font-bold hover:bg-blue-ycube hover:text-white transition"
                    @click="ouvrirImport">Importer un modèle Word</button>
          </div>
          <div class="grid grid-cols-2 xl:grid-cols-5 gap-3">
            <button v-for="m in etat.modeles" :key="m.code" type="button"
                    :class="['rounded-xl p-3.5 flex flex-col gap-1 text-left transition',
                             m.code === codeChoisi ? 'border-2 border-blue-ycube bg-blue-ycube/10' : 'border border-gray-200 hover:bg-gray-50']"
                    @click="codeChoisi = m.code">
              <strong>{{ m.code }} · {{ m.libelle }}</strong>
              <span class="text-[13px] text-gray-500">{{ m.actif ? `v${m.actif.version} · ${m.actif.nom_fichier}` : 'À importer' }}</span>
            </button>
          </div>
          <span class="text-[13px] text-gray-500" :title="`Champs reconnus : ${champsReconnus}`">
            Modèles versionnés. Modification réservée aux profils seniors et au-delà.
            <template v-if="modele?.actif">
              {{ modele.code }} v{{ modele.actif.version }}, importé par {{ modele.actif.importe_par }}
              le {{ formatDateHeureFr(modele.actif.importe_le) }} ·
              <a :href="urlFichierModele(missionId, modele.actif._id)" class="font-semibold text-blue-ycube underline">Télécharger</a>
            </template>
          </span>
          <span v-if="modele?.actif?.champs_inconnus.length" class="text-[13px] text-orange-700">
            Champ(s) du modèle {{ modele.code }} que l'outil ne sait pas alimenter : {{ modele.actif.champs_inconnus.join(', ') }}.
          </span>
        </section>

        <div class="flex gap-5 flex-wrap items-start">
          <!-- Tiers retenus -->
          <section :class="[CARTE, 'flex-[1_1_320px] max-w-[400px] px-[22px] py-5 flex flex-col gap-3']">
            <h2 class="m-0 text-[15px] font-bold tracking-[0.3px] uppercase text-blue-ycube">Tiers retenus · {{ tousLesTiers.length }}</h2>
            <ul class="list-none m-0 p-0 flex flex-col gap-2">
              <li v-for="t in tousLesTiers" :key="t.type_tiers + t.numero">
                <button type="button"
                        :class="['w-full flex justify-between gap-2 px-3.5 py-3 rounded-[10px] text-left transition',
                                 estChoisi(t) ? 'bg-blue-ycube text-white' : 'bg-gray-50 text-gray-800 hover:bg-gray-100']"
                        @click="tiersChoisi = { type_tiers: t.type_tiers, numero: t.numero }">
                  <span><strong>{{ t.coordonnees?.raison_sociale || t.libelle }}</strong><br />
                    <span class="text-[13px]">{{ t.numero }}</span></span>
                  <span :class="['text-[13px] self-center font-bold text-right', estChoisi(t) ? 'text-white' : ETATS[t.etat].classe]">
                    {{ ETATS[t.etat].libelle }}
                  </span>
                </button>
              </li>
            </ul>
            <p v-if="!tousLesTiers.length" class="m-0 text-sm text-gray-500">
              Aucun tiers retenu.
              <button type="button" class="font-semibold text-blue-ycube underline" @click="emit('ouvrir-ecran', 'selection_tiers')">
                Faire la sélection des tiers
              </button>
            </p>
            <div v-if="sansCourriel" class="px-3.5 py-3 rounded-[10px] bg-orange-100 text-orange-700 text-sm">
              {{ sansCourriel }} tiers sans adresse de courriel : envoi postal ou adresse à compléter.
            </div>
          </section>

          <!-- Aperçu du courrier du tiers choisi -->
          <section v-if="tiers" :class="[CARTE, 'flex-[999_1_560px] min-w-0 px-7 py-6 flex flex-col gap-3.5']">
            <div class="flex justify-between items-center gap-3 flex-wrap">
              <h2 class="m-0 text-[15px] font-bold tracking-[0.3px] uppercase text-blue-ycube">Aperçu · {{ tiers.coordonnees?.raison_sociale || tiers.libelle }}</h2>
              <span class="text-[13px] text-gray-500">
                Les champs fusionnés sont surlignés ·
                <button type="button" class="font-semibold text-blue-ycube underline" @click="ouvrirCoordonnees">Coordonnées du tiers</button>
              </span>
            </div>
            <article v-if="modeleDuTiers?.paragraphes?.length"
                     class="border border-gray-200 rounded-lg px-11 py-9 flex flex-col gap-3.5 text-[15px] leading-[1.6]">
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
            </div>
          </section>
        </div>

        <!-- Génération et envoi : en attente -->
        <section :class="[CARTE, 'px-7 py-6 flex flex-col gap-4']">
          <h2 :class="TITRE">Génération et envoi</h2>
          <div class="grid grid-cols-1 xl:grid-cols-3 gap-4 text-gray-400">
            <fieldset class="m-0 border border-gray-200 rounded-xl px-4 py-3.5 flex flex-col gap-2.5" disabled>
              <legend class="px-1 text-[15px] font-semibold">Génération</legend>
              <label class="flex gap-2.5 text-[15px]"><input type="radio" checked /> En lot (tous les tiers prêts)</label>
              <label class="flex gap-2.5 text-[15px]"><input type="radio" /> Ce tiers uniquement</label>
            </fieldset>
            <fieldset class="m-0 border border-gray-200 rounded-xl px-4 py-3.5 flex flex-col gap-2.5" disabled>
              <legend class="px-1 text-[15px] font-semibold">Formats</legend>
              <label class="flex gap-2.5 text-[15px]"><input type="checkbox" checked /> PDF (envoi et archivage)</label>
              <label class="flex gap-2.5 text-[15px]"><input type="checkbox" /> Word (retouche manuelle)</label>
            </fieldset>
            <fieldset class="m-0 border border-gray-200 rounded-xl px-4 py-3.5 flex flex-col gap-2.5" disabled>
              <legend class="px-1 text-[15px] font-semibold">Envoi</legend>
              <label class="flex gap-2.5 text-[15px]"><input type="radio" checked /> Courriel depuis votre messagerie</label>
              <label class="flex gap-2.5 text-[15px]"><input type="radio" /> Courrier postal (impression)</label>
            </fieldset>
          </div>
          <div class="flex justify-end gap-3 flex-wrap"
               title="Génération Word / PDF : en attente du choix des bibliothèques. Envoi : enregistré dans Suivi des réponses.">
            <button type="button" disabled class="h-[46px] px-[22px] rounded-[10px] border border-blue-ycube bg-white text-blue-ycube text-[15px] font-bold opacity-50 cursor-not-allowed">Générer sans envoyer</button>
            <button type="button" disabled class="h-[46px] px-[22px] rounded-[10px] bg-green-ycube-2 text-white text-[15px] font-bold opacity-50 cursor-not-allowed">Générer et envoyer</button>
          </div>
        </section>
      </template>
    </div>

    <!-- Coordonnées du tiers (annuaire du client) : fenêtre centrée -->
    <div v-if="fenetreCoordonnees && tiers" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="fenetreCoordonnees = false">
      <form role="dialog" aria-modal="true" class="bg-white rounded-2xl w-full max-w-xl p-6 relative max-h-[90vh] overflow-auto flex flex-col gap-4"
            @submit.prevent="enregistrer">
        <h3 class="m-0 text-lg font-bold text-blue-ycube">Coordonnées · {{ tiers.numero }} · {{ tiers.libelle }}</h3>
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
          <template v-if="tiers.coordonnees">Version {{ tiers.coordonnees.version }}, par {{ tiers.coordonnees.modifie_par }}
            le {{ formatDateHeureFr(tiers.coordonnees.modifie_le) }}.</template>
        </span>
        <div class="flex justify-end gap-3">
          <button type="button" class="px-5 py-2 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition"
                  @click="fenetreCoordonnees = false">Annuler</button>
          <button type="submit" :disabled="enCours"
                  class="px-5 py-2 rounded-lg bg-blue-ycube text-white font-semibold hover:bg-blue-900 transition disabled:opacity-50">
            Enregistrer les coordonnées
          </button>
        </div>
      </form>
    </div>

    <!-- Import d'un modèle (modale de la charte) -->
    <div v-if="fenetreImport" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="fenetreImport = false">
      <div class="bg-white rounded-2xl w-full max-w-xl p-6 relative max-h-[90vh] overflow-auto flex flex-col gap-4">
        <h3 class="m-0 text-lg font-bold text-blue-ycube">Importer un modèle Word</h3>
        <label class="flex flex-col gap-1.5 text-sm font-semibold">Modèle
          <select v-model="importCode" :class="CHAMP">
            <option v-for="m in etat?.modeles || []" :key="m.code" :value="m.code">
              {{ m.code }} · {{ m.libelle }}{{ m.actif ? ` (remplace la version ${m.actif.version})` : '' }}
            </option>
          </select>
        </label>
        <label class="flex flex-col gap-1.5 text-sm font-semibold">Fichier Word (.docx)
          <input type="file" accept=".docx" class="text-sm font-normal" @change="(e) => (importFichier = e.target.files[0] || null)" />
        </label>
        <span class="text-[13px] text-gray-500">
          Les champs à remplir s'écrivent {{ champ('nom_du_champ') }} dans le modèle. Champs reconnus : {{ champsReconnus }}.
        </span>
        <div class="flex justify-end gap-3">
          <button type="button" class="px-5 py-2 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition"
                  @click="fenetreImport = false">Annuler</button>
          <button type="button" :disabled="enCours || !importFichier"
                  class="px-5 py-2 rounded-lg bg-blue-ycube text-white font-semibold hover:bg-blue-900 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  @click="importer">Importer</button>
        </div>
      </div>
    </div>
  </div>
</template>
