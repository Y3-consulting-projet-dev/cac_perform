<script setup>
// Suivi des réponses — sous-lot c (docs/PLAN_circularisation.md), maquette
// 5_Suivi_reponses. AUCUN envoi automatique : l'auditeur enregistre l'envoi et
// chaque relance ; le serveur calcule échéances (CADENCE_RELANCES, figées à
// l'envoi), statuts du jour, écarts. Saisies dans une fenêtre centrée (comme
// Fiabilité IPE) plutôt que dans le panneau à droite de la maquette.
import { computed, onMounted, ref } from 'vue'
import {
  lireSuivi, enregistrerEnvoi, enregistrerRelance, enregistrerReponse, analyserEcart, documenterProcedure, urlPiece,
} from '@/api/suivi.api'
import { useNotyf } from '@/composables/useNotyf'
import { formatDateHeureFr } from '@/utils/formatDate'

const props = defineProps({ missionId: String })
const emit = defineEmits(['ouvrir-ecran'])
const notyf = useNotyf()

const LONGUEUR_MIN = 15 // même seuil que le serveur (circularisation_service.LONGUEUR_MIN_MOTIF)
const etat = ref(null)
const erreur = ref('')
const filtre = ref('tous')
const enCours = ref(false)
// Fenêtre de saisie : { mode: envoi|relance|reponse|analyse|procedure, cible, champs, fichier }
const fenetre = ref(null)

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

function aujourdHui() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

async function charger() {
  try {
    etat.value = await lireSuivi(props.missionId)
    erreur.value = ''
  } catch (e) {
    erreur.value = e.message
  }
}

const FILTRES = {
  tous: () => true,
  a_relancer: (d) => d.statut.cle === 'a_relancer' || d.statut.cle.startsWith('relance_'),
  reponse_recue: (d) => d.statut.cle === 'reponse_recue',
  ecart: (d) => d.statut.cle === 'ecart',
  sans_reponse: (d) => d.statut.cle === 'sans_reponse',
}
const demandes = computed(() => (etat.value?.demandes || []).filter(FILTRES[filtre.value]))

const BADGES = {
  envoye: 'bg-blue-ycube/10 text-blue-ycube',
  a_relancer: 'bg-orange-100 text-orange-700',
  relance_1: 'bg-orange-100 text-orange-700',
  relance_2: 'bg-orange-100 text-orange-700',
  reponse_recue: 'bg-green-100 text-green-700',
  ecart: 'bg-red-100 text-red-700',
  sans_reponse: 'bg-gray-100 text-gray-700',
}

const TITRES = {
  envoi: 'Enregistrer l’envoi',
  relance: 'Enregistrer la relance',
  reponse: 'Réponse',
  analyse: 'Analyse de l’écart',
  procedure: 'Procédure alternative',
}

function ouvrir(mode, cible) {
  const champs = { date: aujourdHui(), canal: 'courriel', commentaire: '' }
  if (mode === 'envoi') {
    champs.canal = cible.courriel ? 'courriel' : 'postal'
    champs.destinataire = cible.courriel || cible.adresse || ''
  }
  if (mode === 'reponse') Object.assign(champs, { type: 'accord_total', solde_confirme: '' })
  fenetre.value = { mode, cible, champs, fichier: null }
}

async function confirmer() {
  const { mode, cible, champs, fichier } = fenetre.value
  const utilisateur_id = utilisateurConnecte()
  enCours.value = true
  try {
    if (mode === 'envoi') {
      etat.value = await enregistrerEnvoi(props.missionId, {
        type_tiers: cible.type_tiers, numero: cible.numero, canal: champs.canal,
        date_envoi: champs.date, destinataire: champs.destinataire, utilisateur_id,
      })
    } else if (mode === 'relance') {
      etat.value = await enregistrerRelance(props.missionId, cible._id, { date: champs.date, canal: champs.canal, utilisateur_id })
    } else if (mode === 'reponse') {
      etat.value = await enregistrerReponse(props.missionId, cible._id, {
        type: champs.type, canal: champs.canal, recue_le: champs.date,
        solde_confirme: champs.type === 'accord_total' ? '' : champs.solde_confirme,
        commentaire: champs.commentaire, utilisateur_id,
      }, fichier)
    } else {
      const action = mode === 'analyse' ? analyserEcart : documenterProcedure
      etat.value = await action(props.missionId, cible._id, { commentaire: champs.commentaire, utilisateur_id }, fichier)
    }
    notyf.trigger('Enregistré', 'success')
    fenetre.value = null
  } catch (e) {
    notyf.trigger(e.message, 'error')
  } finally {
    enCours.value = false
  }
}

