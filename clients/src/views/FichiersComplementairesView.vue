<script setup>
// Écran de consultation des fichiers complémentaires d'une mission (balances
// auxiliaires clients/fournisseurs, fichier des immobilisations).
// Nouveau périmètre V2 — voir docs/PLAN_import_refonte.md.
//
// Lecture seule pour la consultation ; l'import/remplacement réutilise les
// mêmes services que la création de mission (aucun doublon de logique).
// N'est PAS une étape d'audit : volontairement absent de la barre de
// progression des 11 étapes de GroupingAnalyse.vue. Aucun rapprochement IPE
// n'est calculé ici (voir bandeau "Rapprochement IPE — à venir").
import { ref, inject, onMounted, computed } from 'vue'
import router from '@/router'
import { useNotyf } from '@/composables/useNotyf'
import {
  listerFichiersComplementaires,
  detailFichierComplementaire,
  importerBalanceAuxiliaire,
  importerImmobilisations,
} from '@/api/imports.api'
import {
  obtenirEtatIpe,
  evaluerIpe,
  validerFiabiliteIpe,
} from '@/api/ipe.api'

const props = defineProps(['missionId'])
const notyf = useNotyf()
const axios = inject('axios') // instance /cors existante, utilisée ici en lecture seule uniquement

const LIBELLES_TYPE = {
  auxiliaire_client: 'Balance auxiliaire clients',
  auxiliaire_fournisseur: 'Balance auxiliaire fournisseurs',
  immobilisations: 'Fichier des immobilisations',
}

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
// aucun collectif trouvé).
const STATUT_MODULE_INFO = {
  ok: { label: 'OK', classe: 'bg-green-100 text-green-ycube' },
  ecart: { label: 'Écart', classe: 'bg-red-100 text-red-600' },
  non_evaluable: { label: 'Non évaluable', classe: 'bg-gray-100 text-gray-500' },
}

// Ordre d'affichage fixe pour la synthèse (IPE-1 puis IPE-2 puis IPE-3),
// quel que soit l'ordre des clés dans la réponse API.
const ORDRE_MODULES = ['ipe_1_clients', 'ipe_2_fournisseurs', 'ipe_3_immobilisations']

const infoMission = ref(null)
const fichiers = ref({ auxiliaire_client: [], auxiliaire_fournisseur: [], immobilisations: [] })
const detailOuvert = ref(null)
const loading = ref(false)
const importingType = ref(null)

const ipeEtat = ref(null)
const ipeEvaluationEnCours = ref(false)
const ipeValidationEnCours = ref(false)

// Confirmation obligatoire avant validation (avec commentaire, enregistré
// dans l'historique) et avant invalidation (bouton secondaire).
const confirmationValidationOuverte = ref(false)
const commentaireValidation = ref('')
const confirmationInvalidationOuverte = ref(false)

