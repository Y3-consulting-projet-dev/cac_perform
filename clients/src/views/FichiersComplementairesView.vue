<script setup>
// Écran de consultation des fichiers complémentaires d'une mission (balances
// auxiliaires clients/fournisseurs, fichier des immobilisations).
// Nouveau périmètre V2 — voir docs/PLAN_import_refonte.md.
//
// Lecture seule pour la consultation ; l'import/remplacement réutilise les
// mêmes services que la création de mission (aucun doublon de logique).
// N'est PAS une étape d'audit : volontairement absent de la barre de
// progression des 11 étapes de GroupingAnalyse.vue.
//
// Le rapprochement IPE (Module 1, CAC-IPE-01) ne vit plus ici : écran dédié
// FiabiliteIpeView.vue, pour ne plus confondre les deux entrées de la barre
// latérale de GroupingAnalyse.vue (docs/PLAN_verrou_IPE.md §6).
import { ref, computed, onMounted } from 'vue'
import router from '@/router'
import { useNotyf } from '@/composables/useNotyf'
import {
  obtenirMission,
  listerFichiersComplementaires,
  historiqueFichiersComplementaires,
  detailFichierComplementaire,
  importerBalanceAuxiliaire,
  importerImmobilisations,
  verifierFichierComplementaire,
  retirerFichierComplementaire,
  lireBalanceGenerale,
  detailBalanceGenerale,
  importerBalanceGenerale,
} from '@/api/imports.api'
import { formatDateHeureFr } from '@/utils/formatDate'
import {
  controlesLisibles, nombreAlertes, phraseSynthese, totauxLisibles, colonnesComptes,
  LIBELLES_DONNEES, libellePerimetre, formatMontant, estImmobilisations,
} from '@/utils/lectureFichierComplementaire'

// `integre` : écran affiché dans la zone principale de GroupingAnalyse.vue,
// sous la barre latérale bleue (qui porte déjà le « Retour »).
const props = defineProps({ missionId: String, integre: Boolean })
// Intégré : demande l'écran à GroupingAnalyse.vue, exactement comme le
// bouton « Détail » de la barre latérale (showComponent), sans passer par
// l'adresse — qui ferait perdre ses autres paramètres (?annee=) et ajouterait
// une entrée d'historique au « Retour ».
const emit = defineEmits(['ouvrir-ecran'])
const notyf = useNotyf()

const LIBELLES_TYPE = {
  auxiliaire_client: 'Balance auxiliaire clients',
  auxiliaire_fournisseur: 'Balance auxiliaire fournisseurs',
  immobilisations: 'Fichier des immobilisations',
}

const infoMission = ref(null)
const erreurMission = ref(null) // raison affichée si la mission ne charge pas
const fichiers = ref({ auxiliaire_client: [], auxiliaire_fournisseur: [], immobilisations: [] })
// Versions archivées (actif=false) par type : un remplacement ne supprime rien.
const archives = ref({ auxiliaire_client: [], auxiliaire_fournisseur: [], immobilisations: [] })
const detailOuvert = ref(null)
// Nombre d'alertes des contrôles par fichier actif (badge de la carte) :
// null = résultat indisponible. Lu dans le détail existant, aucun nouvel endpoint.
const alertesParFichier = ref({})
const loading = ref(false)
const importingType = ref(null)

onMounted(async () => {
  await chargerInfoMission()
  await chargerFichiers()
})

// L'import a besoin du client et de l'exercice de la mission : on refuse
// d'importer tant qu'ils ne sont pas connus, en affichant la raison.
async function chargerInfoMission() {
  erreurMission.value = null
  try {
    const mission = await obtenirMission(props.missionId)
    const manquants = ['id_client', 'annee_auditee'].filter((cle) => !mission[cle])
    if (manquants.length) {
      throw new Error(`la mission ne renseigne pas : ${manquants.join(', ')}`)
    }
    infoMission.value = mission
  } catch (e) {
    infoMission.value = null
    erreurMission.value = e.message
  }
}

async function chargerFichiers() {
  loading.value = true
  try {
    fichiers.value = await listerFichiersComplementaires(props.missionId)
    const historiques = await Promise.all(
      Object.keys(LIBELLES_TYPE).map((type) => historiqueFichiersComplementaires(props.missionId, type)),
    )
    archives.value = Object.fromEntries(
      Object.keys(LIBELLES_TYPE).map((type, i) => [type, historiques[i].filter((f) => !f.actif)]),
    )
    await Promise.all([chargerResultatsControles(), chargerBalanceGenerale()])
  } catch (e) {
    notyf.trigger(e.message || 'Erreur lors du chargement des fichiers', 'error')
  } finally {
    loading.value = false
  }
}

