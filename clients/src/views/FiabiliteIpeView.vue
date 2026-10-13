<script setup>
// Écran dédié au rapprochement IPE (Module 1, CAC-IPE-01) d'une mission —
// voir docs/PLAN_verrou_IPE.md §4/§5. Séparé de FichiersComplementairesView.vue
// (qui ne garde que l'import/consultation/remplacement des fichiers) pour ne
// plus confondre les deux entrées de la barre latérale de GroupingAnalyse.vue.
// N'est PAS une étape d'audit : volontairement absent de la barre de
// progression des 11 étapes (voir l'indicateur "Fiabilité IPE" de la barre
// latérale, qui renvoie ici pour le détail).
import { ref, onMounted, computed } from 'vue'
import router from '@/router'
import { useNotyf } from '@/composables/useNotyf'
import {
  obtenirEtatIpe,
  evaluerIpe,
  validerFiabiliteIpe,
} from '@/api/ipe.api'

const props = defineProps(['missionId'])
const notyf = useNotyf()

const LIBELLES_MODULE = {
  ipe_1_clients: 'IPE-1 — Clients (compte 411)',
  ipe_2_fournisseurs: 'IPE-2 — Fournisseurs (comptes 40x)',
  ipe_3_immobilisations: 'IPE-3 — Immobilisations (comptes 2xxx)',
}

const IPE_STATUT_LABELS = {
  anterieure_au_verrou: 'Antérieure au verrou',
  non_commence: 'Non commencé',
  en_cours: 'En cours',
  valide: 'Validé',
}

// 3 statuts visuels distincts (module ou ligne de collectif) — le rouge est
// réservé aux vrais écarts, jamais à "rien à comparer" (fichier absent,
// aucun collectif trouvé). Mêmes couleurs que les badges de statut de
// mission (MissionsView.vue) — charte d'interface, CLAUDE.md.
const STATUT_MODULE_INFO = {
  ok: { label: 'OK', classe: 'bg-green-100 text-green-700' },
  ecart: { label: 'Écart', classe: 'bg-red-100 text-red-700' },
  non_evaluable: { label: 'Non évaluable', classe: 'bg-gray-100 text-gray-700' },
}

// "Validation manager" renommé en "Validation" tant que le rôle de qui
// valide n'est pas vérifié (aucun contrôle d'accès sur les missions
// aujourd'hui — CLAUDE.md, point de sécurité connu).
const ACTION_HISTORIQUE_LABELS = {
  evaluation: 'Rapprochement lancé',
  validation_manager: 'Validation',
  invalidation_automatique: 'Invalidation automatique (fichier remplacé)',
  invalidation_detectee_a_la_lecture: 'Invalidation détectée (fichier modifié)',
}

// Colonne "Résultat" de l'historique : validé / invalidé / rapprochement /
// invalidation automatique — distinct de la colonne "Action" ci-dessus.
function resultatHistorique(entree) {
  if (entree.action === 'evaluation') return 'Rapprochement'
  if (entree.action === 'validation_manager') return entree.resultat?.validee ? 'Validé' : 'Invalidé'
  if (entree.action === 'invalidation_automatique' || entree.action === 'invalidation_detectee_a_la_lecture') {
    return 'Invalidation automatique'
  }
  return '—'
}

// Ordre d'affichage fixe pour la synthèse (IPE-1 puis IPE-2 puis IPE-3),
// quel que soit l'ordre des clés dans la réponse API.
const ORDRE_MODULES = ['ipe_1_clients', 'ipe_2_fournisseurs', 'ipe_3_immobilisations']

// Longueur minimale du commentaire de validation/invalidation — même règle
// que le backend (api/src/schemas/ipe_schemas.py), vérifiée ici aussi pour
// un message immédiat sans aller-retour serveur.
const LONGUEUR_MIN_COMMENTAIRE = 15

// Utilisateur connecté, tel qu'enregistré côté frontend (sessionStorage,
// même convention que clients/src/utils/uploadFile.js) : aucune
// authentification sur les missions aujourd'hui (CLAUDE.md), donc "non
// identifié" si absent — jamais inventé.
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

const ipeEtat = ref(null)
const ipeEvaluationEnCours = ref(false)
const ipeValidationEnCours = ref(false)