onMounted(async () => {
  await chargerInfoMission()
  await chargerFichiers()
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

function ouvrirConfirmationValidation() {
  if (moduleEnEcartNonQualifie.value) return
  commentaireValidation.value = ''
  confirmationValidationOuverte.value = true
}

function annulerValidation() {
  confirmationValidationOuverte.value = false
}

async function confirmerValidation() {
  if (!commentaireValidation.value.trim()) {
    notyf.trigger('Un commentaire est requis pour valider la fiabilité IPE', 'warning')
    return
  }
  ipeValidationEnCours.value = true
  try {
    ipeEtat.value = await validerFiabiliteIpe(props.missionId, true, commentaireValidation.value.trim())
    notyf.trigger('Fiabilité IPE validée', 'success')
    confirmationValidationOuverte.value = false
  } catch (e) {
    notyf.trigger(e.message || 'Erreur lors de la validation', 'error')
  } finally {
    ipeValidationEnCours.value = false
  }
}

function ouvrirConfirmationInvalidation() {
  confirmationInvalidationOuverte.value = true
}

function annulerInvalidation() {
  confirmationInvalidationOuverte.value = false
}

async function confirmerInvalidation() {
  ipeValidationEnCours.value = true
  try {
    ipeEtat.value = await validerFiabiliteIpe(props.missionId, false)
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

async function chargerInfoMission() {
  try {
    infoMission.value = (await axios.get(`/mission/affichage_infos_mission/${props.missionId}`)).data.response
  } catch (e) {
    console.error('Erreur chargement infos mission', e)
  }
}

async function chargerFichiers() {
  loading.value = true
  try {
    fichiers.value = await listerFichiersComplementaires(props.missionId)
  } catch (e) {
    notyf.trigger(e.message || 'Erreur lors du chargement des fichiers', 'error')
  } finally {
    loading.value = false
  }
}

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

async function onImporter(event, type) {
  const fichier = event.target.files[0]
  if (!fichier) return

  if (!infoMission.value) {
    notyf.trigger('Informations de mission non chargées', 'error')
    return
  }

  importingType.value = type
  try {
    const idClient = infoMission.value.id_client
    const annee = infoMission.value.annee_auditee
    if (type === 'immobilisations') {
      await importerImmobilisations(props.missionId, fichier, idClient, annee)
    } else {
      const typeAuxiliaire = type === 'auxiliaire_client' ? 'client' : 'fournisseur'
      await importerBalanceAuxiliaire(props.missionId, fichier, typeAuxiliaire, idClient, annee)
    }
    notyf.trigger("Fichier importé avec succès (l'ancienne version reste dans l'historique)", 'success')
    await chargerFichiers()
  } catch (e) {
    notyf.trigger(e.message || "Erreur lors de l'import", 'error')
  } finally {
    importingType.value = null
    event.target.value = ''
  }
}

function back() {
  router.back()
}
</script>

<template>
  <div class="h-full w-full overflow-y-auto bg-[#f5f7fa] p-6">
    <div class="flex items-center justify-between mb-6">
      <button class="px-4 py-2 rounded-lg bg-white shadow font-semibold flex items-center gap-2" @click="back">
        <i class="fa-solid fa-arrow-left"></i> Retour
      </button>
      <h1 class="text-xl font-bold text-blue-ycube">Fichiers complémentaires de la mission</h1>
      <div></div>
    </div>

    <!-- Rapprochement IPE (Module 1, CAC-IPE-01) — docs/PLAN_verrou_IPE.md §4/§5.
         Écran de diagnostic, pas une étape d'audit : volontairement hors des
         11 étapes de GroupingAnalyse.vue (voir l'indicateur "Fiabilité IPE"
         dans sa barre latérale, qui renvoie ici pour le détail). -->
    <div class="bg-white rounded-xl shadow p-4 mb-6 flex flex-col gap-4 w-full" v-if="ipeEtat">
      <div class="flex items-center justify-between flex-wrap gap-2">
        <h2 class="font-bold text-sm uppercase text-blue-ycube">Rapprochement IPE</h2>
        <span class="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-700">
          {{ IPE_STATUT_LABELS[ipeEtat.statut_affiche] || 'Non commencé' }}
        </span>
      </div>

      <p v-if="!ipeEtat.verrou_applicable" class="text-xs text-gray-500 italic">
        Mission antérieure à l'activation du verrou IPE : jamais bloquée, ce rapprochement reste informatif.
      </p>

      <!-- Synthèse : une ligne par module, statut + écart global -->
      <table class="w-full text-xs">
        <thead>
          <tr class="text-gray-500 text-left border-b">
            <th class="py-1">Module</th>
            <th class="py-1">Statut</th>
            <th class="py-1 text-right">Écart global</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ligne in syntheseModules" :key="ligne.cle" class="border-b last:border-0">
            <td class="py-2">{{ ligne.libelle }}</td>
            <td class="py-2">
              <span
                class="px-2 py-0.5 rounded-full text-xs font-medium"
                :class="ligne.statut ? STATUT_MODULE_INFO[ligne.statut]?.classe : 'bg-gray-100 text-gray-400'"
              >
                {{ ligne.statut ? STATUT_MODULE_INFO[ligne.statut]?.label : 'Non évalué' }}
              </span>
            </td>
            <td class="py-2 text-right font-mono">{{ formatMontant(ligne.ecartGlobal) }}</td>
          </tr>
        </tbody>
      </table>

      <div class="flex flex-wrap items-center gap-2">
        <button
          class="text-xs px-3 py-2 rounded-lg bg-blue-ycube text-white hover:opacity-90 transition disabled:opacity-50"
          :disabled="ipeEvaluationEnCours"
          @click="lancerEvaluationIpe"
        >
          {{ ipeEvaluationEnCours ? 'Rapprochement en cours...' : 'Lancer le rapprochement IPE-1/2/3' }}
        </button>

        <!-- Bouton principal : désactivé tant qu'un module est en écart non qualifié -->
        <button
          class="text-xs px-3 py-2 rounded-lg bg-green-ycube text-white hover:opacity-90 transition disabled:opacity-40 disabled:cursor-not-allowed"
          :disabled="ipeValidationEnCours || moduleEnEcartNonQualifie"
          :title="moduleEnEcartNonQualifie ? 'Qualifiez les écarts avant de valider (voir les modules en écart ci-dessous)' : ''"
          @click="ouvrirConfirmationValidation"
        >
          Valider la fiabilité IPE
        </button>

        <!-- Bouton secondaire, volontairement moins mis en avant -->
        <button
          class="text-xs px-3 py-1.5 rounded-lg border border-gray-300 text-gray-500 hover:bg-gray-50 transition disabled:opacity-40"
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
      <div v-if="confirmationValidationOuverte" class="border border-green-ycube/40 bg-green-50 rounded-lg p-3 flex flex-col gap-2">
        <p class="text-xs font-semibold text-green-ycube">Confirmer la validation de la fiabilité IPE</p>
        <textarea
          v-model="commentaireValidation"
          rows="2"
          class="text-xs border rounded-lg p-2 w-full"
          placeholder="Commentaire (obligatoire, enregistré dans l'historique)"
        ></textarea>
        <div class="flex gap-2">
          <button
            class="text-xs px-3 py-1.5 rounded-lg bg-green-ycube text-white hover:opacity-90 transition disabled:opacity-50"
            :disabled="ipeValidationEnCours"
            @click="confirmerValidation"
          >
            Confirmer
          </button>
          <button class="text-xs px-3 py-1.5 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-100 transition" @click="annulerValidation">
            Annuler
          </button>
        </div>
      </div>

      <!-- Confirmation d'invalidation -->
      <div v-if="confirmationInvalidationOuverte" class="border border-gray-300 bg-gray-50 rounded-lg p-3 flex flex-col gap-2">
        <p class="text-xs font-semibold text-gray-600">Confirmer l'invalidation de la fiabilité IPE ?</p>
        <div class="flex gap-2">
          <button
            class="text-xs px-3 py-1.5 rounded-lg border border-gray-400 text-gray-700 hover:bg-gray-100 transition disabled:opacity-50"
            :disabled="ipeValidationEnCours"
            @click="confirmerInvalidation"
          >
            Confirmer
          </button>
          <button class="text-xs px-3 py-1.5 rounded-lg text-gray-500 hover:bg-gray-100 transition" @click="annulerInvalidation">
            Annuler
          </button>
        </div>
      </div>

      <div v-if="ipeEtat.modules && Object.keys(ipeEtat.modules).length" class="flex flex-col gap-3 mt-2">
        <div v-for="(module, cle) in ipeEtat.modules" :key="cle" class="border rounded-lg p-3 text-xs">
          <div class="flex items-center justify-between">
            <span class="font-semibold">{{ LIBELLES_MODULE[cle] || cle }}</span>
            <span
              class="px-2 py-0.5 rounded-full text-xs font-medium"
              :class="STATUT_MODULE_INFO[module.statut]?.classe || 'bg-gray-100 text-gray-500'"
            >
              {{ STATUT_MODULE_INFO[module.statut]?.label || module.statut }}
            </span>
          </div>

          <div v-if="module.derniere_evaluation" class="mt-2 flex flex-col gap-2 text-gray-600">
            <p v-if="module.statut === 'non_evaluable'" class="italic text-gray-500">
              Non évaluable — {{ module.derniere_evaluation.motif_non_evaluable === 'fichier_complementaire_absent'
                ? 'aucun fichier complémentaire actif pour ce module.'
                : 'aucun compte collectif trouvé dans la balance générale pour ce module.' }}
            </p>
            <p v-else>Écart global : <span class="font-mono">{{ formatMontant(module.derniere_evaluation.ecart_global) }}</span></p>

            <table v-if="module.derniere_evaluation.detail_collectifs?.length" class="w-full text-left">
              <thead>
                <tr class="text-gray-500">
                  <th class="pr-3 py-1">Compte collectif</th>
                  <th class="pr-3 py-1 text-right">Solde balance générale</th>
                  <th class="pr-3 py-1 text-right">Solde auxiliaire</th>
                  <th class="pr-3 py-1 text-right">Tiers rattachés</th>
                  <th class="py-1 text-right">Écart</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="c in module.derniere_evaluation.detail_collectifs"
                  :key="c.numero_compte"
                  :class="module.statut !== 'ecart' ? 'text-gray-500' : (c.ok ? 'text-green-ycube' : 'text-red-500')"
                >
                  <td class="pr-3 py-1">{{ c.numero_compte }}</td>
                  <td class="pr-3 py-1 text-right font-mono">{{ formatMontant(c.solde_balance_generale) }}</td>
                  <td class="pr-3 py-1 text-right font-mono">{{ formatMontant(c.solde_auxiliaire) }}</td>
                  <td class="pr-3 py-1 text-right">{{ c.nb_tiers_rattaches }}</td>
                  <td class="py-1 text-right font-mono">{{ formatMontant(c.ecart) }}</td>
                </tr>
              </tbody>
            </table>
            <p v-else-if="module.statut !== 'non_evaluable'" class="italic">Aucun compte collectif trouvé dans la balance générale pour ce module.</p>

            <p v-if="module.derniere_evaluation.tiers_orphelins?.balance_generale_seulement?.length" class="text-gray-500">
              Comptes collectifs sans tiers rattaché dans l'auxiliaire (TODO(spec: CAC-IPE-01) — traitement attendu non confirmé) :
              {{ module.derniere_evaluation.tiers_orphelins.balance_generale_seulement.join(', ') }}
            </p>
            <p v-if="module.derniere_evaluation.tiers_orphelins?.auxiliaire_seulement?.length" class="text-gray-500">
              Tiers de l'auxiliaire sans compte collectif correspondant (TODO(spec: CAC-IPE-01) — traitement attendu non confirmé) :
              {{ module.derniere_evaluation.tiers_orphelins.auxiliaire_seulement.join(', ') }}
            </p>
            <p v-if="module.derniere_evaluation.lignes_non_calculables?.length" class="text-orange-500">
              {{ module.derniere_evaluation.lignes_non_calculables.length }} ligne(s) auxiliaire(s) sans montant exploitable (mapping incomplet).
            </p>
          </div>
        </div>
      </div>
      <p v-else class="text-xs text-gray-500 italic">
        Aucune évaluation IPE encore lancée pour cette mission.
      </p>
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
          class="border rounded-lg p-3 flex flex-col gap-1 cursor-pointer hover:bg-gray-50"
          @click="voirDetail(f._id)">
          <span class="text-sm font-semibold truncate">{{ f.nom_fichier || 'Fichier sans nom' }}</span>
          <span class="text-xs text-gray-500">{{ f.date_import }}</span>
          <span class="text-xs text-gray-500">{{ f.nb_lignes }} lignes · version {{ f.version }}</span>
        </div>

        <label
          class="mt-2 text-xs text-center border-2 border-dashed border-blue-ycube rounded-lg py-2 cursor-pointer hover:bg-blue-50">
          <input type="file" accept=".xlsx" class="sr-only" :disabled="importingType === type"
            @change="(e) => onImporter(e, type)">
          {{ importingType === type ? 'Import en cours...' : (fichiers[type]?.length ? 'Remplacer' : 'Importer') }}
        </label>
      </div>
    </div>

    <!-- Détail d'un fichier -->
    <div v-if="detailOuvert" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-6"
      @click.self="fermerDetail">
      <div class="bg-white rounded-xl shadow-xl max-w-3xl w-full max-h-[85vh] overflow-y-auto p-6 flex flex-col gap-4">
        <div class="flex justify-between items-start">
          <div>
            <h3 class="font-bold text-blue-ycube">{{ detailOuvert.nom_fichier || 'Fichier sans nom' }}</h3>
            <p class="text-xs text-gray-500">Importé le {{ detailOuvert.date_import }} · version {{ detailOuvert.version }}</p>
          </div>
          <button class="text-gray-400 hover:text-gray-600" @click="fermerDetail">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>

        <!-- Totaux par paire (ouverture, mouvements, solde mouvement, solde final)
             quand le fichier fournit des colonnes débit/crédit séparées ; sinon
             repli "montant unique" (voir fichiers_complementaires_service.py). -->
        <div v-if="detailOuvert.totaux?.totaux && Object.keys(detailOuvert.totaux.totaux).length" class="text-sm">
          <table class="text-xs">
            <thead>
              <tr class="text-gray-500 text-left">
                <th class="pr-4"></th>
                <th class="pr-4">Débit</th>
                <th>Crédit</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(valeurs, libelle) in detailOuvert.totaux.totaux" :key="libelle">
                <td class="pr-4 font-semibold capitalize">{{ libelle }}</td>
                <td class="pr-4">{{ valeurs.debit }}</td>
                <td>{{ valeurs.credit }}</td>
              </tr>
            </tbody>
          </table>
          <p v-if="detailOuvert.totaux.mode === 'montant_signe'" class="text-xs text-gray-500 italic mt-1">
            Fichier à montant unique : convention positif = débit, négatif = crédit (TODO spec CAC-IPE-01).
          </p>
        </div>

        <div v-if="detailOuvert.mapping_utilise" class="text-xs text-gray-500">
          Mapping utilisé :
          <span v-for="(colonne, champ) in detailOuvert.mapping_utilise" :key="champ" class="mr-2">
            {{ champ }} = « {{ colonne }} »
          </span>
        </div>

        <div v-if="detailOuvert.controles_preliminaires" class="text-xs flex flex-col gap-2">
          <p :class="detailOuvert.controles_preliminaires.integrite?.ok ? 'text-green-ycube' : 'text-red-500'">
            Intégrité : {{ detailOuvert.controles_preliminaires.integrite?.ok ? 'OK' : (detailOuvert.controles_preliminaires.integrite?.erreurs || []).join(', ') }}
          </p>
          <p :class="detailOuvert.controles_preliminaires.doublons?.ok ? 'text-green-ycube' : 'text-red-500'">
            Doublons : {{ detailOuvert.controles_preliminaires.doublons?.ok ? 'OK' : 'détectés : ' + (detailOuvert.controles_preliminaires.doublons?.doublons || []).join(', ') }}
          </p>

          <!-- Lignes écartées (sans numéro de compte, ex. lignes de total Excel) :
               traçabilité, jamais une suppression silencieuse. -->
          <div v-if="detailOuvert.controles_preliminaires.lignes_ecartees" class="text-gray-600">
            <p>{{ detailOuvert.controles_preliminaires.lignes_ecartees.nb }} ligne(s) écartée(s) : sans numéro de compte.</p>
            <ul v-if="detailOuvert.controles_preliminaires.lignes_ecartees.nb" class="list-disc ml-4 mt-1">
              <li v-for="e in detailOuvert.controles_preliminaires.lignes_ecartees.lignes" :key="e.ligne_excel">
                Ligne Excel {{ e.ligne_excel }} : {{ e.contenu.code_entite || e.contenu.libelle_compte || '(vide)' }}
              </li>
            </ul>
          </div>

          <!-- Bouclage des totaux Excel (si le fichier en fournit) : comparé à 3
               périmètres (toutes les lignes, comptes de bilan, comptes de gestion),
               jamais sur le libellé de la ligne de total. OK si un périmètre colle. -->
          <div v-if="detailOuvert.controles_preliminaires.bouclage_total?.nb_lignes_de_total_detectees" class="text-gray-600">
            <p class="font-semibold">Bouclage avec les lignes de total du fichier :</p>
            <div v-for="r in detailOuvert.controles_preliminaires.bouclage_total.resultats" :key="r.ligne_excel" class="ml-2 mt-1">
              <p :class="r.ok ? 'text-green-ycube' : 'text-red-500'">
                Ligne Excel {{ r.ligne_excel }} ({{ r.libelle }}) :
                {{ r.ok ? 'OK — périmètre ' + r.perimetre_correspondant : 'écart (aucun périmètre ne correspond)' }}
              </p>
              <ul v-if="!r.ok" class="ml-4">
                <li v-for="(resultatPerimetre, nomPerimetre) in r.par_perimetre" :key="nomPerimetre">
                  {{ nomPerimetre }} :
                  <span v-for="(c, champ) in resultatPerimetre.comparaisons" :key="champ"
                    :class="c.ok ? 'text-green-ycube' : 'text-red-500'" class="mr-2">
                    {{ champ }}={{ c.ok ? 'OK' : c.valeur_fichier + '≠' + c.somme_calculee }}
                  </span>
                </li>
              </ul>
            </div>
          </div>

          <!-- Contrôle arithmétique ligne par ligne : ouv + mvt - final = 0 -->
          <div v-if="detailOuvert.controles_preliminaires.bouclage_ligne?.applicable" class="text-gray-600">
            <p :class="detailOuvert.controles_preliminaires.bouclage_ligne.nb_lignes_en_ecart ? 'text-red-500' : 'text-green-ycube'">
              Bouclage ligne par ligne (ouv + mvt = final) : {{ detailOuvert.controles_preliminaires.bouclage_ligne.nb_lignes_en_ecart ? detailOuvert.controles_preliminaires.bouclage_ligne.nb_lignes_en_ecart + ' ligne(s) en écart' : 'OK' }}
            </p>
            <ul v-if="detailOuvert.controles_preliminaires.bouclage_ligne.nb_lignes_en_ecart" class="list-disc ml-4 mt-1 text-red-500">
              <li v-for="e in detailOuvert.controles_preliminaires.bouclage_ligne.lignes_en_ecart" :key="e.ligne_excel">
                Ligne Excel {{ e.ligne_excel }} — {{ e.numero_compte }} {{ e.libelle_compte }} : écart = {{ e.ecart }}
              </li>
            </ul>
          </div>
        </div>

        <div class="overflow-x-auto border-t pt-3">
          <p v-if="!detailOuvert.lignes || detailOuvert.lignes.length === 0" class="text-xs text-gray-500 italic">
            Aucune ligne.
          </p>
          <table v-else class="min-w-full text-xs">
            <thead>
              <tr class="text-left text-gray-500">
                <th v-for="col in Object.keys(detailOuvert.lignes[0])" :key="col" class="px-2 py-1">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(ligne, i) in detailOuvert.lignes" :key="i" class="border-t">
                <td v-for="col in Object.keys(ligne)" :key="col" class="px-2 py-1">{{ ligne[col] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