async function chargerResultatsControles() {
  const actifs = Object.values(fichiers.value).flat()
  const resultats = await Promise.all(actifs.map(async (f) => {
    try {
      return [f._id, nombreAlertes(await detailFichierComplementaire(props.missionId, f._id))]
    } catch {
      return [f._id, null]
    }
  }))
  alertesParFichier.value = Object.fromEntries(resultats)
}

// Balance générale N : remplaçable ici par l'import V2 (balance_generale_service.py).
// La création de mission reste sur l'import V1.
const TYPE_BALANCE_GENERALE = 'balance_generale'
const balanceGenerale = ref(null) // { active, historique } ; null = non chargée
const erreurBalanceGenerale = ref(null)
const alertesBalanceGenerale = ref(undefined) // undefined = en cours, null = indisponible

async function chargerBalanceGenerale() {
  erreurBalanceGenerale.value = null
  alertesBalanceGenerale.value = undefined
  try {
    balanceGenerale.value = await lireBalanceGenerale(props.missionId)
  } catch (e) {
    balanceGenerale.value = null
    erreurBalanceGenerale.value = e.message
    return
  }
  try {
    alertesBalanceGenerale.value = nombreAlertes(await detailBalanceGenerale(props.missionId, balanceGenerale.value.active._id))
  } catch {
    alertesBalanceGenerale.value = null
  }
}

async function voirDetailBalanceGenerale(balanceId) {
  try {
    detailOuvert.value = await detailBalanceGenerale(props.missionId, balanceId)
  } catch (e) {
    notyf.trigger(e.message || 'Erreur lors du chargement du détail', 'error')
  }
}

// Fenêtre de détail : présentation lisible (lectureFichierComplementaire.js).
const controlesDetail = computed(() => (detailOuvert.value ? controlesLisibles(detailOuvert.value) : []))
const alertesDetail = computed(() => controlesDetail.value.filter((c) => c.statut === 'alerte').length)
const syntheseDetail = computed(() => (detailOuvert.value ? phraseSynthese(detailOuvert.value) : ''))
const totauxDetail = computed(() => (detailOuvert.value ? totauxLisibles(detailOuvert.value) : { lignes: [] }))
const colonnesDetail = computed(() => (detailOuvert.value ? colonnesComptes(detailOuvert.value) : []))
const lignesTotalEnEcart = computed(() =>
  (detailOuvert.value?.controles_preliminaires?.bouclage_total?.resultats || []).filter((r) => !r.ok),
)

async function voirDetail(fichierId) {
  try {
    detailOuvert.value = await detailFichierComplementaire(props.missionId, fichierId)
  } catch (e) {
    notyf.trigger(e.message || 'Erreur lors du chargement du détail', 'error')
  }
}

function fermerDetail() {
  detailOuvert.value = null
}

// Import en deux temps : contrôles (type de comptes, exercice) PUIS
// enregistrement. En cas d'alerte, rien n'est enregistré tant que
// l'utilisateur n'a pas choisi « Importer quand même ».
const importEnAttente = ref(null) // { fichier, type, verification }

async function onImporter(event, type) {
  const fichier = event.target.files[0]
  event.target.value = '' // permet de re-sélectionner le même fichier ensuite
  if (!fichier) return

  if (!infoMission.value) {
    notyf.trigger(`Import impossible — mission non chargée : ${erreurMission.value || 'raison inconnue'}`, 'error')
    return
  }

  importingType.value = type
  try {
    const verification = await verifierFichierComplementaire(props.missionId, fichier, type)
    if (verification.alertes.length || type === TYPE_BALANCE_GENERALE) {
      importEnAttente.value = { fichier, type, verification }
      return
    }
    await enregistrerImport(fichier, type)
  } catch (e) {
    notyf.trigger(e.message || "Erreur lors de l'import", 'error')
  } finally {
    if (!importEnAttente.value) importingType.value = null
  }
}

function annulerImport() {
  importEnAttente.value = null
  importingType.value = null
  notyf.trigger('Import annulé : aucun fichier enregistré.', 'success')
}

async function confirmerImport() {
  const { fichier, type } = importEnAttente.value
  importEnAttente.value = null
  try {
    await enregistrerImport(fichier, type)
  } catch (e) {
    notyf.trigger(e.message || "Erreur lors de l'import", 'error')
  } finally {
    importingType.value = null
  }
}