// Confirmation obligatoire avant validation ET avant invalidation, avec un
// commentaire obligatoire d'au moins LONGUEUR_MIN_COMMENTAIRE caractères
// dans les deux cas, enregistré dans l'historique.
const confirmationValidationOuverte = ref(false)
const commentaireValidation = ref('')
const confirmationInvalidationOuverte = ref(false)
const commentaireInvalidation = ref('')

onMounted(async () => {
  await chargerEtatIpe()
})

async function chargerEtatIpe() {
  try {
    ipeEtat.value = await obtenirEtatIpe(props.missionId)
  } catch (e) {
    notyf.trigger(e.message || "Erreur lors du chargement de l'état IPE", 'error')
  }
}

async function lancerEvaluationIpe() {
  ipeEvaluationEnCours.value = true
  try {
    ipeEtat.value = await evaluerIpe(props.missionId)
    notyf.trigger('Rapprochement IPE effectué', 'success')
  } catch (e) {
    notyf.trigger(e.message || 'Erreur lors du rapprochement IPE', 'error')
  } finally {
    ipeEvaluationEnCours.value = false
  }
}

// Synthèse en haut d'écran : une ligne par module, dans l'ordre fixe
// ORDRE_MODULES, même avant toute évaluation (statut/écart à null).
const syntheseModules = computed(() => {
  const modules = ipeEtat.value?.modules || {}
  return ORDRE_MODULES.map((cle) => ({
    cle,
    libelle: LIBELLES_MODULE[cle] || cle,
    statut: modules[cle]?.statut || null,
    ecartGlobal: modules[cle]?.derniere_evaluation?.ecart_global ?? null,
  }))
})

// Un module "en écart non qualifié" bloque la validation : écart réel
// (jamais "non_evaluable") sans étiquette de qualification renseignée.
const moduleEnEcartNonQualifie = computed(() => {
  const modules = ipeEtat.value?.modules
  if (!modules) return false
  return Object.values(modules).some(
    (m) => m.statut === 'ecart' && !m.derniere_evaluation?.qualification?.etiquette
  )
})

// Historique le plus récent en premier (le backend pousse en ordre chronologique).
const historiqueRecent = computed(() => {
  return [...(ipeEtat.value?.historique || [])].reverse()
})

function ouvrirConfirmationValidation() {
  if (moduleEnEcartNonQualifie.value) return
  commentaireValidation.value = ''
  confirmationValidationOuverte.value = true
}

function annulerValidation() {
  confirmationValidationOuverte.value = false
}

async function confirmerValidation() {
  // Garde contre le double clic : refus synchrone, avant même la mise à
  // jour réactive de :disabled (docs/PLAN_verrou_IPE.md).
  if (ipeValidationEnCours.value) return

  const commentaire = commentaireValidation.value.trim()
  if (commentaire.length < LONGUEUR_MIN_COMMENTAIRE) {
    notyf.trigger(
      `Le commentaire est obligatoire et doit contenir au moins ${LONGUEUR_MIN_COMMENTAIRE} caractères (${commentaire.length} actuellement).`,
      'warning'
    )
    return
  }

  ipeValidationEnCours.value = true
  try {
    ipeEtat.value = await validerFiabiliteIpe(props.missionId, true, commentaire, utilisateurConnecte())
    notyf.trigger('Fiabilité IPE validée', 'success')
    confirmationValidationOuverte.value = false
  } catch (e) {
    notyf.trigger(e.message || 'Erreur lors de la validation', 'error')
  } finally {
    ipeValidationEnCours.value = false
  }
}

function ouvrirConfirmationInvalidation() {
  commentaireInvalidation.value = ''
  confirmationInvalidationOuverte.value = true
}

function annulerInvalidation() {
  confirmationInvalidationOuverte.value = false
}

async function confirmerInvalidation() {
  // Garde contre le double clic : refus synchrone, avant même la mise à
  // jour réactive de :disabled (docs/PLAN_verrou_IPE.md).
  if (ipeValidationEnCours.value) return

  const commentaire = commentaireInvalidation.value.trim()
  if (commentaire.length < LONGUEUR_MIN_COMMENTAIRE) {
    notyf.trigger(
      `Le commentaire est obligatoire et doit contenir au moins ${LONGUEUR_MIN_COMMENTAIRE} caractères (${commentaire.length} actuellement).`,
      'warning'
    )
    return
  }

  ipeValidationEnCours.value = true
  try {
    ipeEtat.value = await validerFiabiliteIpe(props.missionId, false, commentaire, utilisateurConnecte())
    notyf.trigger('Fiabilité IPE invalidée', 'success')
    confirmationInvalidationOuverte.value = false
  } catch (e) {
    notyf.trigger(e.message || "Erreur lors de l'invalidation", 'error')
  } finally {
    ipeValidationEnCours.value = false
  }
}

