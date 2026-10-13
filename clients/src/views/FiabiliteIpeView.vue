<script setup>
// Écran dédié au rapprochement IPE (Module 1, CAC-IPE-01) d'une mission —
// voir docs/PLAN_verrou_IPE.md §4/§5. Séparé de FichiersComplementairesView.vue
// (qui ne garde que l'import/consultation/remplacement des fichiers) pour ne
// plus confondre les deux entrées de la barre latérale de GroupingAnalyse.vue.
// N'est PAS une étape d'audit : volontairement absent de la barre de
// progression des 11 étapes (voir l'indicateur "Fiabilité IPE" de la barre
// latérale, qui renvoie ici pour le détail).
import { ref, onMounted, computed, watch } from 'vue'
import router from '@/router'
import { useNotyf } from '@/composables/useNotyf'
import {
  obtenirEtatIpe,
  evaluerIpe,
  validerFiabiliteIpe,
  soumettrePourRevueIpe,
  demanderCorrectionIpe,
  ajouterRemarqueIpe,
  repondreRemarqueIpe,
  marquerRemarqueTraiteeIpe,
  qualifierEcartIpe,
  justifierNonEvaluableIpe,
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
  soumis_pour_revue: 'Soumis pour revue',
  en_attente_correction: 'En attente de correction',
  valide: 'Validé',
}

// Statuts du circuit de revue (docs/PLAN_verrou_IPE.md) — badge dédié, même
// palette que les statuts de mission (MissionsView.vue) : gris neutre, orange
// en cours de traitement, rouge correction demandée, vert validé.
const STATUT_CIRCUIT_INFO = {
  en_cours: { label: 'En cours', classe: 'bg-gray-100 text-gray-700' },
  soumis_pour_revue: { label: 'Soumis pour revue', classe: 'bg-orange-100 text-orange-700' },
  en_attente_correction: { label: 'En attente de correction', classe: 'bg-red-100 text-red-700' },
  valide: { label: 'Validé', classe: 'bg-green-100 text-green-700' },
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
  soumission_revue: 'Soumission pour revue',
  demande_correction: 'Demande de correction',
  remarque_ajoutee: 'Remarque ajoutée',
  remarque_repondue: 'Réponse à une remarque',
  remarque_traitee: 'Remarque marquée traitée',
  remarque_rouverte: 'Remarque rouverte',
  qualification_ecart: "Qualification d'un écart",
  justification_non_evaluable: 'Justification d\'un module non évaluable',
}

const TYPE_REMARQUE_INFO = {
  information: { label: 'Information', classe: 'bg-gray-100 text-gray-700' },
  demande_correction: { label: 'Demande de correction', classe: 'bg-red-100 text-red-700' },
}