const besoinCommentaire = computed(() => ['reponse', 'analyse', 'procedure'].includes(fenetre.value?.mode))
const peutConfirmer = computed(() => {
  const f = fenetre.value
  if (!f || enCours.value) return false
  if (besoinCommentaire.value && f.champs.commentaire.trim().length < LONGUEUR_MIN) return false
  if (f.mode === 'reponse' && f.champs.type !== 'accord_total' && String(f.champs.solde_confirme).trim() === '') return false
  return true
})

// Écart de la réponse saisie, affiché avant l'enregistrement (même calcul que le serveur).
const ecartPrevu = computed(() => {
  const f = fenetre.value
  if (f?.mode !== 'reponse') return null
  if (f.champs.type === 'accord_total') return 0
  const confirme = Number(String(f.champs.solde_confirme).replace(/\s/g, '').replace(',', '.'))
  return Number.isFinite(confirme) && String(f.champs.solde_confirme).trim() !== '' ? Math.abs(f.cible.solde_comptable) - confirme : null
})

function formatMontant(valeur) {
  if (valeur === null || valeur === undefined) return '—'
  const entier = Math.round(valeur)
  const formate = new Intl.NumberFormat('fr-FR').format(Math.abs(entier))
  return entier === 0 ? formate : `${formate} ${entier < 0 ? 'C' : 'D'}`
}
const formatEntier = (v) => (v === null || v === undefined ? '—' : new Intl.NumberFormat('fr-FR').format(Math.round(v)))
const formatJour = (iso) => (iso ? new Date(`${iso}T00:00:00`).toLocaleDateString('fr-FR') : '—')
const derniere = (liste) => (liste && liste.length ? liste[liste.length - 1] : null)

onMounted(charger)

const CARTE = 'bg-white rounded-[14px] shadow'
const TITRE = 'm-0 text-[17px] font-bold tracking-[0.3px] uppercase text-blue-ycube'
const BOUTON_LIGNE = 'h-9 px-3 rounded-lg border border-blue-ycube bg-white text-blue-ycube text-sm font-bold hover:bg-blue-ycube hover:text-white transition whitespace-nowrap'
const LIEN = 'font-bold text-blue-ycube underline text-left whitespace-nowrap'
const TYPE_SINGULIER = { clients: 'client', fournisseurs: 'fournisseur', avocats: 'avocat', bailleurs: 'bailleur', banques: 'banque' }
const CHAMP = 'h-11 px-3 text-[15px] font-normal border border-gray-300 rounded-[10px] bg-white focus:outline-none focus:ring-2 focus:ring-blue-ycube'
</script>

