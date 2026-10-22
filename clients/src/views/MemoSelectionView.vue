<script setup>
// Mémo de sélection — sous-lot a (docs/PLAN_circularisation.md), maquette
// 3_Memo_selection. Aperçu à l'écran du contenu calculé par le serveur ; figé à
// la soumission ; le Manager valide ou demande une correction (aucun contrôle
// de rôle, faute d'authentification : TODO(décision)).
// Le mémo s'affiche seul, sur toute la largeur ; les actions passent par une
// barre sous le titre et des fenêtres centrées (FenetreCentree, comme
// « Commenter » sur Fiabilité IPE).
// Téléchargement PDF / Word : en attente du choix des bibliothèques de
// génération (PLAN_circularisation §5, question transverse 3).
import { computed, onMounted, ref } from 'vue'
import {
  lireMemo, lireCircularisation, soumettreMemo, validerMemo, demanderCorrectionMemo,
} from '@/api/circularisation.api'
import { useNotyf } from '@/composables/useNotyf'
import { formatDateHeureFr } from '@/utils/formatDate'
import FenetreCentree from '@/components/FenetreCentree.vue'

const props = defineProps({ missionId: String, type: String })
const emit = defineEmits(['retour', 'ouvrir-ecran'])
const notyf = useNotyf()

const LONGUEUR_MIN = 15 // même seuil que circularisation_service.LONGUEUR_MIN_MOTIF
const memo = ref(null)
const selection = ref(null) // état de la sélection (lecture seule) : raison d'un blocage de la soumission
const erreur = ref('')
const commentaire = ref('')
const enCours = ref(false)
// Fenêtre ouverte : 'soumettre' | 'valider' | 'correction' | 'telecharger' | 'etape_suivante' | null
const fenetre = ref(null)
const erreurFenetre = ref('')

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
  try {
    selection.value = (await lireCircularisation(props.missionId)).types.find((t) => t.cle === props.type)?.selection || null
  } catch {
    selection.value = null // la raison de blocage n'est qu'une aide : le serveur reste juge à la soumission
  }
}

function ouvrir(nom) {
  commentaire.value = ''
  erreurFenetre.value = ''
  fenetre.value = nom
}

function fermer() {
  fenetre.value = null
}

async function confirmer() {
  const actions = {
    soumettre: [() => soumettreMemo(props.missionId, props.type, utilisateurConnecte()), 'Mémo soumis pour revue'],
    valider: [() => validerMemo(props.missionId, props.type, commentaire.value.trim(), utilisateurConnecte()), 'Mémo validé'],
    correction: [() => demanderCorrectionMemo(props.missionId, props.type, commentaire.value.trim(), utilisateurConnecte()), 'Correction demandée'],
  }
  const [action, succes] = actions[fenetre.value]
  enCours.value = true
  erreurFenetre.value = ''
  try {
    await action()
    notyf.trigger(succes, 'success')
    fenetre.value = null
    await charger()
  } catch (e) {
    erreurFenetre.value = e.message
  } finally {
    enCours.value = false
  }
}

function etapeSuivante() {
  if (statut.value === 'valide') emit('ouvrir-ecran', 'courriers')
  else ouvrir('etape_suivante')
}

function allerAuxCourriers() {
  fenetre.value = null
  emit('ouvrir-ecran', 'courriers')
}

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

const FENETRES_CIRCUIT = {
  soumettre: { titre: 'Soumettre pour revue', confirmer: 'Confirmer la soumission', commentaire: false,
    explication: 'Le mémo et la sélection seront figés. Le Manager validera ou demandera une correction.' },
  valider: { titre: 'Valider le mémo', confirmer: 'Confirmer la validation', commentaire: true,
    explication: 'La sélection sera validée. Le mémo reste figé dans cette version.' },
  correction: { titre: 'Demander une correction', confirmer: 'Confirmer la demande de correction', commentaire: true,
    explication: 'La sélection redevient modifiable par l’auditeur ; une nouvelle version du mémo sera soumise.' },
}
const circuit = computed(() => FENETRES_CIRCUIT[fenetre.value] || null)

// Raison d'un blocage, affichée avant la confirmation (le serveur reste juge).
const raisonBlocage = computed(() => {
  if (!circuit.value) return ''
  if (!utilisateurConnecte()) return 'Utilisateur non identifié : reconnectez-vous puis réessayez.'
  if (fenetre.value === 'soumettre' && selection.value?.a_refaire) return selection.value.a_refaire
  return ''
})
const peutConfirmer = computed(() => !enCours.value && !raisonBlocage.value
  && (!circuit.value?.commentaire || commentaire.value.trim().length >= LONGUEUR_MIN))

// Téléchargements : indisponibles, chacun avec sa raison (PLAN_circularisation §5).
const TELECHARGEMENTS = [
  { libelle: 'PDF', raison: 'Bibliothèque de génération PDF à valider avec la personne qui gère le serveur.' },
  { libelle: 'Word', raison: 'Bibliothèque de génération Word à valider avec la personne qui gère le serveur.' },
  { libelle: 'Verser au dossier de travail', raison: 'Le dossier de travail n’existe pas encore dans l’outil : à définir.' },
]

