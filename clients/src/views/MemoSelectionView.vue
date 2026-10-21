<script setup>
// Mémo de sélection — sous-lot a (docs/PLAN_circularisation.md), maquette
// 3_Memo_selection. Aperçu à l'écran du contenu calculé par le serveur ; figé à
// la soumission ; le Manager valide ou demande une correction (aucun contrôle
// de rôle, faute d'authentification : TODO(décision)).
// Téléchargement PDF / Word : en attente du choix des bibliothèques de
// génération (PLAN_circularisation §5, question transverse 3).
import { computed, onMounted, ref } from 'vue'
import { lireMemo, soumettreMemo, validerMemo, demanderCorrectionMemo } from '@/api/circularisation.api'
import { useNotyf } from '@/composables/useNotyf'
import { formatDateHeureFr } from '@/utils/formatDate'

const props = defineProps({ missionId: String, type: String })
const emit = defineEmits(['retour', 'ouvrir-ecran'])
const notyf = useNotyf()

const LONGUEUR_MIN = 15 // même seuil que circularisation_service.LONGUEUR_MIN_MOTIF
const memo = ref(null)
const erreur = ref('')
const commentaire = ref('')
const enCours = ref(false)

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
    memo.value = await lireMemo(props.missionId, props.type)
    erreur.value = ''
  } catch (e) {
    erreur.value = e.message
  }
}

async function agir(action, succes) {
  enCours.value = true
  try {
    await action()
    notyf.trigger(succes, 'success')
    commentaire.value = ''
    await charger()
  } catch (e) {
    notyf.trigger(e.message, 'error')
  } finally {
    enCours.value = false
  }
}

const soumettre = () => agir(() => soumettreMemo(props.missionId, props.type, utilisateurConnecte()), 'Mémo soumis pour revue')
const valider = () => agir(() => validerMemo(props.missionId, props.type, commentaire.value.trim(), utilisateurConnecte()), 'Mémo validé')
const demanderCorrection = () => agir(
  () => demanderCorrectionMemo(props.missionId, props.type, commentaire.value.trim(), utilisateurConnecte()), 'Correction demandée')

const c = computed(() => memo.value?.contenu || null)
const doc = computed(() => memo.value?.memo || null)
// Statut affiché : brouillon (jamais soumis ou correction demandée), soumis, validé.
const statut = computed(() => memo.value?.statut === 'brouillon' && doc.value?.statut === 'correction_demandee' ? 'correction_demandee' : memo.value?.statut)
const STATUTS = {
  brouillon: { libelle: 'Brouillon', classe: 'bg-orange-100 text-orange-700' },
  correction_demandee: { libelle: 'Correction demandée', classe: 'bg-orange-100 text-orange-700' },
  soumis: { libelle: 'Soumis pour revue', classe: 'bg-orange-100 text-orange-700' },
  valide: { libelle: 'Validé', classe: 'bg-green-100 text-green-700' },
}
const LIBELLES_IPE = {
  valide: 'validée', anterieure_au_verrou: 'mission antérieure au verrou', non_commence: 'non commencée',
  en_cours: 'en cours, non validée', soumis_pour_revue: 'soumise pour revue, non validée',
  en_attente_correction: 'en attente de correction, non validée',
}

const formatEntier = (v) => (v === null || v === undefined ? '—' : new Intl.NumberFormat('fr-FR').format(Math.round(v)))
const formatTaux = (v) => (v === null || v === undefined ? '—' : `${v.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} %`)

onMounted(charger)

const CARTE_ASIDE = 'bg-white rounded-[14px] shadow px-[22px] py-5 flex flex-col gap-3'
const TITRE_ASIDE = 'm-0 text-[15px] font-bold tracking-[0.3px] uppercase text-blue-ycube'
</script>