async function enregistrerImport(fichier, type) {
  const idClient = infoMission.value.id_client
  const annee = infoMission.value.annee_auditee
  if (type === TYPE_BALANCE_GENERALE) {
    const resultat = await importerBalanceGenerale(props.missionId, fichier, utilisateurConnecte())
    notyf.trigger(
      `Balance générale remplacée : ${resultat.nb_lignes} comptes, ${resultat.nb_sous_totaux_ecartes} ligne(s) de sous-total écartée(s). L'ancienne version reste dans l'historique.`,
      'success', { duration: 6000 },
    )
    await chargerBalanceGenerale()
    return
  }
  if (type === 'immobilisations') {
    await importerImmobilisations(props.missionId, fichier, idClient, annee)
  } else {
    const typeAuxiliaire = type === 'auxiliaire_client' ? 'client' : 'fournisseur'
    await importerBalanceAuxiliaire(props.missionId, fichier, typeAuxiliaire, idClient, annee)
  }
  notyf.trigger("Fichier importé avec succès (l'ancienne version reste dans l'historique)", 'success')
  await chargerFichiers()
}

/* --- Action « Retirer » : archive la version active, tracée (utilisateur + commentaire) --- */
const LONGUEUR_MIN_COMMENTAIRE = 15 // même seuil que le backend (import_schemas.py)
const retraitOuvert = ref(null) // fichier à retirer
const commentaireRetrait = ref('')
const retraitEnCours = ref(false)

// Même lecture de l'utilisateur connecté que FiabiliteIpeView.vue.
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

function ouvrirRetrait(fichier) {
  retraitOuvert.value = fichier
  commentaireRetrait.value = ''
}

async function confirmerRetrait() {
  const utilisateur = utilisateurConnecte()
  if (!utilisateur) {
    notyf.trigger('Utilisateur non identifié : connectez-vous pour retirer un fichier.', 'error')
    return
  }
  if (commentaireRetrait.value.trim().length < LONGUEUR_MIN_COMMENTAIRE) {
    notyf.trigger(`Le commentaire doit contenir au moins ${LONGUEUR_MIN_COMMENTAIRE} caractères.`, 'error')
    return
  }
  retraitEnCours.value = true
  try {
    await retirerFichierComplementaire(props.missionId, retraitOuvert.value._id, utilisateur, commentaireRetrait.value.trim())
    notyf.trigger('Fichier retiré : la version est archivée, rien n\'a été supprimé.', 'success')
    retraitOuvert.value = null
    await chargerFichiers()
  } catch (e) {
    notyf.trigger(e.message || 'Erreur lors du retrait du fichier', 'error')
  } finally {
    retraitEnCours.value = false
  }
}

