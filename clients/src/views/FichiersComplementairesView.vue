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
import { ref, inject, onMounted } from 'vue'
import router from '@/router'
import { useNotyf } from '@/composables/useNotyf'
import {
  listerFichiersComplementaires,
  detailFichierComplementaire,
  importerBalanceAuxiliaire,
  importerImmobilisations,
} from '@/api/imports.api'

const props = defineProps(['missionId'])
const notyf = useNotyf()
const axios = inject('axios') // instance /cors existante, utilisée ici en lecture seule uniquement

const LIBELLES_TYPE = {
  auxiliaire_client: 'Balance auxiliaire clients',
  auxiliaire_fournisseur: 'Balance auxiliaire fournisseurs',
  immobilisations: 'Fichier des immobilisations',
}

const infoMission = ref(null)
const fichiers = ref({ auxiliaire_client: [], auxiliaire_fournisseur: [], immobilisations: [] })
const detailOuvert = ref(null)
const loading = ref(false)
const importingType = ref(null)

onMounted(async () => {
  await chargerInfoMission()
  await chargerFichiers()
})

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
  <div class="min-h-screen bg-[#f5f7fa] p-6">
    <div class="flex items-center justify-between mb-6">
      <button class="px-4 py-2 rounded-lg bg-white shadow font-semibold flex items-center gap-2" @click="back">
        <i class="fa-solid fa-arrow-left"></i> Retour
      </button>
      <h1 class="text-xl font-bold text-blue-ycube">Fichiers complémentaires de la mission</h1>
      <div></div>
    </div>

    <div class="bg-yellow-50 border border-yellow-300 text-yellow-800 text-sm rounded-lg p-4 mb-6">
      <i class="fa-solid fa-lock mr-2"></i>
      <strong>Rapprochement IPE — à venir.</strong>
      Cet écran permet seulement de consulter et gérer les fichiers importés. Aucun rapprochement avec la balance générale (comptes 411, 40x, 2xxx) n'est calculé ici.
    </div>

    <div v-if="loading" class="text-gray-500">Chargement...</div>

    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-6">
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