// Version du mémo affichée : celle soumise ou validée, sinon la prochaine soumission.
const versionAffichee = computed(() => {
  if (!doc.value) return 1
  return statut.value === 'soumis' || statut.value === 'valide' ? doc.value.version : doc.value.version + 1
})
const majuscule = (texte) => (texte ? texte.charAt(0).toUpperCase() + texte.slice(1) : '—')
const formatJour = (iso) => {
  if (!iso) return '—'
  const d = new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString('fr-FR')
}
const formatEntier = (v) => (v === null || v === undefined ? '—' : new Intl.NumberFormat('fr-FR').format(Math.round(v)))
const formatTaux = (v) => (v === null || v === undefined ? '—' : `${v.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} %`)

onMounted(charger)

const BOUTON_PRIMAIRE = 'h-11 px-5 rounded-[10px] bg-blue-ycube text-white font-bold hover:bg-blue-900 transition disabled:opacity-50 disabled:cursor-not-allowed'
const BOUTON_VALIDER = 'h-11 px-5 rounded-[10px] bg-green-ycube-2 text-white font-bold hover:bg-green-ycube transition disabled:opacity-50 disabled:cursor-not-allowed'
const BOUTON_SECONDAIRE = 'h-11 px-5 rounded-[10px] border border-blue-ycube bg-white text-blue-ycube font-bold hover:bg-blue-ycube hover:text-white transition disabled:opacity-50 disabled:cursor-not-allowed'
const BOUTON_ANNULER = 'h-11 px-5 rounded-[10px] border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition'
</script>