// Séparateur de milliers + sens explicite (D/C) plutôt qu'un signe moins —
// même convention que le calcul (solde_reel = débit - crédit) : positif =
// débiteur (D), négatif = créditeur (C).
function formatMontant(valeur) {
  if (valeur === null || valeur === undefined) return '—'
  const entier = Math.round(valeur)
  const formate = new Intl.NumberFormat('fr-FR').format(Math.abs(entier))
  if (entier === 0) return formate
  return `${formate} ${entier < 0 ? 'C' : 'D'}`
}

function formatHorodatage(iso) {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleString('fr-FR')
}

function back() {
  router.back()
}
</script>

<template>
  <div class="h-full w-full overflow-y-auto bg-[#f5f7fa]">
    <!-- En-tête de page — même recette que ClientSpace.vue (charte d'interface, CLAUDE.md) -->
    <div class="bg-white shadow-sm px-6 py-4 flex items-center justify-between">
      <button class="text-blue-ycube font-semibold hover:underline flex items-center gap-2" @click="back">
        <i class="fa-solid fa-arrow-left"></i> Retour
      </button>
      <div class="text-center">
        <h1 class="text-xl font-bold text-blue-ycube">Fiabilité IPE</h1>
        <p class="text-sm text-gray-500">Rapprochement IPE-1/2/3, qualification, validation et historique</p>
      </div>
      <div class="w-20"></div>
    </div>

    <div class="p-6 flex flex-col gap-6">

      <!-- Rapprochement IPE (Module 1, CAC-IPE-01) — docs/PLAN_verrou_IPE.md §4/§5. -->
      <div class="bg-white rounded-xl shadow p-6 flex flex-col gap-4 w-full" v-if="ipeEtat">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <h2 class="font-bold text-sm uppercase text-blue-ycube">Rapprochement IPE</h2>
          <span class="text-xs font-semibold px-3 py-1 rounded-full bg-gray-100 text-gray-700">
            {{ IPE_STATUT_LABELS[ipeEtat.statut_affiche] || 'Non commencé' }}
          </span>
        </div>

        <p v-if="!ipeEtat.verrou_applicable" class="text-xs text-gray-500 italic">
          Mission antérieure à l'activation du verrou IPE : jamais bloquée, ce rapprochement reste informatif.
        </p>

        <!-- Synthèse : une ligne par module, statut + écart global.
             Tableau à en-tête bleu marine (ClientSpace.vue) — charte CLAUDE.md. -->
        <table class="min-w-full text-sm">
          <thead class="bg-blue-ycube text-white h-12 text-left">
            <tr>
              <th class="px-3">Module</th>
              <th class="px-3">Statut</th>
              <th class="px-3 text-right">Écart global</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ligne in syntheseModules" :key="ligne.cle" class="h-12 border-b">
              <td class="px-3">{{ ligne.libelle }}</td>
              <td class="px-3">
                <span
                  class="px-3 py-1 rounded-full text-xs font-semibold"
                  :class="ligne.statut ? STATUT_MODULE_INFO[ligne.statut]?.classe : 'bg-gray-100 text-gray-700'"
                >
                  {{ ligne.statut ? STATUT_MODULE_INFO[ligne.statut]?.label : 'Non évalué' }}
                </span>
              </td>
              <td class="px-3 text-right font-mono">{{ formatMontant(ligne.ecartGlobal) }}</td>
            </tr>
          </tbody>
        </table>

        <!-- Boutons : primaire plein (recette ClientSpace.vue), secondaire en contour — charte CLAUDE.md -->
        <div class="flex flex-wrap items-center gap-3">
          <button
            class="px-5 py-2 rounded-lg bg-blue-ycube text-white font-semibold hover:bg-blue-900 transition disabled:opacity-50"
            :disabled="ipeEvaluationEnCours"
            @click="lancerEvaluationIpe"
          >
            {{ ipeEvaluationEnCours ? 'Rapprochement en cours...' : 'Lancer le rapprochement IPE-1/2/3' }}
          </button>

          <!-- Bouton principal : désactivé tant qu'un module est en écart non qualifié -->
          <button
            class="px-5 py-2 rounded-lg bg-green-ycube-2 text-white font-semibold hover:bg-green-ycube transition disabled:opacity-40 disabled:cursor-not-allowed"
            :disabled="ipeValidationEnCours || moduleEnEcartNonQualifie"
            :title="moduleEnEcartNonQualifie ? 'Qualifiez les écarts avant de valider (voir les modules en écart ci-dessous)' : ''"
            @click="ouvrirConfirmationValidation"
          >
            Valider la fiabilité IPE
          </button>

          <!-- Bouton secondaire, volontairement moins mis en avant -->
          <button
            class="px-5 py-2 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition disabled:opacity-40"
            :disabled="ipeValidationEnCours"
            @click="ouvrirConfirmationInvalidation"
          >
            Invalider
          </button>
        </div>
        <p v-if="moduleEnEcartNonQualifie" class="text-xs text-gray-500 italic">
          Un ou plusieurs modules sont en écart non qualifié : la validation est désactivée tant qu'ils ne sont pas qualifiés (TODO(spec: CAC-IPE-01) — valeurs de qualification non confirmées).
        </p>
        <!-- Validation enregistrée sans contrôle de rôle : aucun système
             d'authentification/droits n'existe sur les missions aujourd'hui
             (CLAUDE.md, point de sécurité connu). -->

        <!-- Confirmation de validation (commentaire obligatoire, enregistré dans l'historique) -->
        <div v-if="confirmationValidationOuverte" class="border border-green-ycube/40 bg-green-50 rounded-lg p-4 flex flex-col gap-2">
          <p class="text-sm font-semibold text-green-ycube">Confirmer la validation de la fiabilité IPE</p>
          <textarea
            v-model="commentaireValidation"
            rows="2"
            class="text-sm border border-gray-300 rounded-lg p-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-ycube"
            placeholder="Commentaire (obligatoire, enregistré dans l'historique)"
          ></textarea>
          <div class="flex gap-3">
            <button
              class="px-5 py-2 rounded-lg bg-green-ycube-2 text-white font-semibold hover:bg-green-ycube transition disabled:opacity-50"
              :disabled="ipeValidationEnCours"
              @click="confirmerValidation"
            >
              Confirmer
            </button>
            <button class="px-5 py-2 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition" @click="annulerValidation">
              Annuler
            </button>
          </div>
        </div>

        <!-- Confirmation d'invalidation (commentaire obligatoire, enregistré dans l'historique) -->
        <div v-if="confirmationInvalidationOuverte" class="border border-gray-300 bg-gray-50 rounded-lg p-4 flex flex-col gap-2">
          <p class="text-sm font-semibold text-gray-700">Confirmer l'invalidation de la fiabilité IPE ?</p>
          <textarea
            v-model="commentaireInvalidation"
            rows="2"
            class="text-sm border border-gray-300 rounded-lg p-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-ycube"
            placeholder="Commentaire (obligatoire, enregistré dans l'historique)"
          ></textarea>
          <div class="flex gap-3">
            <button
              class="px-5 py-2 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition disabled:opacity-50"
              :disabled="ipeValidationEnCours"
              @click="confirmerInvalidation"
            >
              Confirmer
            </button>
            <button class="px-5 py-2 rounded-lg text-gray-600 hover:bg-gray-100 transition" @click="annulerInvalidation">
              Annuler
            </button>
          </div>
        </div>

        <div v-if="ipeEtat.modules && Object.keys(ipeEtat.modules).length" class="flex flex-col gap-4 mt-2">
          <div v-for="(module, cle) in ipeEtat.modules" :key="cle" class="border border-gray-200 rounded-lg p-4 text-sm">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-gray-800">{{ LIBELLES_MODULE[cle] || cle }}</span>
              <span
                class="px-3 py-1 rounded-full text-xs font-semibold"
                :class="STATUT_MODULE_INFO[module.statut]?.classe || 'bg-gray-100 text-gray-700'"
              >
                {{ STATUT_MODULE_INFO[module.statut]?.label || module.statut }}
              </span>
            </div>

            <div v-if="module.derniere_evaluation" class="mt-3 flex flex-col gap-3 text-gray-600">
              <p v-if="module.statut === 'non_evaluable'" class="italic text-gray-500">
                Non évaluable — {{ module.derniere_evaluation.motif_non_evaluable === 'fichier_complementaire_absent'
                  ? 'aucun fichier complémentaire actif pour ce module.'
                  : 'aucun compte collectif trouvé dans la balance générale pour ce module.' }}
              </p>
              <p v-else class="text-sm">Écart global : <span class="font-mono font-semibold text-gray-800">{{ formatMontant(module.derniere_evaluation.ecart_global) }}</span></p>

              <table v-if="module.derniere_evaluation.detail_collectifs?.length" class="min-w-full text-sm">
                <thead class="bg-blue-ycube text-white h-12 text-left">
                  <tr>
                    <th class="px-3">Compte collectif</th>
                    <th class="px-3 text-right">Solde balance générale</th>
                    <th class="px-3 text-right">Solde auxiliaire</th>
                    <th class="px-3 text-right">Tiers rattachés</th>
                    <th class="px-3 text-right">Écart</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="c in module.derniere_evaluation.detail_collectifs"
                    :key="c.numero_compte"
                    class="h-12 border-b"
                    :class="module.statut !== 'ecart' ? 'text-gray-500' : (c.ok ? 'text-green-700' : 'text-red-700')"
                  >
                    <td class="px-3">{{ c.numero_compte }}</td>
                    <td class="px-3 text-right font-mono">{{ formatMontant(c.solde_balance_generale) }}</td>
                    <td class="px-3 text-right font-mono">{{ formatMontant(c.solde_auxiliaire) }}</td>
                    <td class="px-3 text-right">{{ c.nb_tiers_rattaches }}</td>
                    <td class="px-3 text-right font-mono">{{ formatMontant(c.ecart) }}</td>
                  </tr>
                </tbody>
              </table>
              <p v-else-if="module.statut !== 'non_evaluable'" class="italic">Aucun compte collectif trouvé dans la balance générale pour ce module.</p>

              <p v-if="module.derniere_evaluation.tiers_orphelins?.balance_generale_seulement?.length" class="text-gray-500 text-sm">
                Comptes collectifs sans tiers rattaché dans l'auxiliaire (TODO(spec: CAC-IPE-01) — traitement attendu non confirmé) :
                {{ module.derniere_evaluation.tiers_orphelins.balance_generale_seulement.join(', ') }}
              </p>
              <p v-if="module.derniere_evaluation.tiers_orphelins?.auxiliaire_seulement?.length" class="text-gray-500 text-sm">
                Tiers de l'auxiliaire sans compte collectif correspondant (TODO(spec: CAC-IPE-01) — traitement attendu non confirmé) :
                {{ module.derniere_evaluation.tiers_orphelins.auxiliaire_seulement.join(', ') }}
              </p>
              <p v-if="module.derniere_evaluation.lignes_non_calculables?.length" class="text-orange-600 text-sm">
                {{ module.derniere_evaluation.lignes_non_calculables.length }} ligne(s) auxiliaire(s) sans montant exploitable (mapping incomplet).
              </p>
            </div>
          </div>
        </div>
        <p v-else class="text-sm text-gray-500 italic">
          Aucune évaluation IPE encore lancée pour cette mission.
        </p>
      </div>

      <!-- Historique — toutes les actions enregistrées sur Mission1.ipe.historique -->
      <div class="bg-white rounded-xl shadow p-6 flex flex-col gap-4 w-full" v-if="ipeEtat">
        <h2 class="font-bold text-sm uppercase text-blue-ycube">Historique</h2>

        <p v-if="!historiqueRecent.length" class="text-sm text-gray-500 italic">
          Aucune action enregistrée pour le moment.
        </p>

        <table v-else class="min-w-full text-sm">
          <thead class="bg-blue-ycube text-white h-12 text-left">
            <tr>
              <th class="px-3">Date</th>
              <th class="px-3">Action</th>
              <th class="px-3">Utilisateur</th>
              <th class="px-3">Résultat</th>
              <th class="px-3">Commentaire</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entree, i) in historiqueRecent" :key="i" class="h-12 border-b align-top">
              <td class="px-3 py-2 whitespace-nowrap">{{ formatHorodatage(entree.horodatage) }}</td>
              <td class="px-3 py-2">{{ ACTION_HISTORIQUE_LABELS[entree.action] || entree.action }}</td>
              <td class="px-3 py-2">{{ entree.utilisateur_id || 'Non identifié' }}</td>
              <td class="px-3 py-2">{{ resultatHistorique(entree) }}</td>
              <td class="px-3 py-2 text-gray-600">{{ entree.commentaire || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  </div>
</template>
