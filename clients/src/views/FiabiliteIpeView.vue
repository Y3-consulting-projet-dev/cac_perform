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
// Couleurs de la maquette 1_Fiabilite_IPE (jetons maquette-*) ; « Validé » / « OK » / « Qualifiée » :
// absents de la maquette, vert de la charte conservé.
const STATUT_CIRCUIT_INFO = {
  en_cours: { label: 'En cours', classe: 'bg-maquette-gris text-maquette-ardoise' },
  soumis_pour_revue: { label: 'Soumis pour revue', classe: 'bg-maquette-attente-fond text-maquette-attente' },
  en_attente_correction: { label: 'En attente de correction', classe: 'bg-maquette-ecart-fond text-maquette-ecart' },
  valide: { label: 'Validé', classe: 'bg-green-100 text-green-700' },
}

// 3 statuts visuels distincts (module ou ligne de collectif) — le rouge est
// réservé aux vrais écarts, jamais à "rien à comparer" (fichier absent,
// aucun collectif trouvé). Mêmes couleurs que les badges de statut de
// mission (MissionsView.vue) — charte d'interface, CLAUDE.md.
const STATUT_MODULE_INFO = {
  ok: { label: 'OK', classe: 'bg-green-100 text-green-700' },
  ecart: { label: 'Écart', classe: 'bg-maquette-ecart-fond text-maquette-ecart' },
  non_evaluable: { label: 'Non évaluable', classe: 'bg-maquette-gris text-maquette-ardoise' },
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
  information: { label: 'Information', classe: 'bg-maquette-attente-fond text-maquette-attente' },
  demande_correction: { label: 'Demande de correction', classe: 'bg-maquette-ecart-fond text-maquette-ecart' },
}