<template>
  <!-- Disposition de la maquette docs/maquettes/3_Memo_selection.html ; couleurs et police de la charte. -->
  <div class="h-full w-full overflow-y-auto bg-[#f5f7fa] text-gray-800">
    <div class="p-7 flex flex-col gap-5">

      <!-- En-tête : retour en lien (charte), titre, statut -->
      <section class="bg-white rounded-[14px] shadow px-7 py-5 flex items-center justify-between gap-4 flex-wrap">
        <button type="button" class="min-h-11 text-blue-ycube font-semibold hover:underline flex items-center gap-2" @click="emit('retour')">
          <i class="fa-solid fa-arrow-left"></i> Retour à la sélection
        </button>
        <div class="text-center">
          <h1 class="m-0 text-[26px] font-bold text-blue-ycube">Mémo de sélection</h1>
          <p v-if="c" class="m-0 text-gray-500">
            {{ c.type_tiers }} · {{ doc ? `version ${doc.version}` : 'non encore soumis' }} · à verser au dossier
          </p>
        </div>
        <span v-if="statut" :class="['px-3.5 py-1.5 rounded-full text-sm font-bold', STATUTS[statut].classe]">{{ STATUTS[statut].libelle }}</span>
      </section>

      <p v-if="erreur" class="m-0 px-4 py-3 rounded-[10px] bg-red-100 text-red-700 text-sm">{{ erreur }}</p>

      <div v-if="c" class="flex gap-5 flex-wrap items-start">
        <!-- Aperçu du mémo -->
        <article aria-label="Aperçu du mémo"
                 class="flex-[999_1_640px] min-w-0 max-w-[860px] bg-white rounded-md shadow px-16 py-14 flex flex-col gap-[22px] text-[15px] leading-[1.55]">
          <div class="flex justify-between items-start gap-4 border-b-[3px] border-green-ycube-2 pb-4">
            <div>
              <div class="text-[26px] font-extrabold text-blue-ycube">Y<span class="text-green-ycube-2">3</span> Audit &amp; Conseils</div>
              <div class="text-sm text-gray-500">Mémo de sélection des tiers à circulariser</div>
            </div>
            <div class="text-right text-sm text-gray-700">Exercice {{ c.exercice || '—' }}</div>
          </div>
          <div class="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <div><strong>Entité</strong> · {{ c.entite || '—' }}</div>
            <div><strong>Population</strong> · {{ c.type_tiers }}</div>
            <div><strong>Norme</strong> · {{ c.norme }}</div>
            <div><strong>Mode</strong> · Confirmation {{ c.mode.valeur === 'negatif' ? 'négative' : 'positive' }}</div>
          </div>

          <section class="flex flex-col gap-1.5">
            <h2 class="m-0 text-[17px] font-bold text-blue-ycube">1. Population de départ</h2>
            <p class="m-0">
              <span class="first-letter:uppercase inline-block">{{ c.population.libelle_fichier }}</span>
              ({{ c.population.nom_fichier }}), version {{ c.population.version }}, importée le
              {{ formatDateHeureFr(c.population.date_import) }} : {{ c.population.nb_tiers }} tiers.
              Fiabilité IPE à la constitution de la population : {{ LIBELLES_IPE[c.ipe?.statut_affiche] || c.ipe?.statut_affiche || '—' }}.
            </p>
          </section>
          <section class="flex flex-col gap-1.5">
            <h2 class="m-0 text-[17px] font-bold text-blue-ycube">2. Méthode</h2>
            <p class="m-0">
              {{ c.methode }} : chaque tiers retenu ou exclu l'a été avec un motif (section 4).
              <template v-if="c.mode.valeur === 'negatif'">Confirmation négative décidée par {{ c.mode.utilisateur_id }} : « {{ c.mode.motif }} ».</template>
            </p>
          </section>
          <section class="flex flex-col gap-2.5">
            <h2 class="m-0 text-[17px] font-bold text-blue-ycube">3. Résultat</h2>
            <table class="w-full border-collapse text-sm">
              <tbody>
                <tr class="border-b border-gray-200"><td class="py-2">Tiers sélectionnés</td><td class="py-2 text-right font-bold">{{ c.resultat.nb_retenus }} sur {{ c.resultat.nb_tiers }}</td></tr>
                <tr class="border-b border-gray-200"><td class="py-2">Valeur couverte</td><td class="py-2 text-right font-bold">{{ formatEntier(c.resultat.valeur_couverte) }}</td></tr>
                <tr><td class="py-2">Taux de couverture</td><td class="py-2 text-right font-bold">{{ formatTaux(c.resultat.taux_couverture) }}</td></tr>
              </tbody>
            </table>
          </section>
          <section class="flex flex-col gap-1.5">
            <h2 class="m-0 text-[17px] font-bold text-blue-ycube">4. Ajouts et exclusions manuels</h2>
            <p v-if="!c.decisions.length" class="m-0 text-gray-500">Aucun.</p>
            <p v-for="(d, i) in c.decisions" :key="i" class="m-0">
              {{ d.numero }} {{ d.libelle }} {{ d.retenu ? 'ajouté' : 'exclu' }} par {{ d.utilisateur_id }}
              le {{ formatDateHeureFr(d.horodatage) }} : {{ d.motif }}.
            </p>
          </section>
          <section class="grid grid-cols-2 gap-4 mt-3">
            <div class="border-t border-gray-300 pt-2.5 text-sm">
              <strong>Préparé par</strong><br />
              {{ doc?.soumis_par || '—' }}<br />{{ doc?.soumis_le ? formatDateHeureFr(doc.soumis_le) : '—' }}
            </div>
            <div class="border-t border-gray-300 pt-2.5 text-sm">
              <strong>Revu par</strong><br />
              <template v-if="statut === 'valide'">{{ doc.decision.utilisateur_id }}<br />{{ formatDateHeureFr(doc.decision.horodatage) }}</template>
              <template v-else>—<br />—</template>
            </div>
          </section>
        </article>

        <aside class="flex-[1_1_320px] max-w-[400px] flex flex-col gap-4">
          <section :class="CARTE_ASIDE">
            <h2 :class="TITRE_ASIDE">Validation</h2>
            <p class="m-0 text-sm text-gray-700">Le mémo est figé à la soumission. Le Manager valide ou demande une correction.</p>
            <p v-if="statut === 'correction_demandee'" class="m-0 px-3 py-2 rounded-[10px] bg-orange-100 text-orange-700 text-sm">
              Correction demandée par {{ doc.decision.utilisateur_id }} le {{ formatDateHeureFr(doc.decision.horodatage) }} :
              « {{ doc.decision.commentaire }} »
            </p>
            <button v-if="statut === 'brouillon' || statut === 'correction_demandee'" type="button"
                    class="h-[46px] rounded-[10px] bg-blue-ycube text-white text-[15px] font-bold hover:bg-blue-900 transition disabled:opacity-50"
                    :disabled="enCours" @click="soumettre">
              Soumettre pour revue
            </button>
            <template v-if="statut === 'soumis'">
              <textarea v-model="commentaire" rows="3" :placeholder="`Commentaire du Manager (au moins ${LONGUEUR_MIN} caractères)`"
                        class="px-3 py-2 text-sm border border-gray-300 rounded-[10px] focus:outline-none focus:ring-2 focus:ring-blue-ycube"></textarea>
              <button type="button"
                      class="h-11 rounded-[10px] bg-green-ycube-2 text-white font-bold hover:bg-green-ycube transition disabled:opacity-50 disabled:cursor-not-allowed"
                      :disabled="enCours || commentaire.trim().length < LONGUEUR_MIN" @click="valider">
                Valider le mémo
              </button>
              <button type="button"
                      class="h-11 rounded-[10px] border border-blue-ycube bg-white text-blue-ycube font-bold hover:bg-blue-ycube hover:text-white transition disabled:opacity-50 disabled:cursor-not-allowed"
                      :disabled="enCours || commentaire.trim().length < LONGUEUR_MIN" @click="demanderCorrection">
                Demander une correction
              </button>
            </template>
            <p v-if="statut === 'valide'" class="m-0 px-3 py-2 rounded-[10px] bg-green-100 text-green-700 text-sm">
              Validé par {{ doc.decision.utilisateur_id }} le {{ formatDateHeureFr(doc.decision.horodatage) }} : « {{ doc.decision.commentaire }} »
            </p>
          </section>
          <section :class="CARTE_ASIDE">
            <h2 :class="TITRE_ASIDE">Télécharger</h2>
            <button type="button" disabled class="h-11 rounded-[10px] border border-blue-ycube bg-white text-blue-ycube font-bold opacity-50 cursor-not-allowed">PDF</button>
            <button type="button" disabled class="h-11 rounded-[10px] border border-blue-ycube bg-white text-blue-ycube font-bold opacity-50 cursor-not-allowed">Word</button>
            <button type="button" disabled class="h-11 rounded-[10px] bg-green-ycube-2 text-white font-bold opacity-50 cursor-not-allowed">Verser au dossier de travail</button>
            <span class="text-[13px] text-gray-500">
              PDF et Word : bibliothèques de génération à valider. Dossier de travail : à définir (PLAN_circularisation §5).
            </span>
          </section>
          <section :class="CARTE_ASIDE">
            <h2 :class="TITRE_ASIDE">Étape suivante</h2>
            <span class="font-bold text-gray-400" title="Sous-lot b : modèles et courriers">Préparer les courriers de circularisation · à venir</span>
          </section>
        </aside>
      </div>
    </div>
  </div>
</template>
