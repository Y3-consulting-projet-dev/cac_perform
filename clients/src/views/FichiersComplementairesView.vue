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
import { ref, onMounted } from 'vue'
import router from '@/router'
import { useNotyf } from '@/composables/useNotyf'
import {
  obtenirMission,
  listerFichiersComplementaires,
  historiqueFichiersComplementaires,
  detailFichierComplementaire,
  importerBalanceAuxiliaire,
  importerImmobilisations,
} from '@/api/imports.api'

const props = defineProps(['missionId'])
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
    notyf.trigger(`Import impossible — mission non chargée : ${erreurMission.value || 'raison inconnue'}`, 'error')
    event.target.value = ''
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

function allerVersFiabiliteIpe() {
  router.push(`/grouping-analyse/${props.missionId}/fiabilite-ipe`)
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
        <h1 class="text-xl font-bold text-blue-ycube">Fichiers complémentaires</h1>
        <p class="text-sm text-gray-500">Import, consultation et remplacement des balances auxiliaires</p>
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
            <div class="flex items-center justify-between gap-2">
              <span class="text-sm font-semibold truncate">{{ f.nom_fichier || 'Fichier sans nom' }}</span>
              <span class="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700">Active</span>
            </div>
            <span class="text-xs text-gray-500">{{ f.date_import }}</span>
            <span class="text-xs text-gray-500">{{ f.nb_lignes }} lignes · version {{ f.version }}</span>
          </div>

          <div v-if="archives[type]?.length" class="flex flex-col gap-1">
            <p class="text-xs text-gray-500">Versions archivées</p>
            <div v-for="f in archives[type]" :key="f._id"
              class="border rounded-lg p-2 flex items-center justify-between gap-2 cursor-pointer hover:bg-gray-50 text-gray-500"
              @click="voirDetail(f._id)">
              <span class="text-xs truncate">v{{ f.version }} · {{ f.nom_fichier || 'Fichier sans nom' }} · {{ f.nb_lignes }} lignes</span>
              <span class="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700">Archivée</span>
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

    <!-- Détail d'un fichier — même recette de modale que ClientsView.vue (charte CLAUDE.md) -->
    <div v-if="detailOuvert" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click.self="fermerDetail">
      <div class="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-auto p-6 relative flex flex-col gap-4">
        <div class="flex justify-between items-start">
          <div>
            <h3 class="font-bold text-blue-ycube">{{ detailOuvert.nom_fichier || 'Fichier sans nom' }}</h3>
            <p class="text-xs text-gray-500">Importé le {{ detailOuvert.date_import }} · version {{ detailOuvert.version }}</p>
          </div>
          <button class="text-gray-500 hover:text-gray-800" @click="fermerDetail">
            <i class="fa-solid fa-xmark text-2xl"></i>
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
