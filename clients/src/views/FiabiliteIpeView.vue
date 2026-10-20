<script setup>
// Écran dédié au rapprochement IPE (Module 1, CAC-IPE-01) d'une mission —
// voir docs/PLAN_verrou_IPE.md §4/§5. Séparé de FichiersComplementairesView.vue
// (qui ne garde que l'import/consultation/remplacement des fichiers) pour ne
// plus confondre les deux entrées de la barre latérale de GroupingAnalyse.vue.
// N'est PAS une étape d'audit : volontairement absent de la barre de
// progression des 11 étapes (voir l'indicateur "Fiabilité IPE" de la barre
// latérale, qui renvoie ici pour le détail).
import { ref, onMounted, computed, watch } from 'vue'
import * as circuit from '@/utils/circuitIpe'
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
import { obtenirMission, obtenirClient, listerFichiersComplementaires } from '@/api/imports.api'

// `integre` : écran affiché dans la zone principale de GroupingAnalyse.vue,
// sous la barre latérale bleue (qui porte déjà le « Retour »).
const props = defineProps({ missionId: String, integre: Boolean })
// Chaque nouvel état IPE est remonté pour mettre à jour la barre latérale
// (statut, cadenas des étapes) sans recharger la page.
const emit = defineEmits(['etat-ipe', 'ouvrir-ecran'])
const notyf = useNotyf()

// Libellés de la maquette 1_Fiabilite_IPE. Racines : rapprochement_ipe_service.RACINES_COLLECTIFS.
const LIBELLES_MODULE = {
  ipe_1_clients: 'IPE-1 · Clients (racine 41)',
  ipe_2_fournisseurs: 'IPE-2 · Fournisseurs (racine 40)',
  ipe_3_immobilisations: 'IPE-3 · Immobilisations (20 à 28)',
}

// Fichier complémentaire comparé par chaque module (colonne « Fichier » de la synthèse).
const FICHIER_DU_MODULE = {
  ipe_1_clients: { type: 'auxiliaire_client', libelle: 'Balance auxiliaire clients' },
  ipe_2_fournisseurs: { type: 'auxiliaire_fournisseur', libelle: 'Balance auxiliaire fournisseurs' },
  ipe_3_immobilisations: { type: 'immobilisations', libelle: 'Fichier des immobilisations' },
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

// IPE-3 compare des biens (valeur brute, amortissements, valeur nette) à la
// balance générale — jamais des tiers (docs/PLAN_verrou_IPE.md).
const NATURE_LIGNE_IMMO = {
  valeur_brute: 'Valeur brute',
  amortissements: 'Amortissements',
  controle_vnc: 'Contrôle valeur nette',
}

function estImmobilisations(module) {
  return module.derniere_evaluation?.nature === 'immobilisations'
}

// IPE-3 : les amortissements (28) sont comparés en valeur positive alors
// qu'ils sont CRÉDITEURS — on les affiche avec le sens C (une valeur
// négative = débiteur). Le contrôle de valeur nette n'a pas de sens D/C.
function montantImmo(ligne, valeur) {
  if (valeur === null || valeur === undefined) return '—'
  if (ligne.nature === 'controle_vnc') return new Intl.NumberFormat('fr-FR').format(Math.round(valeur))
  return formatMontant(ligne.nature === 'amortissements' ? -valeur : valeur)
}

function libelleLigneEcart(module, ligne) {
  if (!estImmobilisations(module)) return `compte ${ligne.numero_compte}`
  if (ligne.nature === 'controle_vnc') return 'contrôle valeur nette (bien par bien)'
  return `${NATURE_LIGNE_IMMO[ligne.nature] || ligne.nature} — compte ${ligne.numero_compte}`
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
watch(ipeEtat, (etat) => { if (etat) emit('etat-ipe', etat) })
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
  chargerEnTete()
  chargerFichiers()
  await chargerEtatIpe()
})

// Fichiers complémentaires actifs (colonne « Fichier » de la synthèse).
const fichiersActifs = ref({})

async function chargerFichiers() {
  try {
    fichiersActifs.value = await listerFichiersComplementaires(props.missionId)
  } catch (e) {
    console.warn('Fiabilité IPE : fichiers complémentaires indisponibles', e)
  }
}

function fichierDuModule(cle) {
  const attendu = FICHIER_DU_MODULE[cle]
  const actif = attendu ? (fichiersActifs.value[attendu.type] || [])[0] : null
  return actif ? `${attendu.libelle} · v${actif.version || 1}` : 'Aucun fichier importé'
}

// Module affiché en détail : choisi par un clic dans la synthèse ; par défaut,
// le premier module en écart, sinon le premier évalué (docs/PLAN_ecrans_lot1.md §2.2).
const moduleChoisi = ref(null)
const cleModuleAffiche = computed(() => {
  const modules = ipeEtat.value?.modules || {}
  if (moduleChoisi.value && modules[moduleChoisi.value]) return moduleChoisi.value
  return ORDRE_MODULES.find((cle) => modules[cle]?.statut === 'ecart') || ORDRE_MODULES.find((cle) => modules[cle]) || null
})
const modulesAffiches = computed(() => {
  const cle = cleModuleAffiche.value
  return cle ? { [cle]: ipeEtat.value.modules[cle] } : {}
})

function ouvrirFichiersComplementaires() {
  if (props.integre) emit('ouvrir-ecran', 'fichiers_complementaires')
  else router.push({ path: `/grouping-analyse/${props.missionId}`, query: { step: 'fichiers_complementaires' } })
}

// Tiers sans compte collectif (et collectifs sans tiers) : liste complète dans une fenêtre.
// Traitement attendu : TODO(spec: CAC-IPE-01).
const listeOrphelinsOuverte = ref(false)