function allerVersFiabiliteIpe() {
  if (props.integre) {
    emit('ouvrir-ecran', 'fiabilite_ipe')
    return
  }
  router.push({ path: `/grouping-analyse/${props.missionId}`, query: { step: 'fiabilite_ipe' } })
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
        <h1 class="text-xl font-bold text-blue-ycube">Fichiers complémentaires</h1>
        <p class="text-sm text-gray-500">Balance générale, balances auxiliaires et fichier des immobilisations : import, contrôles et remplacement</p>
      </div>
      <div class="w-20"></div>
    </div>

    <div class="p-6 flex flex-col gap-6">

      <!-- Mission non chargée : import impossible, raison affichée -->
      <div v-if="erreurMission" class="bg-white rounded-xl shadow p-6 flex items-center justify-between flex-wrap gap-3 border-l-4 border-red-500">
        <div>
          <h2 class="font-semibold text-sm uppercase text-red-700">Mission non chargée — import impossible</h2>
          <p class="text-sm text-gray-700">{{ erreurMission }}</p>
        </div>
        <button
          class="border border-blue-ycube text-blue-ycube font-semibold hover:bg-blue-ycube hover:text-white transition px-5 py-2 rounded-lg"
          @click="chargerInfoMission"
        >
          Réessayer
        </button>
      </div>
      <p v-else-if="infoMission" class="text-sm text-gray-500">
        Exercice audité : <span class="font-semibold text-gray-800">{{ infoMission.annee_auditee }}</span>
      </p>

      <!-- Lien vers l'écran dédié au rapprochement IPE (Module 1, CAC-IPE-01) -->
      <div class="bg-white rounded-xl shadow p-6 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 class="font-bold text-sm uppercase text-blue-ycube">Rapprochement IPE</h2>
          <p class="text-sm text-gray-500">Synthèse, écarts, qualification, validation et historique sur un écran dédié.</p>
        </div>
        <button
          class="px-5 py-2 rounded-lg bg-blue-ycube text-white font-semibold hover:bg-blue-900 transition"
          @click="allerVersFiabiliteIpe"
        >
          Voir le rapprochement IPE
        </button>
      </div>

      <!-- Balance générale N : remplaçable par l'import V2 (en-tête détecté,
           correspondance des colonnes, sous-totaux écartés). -->
      <div class="bg-white rounded-xl shadow p-4 flex flex-col gap-3">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <h2 class="font-bold text-sm uppercase text-blue-ycube">
            Balance générale{{ infoMission ? ' ' + infoMission.annee_auditee : '' }}
          </h2>
          <span class="text-xs text-gray-500">Balance de l'exercice audité, utilisée par le rapprochement IPE</span>
        </div>

        <p v-if="erreurBalanceGenerale" class="text-sm text-red-700">{{ erreurBalanceGenerale }}</p>

        <template v-else-if="balanceGenerale">
          <div class="border rounded-lg p-3 flex flex-col gap-2 cursor-pointer hover:bg-gray-50"
            @click="voirDetailBalanceGenerale(balanceGenerale.active._id)">
            <div class="flex items-center justify-between gap-2">
              <span class="text-sm font-semibold truncate">
                {{ balanceGenerale.active.nom_fichier || (balanceGenerale.active.origine === 'import_v1' ? 'Import à la création de la mission' : 'Fichier sans nom') }}
              </span>
              <span class="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700">Active</span>
            </div>
            <span class="text-xs text-gray-500">
              <template v-if="balanceGenerale.active.date_import">Importée le {{ formatDateHeureFr(balanceGenerale.active.date_import) }} · </template>
              {{ balanceGenerale.active.nb_lignes }} comptes · version {{ balanceGenerale.active.version }}
              · {{ balanceGenerale.active.origine === 'import_v1' ? 'import d\'origine (création de la mission)' : 'import V2' }}
            </span>
            <div>
              <span v-if="alertesBalanceGenerale === undefined" class="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700">Contrôles…</span>
              <span v-else-if="balanceGenerale.active.origine === 'import_v1'" class="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700">
                Non contrôlée (import d'origine)
              </span>
              <span v-else-if="alertesBalanceGenerale === null" class="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700">Contrôles indisponibles</span>
              <span v-else-if="alertesBalanceGenerale === 0" class="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700">
                <i class="fa-solid fa-check mr-1"></i>Contrôles OK
              </span>
              <span v-else class="px-3 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-700">
                <i class="fa-solid fa-triangle-exclamation mr-1"></i>{{ alertesBalanceGenerale }} {{ alertesBalanceGenerale > 1 ? 'alertes' : 'alerte' }}
              </span>
            </div>
            <div class="flex items-center justify-end gap-2">
              <button
                class="px-3 py-1 text-xs border border-blue-ycube text-blue-ycube font-semibold rounded-lg hover:bg-blue-ycube hover:text-white transition"
                @click.stop="voirDetailBalanceGenerale(balanceGenerale.active._id)"
              >
                Voir le détail
              </button>
            </div>
          </div>

          <div v-if="balanceGenerale.historique.length" class="flex flex-col gap-1">
            <p class="text-xs text-gray-500">Versions précédentes</p>
            <div v-for="b in balanceGenerale.historique" :key="b._id"
              class="border rounded-lg p-2 flex items-center justify-between gap-2 text-gray-500 text-xs">
              <span class="truncate">
                v{{ b.version }} · {{ b.nom_fichier || (b.origine === 'import_v1' ? 'import à la création de la mission' : 'fichier sans nom') }}
                · {{ b.nb_lignes }} lignes<template v-if="b.date_import"> · {{ formatDateHeureFr(b.date_import) }}</template>
              </span>
              <span class="flex items-center gap-2">
                <span class="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700">Remplacée</span>
                <button class="text-blue-ycube font-semibold hover:underline" @click="voirDetailBalanceGenerale(b._id)">Voir le détail</button>
              </span>
            </div>
          </div>
        </template>

        <p v-else class="text-sm text-gray-500">Chargement…</p>

        <label
          class="text-xs text-center border-2 border-dashed border-blue-ycube rounded-lg py-2 cursor-pointer hover:bg-blue-50">
          <input type="file" accept=".xlsx" class="sr-only" :disabled="importingType === TYPE_BALANCE_GENERALE"
            @change="(e) => onImporter(e, TYPE_BALANCE_GENERALE)">
          {{ importingType === TYPE_BALANCE_GENERALE ? 'Import en cours...' : 'Remplacer la balance générale' }}
        </label>
      </div>

      <div v-if="loading" class="text-gray-500">Chargement...</div>

      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">
        <div v-for="type in Object.keys(LIBELLES_TYPE)" :key="type"
          class="bg-white rounded-xl shadow p-4 flex flex-col gap-3">
          <h2 class="font-bold text-sm uppercase text-blue-ycube">{{ LIBELLES_TYPE[type] }}</h2>

          <div v-if="!fichiers[type] || fichiers[type].length === 0" class="text-xs text-gray-500 italic">
            Aucun fichier importé.
          </div>

          <div v-for="f in fichiers[type]" :key="f._id"
            class="border rounded-lg p-3 flex flex-col gap-2 cursor-pointer hover:bg-gray-50"
            @click="voirDetail(f._id)">
            <div class="flex items-center justify-between gap-2">
              <span class="text-sm font-semibold truncate">{{ f.nom_fichier || 'Fichier sans nom' }}</span>
              <span class="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700">Active</span>
            </div>
            <span class="text-xs text-gray-500">Importé le {{ formatDateHeureFr(f.date_import) }} · {{ f.nb_lignes }} lignes · version {{ f.version }}</span>

            <!-- Résultat des contrôles faits à l'import -->
            <div>
              <span v-if="!(f._id in alertesParFichier)" class="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700">
                Contrôles…
              </span>
              <span v-else-if="alertesParFichier[f._id] === null" class="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700">
                Contrôles indisponibles
              </span>
              <span v-else-if="alertesParFichier[f._id] === 0" class="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700">
                <i class="fa-solid fa-check mr-1"></i>Contrôles OK
              </span>
              <span v-else class="px-3 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-700">
                <i class="fa-solid fa-triangle-exclamation mr-1"></i>{{ alertesParFichier[f._id] }} {{ alertesParFichier[f._id] > 1 ? 'alertes' : 'alerte' }}
              </span>
            </div>

            <div class="flex items-center justify-end gap-2">
              <button
                class="px-3 py-1 text-xs border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-100 transition"
                title="Désactiver ce fichier importé par erreur (archivé, rien n'est supprimé)"
                @click.stop="ouvrirRetrait(f)"
              >
                Retirer
              </button>
              <button
                class="px-3 py-1 text-xs border border-blue-ycube text-blue-ycube font-semibold rounded-lg hover:bg-blue-ycube hover:text-white transition"
                @click.stop="voirDetail(f._id)"
              >
                Voir le détail
              </button>
            </div>
          </div>

          <div v-if="archives[type]?.length" class="flex flex-col gap-1">
            <p class="text-xs text-gray-500">Versions archivées</p>
            <div v-for="f in archives[type]" :key="f._id"
              class="border rounded-lg p-2 flex flex-col gap-1 cursor-pointer hover:bg-gray-50 text-gray-500"
              @click="voirDetail(f._id)">
              <div class="flex items-center justify-between gap-2">
                <span class="text-xs truncate">v{{ f.version }} · {{ f.nom_fichier || 'Fichier sans nom' }} · {{ f.nb_lignes }} lignes</span>
                <span class="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700 whitespace-nowrap">
                  {{ f.retrait ? 'Retirée' : 'Remplacée' }}
                </span>
              </div>
              <span class="text-xs">Importé le {{ formatDateHeureFr(f.date_import) }}</span>
              <span v-if="f.retrait" class="text-xs">
                Retirée le {{ formatDateHeureFr(f.retrait.horodatage) }} par {{ f.retrait.utilisateur_id }} : « {{ f.retrait.commentaire }} »
              </span>
              <div class="flex justify-end">
                <button class="text-xs text-blue-ycube font-semibold hover:underline" @click.stop="voirDetail(f._id)">Voir le détail</button>
              </div>
            </div>
          </div>

          <label
            class="mt-2 text-xs text-center border-2 border-dashed border-blue-ycube rounded-lg py-2 cursor-pointer hover:bg-blue-50">
            <input type="file" accept=".xlsx" class="sr-only" :disabled="importingType === type"
              @change="(e) => onImporter(e, type)">
            {{ importingType === type ? 'Import en cours...' : (fichiers[type]?.length ? 'Remplacer' : 'Importer') }}
          </label>
        </div>
      </div>

    </div>

    <!-- Alertes avant enregistrement (type de comptes, exercice) — rien n'est
         enregistré tant que l'utilisateur n'a pas choisi. Modale : charte CLAUDE.md. -->
    <div v-if="importEnAttente" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-3xl p-6 relative max-h-[90vh] overflow-auto flex flex-col gap-4">
        <div>
          <h3 class="text-xl font-bold text-blue-ycube">Vérifier avant d'importer</h3>
          <p class="text-sm text-gray-500">
            {{ importEnAttente.fichier.name }} → {{ LIBELLES_TYPE[importEnAttente.type] || 'Balance générale (exercice audité)' }}
          </p>
        </div>
        <div
          v-for="alerte in importEnAttente.verification.alertes"
          :key="alerte.code"
          class="border-l-4 border-orange-500 bg-orange-50 rounded-lg p-3 text-sm text-gray-800"
        >
          <p class="font-semibold text-orange-700">
            {{ alerte.code === 'type_incoherent' ? 'Type de fichier' : 'Exercice' }}
          </p>
          <p>{{ alerte.message }}</p>
        </div>
        <div
          v-if="importEnAttente.type === TYPE_BALANCE_GENERALE"
          class="border-l-4 border-orange-500 bg-orange-50 rounded-lg p-3 text-sm text-gray-800 flex flex-col gap-1"
        >
          <p class="font-semibold text-orange-700">Remplacement de la balance générale</p>
          <p>Le rapprochement IPE utilisera la nouvelle balance, et une validation IPE déjà donnée sera invalidée.</p>
          <p>
            Les données que les étapes de l'audit ont calculées à la création de la mission (variations N/N-1,
            préparation des leads, états financiers) <span class="font-semibold">ne sont pas recalculées</span> :
            elles restent basées sur l'ancienne balance.
          </p>
          <p>Les lignes de sous-total du fichier seront écartées et visibles dans le détail. L'ancienne balance reste dans l'historique.</p>
        </div>
        <p v-for="info in importEnAttente.verification.informations" :key="info" class="text-xs text-gray-500">{{ info }}</p>
        <p class="text-sm text-gray-700">Rien n'est enregistré tant que vous n'avez pas choisi.</p>
        <div class="flex justify-end gap-3">
          <button
            class="px-5 py-2 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition"
            @click="annulerImport"
          >
            Annuler
          </button>
          <button
            class="px-5 py-2 rounded-lg bg-blue-ycube text-white font-semibold hover:bg-blue-900 transition"
            @click="confirmerImport"
          >
            {{ importEnAttente.type === TYPE_BALANCE_GENERALE ? 'Remplacer la balance générale' : 'Importer quand même' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Retrait d'un fichier importé par erreur : archivé, tracé, jamais supprimé -->
    <div v-if="retraitOuvert" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click.self="retraitOuvert = null">
      <div class="bg-white rounded-2xl w-full max-w-3xl p-6 relative max-h-[90vh] overflow-auto flex flex-col gap-4">
        <div>
          <h3 class="text-xl font-bold text-blue-ycube">Retirer un fichier</h3>
          <p class="text-sm text-gray-500">
            {{ retraitOuvert.nom_fichier || 'Fichier sans nom' }} · version {{ retraitOuvert.version }}
            · importé le {{ formatDateHeureFr(retraitOuvert.date_import) }}
          </p>
        </div>
        <p class="text-sm text-gray-700">
          La version est archivée et le retrait est tracé dans l'historique : rien n'est supprimé.
          La version précédente n'est pas réactivée ; importez le bon fichier ensuite.
          Si ce fichier a servi à une validation IPE, celle-ci est invalidée.
        </p>
        <p class="text-sm">
          <span class="text-gray-500">Utilisateur :</span>
          <span class="font-semibold text-gray-800">{{ utilisateurConnecte() || 'Non identifié — connexion requise' }}</span>
        </p>
        <textarea
          v-model="commentaireRetrait"
          rows="3"
          class="text-sm border border-gray-300 rounded-lg p-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-ycube"
          :placeholder="`Pourquoi retirer ce fichier ? (au moins ${LONGUEUR_MIN_COMMENTAIRE} caractères)`"
        ></textarea>
        <div class="flex justify-end gap-3">
          <button
            class="px-5 py-2 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition"
            @click="retraitOuvert = null"
          >
            Annuler
          </button>
          <button
            class="px-5 py-2 rounded-lg bg-red-500 text-white font-semibold hover:bg-red-600 transition disabled:opacity-40 disabled:cursor-not-allowed"
            :disabled="retraitEnCours || !utilisateurConnecte() || commentaireRetrait.trim().length < LONGUEUR_MIN_COMMENTAIRE"
            @click="confirmerRetrait"
          >
            Retirer le fichier
          </button>
        </div>
      </div>
    </div>

    <!-- Détail d'un fichier — même recette de modale que ClientsView.vue (charte CLAUDE.md) -->
    <div v-if="detailOuvert" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click.self="fermerDetail">
      <div class="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-auto p-6 relative flex flex-col gap-4">
        <div class="flex justify-between items-start">
          <div>
            <h3 class="font-bold text-blue-ycube">
              {{ detailOuvert.nom_fichier || (detailOuvert.origine === 'import_v1' ? 'Balance générale — import à la création de la mission' : 'Fichier sans nom') }}
            </h3>
            <p class="text-xs text-gray-500">
              <template v-if="detailOuvert.date_import">Importé le {{ formatDateHeureFr(detailOuvert.date_import) }} · </template>version {{ detailOuvert.version }}
              · {{ detailOuvert.actif ? 'active' : (detailOuvert.retrait ? 'retirée' : 'remplacée') }}
            </p>
            <p v-if="detailOuvert.retrait" class="text-xs text-gray-500">
              Retirée le {{ formatDateHeureFr(detailOuvert.retrait.horodatage) }} par {{ detailOuvert.retrait.utilisateur_id }} :
              « {{ detailOuvert.retrait.commentaire }} »
            </p>
          </div>
          <button class="text-gray-500 hover:text-gray-800" @click="fermerDetail">
            <i class="fa-solid fa-xmark text-2xl"></i>
          </button>
        </div>

        <!-- a) Synthèse en une phrase -->
        <div
          class="rounded-lg p-3 text-sm font-semibold border-l-4"
          :class="!detailOuvert.controles_preliminaires ? 'bg-gray-50 border-gray-400 text-gray-700'
            : (alertesDetail ? 'bg-orange-50 border-orange-500 text-orange-700' : 'bg-green-50 border-green-500 text-green-700')"
        >
          <i class="fa-solid mr-2" :class="!detailOuvert.controles_preliminaires ? 'fa-circle-info' : (alertesDetail ? 'fa-triangle-exclamation' : 'fa-circle-check')"></i>{{ syntheseDetail }}
        </div>

        <!-- b) Contrôles faits à l'import -->
        <div v-if="controlesDetail.length" class="flex flex-col gap-2">
          <h4 class="font-semibold text-sm uppercase text-blue-ycube">Contrôles</h4>
          <ul class="flex flex-col gap-2 text-sm">
            <li v-for="c in controlesDetail" :key="c.cle" class="flex items-start gap-2">
              <i
                class="fa-solid mt-0.5"
                :class="{
                  'fa-circle-check text-green-600': c.statut === 'ok',
                  'fa-triangle-exclamation text-orange-500': c.statut === 'alerte',
                  'fa-circle-minus text-gray-400': c.statut === 'non_applicable',
                }"
              ></i>
              <div>
                <p :class="c.statut === 'non_applicable' ? 'text-gray-500' : 'text-gray-800'">{{ c.libelle }}</p>
                <p v-if="c.aVerifier" class="text-xs" :class="c.statut === 'alerte' ? 'text-orange-700' : 'text-gray-500'">
                  {{ c.statut === 'alerte' ? 'À vérifier : ' : '' }}{{ c.aVerifier }}
                </p>
              </div>
            </li>
          </ul>
        </div>

        <!-- c) Totaux du fichier -->
        <div v-if="totauxDetail.lignes.length" class="flex flex-col gap-2">
          <h4 class="font-semibold text-sm uppercase text-blue-ycube">Totaux du fichier</h4>
          <table class="min-w-full text-sm">
            <thead class="bg-blue-ycube text-white h-10 text-left">
              <tr v-if="totauxDetail.mode === 'montants'">
                <th class="px-3"></th>
                <th class="px-3 text-right">Montant</th>
              </tr>
              <tr v-else>
                <th class="px-3"></th>
                <th class="px-3 text-right">Débit</th>
                <th class="px-3 text-right">Crédit</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in totauxDetail.lignes" :key="t.libelle" class="h-10 border-b">
                <td class="px-3 font-semibold text-gray-800">{{ t.libelle }}</td>
                <td v-if="totauxDetail.mode === 'montants'" class="px-3 text-right font-mono whitespace-nowrap">{{ t.montant }}</td>
                <template v-else>
                  <td class="px-3 text-right font-mono whitespace-nowrap">{{ t.debit }}</td>
                  <td class="px-3 text-right font-mono whitespace-nowrap">{{ t.credit }}</td>
                </template>
              </tr>
            </tbody>
          </table>
          <p v-if="totauxDetail.montantSigne" class="text-xs text-gray-500 italic">
            Fichier à montant unique : un montant positif est lu comme un débit, un montant négatif comme un crédit (convention à confirmer).
          </p>
        </div>

        <!-- d) Comptes importés : en-tête fixe au défilement -->
        <div class="flex flex-col gap-2">
          <h4 class="font-semibold text-sm uppercase text-blue-ycube">
            {{ estImmobilisations(detailOuvert) ? 'Biens importés' : 'Comptes importés' }}
          </h4>
          <p v-if="!detailOuvert.lignes || detailOuvert.lignes.length === 0" class="text-sm text-gray-500 italic">Aucune ligne.</p>
          <div v-else class="max-h-96 overflow-y-auto border rounded-lg">
            <table class="w-full text-xs">
              <thead class="bg-blue-ycube text-white text-left sticky top-0">
                <tr class="h-10">
                  <th v-for="col in colonnesDetail" :key="col.titre" class="px-2" :class="col.montant ? 'text-right whitespace-nowrap' : ''">
                    {{ col.titre }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(ligne, i) in detailOuvert.lignes" :key="i" class="border-b hover:bg-gray-50">
                  <td
                    v-for="col in colonnesDetail"
                    :key="col.titre"
                    class="px-2 py-1.5"
                    :class="col.montant ? 'text-right font-mono whitespace-nowrap' : (col.large ? 'break-words' : 'whitespace-nowrap')"
                    :title="col.infobulle ? col.infobulle(ligne) : null"
                  >
                    {{ col.valeur(ligne) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="text-xs text-gray-500">D = solde débiteur, C = solde créditeur.</p>
        </div>

        <!-- e) Détail technique, replié -->
        <details class="border-t pt-3 text-xs text-gray-600">
          <summary class="cursor-pointer font-semibold text-blue-ycube">Afficher le détail technique</summary>
          <div class="flex flex-col gap-4 mt-3">
            <div>
              <p class="font-semibold text-gray-700">Lignes écartées</p>
              <p v-if="!detailOuvert.controles_preliminaires?.lignes_ecartees?.nb" class="text-gray-500">Aucune ligne écartée.</p>
              <template v-else>
                <p>Lignes de total ou de sous-total du fichier (ou lignes sans numéro), écartées car ce ne sont pas des comptes :</p>
                <ul class="list-disc ml-4 mt-1">
                  <li v-for="e in detailOuvert.controles_preliminaires.lignes_ecartees.lignes" :key="e.ligne_excel">
                    Ligne Excel {{ e.ligne_excel }} :
                    <template v-if="e.motif === 'sous_total'">
                      sous-total {{ e.contenu?.numero_compte }} « {{ e.contenu?.libelle || 'sans libellé' }} »
                      (résume {{ e.contenu?.nb_comptes_detail }} comptes du fichier)
                    </template>
                    <template v-else>{{ e.contenu?.code_entite || e.contenu?.libelle_compte || e.contenu?.libelle || '(sans libellé)' }}</template>
                  </li>
                </ul>
              </template>
            </div>

            <div v-if="lignesTotalEnEcart.length">
              <p class="font-semibold text-gray-700">Comparaison des lignes de total en écart</p>
              <div v-for="r in lignesTotalEnEcart" :key="r.ligne_excel" class="mt-1">
                <p>Ligne Excel {{ r.ligne_excel }} ({{ r.libelle || 'sans libellé' }}) :</p>
                <ul class="ml-4">
                  <li v-for="(res, perimetre) in r.par_perimetre" :key="perimetre">
                    Comparée à {{ libellePerimetre(perimetre) }} :
                    <span v-for="(c, champ) in res.comparaisons" :key="champ" class="mr-2" :class="c.ok ? 'text-green-700' : 'text-red-600'">
                      {{ LIBELLES_DONNEES[champ] || champ }} {{ c.ok ? 'OK' : formatMontant(c.valeur_fichier) + ' ≠ ' + formatMontant(c.somme_calculee) }}
                    </span>
                  </li>
                </ul>
              </div>
            </div>

            <div v-if="detailOuvert.mapping_utilise">
              <p class="font-semibold text-gray-700 mb-1">Correspondance des colonnes</p>
              <table class="min-w-full text-xs">
                <thead class="bg-blue-ycube text-white text-left">
                  <tr class="h-8">
                    <th class="px-2">Colonne du fichier</th>
                    <th class="px-2"></th>
                    <th class="px-2">Donnée</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(colonne, champ) in detailOuvert.mapping_utilise" :key="champ" class="border-b h-8">
                    <td class="px-2">{{ colonne }}</td>
                    <td class="px-2 text-gray-400">→</td>
                    <td class="px-2">
                      {{ LIBELLES_DONNEES[champ] || champ }}
                      <span class="text-gray-400 font-mono">({{ champ }})</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </details>
      </div>
    </div>
  </div>
</template>