<template>
  <!-- Disposition de la maquette docs/maquettes/3_Memo_selection.html (mémo seul, actions en barre et en
       fenêtres centrées) ; couleurs et police de la charte. -->
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
            {{ c.type_tiers }} · version {{ versionAffichee }} · à verser au dossier
          </p>
        </div>
        <span v-if="statut" :class="['px-3.5 py-1.5 rounded-full text-sm font-bold', STATUTS[statut].classe]">{{ STATUTS[statut].libelle }}</span>
      </section>

      <!-- Barre d'actions -->
      <section v-if="c" aria-label="Actions du mémo" class="bg-white rounded-[14px] shadow px-7 py-4 flex items-center gap-3 flex-wrap">
        <button v-if="statut === 'brouillon' || statut === 'correction_demandee'" type="button" :class="BOUTON_PRIMAIRE" @click="ouvrir('soumettre')">
          Soumettre pour revue
        </button>
        <template v-if="statut === 'soumis'">
          <button type="button" :class="BOUTON_VALIDER" @click="ouvrir('valider')">Valider</button>
          <button type="button" :class="BOUTON_SECONDAIRE" @click="ouvrir('correction')">Demander une correction</button>
        </template>
        <span v-if="statut === 'valide'" class="text-sm text-green-700 font-semibold">
          Validé par {{ doc.decision.utilisateur_id }} le {{ formatDateHeureFr(doc.decision.horodatage) }}
        </span>
        <span v-if="statut === 'correction_demandee'" class="text-sm text-orange-700">
          Correction demandée par {{ doc.decision.utilisateur_id }} : « {{ doc.decision.commentaire }} »
        </span>
        <div class="ml-auto flex gap-3 flex-wrap">
          <button type="button" :class="BOUTON_SECONDAIRE" @click="ouvrir('telecharger')">Télécharger</button>
          <button type="button" :class="BOUTON_SECONDAIRE" @click="etapeSuivante">Étape suivante : courriers</button>
        </div>
      </section>

      <p v-if="erreur" class="m-0 px-4 py-3 rounded-[10px] bg-red-100 text-red-700 text-sm">{{ erreur }}</p>

      <!-- Aperçu du mémo : seul, sur toute la largeur utile -->
      <article v-if="c" aria-label="Aperçu du mémo"
               class="w-full bg-white rounded-md shadow px-16 py-14 flex flex-col gap-[22px] text-[15px] leading-[1.55]">
        <div class="flex justify-between items-start gap-4 border-b-[3px] border-green-ycube-2 pb-4">
          <div>
            <div class="text-[26px] font-extrabold text-blue-ycube">Y<span class="text-green-ycube-2">3</span> Audit &amp; Conseils</div>
            <div class="text-sm text-gray-500">Mémo de sélection des tiers à circulariser</div>
          </div>
          <!-- SYSCOHADA (AUDCIF) : l'exercice couvre l'année civile, clos le 31 décembre. -->
          <div class="text-right text-sm text-gray-700">Exercice clos le 31/12/{{ c.exercice || '—' }}</div>
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
            <span :title="c.population.nom_fichier">{{ majuscule(c.population.libelle_fichier) }}</span>, version {{ c.population.version }}<template
              v-if="c.population.date_import">, importée le {{ formatJour(c.population.date_import) }}</template> :
            {{ c.population.nb_tiers }} compte{{ c.population.nb_tiers > 1 ? 's' : '' }}.
            Fiabilité IPE : {{ LIBELLES_IPE[c.ipe?.statut_affiche] || c.ipe?.statut_affiche || '—' }}.
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
            <span :title="d.libelle">{{ d.numero }}</span> {{ d.retenu ? 'ajouté' : 'exclu' }} par {{ d.utilisateur_id }}
            le {{ formatJour(d.horodatage) }} : {{ d.motif }}.
          </p>
        </section>
        <section class="grid grid-cols-2 gap-4 mt-3">
          <div class="border-t border-gray-300 pt-2.5 text-sm">
            <strong>Préparé par</strong><br />
            <template v-if="statut === 'soumis' || statut === 'valide'">{{ doc.soumis_par }}<br />{{ formatJour(doc.soumis_le) }}</template>
            <template v-else>{{ utilisateurConnecte() || '—' }}<br />—</template>
          </div>
          <div class="border-t border-gray-300 pt-2.5 text-sm">
            <strong>Revu par</strong><br />
            <template v-if="statut === 'valide'">{{ doc.decision.utilisateur_id }}<br />{{ formatJour(doc.decision.horodatage) }}</template>
            <template v-else>—<br />—</template>
          </div>
        </section>
      </article>
    </div>

    <!-- a) Circuit : soumission, validation, demande de correction -->
    <FenetreCentree v-if="circuit" :titre="circuit.titre" :sous-titre="`${c?.type_tiers} · mémo version ${versionAffichee}`"
                    largeur="max-w-xl" @fermer="fermer">
      <p class="m-0 text-sm">
        Statut du mémo :
        <span :class="['px-3 py-1 rounded-full text-xs font-semibold', STATUTS[statut]?.classe]">{{ STATUTS[statut]?.libelle }}</span>
      </p>
      <p class="m-0 text-sm text-gray-700">{{ circuit.explication }}</p>
      <p v-if="raisonBlocage" class="m-0 px-3.5 py-3 rounded-[10px] bg-orange-100 text-orange-700 text-sm">{{ raisonBlocage }}</p>
      <label v-if="circuit.commentaire" class="flex flex-col gap-1.5 text-sm font-semibold">Commentaire
        <textarea v-model="commentaire" rows="3" :placeholder="`Au moins ${LONGUEUR_MIN} caractères`"
                  class="px-3 py-2 text-[15px] font-normal border border-gray-300 rounded-[10px] focus:outline-none focus:ring-2 focus:ring-blue-ycube"></textarea>
        <span class="text-xs font-normal text-gray-500">{{ commentaire.trim().length }} / {{ LONGUEUR_MIN }} caractères minimum</span>
      </label>
      <p v-if="erreurFenetre" class="m-0 px-3.5 py-3 rounded-[10px] bg-red-100 text-red-700 text-sm">{{ erreurFenetre }}</p>
      <div class="flex justify-end gap-3">
        <button type="button" :class="BOUTON_ANNULER" @click="fermer">Annuler</button>
        <button type="button" :class="fenetre === 'valider' ? BOUTON_VALIDER : BOUTON_PRIMAIRE" :disabled="!peutConfirmer" @click="confirmer">
          {{ circuit.confirmer }}
        </button>
      </div>
    </FenetreCentree>

    <!-- b) Télécharger : formats indisponibles, chacun avec sa raison -->
    <FenetreCentree v-if="fenetre === 'telecharger'" titre="Télécharger le mémo" :sous-titre="`${c?.type_tiers} · mémo version ${versionAffichee}`"
                    largeur="max-w-xl" @fermer="fermer">
      <div v-for="t in TELECHARGEMENTS" :key="t.libelle" class="flex flex-col gap-1">
        <button type="button" disabled :class="[BOUTON_SECONDAIRE, 'w-full']">{{ t.libelle }}</button>
        <span class="text-[13px] text-gray-500">{{ t.raison }}</span>
      </div>
    </FenetreCentree>

    <!-- c) Étape suivante : mémo non validé -->
    <FenetreCentree v-if="fenetre === 'etape_suivante'" titre="Mémo non validé" largeur="max-w-md" @fermer="fermer">
      <p class="m-0 text-sm text-gray-700">
        Le mémo est au statut « {{ STATUTS[statut]?.libelle }} ». Les courriers peuvent être préparés, mais la sélection
        peut encore changer tant que le mémo n'est pas validé.
      </p>
      <div class="flex justify-end gap-3">
        <button type="button" :class="BOUTON_ANNULER" @click="fermer">Annuler</button>
        <button type="button" :class="BOUTON_PRIMAIRE" @click="allerAuxCourriers">Y aller quand même</button>
      </div>
    </FenetreCentree>
  </div>
</template>