// Panneau latéral d'un compte en écart (maquette 1_Fiabilite_IPE, docs/PLAN_ecrans_lot1.md §2.4) :
// qualification + fil des remarques. Ouvert par « Commenter » ou un clic sur la ligne ; un seul à la fois.
const panneau = ref(null) // { cle, numeroCompte }

function ouvrirPanneau(cle, numeroCompte) {
  panneau.value = { cle, numeroCompte }
}

function fermerPanneau() {
  panneau.value = null
}

const lignePanneau = computed(() => {
  if (!panneau.value) return null
  const module = ipeEtat.value?.modules?.[panneau.value.cle]
  const ligne = (module?.derniere_evaluation?.detail_collectifs || []).find((c) => c.numero_compte === panneau.value.numeroCompte)
  return module && ligne && !ligne.ok ? { cle: panneau.value.cle, module, ligne } : null
})

// Changer de module dans la synthèse ferme le panneau d'un compte d'un autre module.
watch(cleModuleAffiche, (cle) => {
  if (panneau.value && panneau.value.cle !== cle) fermerPanneau()
})

// Modules non évaluables : justifications regroupées dans une seule carte (§2.5).
const modulesNonEvaluables = computed(() => ORDRE_MODULES.filter((cle) => ipeEtat.value?.modules?.[cle]?.statut === 'non_evaluable'))

// En-tête (maquette 1_Fiabilite_IPE) : « [client] · exercice audité [année] ».
// Échec de chargement : sous-titre sans ces informations, jamais bloquant.
const enTete = ref({ client: null, annee: null })

async function chargerEnTete() {
  try {
    const mission = await obtenirMission(props.missionId)
    enTete.value.annee = mission.annee_auditee || null
    if (mission.id_client) enTete.value.client = (await obtenirClient(mission.id_client)).company_name || null
  } catch (e) {
    console.warn("En-tête Fiabilité IPE : informations de mission indisponibles", e)
  }
}

const sousTitreEnTete = computed(() => [
  enTete.value.client,
  enTete.value.annee ? `exercice audité ${enTete.value.annee}` : null,
  "rapprochement des informations produites par l'entité",
].filter(Boolean).join(' · '))

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
    chargerFichiers()
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

/* --- Circuit de revue en quatre étapes (docs/PLAN_ecrans_lot1.md §2.1) --- */
const ETAPES_CIRCUIT = [
  { cle: 'en_cours', libelle: 'En cours' },
  { cle: 'soumis_pour_revue', libelle: 'Soumis pour revue' },
  { cle: 'en_attente_correction', libelle: 'En attente de correction' },
  { cle: 'valide', libelle: 'Validé' },
]

// Étapes déjà franchies, lues dans l'historique (une soumission, une demande
// de correction, une validation) : marquées d'une coche, l'étape en cours
// restant seule mise en avant.
const etapesFranchies = computed(() => {
  const actions = new Set((ipeEtat.value?.historique || []).map((h) => h.action))
  const franchies = new Set()
  if (statutCircuit.value !== 'en_cours' || actions.has('soumission_revue')) franchies.add('en_cours')
  if (actions.has('soumission_revue')) franchies.add('soumis_pour_revue')
  if (actions.has('demande_correction')) franchies.add('en_attente_correction')
  franchies.delete(statutCircuit.value)
  return franchies
})

const rapprochementLance = computed(() => Object.keys(ipeEtat.value?.modules || {}).length > 0)

// Raison du blocage, écrite à côté de l'action attendue (maquette :
// « Avant de soumettre : 1 écart à qualifier, 2 justifications à écrire »).
const raisonSoumission = computed(() => {
  if (!rapprochementAJour.value) return ipeEtat.value.rapprochement_a_jour.raison
  const blocages = circuit.phraseBlocages(ipeEtat.value)
  return blocages ? `Avant de soumettre : ${blocages}` : ''
})
const raisonValidation = computed(() => {
  const blocages = circuit.phraseBlocages(ipeEtat.value, { avecDemandes: true })
  return blocages ? `Avant de valider : ${blocages}` : ''
})