<template>
  <!-- Disposition de la maquette docs/maquettes/5_Suivi_reponses.html ; couleurs et police de la charte. -->
  <div class="h-full w-full overflow-y-auto bg-[#f5f7fa] text-gray-800">
    <div class="p-7 flex flex-col gap-5">

      <section :class="[CARTE, 'px-7 py-6 flex flex-col gap-1.5 text-center']">
        <h1 class="m-0 text-[26px] font-bold text-blue-ycube">Suivi des réponses</h1>
        <p class="m-0 text-gray-500">Confirmations envoyées, relances et réponses reçues</p>
        <span class="self-center mt-1 px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700">
          Aucun envoi automatique : enregistrez chaque envoi et chaque relance que vous avez faits
        </span>
      </section>

      <p v-if="erreur" class="m-0 px-4 py-3 rounded-[10px] bg-red-100 text-red-700 text-sm">{{ erreur }}</p>

      <template v-if="etat">
        <!-- Indicateurs -->
        <section class="grid grid-cols-2 xl:grid-cols-5 gap-3.5">
          <div :class="[CARTE, 'px-[18px] py-4']"><div class="text-[13px] text-gray-500">Envoyés</div>
            <div class="text-2xl font-extrabold text-blue-ycube">{{ etat.indicateurs.envoyes }}</div></div>
          <div :class="[CARTE, 'px-[18px] py-4']"><div class="text-[13px] text-gray-500">Réponses reçues</div>
            <div class="text-2xl font-extrabold text-green-700">{{ etat.indicateurs.reponses_recues }}</div>
            <div class="text-[13px] text-gray-500">Taux {{ etat.indicateurs.taux_reponse === null ? '—' : `${Math.round(etat.indicateurs.taux_reponse)} %` }}</div></div>
          <div :class="[CARTE, 'px-[18px] py-4']"><div class="text-[13px] text-gray-500">En relance</div>
            <div class="text-2xl font-extrabold text-orange-700">{{ etat.indicateurs.en_relance }}</div></div>
          <div :class="[CARTE, 'px-[18px] py-4']"><div class="text-[13px] text-gray-500">Écarts constatés</div>
            <div class="text-2xl font-extrabold text-red-700">{{ etat.indicateurs.ecarts }}</div></div>
          <div :class="[CARTE, 'px-[18px] py-4']"><div class="text-[13px] text-gray-500">Sans réponse après J+{{ etat.cadence[etat.cadence.length - 1].jour }}</div>
            <div class="text-2xl font-extrabold text-gray-700">{{ etat.indicateurs.sans_reponse }}</div></div>
        </section>

        <!-- Cadence (paramètre CADENCE_RELANCES) -->
        <section :class="[CARTE, 'px-6 py-[18px] grid grid-cols-2 xl:grid-cols-4 gap-3']">
          <div v-for="c in etat.cadence" :key="c.cle" class="flex flex-col gap-0.5">
            <strong class="text-blue-ycube">{{ c.jour ? `J+${c.jour}` : 'J0' }}</strong>
            <span class="text-sm">{{ c.description }}</span>
          </div>
        </section>

        <!-- Tiers retenus sans demande envoyée -->
        <section v-if="etat.a_envoyer.length" :class="[CARTE, 'px-7 py-6 flex flex-col gap-3']">
          <h2 :class="TITRE">À envoyer · {{ etat.a_envoyer.length }}</h2>
          <ul class="list-none m-0 p-0 flex flex-col gap-2">
            <li v-for="t in etat.a_envoyer" :key="t.type_tiers + t.numero"
                class="flex justify-between items-center gap-3 px-3.5 py-3 rounded-[10px] bg-gray-50">
              <span><strong>{{ t.raison_sociale || t.libelle }}</strong><br />
                <span class="text-[13px] text-gray-500">{{ t.numero }} · {{ t.type_libelle.toLowerCase() }} ·
                  {{ t.courriel || t.adresse || 'coordonnées manquantes' }}</span></span>
              <button type="button" :class="BOUTON_LIGNE" @click="ouvrir('envoi', t)">Enregistrer l’envoi</button>
            </li>
          </ul>
        </section>

        <!-- Demandes de confirmation -->
        <section :class="[CARTE, 'px-7 py-6 flex flex-col gap-3.5']">
          <div class="flex justify-between items-center gap-3 flex-wrap">
            <h2 :class="TITRE">Demandes de confirmation</h2>
            <label class="flex items-center gap-2 text-sm">Statut
              <select v-model="filtre" class="h-10 px-2.5 text-sm border border-gray-300 rounded-[10px] bg-white">
                <option value="tous">Tous</option>
                <option value="a_relancer">À relancer</option>
                <option value="reponse_recue">Réponse reçue</option>
                <option value="ecart">Écart constaté</option>
                <option value="sans_reponse">Sans réponse</option>
              </select>
            </label>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-[15px] border-collapse">
              <thead class="bg-blue-ycube text-white text-left">
                <tr>
                  <th class="px-4 py-3.5">Tiers</th>
                  <th class="px-4 py-3.5">Envoyé le</th>
                  <th class="px-4 py-3.5">Statut</th>
                  <th class="px-4 py-3.5">Prochaine étape</th>
                  <th class="px-4 py-3.5 text-right">Écart</th>
                  <th class="px-4 py-3.5">Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="d in demandes" :key="d._id" class="border-b border-gray-200 last:border-b-0 hover:bg-gray-50 align-top">
                  <td class="px-4 py-3"><strong>{{ d.libelle }}</strong><br />
                    <span class="text-[13px] text-gray-500" :title="`Envoi : ${d.canal === 'postal' ? 'courrier' : 'courriel'} · ${d.destinataire}`">{{ d.numero }} · {{ TYPE_SINGULIER[d.type_tiers] }}</span></td>
                  <td class="px-4 py-3 whitespace-nowrap">{{ formatJour(d.date_envoi) }}</td>
                  <td class="px-4 py-3 whitespace-nowrap">
                    <span :class="['px-2.5 py-0.5 rounded-full text-[13px] font-bold', BADGES[d.statut.cle]]">{{ d.statut.libelle }}</span>
                  </td>
                  <td class="px-4 py-3">
                    {{ d.statut.prochaine_etape }}
                    <template v-for="p in [derniere(d.reponses)?.piece, derniere(d.analyses_ecart)?.piece, derniere(d.procedures_alternatives)?.piece].filter(Boolean)" :key="p.fichier_id">
                      <br /><a :href="urlPiece(missionId, p.fichier_id)" class="text-[13px] font-semibold text-blue-ycube hover:underline">{{ p.nom_fichier }}</a>
                    </template>
                  </td>
                  <td class="px-4 py-3 text-right whitespace-nowrap"
                      :class="derniere(d.reponses)?.ecart ? 'text-red-700 font-bold' : 'text-gray-500'">
                    {{ derniere(d.reponses) ? formatEntier(derniere(d.reponses).ecart) : '—' }}
                  </td>
                  <td class="px-4 py-3">
                    <!-- Maquette : un bouton pour l'action attendue, des liens pour les suites (écart, procédure). -->
                    <div class="flex flex-col gap-1.5 items-start">
                      <button v-if="d.statut.cle === 'a_relancer'" type="button" :class="BOUTON_LIGNE" @click="ouvrir('relance', d)">Enregistrer la relance</button>
                      <button v-if="d.statut.cle === 'ecart' && !d.analyses_ecart.length" type="button" :class="LIEN" @click="ouvrir('analyse', d)">Analyser l’écart</button>
                      <button v-if="d.statut.cle === 'sans_reponse' && !d.procedures_alternatives.length" type="button" :class="LIEN" @click="ouvrir('procedure', d)">Documenter</button>
                      <button v-if="['envoye', 'relance_1', 'relance_2'].includes(d.statut.cle)" type="button" :class="BOUTON_LIGNE" @click="ouvrir('reponse', d)">Saisir la réponse</button>
                      <button v-else type="button" :class="LIEN" @click="ouvrir('reponse', d)">
                        {{ d.reponses.length ? 'Corriger la réponse' : 'Saisir la réponse' }}
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!demandes.length">
                  <td colspan="6" class="px-4 py-6 text-center text-gray-500">
                    {{ etat.demandes.length ? 'Aucune demande pour ce filtre.' : 'Aucune demande envoyée.' }}
                    <button v-if="!etat.demandes.length && !etat.a_envoyer.length" type="button"
                            class="font-semibold text-blue-ycube hover:underline" @click="emit('ouvrir-ecran', 'selection_tiers')">
                      Faire la sélection des tiers
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
    </div>

    <!-- Fenêtre de saisie centrée (modale de la charte) -->
    <div v-if="fenetre" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="fenetre = null">
      <div role="dialog" aria-modal="true" class="bg-white rounded-2xl w-full max-w-xl border-[22px] border-white p-0.5 relative max-h-[90vh] overflow-auto flex flex-col gap-4">
        <div class="flex justify-between items-start gap-3">
          <div>
            <h3 class="m-0 text-lg font-bold text-blue-ycube">{{ TITRES[fenetre.mode] }} · {{ fenetre.cible.raison_sociale || fenetre.cible.libelle }}</h3>
            <span class="text-sm text-gray-500">
              {{ fenetre.cible.numero }} · solde comptable {{ formatMontant(fenetre.cible.solde_comptable ?? fenetre.cible.solde) }}
            </span>
          </div>
          <button type="button" aria-label="Fermer" class="w-11 h-11 shrink-0 rounded-[10px] bg-[#f5f7fa] text-blue-ycube hover:bg-gray-100 transition flex items-center justify-center" @click="fenetre = null">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg>
          </button>
        </div>

        <div v-if="['envoi', 'relance', 'reponse'].includes(fenetre.mode)" class="grid grid-cols-2 gap-3">
          <label class="flex flex-col gap-1.5 text-sm font-semibold">
            {{ fenetre.mode === 'envoi' ? 'Envoyé le' : fenetre.mode === 'relance' ? 'Relancé le' : 'Reçue le' }}
            <input v-model="fenetre.champs.date" type="date" :max="aujourdHui()" :class="CHAMP" />
          </label>
          <label class="flex flex-col gap-1.5 text-sm font-semibold">{{ fenetre.mode === 'reponse' ? 'Reçue par' : 'Canal' }}
            <select v-model="fenetre.champs.canal" :class="CHAMP">
              <option value="courriel">Courriel</option>
              <option value="postal">Courrier</option>
            </select>
          </label>
        </div>

        <label v-if="fenetre.mode === 'envoi'" class="flex flex-col gap-1.5 text-sm font-semibold">Destinataire
          <input v-model="fenetre.champs.destinataire" :class="CHAMP"
                 :placeholder="fenetre.champs.canal === 'courriel' ? 'compta@tiers.ci' : 'Adresse postale'" />
          <span class="text-xs font-normal text-gray-500">
            Les échéances (relances, procédure alternative) sont calculées depuis cette date et figées.
          </span>
        </label>

        <template v-if="fenetre.mode === 'reponse'">
          <fieldset class="m-0 border border-gray-200 rounded-xl px-4 py-3 flex flex-col gap-2">
            <legend class="px-1 text-sm font-semibold">Réponse du tiers</legend>
            <label v-for="(libelle, cle) in etat.types_reponse" :key="cle" class="flex gap-2.5 items-center text-[15px]">
              <input v-model="fenetre.champs.type" type="radio" :value="cle" class="w-[18px] h-[18px] accent-blue-ycube" />
              {{ libelle.charAt(0).toUpperCase() + libelle.slice(1) }}
            </label>
          </fieldset>
          <label v-if="fenetre.champs.type !== 'accord_total'" class="flex flex-col gap-1.5 text-sm font-semibold">Solde confirmé par le tiers (FCFA)
            <input v-model="fenetre.champs.solde_confirme" inputmode="decimal" :class="CHAMP" placeholder="Montant" />
          </label>
          <div v-if="ecartPrevu !== null" class="px-3.5 py-3 rounded-[10px] text-sm"
               :class="ecartPrevu ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'">
            Écart calculé : {{ formatEntier(ecartPrevu) }} FCFA.
            <template v-if="ecartPrevu">Une analyse de l’écart sera demandée.</template>
          </div>
        </template>

        <label v-if="['reponse', 'analyse', 'procedure'].includes(fenetre.mode)" class="flex flex-col gap-1.5 text-sm font-semibold">
          {{ fenetre.mode === 'reponse' ? 'Joindre la réponse signée (facultatif)' : 'Pièce justificative (facultatif)' }}
          <input type="file" class="text-sm font-normal" @change="(e) => (fenetre.fichier = e.target.files[0] || null)" />
        </label>

        <label v-if="besoinCommentaire" class="flex flex-col gap-1.5 text-sm font-semibold">Commentaire
          <textarea v-model="fenetre.champs.commentaire" rows="3" :placeholder="`Au moins ${LONGUEUR_MIN} caractères`"
                    class="px-3 py-2 text-[15px] font-normal border border-gray-300 rounded-[10px] focus:outline-none focus:ring-2 focus:ring-blue-ycube"></textarea>
        </label>

        <p v-if="fenetre.mode === 'reponse' && fenetre.cible.reponses?.length" class="m-0 text-[13px] text-gray-500">
          Réponse actuelle (version {{ derniere(fenetre.cible.reponses).version }}), saisie par {{ derniere(fenetre.cible.reponses).utilisateur_id }}
          le {{ formatDateHeureFr(derniere(fenetre.cible.reponses).horodatage) }} : une nouvelle version sera créée.
        </p>

        <div class="flex justify-end gap-3">
          <button type="button" class="px-5 py-2 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition" @click="fenetre = null">Annuler</button>
          <button type="button" :disabled="!peutConfirmer"
                  class="px-5 py-2 rounded-lg bg-blue-ycube text-white font-semibold hover:bg-blue-900 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  @click="confirmer">Enregistrer</button>
        </div>
      </div>
    </div>
  </div>
</template>