// Numéro affiché d'un compte collectif : celui de la balance générale (« 401000 », maquette),
// le collectif normalisé (« 401 ») restant la clé des qualifications et remarques.
// Rapprochement antérieur à cette donnée : collectif normalisé.
function numeroBalanceGenerale(ligne) {
  return ligne?.comptes_balance_generale?.length ? ligne.comptes_balance_generale.join(', ') : ligne?.numero_compte
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
  <!-- Mise en page et couleurs de la maquette docs/maquettes/1_Fiabilite_IPE.html (référence visuelle,
       avant la charte) : jetons maquette-* de style.css, police Nunito Sans. Aucune logique changée. -->
  <div class="h-full w-full overflow-y-auto bg-maquette-fond font-maquette text-maquette-texte">
    <div class="p-7 flex flex-col gap-5">

      <!-- En-tête : carte centrée (maquette) ; « Retour » seulement hors de la barre latérale -->
      <section class="relative bg-white rounded-[14px] shadow-[0_1px_3px_rgba(15,58,90,0.08)] px-7 py-6 flex flex-col gap-1.5 text-center">
        <button
          v-if="!integre"
          class="absolute left-7 top-1/2 -translate-y-1/2 text-maquette-marine font-semibold hover:underline flex items-center gap-2"
          @click="back"
        >
          <i class="fa-solid fa-arrow-left"></i> Retour
        </button>
        <h1 class="m-0 text-[26px] font-bold text-maquette-marine">Fiabilité IPE</h1>
        <p class="m-0 text-maquette-texte-doux">{{ sousTitreEnTete }}</p>
      </section>

      <!-- Circuit de revue (docs/PLAN_ecrans_lot1.md §2.1) : quatre étapes, l'étape en cours mise en avant ;
           seules les actions du statut courant, l'action attendue visible avec la raison du blocage.
           Le serveur reste juge (revue_ipe_service). TODO(décision) : qui peut soumettre, valider,
           demander une correction n'est pas vérifié. -->
      <section v-if="ipeEtat" class="bg-white rounded-[14px] shadow-[0_1px_3px_rgba(15,58,90,0.08)] px-7 py-6 flex flex-col gap-[18px]">
        <div class="flex items-center justify-between gap-3 flex-wrap">
          <h2 class="m-0 text-[17px] font-bold tracking-[0.3px] uppercase text-maquette-marine">Circuit de revue</h2>
          <span
            class="px-3 py-1 rounded-full text-[13px] font-semibold"
            :class="ipeEtat.verrou_applicable ? (STATUT_CIRCUIT_INFO[statutCircuit]?.classe || 'bg-maquette-gris text-maquette-ardoise') : 'bg-maquette-gris text-maquette-ardoise'"
            :title="ipeEtat.verrou_applicable ? '' : 'Mission antérieure à l\'activation du verrou IPE : jamais bloquée, ce rapprochement reste informatif.'"
          >
            {{ IPE_STATUT_LABELS[ipeEtat.statut_affiche] || 'Non commencé' }}
          </span>
        </div>

        <ol class="list-none m-0 p-0 grid grid-cols-2 lg:grid-cols-4 gap-2">
          <li
            v-for="(etape, i) in ETAPES_CIRCUIT"
            :key="etape.cle"
            class="px-3.5 py-3 rounded-[10px] text-sm flex items-center gap-2"
            :class="statutCircuit === etape.cle ? 'bg-maquette-marine text-white font-bold' : 'bg-maquette-gris text-maquette-ardoise font-semibold'"
            :aria-current="statutCircuit === etape.cle ? 'step' : null"
          >
            <i v-if="etapesFranchies.has(etape.cle)" class="fa-solid fa-check text-maquette-vert"></i>
            {{ i + 1 }} · {{ etape.libelle }}
          </li>
        </ol>

        <p v-if="!ipeEtat.verrou_applicable" class="m-0 -mt-1.5 text-[13px] text-maquette-texte-doux">
          Mission antérieure à l'activation du verrou IPE : jamais bloquée, ce rapprochement reste informatif.
        </p>

        <div class="flex items-center gap-3 flex-wrap">
          <template v-if="statutCircuit === 'en_cours' || statutCircuit === 'en_attente_correction'">
            <button
              class="h-[46px] px-[22px] rounded-[10px] bg-maquette-marine text-white text-[15px] font-bold hover:bg-maquette-marine-fonce transition disabled:bg-maquette-champ disabled:text-maquette-ardoise disabled:cursor-not-allowed"
              :disabled="ipeEvaluationEnCours"
              @click="lancerEvaluationIpe"
            >
              {{ ipeEvaluationEnCours ? 'Rapprochement en cours...' : (rapprochementLance ? 'Relancer le rapprochement' : 'Lancer le rapprochement') }}
            </button>
            <button
              class="h-[46px] px-[22px] rounded-[10px] bg-maquette-marine text-white text-[15px] font-bold hover:bg-maquette-marine-fonce transition disabled:bg-maquette-champ disabled:text-maquette-ardoise disabled:cursor-not-allowed"
              :disabled="soumissionEnCours || !peutSoumettre"
              @click="soumettrePourRevue"
            >
              {{ soumissionEnCours ? 'Soumission en cours...' : 'Soumettre pour revue' }}
            </button>
            <span v-if="raisonSoumission" class="text-sm text-maquette-attente bg-maquette-attente-fond px-3 py-2 rounded-lg">{{ raisonSoumission }}</span>
          </template>

          <template v-else-if="statutCircuit === 'soumis_pour_revue'">
            <button
              class="h-[46px] px-[22px] rounded-[10px] border border-maquette-ecart bg-white text-maquette-ecart text-[15px] font-bold hover:bg-maquette-ecart-fond transition disabled:border-maquette-champ disabled:text-maquette-ardoise disabled:bg-white disabled:cursor-not-allowed"
              :disabled="!peutDemanderCorrection"
              :title="!utilisateurIdentifie ? 'Utilisateur non identifié : impossible de créer une demande de correction' : ''"
              @click="ouvrirDemandeCorrection"
            >
              Demander une correction
            </button>
            <button
              class="h-[46px] px-[22px] rounded-[10px] bg-maquette-vert text-white text-[15px] font-bold hover:brightness-95 transition disabled:bg-maquette-champ disabled:text-maquette-ardoise disabled:cursor-not-allowed"
              :disabled="ipeValidationEnCours || !peutValider"
              @click="ouvrirConfirmationValidation"
            >
              Valider la fiabilité IPE
            </button>
            <span v-if="raisonValidation" class="text-sm text-maquette-attente bg-maquette-attente-fond px-3 py-2 rounded-lg">{{ raisonValidation }}</span>
            <span v-if="!utilisateurIdentifie" class="text-sm text-maquette-ardoise bg-maquette-gris px-3 py-2 rounded-lg">
              Connectez-vous pour demander une correction
            </span>
          </template>

          <template v-else-if="statutCircuit === 'valide'">
            <button
              class="h-[46px] px-[22px] rounded-[10px] border border-maquette-champ bg-white text-maquette-ardoise text-[15px] font-bold hover:bg-maquette-gris transition disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="ipeValidationEnCours"
              @click="ouvrirConfirmationInvalidation"
            >
              Invalider
            </button>
          </template>

          <a
            href="#commentaires-generaux"
            class="ml-auto text-sm font-semibold text-maquette-marine underline hover:text-maquette-marine-fonce"
            @click.prevent="allerAuxCommentairesGeneraux"
          >
            Commentaires généraux ({{ remarquesGenerales.length }})
          </a>
        </div>

        <!-- Confirmations (commentaire obligatoire, enregistré dans l'historique) -->
        <div v-if="confirmationDemandeCorrectionOuverte" class="rounded-xl bg-maquette-ecart-fond p-4 flex flex-col gap-2.5">
          <p class="m-0 text-[15px] font-bold text-maquette-ecart">Confirmer la demande de correction</p>
          <textarea
            v-model="commentaireDemandeCorrection"
            rows="2"
            class="text-[15px] px-3 py-2.5 border border-maquette-champ rounded-[10px] bg-white resize-y focus:outline-none focus:ring-2 focus:ring-maquette-marine"
            placeholder="Commentaire (obligatoire, enregistré dans l'historique)"
          ></textarea>
          <div class="flex gap-3">
            <button
              class="h-11 px-[18px] rounded-[10px] bg-maquette-ecart text-white font-bold hover:brightness-95 transition disabled:opacity-50"
              :disabled="demandeCorrectionEnCours"
              @click="confirmerDemandeCorrection"
            >
              Confirmer
            </button>
            <button class="h-11 px-[18px] rounded-[10px] border border-maquette-champ bg-white text-maquette-ardoise font-bold hover:bg-maquette-gris transition" @click="annulerDemandeCorrection">
              Annuler
            </button>
          </div>
        </div>

        <div v-if="confirmationValidationOuverte" class="rounded-xl bg-maquette-clair p-4 flex flex-col gap-2.5">
          <p class="m-0 text-[15px] font-bold text-maquette-marine">Confirmer la validation de la fiabilité IPE</p>
          <textarea
            v-model="commentaireValidation"
            rows="2"
            class="text-[15px] px-3 py-2.5 border border-maquette-champ rounded-[10px] bg-white resize-y focus:outline-none focus:ring-2 focus:ring-maquette-marine"
            placeholder="Commentaire (obligatoire, enregistré dans l'historique)"
          ></textarea>
          <div class="flex gap-3">
            <button
              class="h-11 px-[18px] rounded-[10px] bg-maquette-vert text-white font-bold hover:brightness-95 transition disabled:opacity-50"
              :disabled="ipeValidationEnCours"
              @click="confirmerValidation"
            >
              Confirmer
            </button>
            <button class="h-11 px-[18px] rounded-[10px] border border-maquette-champ bg-white text-maquette-ardoise font-bold hover:bg-maquette-gris transition" @click="annulerValidation">
              Annuler
            </button>
          </div>
        </div>

        <div v-if="confirmationInvalidationOuverte" class="rounded-xl bg-maquette-clair p-4 flex flex-col gap-2.5">
          <p class="m-0 text-[15px] font-bold text-maquette-ardoise">Confirmer l'invalidation de la fiabilité IPE ?</p>
          <textarea
            v-model="commentaireInvalidation"
            rows="2"
            class="text-[15px] px-3 py-2.5 border border-maquette-champ rounded-[10px] bg-white resize-y focus:outline-none focus:ring-2 focus:ring-maquette-marine"
            placeholder="Commentaire (obligatoire, enregistré dans l'historique)"
          ></textarea>
          <div class="flex gap-3">
            <button
              class="h-11 px-[18px] rounded-[10px] bg-maquette-marine text-white font-bold hover:bg-maquette-marine-fonce transition disabled:opacity-50"
              :disabled="ipeValidationEnCours"
              @click="confirmerInvalidation"
            >
              Confirmer
            </button>
            <button class="h-11 px-[18px] rounded-[10px] border border-maquette-champ bg-white text-maquette-ardoise font-bold hover:bg-maquette-gris transition" @click="annulerInvalidation">
              Annuler
            </button>
          </div>
        </div>
      </section>

      <!-- Deux colonnes (maquette) : synthèse, détail et justifications à gauche ; panneau du compte à droite. -->
      <div v-if="ipeEtat" class="flex gap-5 flex-wrap items-start">
        <div class="flex-[999_1_560px] min-w-0 flex flex-col gap-5">

          <!-- Synthèse (§2.2) : un clic sur une ligne choisit le module affiché en détail -->
          <section class="bg-white rounded-[14px] shadow-[0_1px_3px_rgba(15,58,90,0.08)] px-7 py-6 flex flex-col gap-3.5">
            <h2 class="m-0 text-[17px] font-bold tracking-[0.3px] uppercase text-maquette-marine">Synthèse</h2>
            <div class="overflow-x-auto">
              <table class="w-full border-collapse text-[15px]">
                <thead>
                  <tr class="bg-maquette-marine text-white text-left">
                    <th class="px-4 py-3.5">Module</th>
                    <th class="px-4 py-3.5">Fichier</th>
                    <th class="px-4 py-3.5">Statut</th>
                    <th class="px-4 py-3.5 text-right">Écart global</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(ligne, i) in syntheseModules"
                    :key="ligne.cle"
                    class="transition"
                    :class="[
                      i < syntheseModules.length - 1 ? 'border-b border-maquette-trait' : '',
                      ipeEtat.modules?.[ligne.cle] ? 'cursor-pointer hover:bg-maquette-clair' : '',
                      cleModuleAffiche === ligne.cle ? 'bg-maquette-clair' : '',
                    ]"
                    :aria-selected="cleModuleAffiche === ligne.cle"
                    @click="ipeEtat.modules?.[ligne.cle] && (moduleChoisi = ligne.cle)"
                  >
                    <td class="px-4 py-3.5" :class="cleModuleAffiche === ligne.cle ? 'font-bold' : ''">{{ ligne.libelle }}</td>
                    <td class="px-4 py-3.5 text-maquette-texte-doux">{{ fichierDuModule(ligne.cle) }}</td>
                    <td class="px-4 py-3.5">
                      <span
                        class="px-2.5 py-1 rounded-full text-[13px] font-bold whitespace-nowrap"
                        :class="ligne.statut ? STATUT_MODULE_INFO[ligne.statut]?.classe : 'bg-maquette-gris text-maquette-ardoise'"
                      >
                        {{ ligne.statut ? STATUT_MODULE_INFO[ligne.statut]?.label : 'Non évalué' }}
                      </span>
                    </td>
                    <td class="px-4 py-3.5 text-right tabular-nums whitespace-nowrap" :class="ligne.ecartGlobal === null ? 'text-maquette-texte-doux' : ''">
                      {{ ligne.ecartGlobal === null ? '—' : formatMontant(ligne.ecartGlobal) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <!-- Détail du module choisi (§2.3) -->
          <section class="bg-white rounded-[14px] shadow-[0_1px_3px_rgba(15,58,90,0.08)] px-7 py-6 flex flex-col gap-3.5">
            <template v-if="ipeEtat.modules && Object.keys(ipeEtat.modules).length">
              <template v-for="(module, cle) in modulesAffiches" :key="cle">
                <div class="flex justify-between items-center gap-3 flex-wrap">
                  <h2 class="m-0 text-[17px] font-bold tracking-[0.3px] uppercase text-maquette-marine flex items-center gap-3">
                    {{ (LIBELLES_MODULE[cle] || cle).split(' (')[0] }} · détail {{ estImmobilisations(module) ? 'par compte' : 'par compte collectif' }}
                    <span
                      class="px-2.5 py-1 rounded-full text-[13px] font-bold normal-case tracking-normal"
                      :class="STATUT_MODULE_INFO[module.statut]?.classe || 'bg-maquette-gris text-maquette-ardoise'"
                    >
                      {{ STATUT_MODULE_INFO[module.statut]?.label || module.statut }}
                    </span>
                  </h2>
                  <a href="#" class="text-sm font-semibold text-maquette-marine underline hover:text-maquette-marine-fonce" @click.prevent="ouvrirFichiersComplementaires">
                    Voir le fichier dans Fichiers complémentaires
                  </a>
                </div>

                <template v-if="module.derniere_evaluation">
                  <p v-if="module.statut === 'non_evaluable'" class="m-0 text-sm text-maquette-texte-doux">
                    Non évaluable — {{ module.derniere_evaluation.motif_non_evaluable === 'fichier_complementaire_absent'
                      ? (estImmobilisations(module) ? 'aucun fichier des immobilisations importé.' : 'aucun fichier complémentaire actif pour ce module.')
                      : (estImmobilisations(module) ? 'aucun compte d\'immobilisation trouvé dans la balance générale.' : 'aucun compte collectif trouvé dans la balance générale pour ce module.') }}
                    Justification à écrire dans « Modules non évaluables ».
                  </p>

                  <p v-else-if="estImmobilisations(module)" class="m-0 text-sm text-maquette-ardoise">
                    Écart global sur les valeurs brutes :
                    <span class="font-bold tabular-nums">{{ formatMontant(module.derniere_evaluation.ecart_global) }}</span>
                    — comparaison {{ module.derniere_evaluation.mode_comparaison === 'par_compte' ? 'par compte' : 'par total (aucun compte par bien dans le fichier)' }}
                  </p>

                  <!-- IPE-3 : biens vs comptes 20 à 27 (valeur brute) et 28 (amortissements).
                       Granularité, tolérance, dépréciations (29) : TODO(spec: CAC-IPE-01 §3). -->
                  <div v-if="estImmobilisations(module) && module.derniere_evaluation.detail_collectifs?.length" class="overflow-x-auto">
                    <table class="w-full border-collapse text-[15px]">
                      <thead>
                        <tr class="bg-maquette-marine text-white text-left">
                          <th class="px-4 py-3.5">Compte</th>
                          <th class="px-4 py-3.5">Nature</th>
                          <th class="px-4 py-3.5 text-right">Balance générale</th>
                          <th class="px-4 py-3.5 text-right">Fichier</th>
                          <th class="px-4 py-3.5 text-right">Biens</th>
                          <th class="px-4 py-3.5 text-right">Écart</th>
                          <th class="px-4 py-3.5">Qualification</th>
                          <th class="px-4 py-3.5">Remarques</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="c in module.derniere_evaluation.detail_collectifs"
                          :key="c.numero_compte"
                          class="border-b border-maquette-trait"
                          :class="[
                            !c.ok && module.statut === 'ecart' ? 'cursor-pointer hover:bg-maquette-clair' : '',
                            panneau?.cle === cle && panneau?.numeroCompte === c.numero_compte ? '!bg-maquette-selection' : '',
                          ]"
                          @click="!c.ok && module.statut === 'ecart' && ouvrirPanneau(cle, c.numero_compte)"
                        >
                          <td class="px-4 py-3.5 font-bold">{{ c.nature === 'controle_vnc' ? '—' : c.numero_compte }}</td>
                          <td class="px-4 py-3.5">{{ NATURE_LIGNE_IMMO[c.nature] || c.nature }}</td>
                          <td class="px-4 py-3.5 text-right tabular-nums whitespace-nowrap">{{ montantImmo(c, c.solde_balance_generale) }}</td>
                          <td class="px-4 py-3.5 text-right tabular-nums whitespace-nowrap">{{ montantImmo(c, c.montant_fichier) }}</td>
                          <td class="px-4 py-3.5 text-right">{{ c.nb_biens }}</td>
                          <td class="px-4 py-3.5 text-right tabular-nums whitespace-nowrap" :class="!c.ok && module.statut === 'ecart' ? 'font-bold text-maquette-ecart' : 'text-maquette-texte-doux'">{{ montantImmo(c, c.ecart) }}</td>
                          <td class="px-4 py-3.5">
                            <span v-if="c.ok || module.statut !== 'ecart'" class="text-maquette-texte-doux">—</span>
                            <span
                              v-else
                              class="px-2.5 py-1 rounded-full text-[13px] font-bold whitespace-nowrap"
                              :class="qualificationComplete(qualificationPour(cle, c.numero_compte)) ? 'bg-green-100 text-green-700' : 'bg-maquette-attente-fond text-maquette-attente'"
                            >
                              {{ qualificationComplete(qualificationPour(cle, c.numero_compte)) ? 'Qualifiée' : 'À qualifier' }}
                            </span>
                          </td>
                          <td class="px-4 py-3.5">
                            <button
                              v-if="!c.ok && module.statut === 'ecart'"
                              class="h-9 px-3 rounded-lg border border-maquette-marine bg-white text-maquette-marine font-bold inline-flex items-center gap-1.5 whitespace-nowrap hover:bg-maquette-clair transition"
                              @click.stop="ouvrirPanneau(cle, c.numero_compte)"
                            >
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z" /></svg>
                              Commenter · {{ remarquesPourCollectif(cle, c.numero_compte).length }}
                            </button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div v-if="estImmobilisations(module) && module.statut !== 'non_evaluable'" class="flex flex-col gap-1 text-sm text-maquette-ardoise">
                    <p v-if="module.derniere_evaluation.mode_comparaison === 'par_compte' && module.derniere_evaluation.totaux" class="m-0">
                      Totaux — valeurs brutes : balance générale
                      <span class="tabular-nums">{{ formatMontant(module.derniere_evaluation.totaux.valeur_brute.solde_balance_generale) }}</span>,
                      fichier <span class="tabular-nums">{{ formatMontant(module.derniere_evaluation.totaux.valeur_brute.montant_fichier) }}</span> ;
                      amortissements : balance générale
                      <span class="tabular-nums">{{ montantImmo(module.derniere_evaluation.totaux.amortissements, module.derniere_evaluation.totaux.amortissements.solde_balance_generale) }}</span>,
                      fichier <span class="tabular-nums">{{ montantImmo(module.derniere_evaluation.totaux.amortissements, module.derniere_evaluation.totaux.amortissements.montant_fichier) }}</span>.
                    </p>
                    <p v-if="!module.derniere_evaluation.controle_vnc?.applicable" class="m-0 text-maquette-texte-doux">
                      Contrôle de la valeur nette non effectué : le fichier ne fournit pas de valeur nette.
                    </p>
                    <p v-else-if="module.derniere_evaluation.controle_vnc.biens_en_ecart.length" class="m-0 text-maquette-ecart">
                      Valeur nette ≠ valeur brute − amortissements pour
                      {{ module.derniere_evaluation.controle_vnc.biens_en_ecart.length }} bien(s) sur
                      {{ module.derniere_evaluation.controle_vnc.nb_biens_controles }} :
                      {{ module.derniere_evaluation.controle_vnc.biens_en_ecart.map((e) => `${e.bien} (${formatMontant(e.ecart)})`).join(', ') }}
                    </p>
                    <p v-else class="m-0 text-green-700">
                      Valeur nette cohérente pour les {{ module.derniere_evaluation.controle_vnc.nb_biens_controles }} bien(s) contrôlé(s).
                    </p>
                    <p v-if="module.derniere_evaluation.biens_sans_compte_correspondant?.length" class="m-0 text-maquette-ecart">
                      Biens dont le compte n'existe pas dans la balance générale :
                      {{ module.derniere_evaluation.biens_sans_compte_correspondant.join(', ') }}
                    </p>
                    <p v-if="module.derniere_evaluation.biens_amortis_sans_compte_amortissement?.length" class="m-0 text-maquette-ecart">
                      Biens amortis sans compte d'amortissement (28) correspondant :
                      {{ module.derniere_evaluation.biens_amortis_sans_compte_amortissement.join(', ') }}
                    </p>
                    <p class="m-0 text-maquette-texte-doux">Dépréciations (comptes 29) non prises en compte — TODO(spec: CAC-IPE-01 §3).</p>
                  </div>

                  <!-- Tiers (IPE-1, IPE-2) : compte de la balance générale (« 401000 »), comme la maquette -->
                  <div v-if="!estImmobilisations(module) && module.derniere_evaluation.detail_collectifs?.length" class="overflow-x-auto">
                    <table class="w-full border-collapse text-[15px]">
                      <thead>
                        <tr class="bg-maquette-marine text-white text-left">
                          <th class="px-4 py-3.5">Compte</th>
                          <th class="px-4 py-3.5 text-right">Balance générale</th>
                          <th class="px-4 py-3.5 text-right">Auxiliaire</th>
                          <th class="px-4 py-3.5 text-right">Tiers</th>
                          <th class="px-4 py-3.5 text-right">Écart</th>
                          <th class="px-4 py-3.5">Qualification</th>
                          <th class="px-4 py-3.5">Remarques</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="c in module.derniere_evaluation.detail_collectifs"
                          :key="c.numero_compte"
                          class="border-b border-maquette-trait"
                          :class="[
                            !c.ok && module.statut === 'ecart' ? 'cursor-pointer hover:bg-maquette-clair' : '',
                            panneau?.cle === cle && panneau?.numeroCompte === c.numero_compte ? '!bg-maquette-selection' : '',
                          ]"
                          @click="!c.ok && module.statut === 'ecart' && ouvrirPanneau(cle, c.numero_compte)"
                        >
                          <td class="px-4 py-3.5 font-bold" :data-collectif="c.numero_compte">{{ numeroBalanceGenerale(c) }}</td>
                          <td class="px-4 py-3.5 text-right tabular-nums whitespace-nowrap">{{ formatMontant(c.solde_balance_generale) }}</td>
                          <td class="px-4 py-3.5 text-right tabular-nums whitespace-nowrap">{{ formatMontant(c.solde_auxiliaire) }}</td>
                          <td class="px-4 py-3.5 text-right">{{ c.nb_tiers_rattaches }}</td>
                          <td class="px-4 py-3.5 text-right tabular-nums whitespace-nowrap" :class="!c.ok && module.statut === 'ecart' ? 'font-bold text-maquette-ecart' : 'text-maquette-texte-doux'">{{ formatMontant(c.ecart) }}</td>
                          <td class="px-4 py-3.5">
                            <span v-if="c.ok || module.statut !== 'ecart'" class="text-maquette-texte-doux">—</span>
                            <span
                              v-else
                              class="px-2.5 py-1 rounded-full text-[13px] font-bold whitespace-nowrap"
                              :class="qualificationComplete(qualificationPour(cle, c.numero_compte)) ? 'bg-green-100 text-green-700' : 'bg-maquette-attente-fond text-maquette-attente'"
                            >
                              {{ qualificationComplete(qualificationPour(cle, c.numero_compte)) ? 'Qualifiée' : 'À qualifier' }}
                            </span>
                          </td>
                          <td class="px-4 py-3.5">
                            <button
                              v-if="!c.ok && module.statut === 'ecart'"
                              class="h-9 px-3 rounded-lg border border-maquette-marine bg-white text-maquette-marine font-bold inline-flex items-center gap-1.5 whitespace-nowrap hover:bg-maquette-clair transition"
                              @click.stop="ouvrirPanneau(cle, c.numero_compte)"
                            >
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z" /></svg>
                              Commenter · {{ remarquesPourCollectif(cle, c.numero_compte).length }}
                            </button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <p v-else-if="!estImmobilisations(module) && module.statut !== 'non_evaluable'" class="m-0 text-sm text-maquette-texte-doux">
                    Aucun compte collectif trouvé dans la balance générale pour ce module.
                  </p>

                  <!-- Tiers sans compte collectif : traitement attendu TODO(spec: CAC-IPE-01) -->
                  <div
                    v-if="module.derniere_evaluation.tiers_orphelins?.auxiliaire_seulement?.length || module.derniere_evaluation.tiers_orphelins?.balance_generale_seulement?.length"
                    class="flex items-center justify-between gap-3 flex-wrap px-4 py-3.5 rounded-[10px] bg-maquette-clair"
                  >
                    <span class="text-sm text-maquette-ardoise">
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
                    <a href="#" class="text-sm font-semibold text-maquette-marine underline hover:text-maquette-marine-fonce" @click.prevent="listeOrphelinsOuverte = true">Voir la liste</a>
                  </div>

                  <!-- Liste complète (modale) -->
                  <div v-if="listeOrphelinsOuverte" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="listeOrphelinsOuverte = false">
                    <div class="bg-white rounded-[14px] w-full max-w-3xl p-6 relative max-h-[90vh] overflow-auto flex flex-col gap-4 text-sm shadow-[0_8px_24px_rgba(15,58,90,0.16)]">
                      <div class="flex justify-between items-start gap-3">
                        <h3 class="m-0 text-lg font-bold text-maquette-marine">{{ (LIBELLES_MODULE[cle] || cle).split(' (')[0] }} · rattachements manquants</h3>
                        <button class="w-11 h-11 rounded-[10px] bg-maquette-fond text-maquette-marine hover:bg-maquette-gris transition" aria-label="Fermer" @click="listeOrphelinsOuverte = false">
                          <i class="fa-solid fa-xmark"></i>
                        </button>
                      </div>
                      <div v-if="module.derniere_evaluation.tiers_orphelins.auxiliaire_seulement?.length">
                        <p class="m-0 mb-1 font-bold">
                          Tiers de l'auxiliaire sans compte collectif dans la balance générale
                          ({{ module.derniere_evaluation.tiers_orphelins.auxiliaire_seulement.length }})
                        </p>
                        <p class="m-0 text-maquette-ardoise leading-relaxed">{{ module.derniere_evaluation.tiers_orphelins.auxiliaire_seulement.join(', ') }}</p>
                      </div>
                      <div v-if="module.derniere_evaluation.tiers_orphelins.balance_generale_seulement?.length">
                        <p class="m-0 mb-1 font-bold">
                          Comptes collectifs de la balance générale sans tiers dans l'auxiliaire
                          ({{ module.derniere_evaluation.tiers_orphelins.balance_generale_seulement.length }})
                        </p>
                        <p class="m-0 text-maquette-ardoise">{{ module.derniere_evaluation.tiers_orphelins.balance_generale_seulement.join(', ') }}</p>
                      </div>
                      <p class="m-0 text-xs text-maquette-texte-doux">Traitement de ces rattachements : à confirmer par la spécification CAC-IPE-01.</p>
                    </div>
                  </div>
                  <p v-if="module.derniere_evaluation.lignes_non_calculables?.length" class="m-0 text-sm text-maquette-attente">
                    {{ module.derniere_evaluation.lignes_non_calculables.length }}
                    {{ estImmobilisations(module) ? 'bien(s) sans valeur brute exploitable' : 'ligne(s) auxiliaire(s) sans montant exploitable' }} (mapping incomplet).
                  </p>
                </template>
              </template>
            </template>
            <p v-else class="m-0 text-sm text-maquette-texte-doux">Aucune évaluation IPE encore lancée pour cette mission.</p>
          </section>

          <!-- Modules non évaluables · justification (§2.5) : exigée dès la soumission et à la validation.
               Traitement métier : TODO(spec: CAC-IPE-01). -->
          <section v-if="modulesNonEvaluables.length" class="bg-white rounded-[14px] shadow-[0_1px_3px_rgba(15,58,90,0.08)] px-7 py-6 flex flex-col gap-3">
            <h2 class="m-0 text-[17px] font-bold tracking-[0.3px] uppercase text-maquette-marine">Modules non évaluables · justification</h2>
            <div v-for="cleModule in modulesNonEvaluables" :key="cleModule" class="flex flex-col gap-1.5">
              <label :for="`justification-${cleModule}`" class="text-sm font-bold">
                {{ (LIBELLES_MODULE[cleModule] || cleModule).split(' (')[0] }}
                <span v-if="ipeEtat.justifications_non_evaluables?.[cleModule]" class="font-normal text-maquette-texte-doux">
                  — enregistrée par {{ ipeEtat.justifications_non_evaluables[cleModule].utilisateur_id || 'Non identifié' }},
                  {{ formatHorodatage(ipeEtat.justifications_non_evaluables[cleModule].horodatage) }}
                </span>
              </label>
              <textarea
                :id="`justification-${cleModule}`"
                v-model="justificationsEnCours[cleModule]"
                :disabled="!peutEditerAuditeur"
                rows="2"
                class="text-[15px] px-3 py-2.5 border border-maquette-champ rounded-[10px] resize-y focus:outline-none focus:ring-2 focus:ring-maquette-marine disabled:bg-maquette-clair"
                :placeholder="`Pourquoi ce module ne peut pas être évalué (au moins ${LONGUEUR_MIN_COMMENTAIRE} caractères)`"
              ></textarea>
              <div>
                <button
                  class="h-10 px-4 rounded-[10px] bg-maquette-marine text-white text-sm font-bold hover:bg-maquette-marine-fonce transition disabled:bg-maquette-champ disabled:text-maquette-ardoise disabled:cursor-not-allowed"
                  :disabled="!peutEditerAuditeur || justificationEnCours === cleModule"
                  :title="!peutEditerAuditeur ? 'Modifiable uniquement « En cours » ou « En attente de correction »' : ''"
                  @click="enregistrerJustification(cleModule)"
                >
                  Enregistrer
                </button>
              </div>
            </div>
          </section>
        </div>

        <!-- Panneau du compte en écart (§2.4) : à droite du détail, ombre de la maquette -->
        <aside
          v-if="lignePanneau"
          :aria-label="`Panneau de qualification du compte ${numeroBalanceGenerale(lignePanneau.ligne)}`"
          class="flex-[1_1_380px] max-w-[460px] lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)] overflow-y-auto bg-white rounded-[14px] shadow-[0_8px_24px_rgba(15,58,90,0.16)] p-6 flex flex-col gap-4"
        >
          <div class="flex justify-between items-start gap-3">
            <div class="flex flex-col gap-1">
              <h2 class="m-0 text-lg font-bold text-maquette-marine">
                Écart · {{ estImmobilisations(lignePanneau.module) ? libelleLigneEcart(lignePanneau.module, lignePanneau.ligne) : `compte ${numeroBalanceGenerale(lignePanneau.ligne)}` }}
              </h2>
              <span class="text-sm text-maquette-texte-doux">
                <template v-if="estImmobilisations(lignePanneau.module)">
                  {{ montantImmo(lignePanneau.ligne, lignePanneau.ligne.ecart) }} · {{ lignePanneau.ligne.nb_biens }} bien(s)
                </template>
                <template v-else>
                  {{ formatMontant(lignePanneau.ligne.ecart) }} · {{ lignePanneau.ligne.nb_tiers_rattaches }} tiers rattaché{{ lignePanneau.ligne.nb_tiers_rattaches > 1 ? 's' : '' }}
                </template>
              </span>
            </div>
            <button class="w-11 h-11 shrink-0 rounded-[10px] bg-maquette-fond text-maquette-marine hover:bg-maquette-gris transition flex items-center justify-center" aria-label="Fermer le panneau" @click="fermerPanneau">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg>
            </button>
          </div>

          <!-- Qualification : cause de la liste provisoire (TODO(spec: CAC-IPE-01)) + commentaire -->
          <div class="flex flex-col gap-2.5 p-4 rounded-xl bg-maquette-clair">
            <div class="flex items-center justify-between gap-2">
              <h3 class="m-0 text-[15px] font-bold">Qualification</h3>
              <span
                class="px-2.5 py-1 rounded-full text-[13px] font-bold"
                :class="qualificationComplete(qualificationPour(lignePanneau.cle, lignePanneau.ligne.numero_compte)) ? 'bg-green-100 text-green-700' : 'bg-maquette-attente-fond text-maquette-attente'"
              >
                {{ qualificationComplete(qualificationPour(lignePanneau.cle, lignePanneau.ligne.numero_compte)) ? 'Qualifiée' : 'À qualifier' }}
              </span>
            </div>
            <label class="flex flex-col gap-1.5 text-sm font-semibold">
              Cause de l'écart
              <select
                v-model="formulairesQualification[`${lignePanneau.cle}:${lignePanneau.ligne.numero_compte}`].cause"
                :disabled="!peutEditerAuditeur"
                class="h-11 text-[15px] font-normal px-2.5 border border-maquette-champ rounded-[10px] bg-white focus:outline-none focus:ring-2 focus:ring-maquette-marine disabled:bg-maquette-clair"
              >
                <option value="" disabled>Choisir une cause</option>
                <option v-for="cause in causesEcart" :key="cause" :value="cause">{{ cause }}</option>
              </select>
            </label>
            <label class="flex flex-col gap-1.5 text-sm font-semibold">
              Commentaire
              <textarea
                v-model="formulairesQualification[`${lignePanneau.cle}:${lignePanneau.ligne.numero_compte}`].commentaire"
                :disabled="!peutEditerAuditeur"
                rows="3"
                class="text-[15px] font-normal px-3 py-2.5 border border-maquette-champ rounded-[10px] bg-white resize-y focus:outline-none focus:ring-2 focus:ring-maquette-marine disabled:bg-maquette-clair"
                :placeholder="`Expliquer l'écart (au moins ${LONGUEUR_MIN_COMMENTAIRE} caractères)`"
              ></textarea>
            </label>
            <button
              class="h-11 rounded-[10px] bg-maquette-vert text-white text-[15px] font-bold hover:brightness-95 transition disabled:bg-maquette-champ disabled:text-maquette-ardoise disabled:cursor-not-allowed"
              :disabled="!peutEditerAuditeur || qualificationEnCours === `${lignePanneau.cle}:${lignePanneau.ligne.numero_compte}`"
              :title="!peutEditerAuditeur ? 'Modifiable uniquement « En cours » ou « En attente de correction »' : ''"
              @click="enregistrerQualification(lignePanneau.cle, lignePanneau.ligne.numero_compte)"
            >
              Enregistrer la qualification
            </button>
            <p v-if="qualificationPour(lignePanneau.cle, lignePanneau.ligne.numero_compte)" class="m-0 text-[13px] text-maquette-texte-doux">
              Qualifiée par {{ qualificationPour(lignePanneau.cle, lignePanneau.ligne.numero_compte).utilisateur_id || 'Non identifié' }},
              {{ formatHorodatage(qualificationPour(lignePanneau.cle, lignePanneau.ligne.numero_compte).horodatage) }}
            </p>
          </div>

          <!-- Fil des remarques (niveau 2) : « Répondre » et « Marquer traitée » conservés (circuit de revue) -->
          <div class="flex flex-col gap-2.5">
            <h3 class="m-0 text-[15px] font-bold">Remarques ({{ remarquesPourCollectif(lignePanneau.cle, lignePanneau.ligne.numero_compte).length }})</h3>
            <p v-if="!remarquesPourCollectif(lignePanneau.cle, lignePanneau.ligne.numero_compte).length" class="m-0 text-sm text-maquette-texte-doux">Aucune remarque.</p>
            <article
              v-for="r in remarquesPourCollectif(lignePanneau.cle, lignePanneau.ligne.numero_compte)"
              :key="r._id"
              class="border border-maquette-trait rounded-xl p-3.5 flex flex-col gap-1.5"
            >
              <div class="flex justify-between gap-2 flex-wrap">
                <span class="text-[13px] font-bold px-2 py-0.5 rounded-md" :class="TYPE_REMARQUE_INFO[r.type]?.classe || TYPE_REMARQUE_INFO.information.classe">
                  {{ TYPE_REMARQUE_INFO[r.type]?.label || 'Information' }}
                </span>
                <span class="text-[13px] text-maquette-texte-doux">{{ r.utilisateur_id || 'Non identifié' }} · {{ formatHorodatage(r.horodatage) }}</span>
              </div>
              <p class="m-0 text-sm">{{ r.commentaire }}</p>
              <p v-if="r.reponse" class="m-0 ml-3 text-sm text-maquette-ardoise italic">
                Réponse de {{ r.reponse.utilisateur_id || 'Non identifié' }} ({{ formatHorodatage(r.reponse.horodatage) }}) : {{ r.reponse.commentaire }}
              </p>
              <div class="flex items-center gap-2 text-[13px]">
                <span class="px-2 py-0.5 rounded-md font-bold" :class="r.traitee ? 'bg-green-100 text-green-700' : 'bg-maquette-gris text-maquette-ardoise'">
                  {{ r.traitee ? 'Traitée' : 'Non traitée' }}
                </span>
                <button
                  class="font-semibold text-maquette-marine underline disabled:text-maquette-champ disabled:no-underline disabled:cursor-not-allowed"
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
                  class="flex-1 h-9 text-sm px-2.5 border border-maquette-champ rounded-lg focus:outline-none focus:ring-2 focus:ring-maquette-marine"
                />
                <button class="text-sm font-semibold text-maquette-marine underline" @click="envoyerReponse(r)">Répondre</button>
              </div>
            </article>

            <label class="flex flex-col gap-1.5 text-sm font-semibold">
              Nouvelle remarque
              <textarea
                v-model="nouvellesRemarquesEcart[`${lignePanneau.cle}:${lignePanneau.ligne.numero_compte}`]"
                rows="2"
                class="text-[15px] font-normal px-3 py-2.5 border border-maquette-champ rounded-[10px] resize-y focus:outline-none focus:ring-2 focus:ring-maquette-marine"
                placeholder="Ajouter une remarque sur cet écart"
              ></textarea>
            </label>
            <div class="flex gap-2.5 flex-wrap">
              <select
                aria-label="Type de remarque"
                :value="typesNouvellesRemarquesEcart[`${lignePanneau.cle}:${lignePanneau.ligne.numero_compte}`] || 'information'"
                class="h-11 text-[15px] px-2.5 border border-maquette-champ rounded-[10px] bg-white focus:outline-none focus:ring-2 focus:ring-maquette-marine"
                @change="typesNouvellesRemarquesEcart[`${lignePanneau.cle}:${lignePanneau.ligne.numero_compte}`] = $event.target.value"
              >
                <option value="information">Information</option>
                <option value="demande_correction" :disabled="!utilisateurIdentifie">Demande de correction</option>
              </select>
              <button
                class="h-11 px-[18px] rounded-[10px] bg-maquette-marine text-white font-bold hover:bg-maquette-marine-fonce transition"
                @click="ajouterRemarqueEcart(lignePanneau.cle, lignePanneau.ligne.numero_compte)"
              >
                Ajouter
              </button>
            </div>
          </div>
        </aside>
      </div>

      <!-- Commentaires généraux (niveau 1) : hors maquette, gardés en bas dans le même style -->
      <section id="commentaires-generaux" v-if="ipeEtat" class="scroll-mt-4 bg-white rounded-[14px] shadow-[0_1px_3px_rgba(15,58,90,0.08)] px-7 py-6 flex flex-col gap-3">
        <h2 class="m-0 text-[17px] font-bold tracking-[0.3px] uppercase text-maquette-marine">Commentaires généraux</h2>
        <p v-if="!remarquesGenerales.length" class="m-0 text-sm text-maquette-texte-doux">Aucun commentaire général.</p>

        <article v-for="r in remarquesGenerales" :key="r._id" class="border border-maquette-trait rounded-xl p-3.5 flex flex-col gap-1.5">
          <div class="flex justify-between gap-2 flex-wrap">
            <span class="text-[13px] font-bold px-2 py-0.5 rounded-md" :class="TYPE_REMARQUE_INFO[r.type]?.classe || TYPE_REMARQUE_INFO.information.classe">
              {{ TYPE_REMARQUE_INFO[r.type]?.label || 'Information' }}
            </span>
            <span class="text-[13px] text-maquette-texte-doux">{{ r.utilisateur_id || 'Non identifié' }} · {{ formatHorodatage(r.horodatage) }}</span>
          </div>
          <p class="m-0 text-sm">{{ r.commentaire }}</p>
          <p v-if="r.reponse" class="m-0 ml-3 text-sm text-maquette-ardoise italic">
            Réponse de {{ r.reponse.utilisateur_id || 'Non identifié' }} ({{ formatHorodatage(r.reponse.horodatage) }}) : {{ r.reponse.commentaire }}
          </p>
          <div class="flex items-center gap-2 text-[13px]">
            <span class="px-2 py-0.5 rounded-md font-bold" :class="r.traitee ? 'bg-green-100 text-green-700' : 'bg-maquette-gris text-maquette-ardoise'">
              {{ r.traitee ? 'Traitée' : 'Non traitée' }}
            </span>
            <button
              class="font-semibold text-maquette-marine underline disabled:text-maquette-champ disabled:no-underline disabled:cursor-not-allowed"
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
              class="flex-1 h-9 text-sm px-2.5 border border-maquette-champ rounded-lg focus:outline-none focus:ring-2 focus:ring-maquette-marine"
            />
            <button class="text-sm font-semibold text-maquette-marine underline" @click="envoyerReponse(r)">Répondre</button>
          </div>
        </article>

        <div class="flex gap-2.5 flex-wrap">
          <select
            v-model="typeNouvelleRemarqueGenerale"
            aria-label="Type de commentaire"
            class="h-11 text-[15px] px-2.5 border border-maquette-champ rounded-[10px] bg-white focus:outline-none focus:ring-2 focus:ring-maquette-marine"
          >
            <option value="information">Information</option>
            <option value="demande_correction" :disabled="!utilisateurIdentifie">Demande de correction</option>
          </select>
          <input
            v-model="nouvelleRemarqueGenerale"
            type="text"
            placeholder="Ajouter un commentaire général sur le contrôle..."
            class="flex-1 min-w-[16rem] h-11 text-[15px] px-3 border border-maquette-champ rounded-[10px] focus:outline-none focus:ring-2 focus:ring-maquette-marine"
          />
          <button
            class="h-11 px-[18px] rounded-[10px] bg-maquette-marine text-white font-bold hover:bg-maquette-marine-fonce transition"
            @click="ajouterRemarqueGenerale"
          >
            Ajouter
          </button>
        </div>
      </section>

      <!-- Historique : hors maquette, gardé en bas dans le même style -->
      <section v-if="ipeEtat" class="bg-white rounded-[14px] shadow-[0_1px_3px_rgba(15,58,90,0.08)] px-7 py-6 flex flex-col gap-3.5">
        <h2 class="m-0 text-[17px] font-bold tracking-[0.3px] uppercase text-maquette-marine">Historique</h2>
        <p v-if="!historiqueRecent.length" class="m-0 text-sm text-maquette-texte-doux">Aucune action enregistrée pour le moment.</p>
        <div v-else class="overflow-x-auto">
          <table class="w-full border-collapse text-[15px]">
            <thead>
              <tr class="bg-maquette-marine text-white text-left">
                <th class="px-4 py-3.5">Date</th>
                <th class="px-4 py-3.5">Action</th>
                <th class="px-4 py-3.5">Utilisateur</th>
                <th class="px-4 py-3.5">Résultat</th>
                <th class="px-4 py-3.5">Commentaire</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(entree, i) in historiqueRecent" :key="i" class="border-b border-maquette-trait align-top">
                <td class="px-4 py-3.5 whitespace-nowrap tabular-nums">{{ formatHorodatage(entree.horodatage) }}</td>
                <td class="px-4 py-3.5">{{ ACTION_HISTORIQUE_LABELS[entree.action] || entree.action }}</td>
                <td class="px-4 py-3.5">{{ entree.utilisateur_id || 'Non identifié' }}</td>
                <td class="px-4 py-3.5">{{ resultatHistorique(entree) }}</td>
                <td class="px-4 py-3.5 text-maquette-texte-doux">{{ entree.commentaire || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

    </div>
  </div>
</template>