function allerAuxCommentairesGeneraux() {
  document.getElementById('commentaires-generaux')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

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

const statutCircuit = computed(() => circuit.statutCircuit(ipeEtat.value))

// Causes d'écart : liste provisoire renvoyée par le backend
// (revue_ipe_service.CAUSES_ECART, TODO(spec: CAC-IPE-01)) — jamais recopiée ici.
const causesEcart = computed(() => ipeEtat.value?.causes_ecart || [])

// La qualification des écarts et la justification des modules non
// évaluables sont figées une fois le contrôle soumis ou validé.
const peutEditerAuditeur = computed(() => circuit.STATUTS_EDITION_AUDITEUR.includes(statutCircuit.value))

// Points bloquants : calcul partagé avec la barre latérale (utils/circuitIpe.js),
// reflet de revue_ipe_service (ecarts_non_qualifies, refus_soumission, refus_validation).
function qualificationPour(module, numeroCompte) {
  return circuit.qualificationPour(ipeEtat.value, module, numeroCompte)
}

function qualificationComplete(q) {
  return circuit.qualificationComplete(ipeEtat.value, q)
}

const ecartsNonQualifies = computed(() => circuit.ecartsNonQualifies(ipeEtat.value))
const demandesCorrectionNonTraitees = computed(() => circuit.demandesCorrectionNonTraitees(ipeEtat.value))
const modulesNonEvaluablesSansJustification = computed(() => circuit.modulesNonEvaluablesSansJustification(ipeEtat.value))

// Reflet de revue_ipe_service.refus_soumission : qualification des écarts ET
// justification des modules non évaluables, dès la soumission.
// Rapprochement exigé, sur les versions actuelles des fichiers (décision du
// 20/10/2026) : état calculé par le serveur (revue_ipe_service.refus_rapprochement).
const rapprochementAJour = computed(() => ipeEtat.value?.rapprochement_a_jour?.ok !== false)

const peutSoumettre = computed(
  () =>
    peutEditerAuditeur.value &&
    rapprochementAJour.value &&
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
      <button v-if="!integre" class="text-blue-ycube font-semibold hover:underline flex items-center gap-2" @click="back">
        <i class="fa-solid fa-arrow-left"></i> Retour
      </button>
      <div v-else class="w-20"></div>
      <div class="text-center">
        <h1 class="text-xl font-bold text-blue-ycube">Fiabilité IPE</h1>
        <p class="text-sm text-gray-500">{{ sousTitreEnTete }}</p>
      </div>
      <div class="w-20"></div>
    </div>

    <div class="p-6 flex flex-col gap-6">

      <!-- Circuit de revue (maquette 1_Fiabilite_IPE, docs/PLAN_ecrans_lot1.md §2.1) :
           quatre étapes, l'étape en cours mise en avant ; seules les actions du statut
           courant sont affichées, l'action attendue reste visible avec la raison du
           blocage à côté. Le serveur reste juge (revue_ipe_service). -->
      <div class="bg-white rounded-xl shadow p-6 flex flex-col gap-4 w-full" v-if="ipeEtat">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <h2 class="font-bold text-sm uppercase text-blue-ycube">Circuit de revue</h2>
          <span
            class="text-xs font-semibold px-3 py-1 rounded-full"
            :class="ipeEtat.verrou_applicable ? (STATUT_CIRCUIT_INFO[statutCircuit]?.classe || 'bg-gray-100 text-gray-700') : 'bg-gray-100 text-gray-700'"
            :title="ipeEtat.verrou_applicable ? '' : 'Mission antérieure à l\'activation du verrou IPE : jamais bloquée, ce rapprochement reste informatif.'"
          >
            {{ IPE_STATUT_LABELS[ipeEtat.statut_affiche] || 'Non commencé' }}
          </span>
        </div>

        <ol class="grid grid-cols-2 lg:grid-cols-4 gap-2">
          <li
            v-for="(etape, i) in ETAPES_CIRCUIT"
            :key="etape.cle"
            class="rounded-lg px-4 py-3 text-sm flex items-center gap-2"
            :class="statutCircuit === etape.cle ? 'bg-blue-ycube text-white font-bold' : 'bg-gray-100 text-gray-600 font-semibold'"
            :aria-current="statutCircuit === etape.cle ? 'step' : null"
          >
            <i v-if="etapesFranchies.has(etape.cle)" class="fa-solid fa-check text-green-ycube"></i>
            {{ i + 1 }} · {{ etape.libelle }}
          </li>
        </ol>

        <p v-if="!ipeEtat.verrou_applicable" class="text-xs text-gray-500 italic">
          Mission antérieure à l'activation du verrou IPE : jamais bloquée, ce rapprochement reste informatif.
        </p>

        <!-- Actions du statut courant. Boutons : primaire plein, secondaire en contour — charte CLAUDE.md.
             TODO(décision) : qui peut soumettre, valider et demander une correction n'est pas vérifié. -->
        <div class="flex flex-wrap items-center gap-3">
          <template v-if="statutCircuit === 'en_cours' || statutCircuit === 'en_attente_correction'">
            <button
              class="px-5 py-2 rounded-lg bg-blue-ycube text-white font-semibold hover:bg-blue-900 transition disabled:opacity-50"
              :disabled="ipeEvaluationEnCours"
              @click="lancerEvaluationIpe"
            >
              {{ ipeEvaluationEnCours ? 'Rapprochement en cours...' : (rapprochementLance ? 'Relancer le rapprochement' : 'Lancer le rapprochement') }}
            </button>
            <button
              class="px-5 py-2 rounded-lg bg-blue-ycube-3 text-white font-semibold hover:opacity-90 transition disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="soumissionEnCours || !peutSoumettre"
              @click="soumettrePourRevue"
            >
              {{ soumissionEnCours ? 'Soumission en cours...' : 'Soumettre pour revue' }}
            </button>
            <span v-if="raisonSoumission" class="text-sm text-orange-800 bg-orange-50 px-3 py-2 rounded-lg">{{ raisonSoumission }}</span>
          </template>

          <template v-else-if="statutCircuit === 'soumis_pour_revue'">
            <button
              class="px-5 py-2 rounded-lg border border-red-300 text-red-700 font-semibold hover:bg-red-50 transition disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="!peutDemanderCorrection"
              :title="!utilisateurIdentifie ? 'Utilisateur non identifié : impossible de créer une demande de correction' : ''"
              @click="ouvrirDemandeCorrection"
            >
              Demander une correction
            </button>
            <button
              class="px-5 py-2 rounded-lg bg-green-ycube-2 text-white font-semibold hover:bg-green-ycube transition disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="ipeValidationEnCours || !peutValider"
              @click="ouvrirConfirmationValidation"
            >
              Valider la fiabilité IPE
            </button>
            <span v-if="raisonValidation" class="text-sm text-orange-800 bg-orange-50 px-3 py-2 rounded-lg">{{ raisonValidation }}</span>
            <span v-if="!utilisateurIdentifie" class="text-sm text-gray-600 bg-gray-100 px-3 py-2 rounded-lg">
              Connectez-vous pour demander une correction
            </span>
          </template>

          <template v-else-if="statutCircuit === 'valide'">
            <button
              class="px-5 py-2 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition disabled:opacity-40"
              :disabled="ipeValidationEnCours"
              @click="ouvrirConfirmationInvalidation"
            >
              Invalider
            </button>
          </template>

          <a
            href="#commentaires-generaux"
            class="ml-auto text-sm font-semibold text-blue-ycube hover:underline"
            @click.prevent="allerAuxCommentairesGeneraux"
          >
            Commentaires généraux ({{ remarquesGenerales.length }})
          </a>
        </div>
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

      </div>

      <!-- Deux colonnes (maquette) : synthèse, détail et justifications à gauche ; panneau du compte à droite. -->
      <div v-if="ipeEtat" class="flex flex-col lg:flex-row gap-6 items-start">
      <div class="flex-1 min-w-0 w-full flex flex-col gap-6">

      <!-- Synthèse (maquette 1_Fiabilite_IPE, docs/PLAN_ecrans_lot1.md §2.2) : un clic sur
           une ligne choisit le module affiché en détail. En-tête bleu marine — charte CLAUDE.md. -->
      <div class="bg-white rounded-xl shadow p-6 flex flex-col gap-4 w-full">
        <h2 class="font-bold text-sm uppercase text-blue-ycube">Synthèse</h2>
        <table class="min-w-full text-sm">
          <thead class="bg-blue-ycube text-white h-12 text-left">
            <tr>
              <th class="px-3">Module</th>
              <th class="px-3">Fichier</th>
              <th class="px-3">Statut</th>
              <th class="px-3 text-right">Écart global</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="ligne in syntheseModules"
              :key="ligne.cle"
              class="h-12 border-b transition"
              :class="[
                ipeEtat.modules?.[ligne.cle] ? 'cursor-pointer hover:bg-gray-50' : '',
                cleModuleAffiche === ligne.cle ? 'bg-gray-50 font-semibold' : '',
              ]"
              :aria-selected="cleModuleAffiche === ligne.cle"
              @click="ipeEtat.modules?.[ligne.cle] && (moduleChoisi = ligne.cle)"
            >
              <td class="px-3">{{ ligne.libelle }}</td>
              <td class="px-3 text-gray-500 font-normal">{{ fichierDuModule(ligne.cle) }}</td>
              <td class="px-3">
                <span
                  class="px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap"
                  :class="ligne.statut ? STATUT_MODULE_INFO[ligne.statut]?.classe : 'bg-gray-100 text-gray-700'"
                >
                  {{ ligne.statut ? STATUT_MODULE_INFO[ligne.statut]?.label : 'Non évalué' }}
                </span>
              </td>
              <td class="px-3 text-right font-mono whitespace-nowrap">{{ formatMontant(ligne.ecartGlobal) }}</td>
            </tr>
          </tbody>
        </table>

      </div>

      <!-- Détail du module choisi (docs/PLAN_ecrans_lot1.md §2.3) -->
      <div class="bg-white rounded-xl shadow p-6 flex flex-col gap-4 w-full">
        <div v-if="ipeEtat.modules && Object.keys(ipeEtat.modules).length" class="flex flex-col gap-4">
          <div v-for="(module, cle) in modulesAffiches" :key="cle" class="text-sm flex flex-col gap-1">
            <div class="flex items-center justify-between flex-wrap gap-2">
              <h2 class="font-bold text-sm uppercase text-blue-ycube">
                {{ (LIBELLES_MODULE[cle] || cle).split(' (')[0] }} · détail {{ estImmobilisations(module) ? 'par compte' : 'par compte collectif' }}
              </h2>
              <div class="flex items-center gap-3">
                <span
                  class="px-3 py-1 rounded-full text-xs font-semibold"
                  :class="STATUT_MODULE_INFO[module.statut]?.classe || 'bg-gray-100 text-gray-700'"
                >
                  {{ STATUT_MODULE_INFO[module.statut]?.label || module.statut }}
                </span>
                <a
                  href="#"
                  class="text-sm font-semibold text-blue-ycube hover:underline"
                  @click.prevent="ouvrirFichiersComplementaires"
                >
                  Voir le fichier dans Fichiers complémentaires
                </a>
              </div>
            </div>

            <div v-if="module.derniere_evaluation" class="mt-3 flex flex-col gap-3 text-gray-600">
              <p v-if="module.statut === 'non_evaluable'" class="italic text-gray-500">
                Non évaluable — {{ module.derniere_evaluation.motif_non_evaluable === 'fichier_complementaire_absent'
                  ? (estImmobilisations(module) ? 'aucun fichier des immobilisations importé.' : 'aucun fichier complémentaire actif pour ce module.')
                  : (estImmobilisations(module) ? 'aucun compte d\'immobilisation trouvé dans la balance générale.' : 'aucun compte collectif trouvé dans la balance générale pour ce module.') }}
              </p>

              <p v-else-if="estImmobilisations(module)" class="text-sm">
                {{ estImmobilisations(module) ? 'Écart global sur les valeurs brutes' : 'Écart global' }} :
                <span class="font-mono font-semibold text-gray-800">{{ formatMontant(module.derniere_evaluation.ecart_global) }}</span>
                <span v-if="estImmobilisations(module)" class="text-gray-500">
                  — comparaison {{ module.derniere_evaluation.mode_comparaison === 'par_compte' ? 'par compte' : 'par total (aucun compte par bien dans le fichier)' }}
                </span>
              </p>

              <!-- IPE-3 : biens vs comptes 20 à 27 (valeur brute) et 28 (amortissements).
                   Granularité, tolérance, dépréciations (29) : TODO(spec: CAC-IPE-01 §3). -->
              <div v-if="estImmobilisations(module) && module.derniere_evaluation.detail_collectifs?.length" class="overflow-x-auto">
              <table class="min-w-full text-sm">
                <thead class="bg-blue-ycube text-white h-12 text-left">
                  <tr>
                    <th class="px-3">Compte</th>
                    <th class="px-3">Nature</th>
                    <th class="px-3 text-right">Balance générale</th>
                    <th class="px-3 text-right">Fichier des immobilisations</th>
                    <th class="px-3 text-right">Biens</th>
                    <th class="px-3 text-right">Écart</th>
                    <th class="px-3">Qualification</th>
                    <th class="px-3">Remarques</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="c in module.derniere_evaluation.detail_collectifs"
                    :key="c.numero_compte"
                    class="h-12 border-b"
                    :class="[
                      module.statut !== 'ecart' ? 'text-gray-500' : (c.ok ? 'text-green-700' : 'text-red-700 cursor-pointer hover:bg-gray-50'),
                      panneau?.cle === cle && panneau?.numeroCompte === c.numero_compte ? '!bg-blue-50' : '',
                    ]"
                    @click="!c.ok && module.statut === 'ecart' && ouvrirPanneau(cle, c.numero_compte)"
                  >
                    <td class="px-3">{{ c.nature === 'controle_vnc' ? '—' : c.numero_compte }}</td>
                    <td class="px-3">{{ NATURE_LIGNE_IMMO[c.nature] || c.nature }}</td>
                    <td class="px-3 text-right font-mono">{{ montantImmo(c, c.solde_balance_generale) }}</td>
                    <td class="px-3 text-right font-mono">{{ montantImmo(c, c.montant_fichier) }}</td>
                    <td class="px-3 text-right">{{ c.nb_biens }}</td>
                    <td class="px-3 text-right font-mono">{{ montantImmo(c, c.ecart) }}</td>
                    <td class="px-3">
                      <span v-if="c.ok || module.statut !== 'ecart'" class="text-gray-400">—</span>
                      <span
                        v-else
                        class="px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap"
                        :class="qualificationComplete(qualificationPour(cle, c.numero_compte)) ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'"
                      >
                        {{ qualificationComplete(qualificationPour(cle, c.numero_compte)) ? 'Qualifiée' : 'À qualifier' }}
                      </span>
                    </td>
                    <td class="px-3">
                      <button
                        v-if="!c.ok && module.statut === 'ecart'"
                        class="px-3 py-1 rounded-lg border border-blue-ycube text-blue-ycube text-xs font-semibold hover:bg-blue-ycube hover:text-white transition inline-flex items-center gap-1 whitespace-nowrap"
                        @click.stop="ouvrirPanneau(cle, c.numero_compte)"
                      >
                        <i class="fa-regular fa-comment"></i> Commenter · {{ remarquesPourCollectif(cle, c.numero_compte).length }}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
              </div>
              <div v-if="estImmobilisations(module) && module.statut !== 'non_evaluable'" class="flex flex-col gap-1 text-sm">
                <p v-if="module.derniere_evaluation.mode_comparaison === 'par_compte' && module.derniere_evaluation.totaux">
                  Totaux — valeurs brutes : balance générale
                  <span class="font-mono">{{ formatMontant(module.derniere_evaluation.totaux.valeur_brute.solde_balance_generale) }}</span>,
                  fichier <span class="font-mono">{{ formatMontant(module.derniere_evaluation.totaux.valeur_brute.montant_fichier) }}</span> ;
                  amortissements : balance générale
                  <span class="font-mono">{{ montantImmo(module.derniere_evaluation.totaux.amortissements, module.derniere_evaluation.totaux.amortissements.solde_balance_generale) }}</span>,
                  fichier <span class="font-mono">{{ montantImmo(module.derniere_evaluation.totaux.amortissements, module.derniere_evaluation.totaux.amortissements.montant_fichier) }}</span>.
                </p>
                <p v-if="!module.derniere_evaluation.controle_vnc?.applicable" class="text-gray-500">
                  Contrôle de la valeur nette non effectué : le fichier ne fournit pas de valeur nette.
                </p>
                <div v-else-if="module.derniere_evaluation.controle_vnc.biens_en_ecart.length" class="text-red-700">
                  Valeur nette ≠ valeur brute − amortissements pour
                  {{ module.derniere_evaluation.controle_vnc.biens_en_ecart.length }} bien(s) sur
                  {{ module.derniere_evaluation.controle_vnc.nb_biens_controles }} :
                  {{ module.derniere_evaluation.controle_vnc.biens_en_ecart.map((e) => `${e.bien} (${formatMontant(e.ecart)})`).join(', ') }}
                </div>
                <p v-else class="text-green-700">
                  Valeur nette cohérente pour les {{ module.derniere_evaluation.controle_vnc.nb_biens_controles }} bien(s) contrôlé(s).
                </p>
                <p v-if="module.derniere_evaluation.biens_sans_compte_correspondant?.length" class="text-red-700">
                  Biens dont le compte n'existe pas dans la balance générale :
                  {{ module.derniere_evaluation.biens_sans_compte_correspondant.join(', ') }}
                </p>
                <p v-if="module.derniere_evaluation.biens_amortis_sans_compte_amortissement?.length" class="text-red-700">
                  Biens amortis sans compte d'amortissement (28) correspondant :
                  {{ module.derniere_evaluation.biens_amortis_sans_compte_amortissement.join(', ') }}
                </p>
                <p class="text-gray-500">Dépréciations (comptes 29) non prises en compte — TODO(spec: CAC-IPE-01 §3).</p>
              </div>

              <div v-if="!estImmobilisations(module) && module.derniere_evaluation.detail_collectifs?.length" class="overflow-x-auto">
              <table class="min-w-full text-sm">
                <thead class="bg-blue-ycube text-white h-12 text-left">
                  <tr>
                    <th class="px-2">Compte</th>
                    <th class="px-2 text-right">Balance générale</th>
                    <th class="px-2 text-right">Auxiliaire</th>
                    <th class="px-2 text-right">Tiers</th>
                    <th class="px-2 text-right">Écart</th>
                    <th class="px-2">Qualification</th>
                    <th class="px-2">Remarques</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="c in module.derniere_evaluation.detail_collectifs"
                    :key="c.numero_compte"
                    class="h-12 border-b text-gray-800"
                    :class="[
                      !c.ok && module.statut === 'ecart' ? 'cursor-pointer hover:bg-gray-50' : '',
                      panneau?.cle === cle && panneau?.numeroCompte === c.numero_compte ? '!bg-blue-50' : '',
                    ]"
                    @click="!c.ok && module.statut === 'ecart' && ouvrirPanneau(cle, c.numero_compte)"
                  >
                    <td class="px-2 font-semibold">{{ c.numero_compte }}</td>
                    <td class="px-2 text-right font-mono whitespace-nowrap">{{ formatMontant(c.solde_balance_generale) }}</td>
                    <td class="px-2 text-right font-mono whitespace-nowrap">{{ formatMontant(c.solde_auxiliaire) }}</td>
                    <td class="px-2 text-right">{{ c.nb_tiers_rattaches }}</td>
                    <td class="px-2 text-right font-mono whitespace-nowrap" :class="!c.ok && module.statut === 'ecart' ? 'font-bold text-red-700' : 'text-gray-500'">{{ formatMontant(c.ecart) }}</td>
                    <td class="px-2">
                      <span v-if="c.ok || module.statut !== 'ecart'" class="text-gray-400">—</span>
                      <span
                        v-else
                        class="px-2 py-1 rounded-full text-xs font-semibold whitespace-nowrap"
                        :class="qualificationComplete(qualificationPour(cle, c.numero_compte)) ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'"
                      >
                        {{ qualificationComplete(qualificationPour(cle, c.numero_compte)) ? 'Qualifiée' : 'À qualifier' }}
                      </span>
                    </td>
                    <td class="px-2">
                      <button
                        v-if="!c.ok && module.statut === 'ecart'"
                        class="px-2 py-1 rounded-lg border border-blue-ycube text-blue-ycube text-xs font-semibold hover:bg-blue-ycube hover:text-white transition inline-flex items-center gap-1 whitespace-nowrap"
                        @click.stop="ouvrirPanneau(cle, c.numero_compte)"
                      >
                        <i class="fa-regular fa-comment"></i> Commenter · {{ remarquesPourCollectif(cle, c.numero_compte).length }}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
              </div>
              <p v-else-if="!estImmobilisations(module) && module.statut !== 'non_evaluable'" class="italic">Aucun compte collectif trouvé dans la balance générale pour ce module.</p>

              <!-- Tiers sans compte collectif (maquette) : traitement attendu TODO(spec: CAC-IPE-01) -->
              <div
                v-if="module.derniere_evaluation.tiers_orphelins?.auxiliaire_seulement?.length || module.derniere_evaluation.tiers_orphelins?.balance_generale_seulement?.length"
                class="flex items-center justify-between gap-3 flex-wrap rounded-lg bg-gray-50 px-4 py-3 text-sm text-gray-700"
              >
                <span>
                  <template v-if="module.derniere_evaluation.tiers_orphelins.auxiliaire_seulement?.length">
                    <strong>{{ module.derniere_evaluation.tiers_orphelins.auxiliaire_seulement.length }} tiers de l'auxiliaire</strong>
                    sans compte collectif dans la balance générale
                    ({{ module.derniere_evaluation.tiers_orphelins.auxiliaire_seulement.slice(0, 3).join(', ') }}{{ module.derniere_evaluation.tiers_orphelins.auxiliaire_seulement.length > 3 ? '…' : '' }}).
                  </template>
                  <template v-if="module.derniere_evaluation.tiers_orphelins.balance_generale_seulement?.length">
                    <strong>{{ module.derniere_evaluation.tiers_orphelins.balance_generale_seulement.length }} compte(s) collectif(s)</strong>
                    sans tiers dans l'auxiliaire.
                  </template>
                  Traitement à confirmer par la spec.
                </span>
                <a href="#" class="font-semibold text-blue-ycube hover:underline" @click.prevent="listeOrphelinsOuverte = true">Voir la liste</a>
              </div>

              <!-- Liste complète — modale, recette ClientsView.vue (charte CLAUDE.md) -->
              <div v-if="listeOrphelinsOuverte" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="listeOrphelinsOuverte = false">
                <div class="bg-white rounded-2xl w-full max-w-3xl p-6 relative max-h-[90vh] overflow-auto flex flex-col gap-4 text-sm">
                  <div class="flex justify-between items-start">
                    <h3 class="text-xl font-bold text-blue-ycube">{{ (LIBELLES_MODULE[cle] || cle).split(' (')[0] }} · rattachements manquants</h3>
                    <button class="text-gray-500 hover:text-gray-800" aria-label="Fermer" @click="listeOrphelinsOuverte = false">
                      <i class="fa-solid fa-xmark text-2xl"></i>
                    </button>
                  </div>
                  <div v-if="module.derniere_evaluation.tiers_orphelins.auxiliaire_seulement?.length">
                    <p class="font-semibold text-gray-800 mb-1">
                      Tiers de l'auxiliaire sans compte collectif dans la balance générale
                      ({{ module.derniere_evaluation.tiers_orphelins.auxiliaire_seulement.length }})
                    </p>
                    <p class="text-gray-700 leading-relaxed">{{ module.derniere_evaluation.tiers_orphelins.auxiliaire_seulement.join(', ') }}</p>
                  </div>
                  <div v-if="module.derniere_evaluation.tiers_orphelins.balance_generale_seulement?.length">
                    <p class="font-semibold text-gray-800 mb-1">
                      Comptes collectifs de la balance générale sans tiers dans l'auxiliaire
                      ({{ module.derniere_evaluation.tiers_orphelins.balance_generale_seulement.length }})
                    </p>
                    <p class="text-gray-700">{{ module.derniere_evaluation.tiers_orphelins.balance_generale_seulement.join(', ') }}</p>
                  </div>
                  <p class="text-xs text-gray-500">Traitement de ces rattachements : à confirmer par la spécification CAC-IPE-01.</p>
                </div>
              </div>
              <p v-if="module.derniere_evaluation.lignes_non_calculables?.length" class="text-orange-600 text-sm">
                {{ module.derniere_evaluation.lignes_non_calculables.length }}
                {{ estImmobilisations(module) ? 'bien(s) sans valeur brute exploitable' : 'ligne(s) auxiliaire(s) sans montant exploitable' }} (mapping incomplet).
              </p>
            </div>
          </div>
        </div>
        <p v-else class="text-sm text-gray-500 italic">
          Aucune évaluation IPE encore lancée pour cette mission.
        </p>
      </div>

      <!-- Modules non évaluables · justification (§2.5) : exigée dès la soumission et à la validation.
           Traitement métier de ces modules : TODO(spec: CAC-IPE-01). -->
      <div v-if="modulesNonEvaluables.length" class="bg-white rounded-xl shadow p-6 flex flex-col gap-4 w-full">
        <h2 class="font-bold text-sm uppercase text-blue-ycube">Modules non évaluables · justification</h2>
        <div v-for="cleModule in modulesNonEvaluables" :key="cleModule" class="flex flex-col gap-2">
          <label :for="`justification-${cleModule}`" class="text-sm font-semibold text-gray-800">
            {{ (LIBELLES_MODULE[cleModule] || cleModule).split(' (')[0] }}
            <span v-if="ipeEtat.justifications_non_evaluables?.[cleModule]" class="font-normal text-gray-500">
              — enregistrée par {{ ipeEtat.justifications_non_evaluables[cleModule].utilisateur_id || 'Non identifié' }},
              {{ formatHorodatage(ipeEtat.justifications_non_evaluables[cleModule].horodatage) }}
            </span>
          </label>
          <div class="flex flex-wrap gap-3 items-start">
            <textarea
              :id="`justification-${cleModule}`"
              v-model="justificationsEnCours[cleModule]"
              :disabled="!peutEditerAuditeur"
              rows="2"
              class="flex-1 min-w-[16rem] text-sm border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-ycube disabled:bg-gray-50"
              :placeholder="`Pourquoi ce module ne peut pas être évalué (au moins ${LONGUEUR_MIN_COMMENTAIRE} caractères)`"
            ></textarea>
            <button
              class="px-5 py-2 rounded-lg bg-blue-ycube text-white text-sm font-semibold hover:bg-blue-900 transition disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="!peutEditerAuditeur || justificationEnCours === cleModule"
              :title="!peutEditerAuditeur ? 'Modifiable uniquement « En cours » ou « En attente de correction »' : ''"
              @click="enregistrerJustification(cleModule)"
            >
              Enregistrer
            </button>
          </div>
        </div>
      </div>
      </div>

      <!-- Panneau du compte en écart (§2.4) : remplace les blocs d'écart sous le tableau.
           Ombre simple + bordure (la charte réserve les ombres marquées aux modales). -->
      <aside
        v-if="lignePanneau"
        :aria-label="`Panneau de qualification du compte ${lignePanneau.ligne.numero_compte}`"
        class="w-full lg:w-[380px] shrink-0 lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)] overflow-y-auto bg-white rounded-xl shadow border border-blue-ycube/20 p-6 flex flex-col gap-4 text-sm"
      >
        <div class="flex justify-between items-start gap-3">
          <div class="flex flex-col gap-1">
            <h2 class="text-lg font-bold text-blue-ycube">Écart · {{ libelleLigneEcart(lignePanneau.module, lignePanneau.ligne) }}</h2>
            <span class="text-gray-500">
              <template v-if="estImmobilisations(lignePanneau.module)">
                {{ montantImmo(lignePanneau.ligne, lignePanneau.ligne.ecart) }} · {{ lignePanneau.ligne.nb_biens }} bien(s)
              </template>
              <template v-else>
                {{ formatMontant(lignePanneau.ligne.ecart) }} · {{ lignePanneau.ligne.nb_tiers_rattaches }} tiers rattaché(s)
              </template>
            </span>
          </div>
          <button class="w-10 h-10 rounded-lg bg-gray-100 text-blue-ycube hover:bg-gray-200 transition" aria-label="Fermer le panneau" @click="fermerPanneau">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>

        <!-- Qualification : cause de la liste provisoire (TODO(spec: CAC-IPE-01)) + commentaire -->
        <div class="flex flex-col gap-3 rounded-lg bg-gray-50 p-4">
          <div class="flex items-center justify-between gap-2">
            <h3 class="font-semibold text-gray-800">Qualification</h3>
            <span
              class="px-3 py-1 rounded-full text-xs font-semibold"
              :class="qualificationComplete(qualificationPour(lignePanneau.cle, lignePanneau.ligne.numero_compte)) ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'"
            >
              {{ qualificationComplete(qualificationPour(lignePanneau.cle, lignePanneau.ligne.numero_compte)) ? 'Qualifiée' : 'À qualifier' }}
            </span>
          </div>
          <label class="flex flex-col gap-1 font-semibold text-gray-700">
            Cause de l'écart
            <select
              v-model="formulairesQualification[`${lignePanneau.cle}:${lignePanneau.ligne.numero_compte}`].cause"
              :disabled="!peutEditerAuditeur"
              class="h-11 border border-gray-300 rounded-lg px-2 font-normal bg-white focus:outline-none focus:ring-2 focus:ring-blue-ycube disabled:bg-gray-50"
            >
              <option value="" disabled>Choisir une cause</option>
              <option v-for="cause in causesEcart" :key="cause" :value="cause">{{ cause }}</option>
            </select>
          </label>
          <label class="flex flex-col gap-1 font-semibold text-gray-700">
            Commentaire
            <textarea
              v-model="formulairesQualification[`${lignePanneau.cle}:${lignePanneau.ligne.numero_compte}`].commentaire"
              :disabled="!peutEditerAuditeur"
              rows="3"
              class="border border-gray-300 rounded-lg p-2 font-normal focus:outline-none focus:ring-2 focus:ring-blue-ycube disabled:bg-gray-50"
              :placeholder="`Expliquer l'écart (au moins ${LONGUEUR_MIN_COMMENTAIRE} caractères)`"
            ></textarea>
          </label>
          <button
            class="h-11 rounded-lg bg-green-ycube-2 text-white font-semibold hover:bg-green-ycube transition disabled:opacity-40 disabled:cursor-not-allowed"
            :disabled="!peutEditerAuditeur || qualificationEnCours === `${lignePanneau.cle}:${lignePanneau.ligne.numero_compte}`"
            :title="!peutEditerAuditeur ? 'Modifiable uniquement « En cours » ou « En attente de correction »' : ''"
            @click="enregistrerQualification(lignePanneau.cle, lignePanneau.ligne.numero_compte)"
          >
            Enregistrer la qualification
          </button>
          <p v-if="qualificationPour(lignePanneau.cle, lignePanneau.ligne.numero_compte)" class="text-xs text-gray-500">
            Qualifiée par {{ qualificationPour(lignePanneau.cle, lignePanneau.ligne.numero_compte).utilisateur_id || 'Non identifié' }},
            {{ formatHorodatage(qualificationPour(lignePanneau.cle, lignePanneau.ligne.numero_compte).horodatage) }}
          </p>
        </div>

        <!-- Fil des remarques (niveau 2) : réponse et « Marquer traitée » conservés (circuit de revue) -->
        <div class="flex flex-col gap-3">
          <h3 class="font-semibold text-gray-800">Remarques ({{ remarquesPourCollectif(lignePanneau.cle, lignePanneau.ligne.numero_compte).length }})</h3>
          <p v-if="!remarquesPourCollectif(lignePanneau.cle, lignePanneau.ligne.numero_compte).length" class="text-gray-500 italic">Aucune remarque.</p>
          <article
            v-for="r in remarquesPourCollectif(lignePanneau.cle, lignePanneau.ligne.numero_compte)"
            :key="r._id"
            class="border border-gray-200 rounded-lg p-3 flex flex-col gap-2"
          >
            <div class="flex justify-between gap-2 flex-wrap">
              <span class="px-2 py-0.5 rounded-full text-xs font-semibold" :class="TYPE_REMARQUE_INFO[r.type]?.classe || TYPE_REMARQUE_INFO.information.classe">
                {{ TYPE_REMARQUE_INFO[r.type]?.label || 'Information' }}
              </span>
              <span class="text-xs text-gray-500">{{ r.utilisateur_id || 'Non identifié' }} · {{ formatHorodatage(r.horodatage) }}</span>
            </div>
            <p class="text-gray-800">{{ r.commentaire }}</p>
            <p v-if="r.reponse" class="ml-3 text-gray-600 italic">
              Réponse de {{ r.reponse.utilisateur_id || 'Non identifié' }} ({{ formatHorodatage(r.reponse.horodatage) }}) : {{ r.reponse.commentaire }}
            </p>
            <div class="flex items-center gap-2 text-xs">
              <span class="px-2 py-0.5 rounded-full font-semibold" :class="r.traitee ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'">
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
            <div v-if="!r.reponse" class="flex gap-2">
              <input
                v-model="reponsesEnCours[r._id]"
                type="text"
                placeholder="Répondre..."
                class="flex-1 border border-gray-300 rounded-lg px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-blue-ycube"
              />
              <button class="text-xs text-blue-ycube font-semibold hover:underline" @click="envoyerReponse(r)">Répondre</button>
            </div>
          </article>

          <label class="flex flex-col gap-1 font-semibold text-gray-700">
            Nouvelle remarque
            <textarea
              v-model="nouvellesRemarquesEcart[`${lignePanneau.cle}:${lignePanneau.ligne.numero_compte}`]"
              rows="2"
              class="border border-gray-300 rounded-lg p-2 font-normal focus:outline-none focus:ring-2 focus:ring-blue-ycube"
              placeholder="Ajouter une remarque sur cet écart"
            ></textarea>
          </label>
          <div class="flex gap-2 flex-wrap">
            <select
              aria-label="Type de remarque"
              :value="typesNouvellesRemarquesEcart[`${lignePanneau.cle}:${lignePanneau.ligne.numero_compte}`] || 'information'"
              class="h-11 border border-gray-300 rounded-lg px-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-ycube"
              @change="typesNouvellesRemarquesEcart[`${lignePanneau.cle}:${lignePanneau.ligne.numero_compte}`] = $event.target.value"
            >
              <option value="information">Information</option>
              <option value="demande_correction" :disabled="!utilisateurIdentifie">Demande de correction</option>
            </select>
            <button
              class="h-11 px-5 rounded-lg bg-blue-ycube text-white font-semibold hover:bg-blue-900 transition"
              @click="ajouterRemarqueEcart(lignePanneau.cle, lignePanneau.ligne.numero_compte)"
            >
              Ajouter
            </button>
          </div>
        </div>
      </aside>
      </div>

      <!-- Commentaire général — niveau 1 des remarques (docs/PLAN_verrou_IPE.md),
           sur le contrôle dans son ensemble, pas sur un écart précis. -->
      <div id="commentaires-generaux" class="bg-white rounded-xl shadow p-6 flex flex-col gap-3 w-full scroll-mt-4" v-if="ipeEtat">
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