// Colonne "Résultat" de l'historique : validé / invalidé / rapprochement /
// invalidation automatique — distinct de la colonne "Action" ci-dessus.
function resultatHistorique(entree) {
  if (entree.action === 'evaluation') return 'Rapprochement'
  if (entree.action === 'validation_manager') return entree.resultat?.validee ? 'Validé' : 'Invalidé'
  if (entree.action === 'invalidation_automatique' || entree.action === 'invalidation_detectee_a_la_lecture') {
    return 'Invalidation automatique'
  }
  if (entree.action === 'soumission_revue') return 'Soumis pour revue'
  if (entree.action === 'demande_correction') return 'En attente de correction'
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

// Historique le plus récent en premier (le backend pousse en ordre chronologique).
const historiqueRecent = computed(() => {
  return [...(ipeEtat.value?.historique || [])].reverse()
})

/* ================================
   CIRCUIT DE REVUE (docs/PLAN_verrou_IPE.md)
   en_cours -> soumis_pour_revue -> valide
                     ^                |
                     |                v (invalider repasse à en_cours)
             en_attente_correction <--+ (demande de correction manager)
================================ */

const statutCircuit = computed(() => ipeEtat.value?.statut_circuit || 'en_cours')

// Causes d'écart : liste provisoire renvoyée par le backend
// (revue_ipe_service.CAUSES_ECART, TODO(spec: CAC-IPE-01)) — jamais recopiée ici.
const causesEcart = computed(() => ipeEtat.value?.causes_ecart || [])

// La qualification des écarts et la justification des modules non
// évaluables sont figées une fois le contrôle soumis ou validé.
const peutEditerAuditeur = computed(() => ['en_cours', 'en_attente_correction'].includes(statutCircuit.value))

function qualificationPour(module, numeroCompte) {
  return (ipeEtat.value?.qualifications_ecarts || []).find(
    (q) => q.module === module && q.numero_compte === numeroCompte
  )
}

function qualificationComplete(q) {
  return !!q && causesEcart.value.includes(q.cause) && !!(q.commentaire || '').trim()
}

// Reflet côté frontend de revue_ipe_service.ecarts_non_qualifies (backend) :
// un écart réel (collectif "ok: false" d'un module "ecart") sans
// qualification complète (cause + commentaire) bloque la soumission.
const ecartsNonQualifies = computed(() => {
  const manquants = []
  for (const [cle, module] of Object.entries(ipeEtat.value?.modules || {})) {
    if (module.statut !== 'ecart') continue
    for (const c of module.derniere_evaluation?.detail_collectifs || []) {
      if (c.ok) continue
      if (!qualificationComplete(qualificationPour(cle, c.numero_compte))) manquants.push(`${cle}:${c.numero_compte}`)
    }
  }
  return manquants
})

// Reflet de revue_ipe_service.refus_validation : bloquent la validation.
const demandesCorrectionNonTraitees = computed(() =>
  (ipeEtat.value?.remarques || []).filter((r) => r.type === 'demande_correction' && !r.traitee)
)
const modulesNonEvaluablesSansJustification = computed(() =>
  Object.entries(ipeEtat.value?.modules || {})
    .filter(([cle, m]) => m.statut === 'non_evaluable' && !(ipeEtat.value?.justifications_non_evaluables?.[cle]?.commentaire || '').trim())
    .map(([cle]) => cle)
)

// Reflet de revue_ipe_service.refus_soumission : qualification des écarts ET
// justification des modules non évaluables, dès la soumission.
const peutSoumettre = computed(
  () =>
    peutEditerAuditeur.value &&
    ecartsNonQualifies.value.length === 0 &&
    modulesNonEvaluablesSansJustification.value.length === 0
)

// Une demande de correction exige un utilisateur identifié (sinon personne ne
// pourrait la marquer traitée) — même règle que le backend.
const utilisateurIdentifie = computed(() => !!utilisateurConnecte())
const peutDemanderCorrection = computed(() => statutCircuit.value === 'soumis_pour_revue' && utilisateurIdentifie.value)
const peutValider = computed(
  () =>
    statutCircuit.value === 'soumis_pour_revue' &&
    ecartsNonQualifies.value.length === 0 &&
    demandesCorrectionNonTraitees.value.length === 0 &&
    modulesNonEvaluablesSansJustification.value.length === 0
)

const raisonValidationImpossible = computed(() => {
  if (statutCircuit.value !== 'soumis_pour_revue') return 'Le contrôle doit être « Soumis pour revue ».'
  if (ecartsNonQualifies.value.length) return 'Chaque écart doit être qualifié (cause + commentaire).'
  if (demandesCorrectionNonTraitees.value.length) return 'Des demandes de correction ne sont pas traitées.'
  if (modulesNonEvaluablesSansJustification.value.length) return 'Chaque module non évaluable doit être justifié.'
  return ''
})

/* --- Qualification d'un écart (cause + commentaire, par compte collectif) --- */

const formulairesQualification = ref({})
const justificationsEnCours = ref({})

// Pré-remplit les formulaires (qualification de chaque écart, justification
// de chaque module non évaluable) à chaque nouvel état, sans écraser une
// saisie en cours. Exécuté avant le rendu (flush "pre").
watch(ipeEtat, (etat) => {
  for (const [cle, module] of Object.entries(etat?.modules || {})) {
    if (module.statut === 'ecart') {
      for (const c of module.derniere_evaluation?.detail_collectifs || []) {
        if (c.ok) continue
        const id = `${cle}:${c.numero_compte}`
        if (!formulairesQualification.value[id]) {
          const existante = qualificationPour(cle, c.numero_compte)
          formulairesQualification.value[id] = { cause: existante?.cause || '', commentaire: existante?.commentaire || '' }
        }
      }
    }
    if (module.statut === 'non_evaluable' && justificationsEnCours.value[cle] === undefined) {
      justificationsEnCours.value[cle] = etat.justifications_non_evaluables?.[cle]?.commentaire || ''
    }
  }
})

const qualificationEnCours = ref(null)

async function enregistrerQualification(module, numeroCompte) {
  const cle = `${module}:${numeroCompte}`
  if (qualificationEnCours.value) return
  const { cause, commentaire } = formulairesQualification.value[cle] || { cause: '', commentaire: '' }
  if (!cause) {
    notyf.trigger("Choisissez la cause de l'écart", 'warning')
    return
  }
  if (commentaire.trim().length < LONGUEUR_MIN_COMMENTAIRE) {
    notyf.trigger(`Le commentaire doit contenir au moins ${LONGUEUR_MIN_COMMENTAIRE} caractères.`, 'warning')
    return
  }
  qualificationEnCours.value = cle
  try {
    ipeEtat.value = await qualifierEcartIpe(props.missionId, module, numeroCompte, cause, commentaire.trim(), utilisateurConnecte())
    notyf.trigger('Écart qualifié', 'success')
  } catch (e) {
    notyf.trigger(e.message || "Erreur lors de la qualification de l'écart", 'error')
  } finally {
    qualificationEnCours.value = null
  }
}

/* --- Justification écrite d'un module non évaluable --- */

const justificationEnCours = ref(null)

async function enregistrerJustification(module) {
  if (justificationEnCours.value) return
  const commentaire = (justificationsEnCours.value[module] || '').trim()
  if (commentaire.length < LONGUEUR_MIN_COMMENTAIRE) {
    notyf.trigger(`La justification doit contenir au moins ${LONGUEUR_MIN_COMMENTAIRE} caractères.`, 'warning')
    return
  }
  justificationEnCours.value = module
  try {
    ipeEtat.value = await justifierNonEvaluableIpe(props.missionId, module, commentaire, utilisateurConnecte())
    notyf.trigger('Justification enregistrée', 'success')
  } catch (e) {
    notyf.trigger(e.message || 'Erreur lors de la justification du module', 'error')
  } finally {
    justificationEnCours.value = null
  }
}

const soumissionEnCours = ref(false)

async function soumettrePourRevue() {
  if (soumissionEnCours.value || !peutSoumettre.value) return
  soumissionEnCours.value = true
  try {
    ipeEtat.value = await soumettrePourRevueIpe(props.missionId, null, utilisateurConnecte())
    notyf.trigger('Contrôle IPE soumis pour revue', 'success')
  } catch (e) {
    notyf.trigger(e.message || 'Erreur lors de la soumission pour revue', 'error')
  } finally {
    soumissionEnCours.value = false
  }
}

const confirmationDemandeCorrectionOuverte = ref(false)
const commentaireDemandeCorrection = ref('')
const demandeCorrectionEnCours = ref(false)

function ouvrirDemandeCorrection() {
  if (!peutDemanderCorrection.value) return
  commentaireDemandeCorrection.value = ''
  confirmationDemandeCorrectionOuverte.value = true
}

function annulerDemandeCorrection() {
  confirmationDemandeCorrectionOuverte.value = false
}

async function confirmerDemandeCorrection() {
  if (demandeCorrectionEnCours.value) return

  const commentaire = commentaireDemandeCorrection.value.trim()
  if (commentaire.length < LONGUEUR_MIN_COMMENTAIRE) {
    notyf.trigger(
      `Le commentaire est obligatoire et doit contenir au moins ${LONGUEUR_MIN_COMMENTAIRE} caractères (${commentaire.length} actuellement).`,
      'warning'
    )
    return
  }

  demandeCorrectionEnCours.value = true
  try {
    ipeEtat.value = await demanderCorrectionIpe(props.missionId, commentaire, utilisateurConnecte())
    notyf.trigger('Correction demandée', 'success')
    confirmationDemandeCorrectionOuverte.value = false
  } catch (e) {
    notyf.trigger(e.message || 'Erreur lors de la demande de correction', 'error')
  } finally {
    demandeCorrectionEnCours.value = false
  }
}

/* ================================
   REMARQUES à deux niveaux : générale (sur le contrôle) et sur un écart
   précis (par module + compte collectif) — docs/PLAN_verrou_IPE.md.
================================ */

const remarquesGenerales = computed(() => (ipeEtat.value?.remarques || []).filter((r) => !r.module))

function remarquesPourCollectif(module, numeroCompte) {
  return (ipeEtat.value?.remarques || []).filter((r) => r.module === module && r.numero_compte === numeroCompte)
}

const nouvelleRemarqueGenerale = ref('')
const typeNouvelleRemarqueGenerale = ref('information')
const nouvellesRemarquesEcart = ref({})
const typesNouvellesRemarquesEcart = ref({})
const reponsesEnCours = ref({})
const remarqueActionEnCours = ref(null)

async function ajouterRemarqueGenerale() {
  const texte = nouvelleRemarqueGenerale.value.trim()
  if (!texte) {
    notyf.trigger('La remarque ne peut pas être vide', 'warning')
    return
  }
  try {
    ipeEtat.value = await ajouterRemarqueIpe(props.missionId, texte, {
      type: typeNouvelleRemarqueGenerale.value,
      utilisateurId: utilisateurConnecte(),
    })
    nouvelleRemarqueGenerale.value = ''
    typeNouvelleRemarqueGenerale.value = 'information'
    notyf.trigger('Remarque ajoutée', 'success')
  } catch (e) {
    notyf.trigger(e.message || "Erreur lors de l'ajout de la remarque", 'error')
  }
}

async function ajouterRemarqueEcart(module, numeroCompte) {
  const cle = `${module}:${numeroCompte}`
  const texte = (nouvellesRemarquesEcart.value[cle] || '').trim()
  if (!texte) {
    notyf.trigger('La remarque ne peut pas être vide', 'warning')
    return
  }
  try {
    ipeEtat.value = await ajouterRemarqueIpe(props.missionId, texte, {
      module,
      numeroCompte,
      type: typesNouvellesRemarquesEcart.value[cle] || 'information',
      utilisateurId: utilisateurConnecte(),
    })
    nouvellesRemarquesEcart.value[cle] = ''
    typesNouvellesRemarquesEcart.value[cle] = 'information'
    notyf.trigger('Remarque ajoutée', 'success')
  } catch (e) {
    notyf.trigger(e.message || "Erreur lors de l'ajout de la remarque", 'error')
  }
}

// Reflet de revue_ipe_service.refus_marquage_remarque : seul l'auteur
// enregistré peut (dé)marquer, et "traitée" seulement après la réponse de
// l'auditeur. TODO(décision) : en attendant les rôles.
function raisonMarquageImpossible(remarque) {
  if (!utilisateurConnecte()) {
    return 'Utilisateur non identifié : impossible de marquer une remarque traitée ou de la rouvrir.'
  }
  if (remarque.utilisateur_id !== utilisateurConnecte()) {
    return "Seul l'auteur de la remarque peut la marquer traitée ou la rouvrir."
  }
  if (!remarque.traitee && !remarque.reponse) {
    return "La remarque ne peut être marquée traitée qu'après la réponse de l'auditeur."
  }
  return ''
}

async function envoyerReponse(remarque) {
  const texte = (reponsesEnCours.value[remarque._id] || '').trim()
  if (!texte) {
    notyf.trigger('La réponse ne peut pas être vide', 'warning')
    return
  }
  if (remarqueActionEnCours.value) return
  remarqueActionEnCours.value = remarque._id
  try {
    ipeEtat.value = await repondreRemarqueIpe(props.missionId, remarque._id, texte, utilisateurConnecte())
    reponsesEnCours.value[remarque._id] = ''
    notyf.trigger('Réponse envoyée', 'success')
  } catch (e) {
    notyf.trigger(e.message || 'Erreur lors de la réponse à la remarque', 'error')
  } finally {
    remarqueActionEnCours.value = null
  }
}

async function basculerTraitee(remarque) {
  if (remarqueActionEnCours.value) return
  const raison = raisonMarquageImpossible(remarque)
  if (raison) {
    notyf.trigger(raison, 'warning')
    return
  }
  remarqueActionEnCours.value = remarque._id
  try {
    ipeEtat.value = await marquerRemarqueTraiteeIpe(props.missionId, remarque._id, !remarque.traitee, utilisateurConnecte())
  } catch (e) {
    notyf.trigger(e.message || 'Erreur lors de la mise à jour de la remarque', 'error')
  } finally {
    remarqueActionEnCours.value = null
  }
}

function ouvrirConfirmationValidation() {
  if (!peutValider.value) return
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
          <span
            class="text-xs font-semibold px-3 py-1 rounded-full"
            :class="ipeEtat.verrou_applicable ? (STATUT_CIRCUIT_INFO[statutCircuit]?.classe || 'bg-gray-100 text-gray-700') : 'bg-gray-100 text-gray-700'"
          >
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

          <!-- Action auditeur : désactivée tant qu'un écart réel n'a aucune remarque attachée,
               ou si le statut actuel ne permet pas de soumettre. TODO(décision) : qui a le
               droit de soumettre n'est pas vérifié aujourd'hui. -->
          <button
            class="px-5 py-2 rounded-lg bg-blue-ycube-3 text-white font-semibold hover:opacity-90 transition disabled:opacity-40 disabled:cursor-not-allowed"
            :disabled="soumissionEnCours || !peutSoumettre"
            :title="ecartsNonQualifies.length || modulesNonEvaluablesSansJustification.length
              ? 'Qualifiez chaque écart (cause + commentaire) et justifiez chaque module non évaluable avant de soumettre'
              : ''"
            @click="soumettrePourRevue"
          >
            {{ soumissionEnCours ? 'Soumission en cours...' : 'Soumettre pour revue' }}
          </button>

          <!-- Action manager : possible seulement depuis "Soumis pour revue". Ne valide ni
               n'invalide — TODO(décision) : qui a le droit de demander une correction n'est
               pas vérifié aujourd'hui. -->
          <button
            class="px-5 py-2 rounded-lg border border-red-300 text-red-700 font-semibold hover:bg-red-50 transition disabled:opacity-40 disabled:cursor-not-allowed"
            :disabled="!peutDemanderCorrection"
            :title="!utilisateurIdentifie ? 'Utilisateur non identifié : impossible de créer une demande de correction' : ''"
            @click="ouvrirDemandeCorrection"
          >
            Demander une correction
          </button>

          <!-- Action manager : possible seulement depuis "Soumis pour revue".
               TODO(décision) : qui a le droit de valider n'est pas vérifié aujourd'hui. -->
          <button
            class="px-5 py-2 rounded-lg bg-green-ycube-2 text-white font-semibold hover:bg-green-ycube transition disabled:opacity-40 disabled:cursor-not-allowed"
            :disabled="ipeValidationEnCours || !peutValider"
            :title="raisonValidationImpossible"
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
        <ul
          v-if="ecartsNonQualifies.length || demandesCorrectionNonTraitees.length || modulesNonEvaluablesSansJustification.length"
          class="text-xs text-gray-500 italic list-disc ml-5"
        >
          <li v-if="ecartsNonQualifies.length">
            Écart(s) non qualifié(s) — cause + commentaire requis (bloque la soumission et la validation) :
            {{ ecartsNonQualifies.join(', ') }}.
          </li>
          <li v-if="demandesCorrectionNonTraitees.length">
            {{ demandesCorrectionNonTraitees.length }} demande(s) de correction non traitée(s) (bloque la validation).
          </li>
          <li v-if="modulesNonEvaluablesSansJustification.length">
            Module(s) non évaluable(s) sans justification écrite (bloque la soumission et la validation) :
            {{ modulesNonEvaluablesSansJustification.map((m) => LIBELLES_MODULE[m] || m).join(', ') }}.
          </li>
        </ul>
        <!-- Validation/soumission/demande de correction enregistrées sans
             contrôle de rôle : aucun système d'authentification/droits
             n'existe sur les missions aujourd'hui (CLAUDE.md, point de
             sécurité connu). TODO(décision) : qui peut valider et demander
             une correction. -->

        <!-- Confirmation de demande de correction (commentaire obligatoire) -->
        <div v-if="confirmationDemandeCorrectionOuverte" class="border border-red-300 bg-red-50 rounded-lg p-4 flex flex-col gap-2">
          <p class="text-sm font-semibold text-red-700">Confirmer la demande de correction</p>
          <textarea
            v-model="commentaireDemandeCorrection"
            rows="2"
            class="text-sm border border-gray-300 rounded-lg p-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-ycube"
            placeholder="Commentaire (obligatoire, enregistré dans l'historique)"
          ></textarea>
          <div class="flex gap-3">
            <button
              class="px-5 py-2 rounded-lg bg-red-600 text-white font-semibold hover:bg-red-700 transition disabled:opacity-50"
              :disabled="demandeCorrectionEnCours"
              @click="confirmerDemandeCorrection"
            >
              Confirmer
            </button>
            <button class="px-5 py-2 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition" @click="annulerDemandeCorrection">
              Annuler
            </button>
          </div>
        </div>

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

              <!-- Justification écrite exigée pour valider malgré un module non évaluable.
                   Le traitement métier de ces modules reste TODO(spec: CAC-IPE-01). -->
              <div v-if="module.statut === 'non_evaluable'" class="border border-gray-200 rounded-lg p-3 flex flex-col gap-2">
                <p class="text-xs font-semibold text-gray-700">
                  Justification (obligatoire pour soumettre et valider)
                  <span v-if="ipeEtat.justifications_non_evaluables?.[cle]" class="font-normal text-gray-500">
                    — enregistrée par {{ ipeEtat.justifications_non_evaluables[cle].utilisateur_id || 'Non identifié' }},
                    {{ formatHorodatage(ipeEtat.justifications_non_evaluables[cle].horodatage) }}
                  </span>
                </p>
                <textarea
                  v-model="justificationsEnCours[cle]"
                  :disabled="!peutEditerAuditeur"
                  rows="2"
                  class="text-sm border border-gray-300 rounded-lg p-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-ycube disabled:bg-gray-50"
                  :placeholder="`Pourquoi valider sans ce module ? (au moins ${LONGUEUR_MIN_COMMENTAIRE} caractères)`"
                ></textarea>
                <div>
                  <button
                    class="px-5 py-2 rounded-lg bg-blue-ycube text-white text-sm font-semibold hover:bg-blue-900 transition disabled:opacity-40 disabled:cursor-not-allowed"
                    :disabled="!peutEditerAuditeur || justificationEnCours === cle"
                    :title="!peutEditerAuditeur ? 'Modifiable uniquement « En cours » ou « En attente de correction »' : ''"
                    @click="enregistrerJustification(cle)"
                  >
                    Enregistrer la justification
                  </button>
                </div>
              </div>
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

              <!-- Un bloc par écart réel (compte collectif) : qualification (cause +
                   commentaire, exigée pour soumettre et valider) puis remarques de
                   niveau 2 (docs/PLAN_verrou_IPE.md). -->
              <template v-if="module.statut === 'ecart'">
              <div
                v-for="c in (module.derniere_evaluation.detail_collectifs || []).filter((c) => !c.ok)"
                :key="'ecart-' + c.numero_compte"
                class="border border-gray-200 rounded-lg p-3 flex flex-col gap-3 text-xs"
              >
                <div class="flex items-center justify-between flex-wrap gap-2">
                  <p class="font-semibold text-gray-700 text-sm">Écart — collectif {{ c.numero_compte }}</p>
                  <span
                    class="px-3 py-1 rounded-full text-xs font-semibold"
                    :class="qualificationComplete(qualificationPour(cle, c.numero_compte)) ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
                  >
                    {{ qualificationComplete(qualificationPour(cle, c.numero_compte)) ? 'Qualifié' : 'À qualifier' }}
                  </span>
                </div>

                <!-- Qualification : cause choisie dans la liste provisoire (TODO(spec: CAC-IPE-01)) + commentaire -->
                <div class="flex flex-col gap-2">
                  <div class="flex flex-wrap gap-2 items-start">
                    <select
                      v-model="formulairesQualification[`${cle}:${c.numero_compte}`].cause"
                      :disabled="!peutEditerAuditeur"
                      class="border border-gray-300 rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-ycube disabled:bg-gray-50"
                    >
                      <option value="" disabled>Cause de l'écart...</option>
                      <option v-for="cause in causesEcart" :key="cause" :value="cause">{{ cause }}</option>
                    </select>
                    <textarea
                      v-model="formulairesQualification[`${cle}:${c.numero_compte}`].commentaire"
                      :disabled="!peutEditerAuditeur"
                      rows="2"
                      class="flex-1 min-w-[16rem] text-sm border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-ycube disabled:bg-gray-50"
                      :placeholder="`Commentaire (au moins ${LONGUEUR_MIN_COMMENTAIRE} caractères)`"
                    ></textarea>
                  </div>
                  <div class="flex items-center gap-3">
                    <button
                      class="px-5 py-2 rounded-lg bg-blue-ycube text-white text-sm font-semibold hover:bg-blue-900 transition disabled:opacity-40 disabled:cursor-not-allowed"
                      :disabled="!peutEditerAuditeur || qualificationEnCours === `${cle}:${c.numero_compte}`"
                      :title="!peutEditerAuditeur ? 'Modifiable uniquement « En cours » ou « En attente de correction »' : ''"
                      @click="enregistrerQualification(cle, c.numero_compte)"
                    >
                      Enregistrer la qualification
                    </button>
                    <span v-if="qualificationPour(cle, c.numero_compte)" class="text-gray-500">
                      Qualifié par {{ qualificationPour(cle, c.numero_compte).utilisateur_id || 'Non identifié' }},
                      {{ formatHorodatage(qualificationPour(cle, c.numero_compte).horodatage) }}
                    </span>
                  </div>
                </div>

                <!-- Remarques sur cet écart -->
                <div class="border-t pt-2 flex flex-col gap-2">
                  <p class="font-semibold text-gray-700">Remarques</p>
                  <p v-if="!remarquesPourCollectif(cle, c.numero_compte).length" class="text-gray-500 italic">Aucune remarque.</p>

                  <div v-for="r in remarquesPourCollectif(cle, c.numero_compte)" :key="r._id" class="border-t pt-2 flex flex-col gap-1">
                    <div class="flex items-center gap-2">
                      <span class="px-2 py-0.5 rounded-full text-xs font-semibold" :class="TYPE_REMARQUE_INFO[r.type]?.classe || TYPE_REMARQUE_INFO.information.classe">
                        {{ TYPE_REMARQUE_INFO[r.type]?.label || 'Information' }}
                      </span>
                      <span><span class="font-semibold">{{ r.utilisateur_id || 'Non identifié' }}</span> — {{ formatHorodatage(r.horodatage) }}</span>
                    </div>
                    <p class="text-gray-700">{{ r.commentaire }}</p>
                    <p v-if="r.reponse" class="ml-3 text-gray-600 italic">
                      Réponse de {{ r.reponse.utilisateur_id || 'Non identifié' }} ({{ formatHorodatage(r.reponse.horodatage) }}) : {{ r.reponse.commentaire }}
                    </p>
                    <div class="flex items-center gap-2">
                      <span
                        class="px-2 py-0.5 rounded-full text-xs font-semibold"
                        :class="r.traitee ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'"
                      >
                        {{ r.traitee ? 'Traitée' : 'Non traitée' }}
                      </span>
                      <button
                        class="text-blue-ycube font-semibold hover:underline disabled:text-gray-400 disabled:no-underline disabled:cursor-not-allowed"
                        :disabled="!!raisonMarquageImpossible(r)"
                        :title="raisonMarquageImpossible(r)"
                        @click="basculerTraitee(r)"
                      >
                        {{ r.traitee ? 'Rouvrir' : 'Marquer traitée' }}
                      </button>
                    </div>
                    <div v-if="!r.reponse" class="flex gap-2 mt-1">
                      <input
                        v-model="reponsesEnCours[r._id]"
                        type="text"
                        placeholder="Répondre..."
                        class="flex-1 border border-gray-300 rounded-lg px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-blue-ycube"
                      />
                      <button class="text-blue-ycube font-semibold hover:underline" @click="envoyerReponse(r)">Répondre</button>
                    </div>
                  </div>

                  <div class="flex gap-2 mt-1">
                    <select
                      :value="typesNouvellesRemarquesEcart[`${cle}:${c.numero_compte}`] || 'information'"
                      @change="typesNouvellesRemarquesEcart[`${cle}:${c.numero_compte}`] = $event.target.value"
                      class="border border-gray-300 rounded-lg px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-blue-ycube"
                    >
                      <option value="information">Information</option>
                      <option value="demande_correction" :disabled="!utilisateurIdentifie">Demande de correction</option>
                    </select>
                    <input
                      v-model="nouvellesRemarquesEcart[`${cle}:${c.numero_compte}`]"
                      type="text"
                      placeholder="Ajouter une remarque sur cet écart..."
                      class="flex-1 border border-gray-300 rounded-lg px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-blue-ycube"
                    />
                    <button
                      class="px-3 py-1 rounded-lg bg-blue-ycube text-white text-xs font-semibold hover:bg-blue-900 transition"
                      @click="ajouterRemarqueEcart(cle, c.numero_compte)"
                    >
                      Ajouter
                    </button>
                  </div>
                </div>
              </div>
              </template>

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

      <!-- Commentaire général — niveau 1 des remarques (docs/PLAN_verrou_IPE.md),
           sur le contrôle dans son ensemble, pas sur un écart précis. -->
      <div class="bg-white rounded-xl shadow p-6 flex flex-col gap-3 w-full" v-if="ipeEtat">
        <h2 class="font-bold text-sm uppercase text-blue-ycube">Commentaires généraux</h2>

        <p v-if="!remarquesGenerales.length" class="text-sm text-gray-500 italic">Aucun commentaire général.</p>

        <div v-for="r in remarquesGenerales" :key="r._id" class="border-t pt-3 flex flex-col gap-1 text-sm">
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded-full text-xs font-semibold" :class="TYPE_REMARQUE_INFO[r.type]?.classe || TYPE_REMARQUE_INFO.information.classe">
              {{ TYPE_REMARQUE_INFO[r.type]?.label || 'Information' }}
            </span>
            <span><span class="font-semibold">{{ r.utilisateur_id || 'Non identifié' }}</span> — {{ formatHorodatage(r.horodatage) }}</span>
          </div>
          <p class="text-gray-700">{{ r.commentaire }}</p>
          <p v-if="r.reponse" class="ml-3 text-gray-600 italic">
            Réponse de {{ r.reponse.utilisateur_id || 'Non identifié' }} ({{ formatHorodatage(r.reponse.horodatage) }}) : {{ r.reponse.commentaire }}
          </p>
          <div class="flex items-center gap-2">
            <span
              class="px-2 py-0.5 rounded-full text-xs font-semibold"
              :class="r.traitee ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'"
            >
              {{ r.traitee ? 'Traitée' : 'Non traitée' }}
            </span>
            <button
              class="text-blue-ycube font-semibold hover:underline text-xs disabled:text-gray-400 disabled:no-underline disabled:cursor-not-allowed"
              :disabled="!!raisonMarquageImpossible(r)"
              :title="raisonMarquageImpossible(r)"
              @click="basculerTraitee(r)"
            >
              {{ r.traitee ? 'Rouvrir' : 'Marquer traitée' }}
            </button>
          </div>
          <div v-if="!r.reponse" class="flex gap-2 mt-1">
            <input
              v-model="reponsesEnCours[r._id]"
              type="text"
              placeholder="Répondre..."
              class="flex-1 border border-gray-300 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-ycube"
            />
            <button class="text-blue-ycube font-semibold hover:underline" @click="envoyerReponse(r)">Répondre</button>
          </div>
        </div>

        <div class="flex gap-2 pt-2">
          <select
            v-model="typeNouvelleRemarqueGenerale"
            class="border border-gray-300 rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-ycube"
          >
            <option value="information">Information</option>
            <option value="demande_correction" :disabled="!utilisateurIdentifie">Demande de correction</option>
          </select>
          <input
            v-model="nouvelleRemarqueGenerale"
            type="text"
            placeholder="Ajouter un commentaire général sur le contrôle..."
            class="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-ycube"
          />
          <button
            class="px-5 py-2 rounded-lg bg-blue-ycube text-white font-semibold hover:bg-blue-900 transition"
            @click="ajouterRemarqueGenerale"
          >
            Ajouter
          </button>
        </div>
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
