<script setup>
import { ref, onMounted } from 'vue';
import router from '@/router';
import { uploadFile } from '@/utils/uploadFile';
import { useNotyf } from '../composables/useNotyf';
import {
  apercuMapping,
  enregistrerMapping,
  recupererMapping,
  controlesPreliminaires,
  importerBalanceAuxiliaire,
  importerImmobilisations,
} from '@/api/imports.api';

const props = defineProps(['clientId'])
const notyf = useNotyf()

const field = ref({
  date_debut: "",
  date_fin: "",
  annee_auditee: "",
  date_debut_mandat: "",
  date_fin_mandat: ""
})

const selectedFile = ref([])

// --- Refonte import V2 (docs/PLAN_import_refonte.md) : état additionnel,
// n'intervient pas dans le flux de création de mission existant ci-dessus. ---
const logicielComptable = ref("")
const apercuResult = ref(null)
const mappingEdite = ref({})
const memoriserCeMapping = ref(false)
const loadingApercu = ref(false)

const controlesResult = ref(null)
const loadingControles = ref(false)

const fichierAuxiliaireClient = ref(null)
const fichierAuxiliaireFournisseur = ref(null)
const fichierImmobilisations = ref(null)

async function analyserMapping() {
  if (!selectedFile.value[0]) {
    notyf.trigger("Importez d'abord la balance N", 'info')
    return
  }
  loadingApercu.value = true
  try {
    const resultat = await apercuMapping(selectedFile.value[0])
    apercuResult.value = resultat
    mappingEdite.value = { ...resultat.mapping_propose }
  } catch (e) {
    notyf.trigger(e.message || "Erreur lors de l'analyse du mapping", 'error')
  } finally {
    loadingApercu.value = false
  }
}

async function lancerControlesPreliminaires() {
  if (!selectedFile.value[0]) {
    notyf.trigger("Importez d'abord la balance N", 'info')
    return
  }
  loadingControles.value = true
  try {
    controlesResult.value = await controlesPreliminaires(selectedFile.value[0])
  } catch (e) {
    notyf.trigger(e.message || "Erreur lors des contrôles préliminaires", 'error')
  } finally {
    loadingControles.value = false
  }
}

function onFichierAuxiliaireClient(event) {
  fichierAuxiliaireClient.value = event.target.files[0] || null
}

function onFichierAuxiliaireFournisseur(event) {
  fichierAuxiliaireFournisseur.value = event.target.files[0] || null
}

function onFichierImmobilisations(event) {
  fichierImmobilisations.value = event.target.files[0] || null
}

async function importerFichiersComplementaires(missionId) {
  // Plomberie uniquement : réception/stockage. Les échecs ici ne remettent
  // pas en cause la mission déjà créée (flux existant), ils sont juste
  // signalés séparément.
  if (fichierAuxiliaireClient.value) {
    try {
      await importerBalanceAuxiliaire(missionId, fichierAuxiliaireClient.value, 'client', props.clientId, field.value.annee_auditee)
      notyf.trigger('Balance auxiliaire clients importée', 'success')
    } catch (e) {
      notyf.trigger(e.message || "Erreur lors de l'import de la balance auxiliaire clients", 'error')
    }
  }

  if (fichierAuxiliaireFournisseur.value) {
    try {
      await importerBalanceAuxiliaire(missionId, fichierAuxiliaireFournisseur.value, 'fournisseur', props.clientId, field.value.annee_auditee)
      notyf.trigger('Balance auxiliaire fournisseurs importée', 'success')
    } catch (e) {
      notyf.trigger(e.message || "Erreur lors de l'import de la balance auxiliaire fournisseurs", 'error')
    }
  }

  if (fichierImmobilisations.value) {
    try {
      await importerImmobilisations(missionId, fichierImmobilisations.value, props.clientId, field.value.annee_auditee)
      notyf.trigger('Fichier des immobilisations importé', 'success')
    } catch (e) {
      notyf.trigger(e.message || "Erreur lors de l'import du fichier des immobilisations", 'error')
    }
  }

  if (memoriserCeMapping.value && logicielComptable.value && Object.keys(mappingEdite.value).length) {
    try {
      await enregistrerMapping(props.clientId, logicielComptable.value, mappingEdite.value)
      notyf.trigger('Mapping mémorisé pour ce client', 'success')
    } catch (e) {
      notyf.trigger(e.message || 'Erreur lors de la mémorisation du mapping', 'error')
    }
  }
}

onMounted(() => {
    console.log(props)
})

function onFileChange1(event) {
    selectedFile.value.push(event.target.files[0])
    selectedFile.value.push("")
}

function onFileChange2(event, index) {
    selectedFile.value[index] = event.target.files[0]
}

function addBalance() {
    if (!selectedFile.value[0]) {
        notyf.trigger("Importez d'abord la balance N", 'info')
    } else {
        selectedFile.value.push("")
    }
}

async function addMission() {
    // validation simple: 2 fichiers requis (N puis N-1)
    const files = (selectedFile.value || []).filter(f => !!f && (f.name || f.size !== undefined))
    if (files.length != 2) {
        notyf.trigger("Téléversez exactement 2 fichiers: d'abord la balance N, puis la balance N-1", 'info')
        return
    }

    // Vérifier que les fichiers sont au bon format Excel
    const validFormats = ['.xlsx']
    const invalidFiles = files.filter(f => !validFormats.some(format => f.name.toLowerCase().endsWith(format)))
    if (invalidFiles.length > 0) {
        notyf.trigger(`Format de fichier non supporté: ${invalidFiles.map(f => f.name).join(', ')}. Format accepté: ${validFormats.join(', ')}`, 'error')
        return
    }

    if (!field.value.annee_auditee || !field.value.date_debut || !field.value.date_fin) {
        notyf.trigger("Renseignez l'année auditée et les dates de mission", 'info')
        return
    }

    const result = await uploadFile(field.value.annee_auditee, files, field.value.date_debut, field.value.date_fin, field.value.date_debut_mandat, field.value.date_fin_mandat, props.clientId)
    if (result && result._id) {
        notyf.trigger("Mission ajouté avec succès", "success")
        await importerFichiersComplementaires(result._id)
        back()
    } else {
        notyf.trigger("Erreur lors de la création de la mission", "error")
    }
}

function back() {
    router.back()
}
</script>

<template>
    <div
        class="h-full w-full bg-gradient-to-r from-blue-ycube to-green-ycube flex overflow-y-auto items-start justify-center py-10">
        <div class="flex flex-col bg-white px-6 py-6 w-[60%] rounded-md shadow-lg overflow-auto">
            <div class="flex">
                <button class="px-6 py-2 rounded-md bg-gray-ycube-1" @click="back">Retour</button>
            </div>
            <div class="flex flex-col space-y-5 overflow-auto">
                <h1 class="text-justifyfont-bold text-blue-ycube text-xl">Nouvelle mission</h1>
                <div class="flex-auto flex flex-col space-y-4">
                    <div class="flex space-x-6">
                        <div class="w-1/2">
                            <label for="" class="text-xs uppercase font-bold">Date de début</label>
                            <input v-model="field.date_debut" type="date"
                                class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                        </div>
                        <div class="w-1/2">
                            <label for="" class="text-xs uppercase font-bold">Date de fin</label>
                            <input v-model="field.date_fin" type="date"
                                class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                        </div>
                    </div>

                    <div class="flex space-x-6">
                        <div class="w-1/2">
                            <label for="" class="text-xs uppercase font-bold">Année auditée</label>
                            <input v-model="field.annee_auditee" type="text"
                                class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                        </div>
                        <div class="w-1/2 flex flex-col justify-end">
                            <label for="" class="text-xs uppercase font-bold">Importer une balance</label>
                            <input type="file" id="file" class="sr-only" accept=".xlsx" @change="onFileChange1">
                            <label for="file"
                                class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                                <div>
                                    <span v-if="selectedFile[0]" class="mt-2 block text-xs select-none">{{
                                        selectedFile[0].name }}</span>
                                    <span v-else class="mt-2 block text-xs italic select-none">Aucun fichier
                                        sélectionné</span>
                                </div>
                            </label>
                        </div>
                    </div>
                </div>

                <div class="flex space-x-6">
  <div class="w-1/2">
    <label class="text-xs uppercase font-bold">Début du mandat</label>
    <input v-model="field.date_debut_mandat" type="date" class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10" />
  </div>

  <div class="w-1/2">
    <label class="text-xs uppercase font-bold">Fin du mandat</label>
    <input v-model="field.date_fin_mandat" type="date" class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10" />
  </div>
</div>


                <div v-if="selectedFile[0]" class="flex flex-col space-y-3">
                    <div v-for="n in selectedFile.length - 1" :key="n"
                        class="w-1/2 flex flex-col justify-end overflow-auto">
                        <label for="" class="text-xs uppercase font-bold">Balance N-{{ n }}</label>
                        <input type="file" :id="'file' + n" class="sr-only" @change="(e) => onFileChange2(e, n)">
                        <label :for="'file' + n"
                            class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                            <div>
                                <span v-if="selectedFile[n]" class="mt-2 block text-xs select-none">{{
                                    selectedFile[n].name }}</span>
                                <span v-else class="mt-2 block text-xs italic select-none">Aucun fichier
                                    sélectionné</span>
                            </div>
                        </label>
                    </div>
                </div>


                <!-- Refonte import V2 (docs/PLAN_import_refonte.md) : correspondance de
                     colonnes, contrôles préliminaires, fichiers complémentaires.
                     N'intervient pas dans la validation/soumission existante ci-dessous. -->
                <div v-if="selectedFile[0]" class="border-t pt-4 flex flex-col space-y-4">
                    <h2 class="text-sm font-bold uppercase text-blue-ycube">Correspondance des colonnes (optionnel)</h2>

                    <div class="flex space-x-6 items-end">
                        <div class="w-1/2">
                            <label class="text-xs uppercase font-bold">Logiciel comptable</label>
                            <input v-model="logicielComptable" type="text" placeholder="ex: Sage"
                                class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                        </div>
                        <div class="w-1/2">
                            <button class="bg-blue-ycube px-5 py-2 rounded-md text-sm font-semibold text-gray-ycube"
                                :disabled="loadingApercu" @click="analyserMapping">
                                {{ loadingApercu ? 'Analyse en cours...' : 'Analyser la balance N' }}
                            </button>
                        </div>
                    </div>

                    <div v-if="apercuResult" class="flex flex-col space-y-2">
                        <p class="text-xs text-gray-600">
                            Feuille « {{ apercuResult.feuille }} », format détecté : <strong>{{ apercuResult.format_propose }}</strong>
                            ({{ apercuResult.nb_lignes_detectees }} lignes)
                        </p>
                        <div v-for="champ in Object.keys(mappingEdite)" :key="champ" class="flex items-center space-x-3">
                            <span class="text-xs uppercase font-bold w-32">{{ champ }}</span>
                            <select v-model="mappingEdite[champ]" class="flex-1 border-2 border-blue-ycube rounded-lg pl-2 h-9 text-sm">
                                <option v-for="colonne in apercuResult.colonnes_detectees" :key="colonne" :value="colonne">{{ colonne }}</option>
                            </select>
                        </div>
                        <label class="flex items-center space-x-2 text-xs">
                            <input type="checkbox" v-model="memoriserCeMapping">
                            <span>Mémoriser ce mapping pour ce client + ce logiciel comptable</span>
                        </label>
                    </div>

                    <div class="flex items-center space-x-4">
                        <button class="bg-gray-ycube-1 px-5 py-2 rounded-md text-sm font-semibold"
                            :disabled="loadingControles" @click="lancerControlesPreliminaires">
                            {{ loadingControles ? 'Vérification...' : 'Lancer les contrôles préliminaires' }}
                        </button>
                    </div>

                    <div v-if="controlesResult" class="text-xs flex flex-col space-y-1">
                        <p :class="controlesResult.integrite.ok ? 'text-green-ycube' : 'text-red-500'">
                            Intégrité : {{ controlesResult.integrite.ok ? 'OK' : controlesResult.integrite.erreurs.join(', ') }}
                        </p>
                        <p v-if="controlesResult.colonnes_requises"
                            :class="controlesResult.colonnes_requises.ok ? 'text-green-ycube' : 'text-red-500'">
                            Colonnes requises : {{ controlesResult.colonnes_requises.ok ? 'OK' : 'manquantes : ' + controlesResult.colonnes_requises.champs_manquants.join(', ') }}
                        </p>
                    </div>

                    <h2 class="text-sm font-bold uppercase text-blue-ycube pt-2">Fichiers complémentaires (optionnel)</h2>
                    <div class="flex space-x-6">
                        <div class="w-1/3">
                            <label class="text-xs uppercase font-bold">Balance auxiliaire clients</label>
                            <input type="file" accept=".xlsx" @change="onFichierAuxiliaireClient"
                                class="w-full border-2 border-blue-ycube rounded-lg pl-2 h-10 text-xs">
                        </div>
                        <div class="w-1/3">
                            <label class="text-xs uppercase font-bold">Balance auxiliaire fournisseurs</label>
                            <input type="file" accept=".xlsx" @change="onFichierAuxiliaireFournisseur"
                                class="w-full border-2 border-blue-ycube rounded-lg pl-2 h-10 text-xs">
                        </div>
                        <div class="w-1/3">
                            <label class="text-xs uppercase font-bold">Fichier des immobilisations</label>
                            <input type="file" accept=".xlsx" @change="onFichierImmobilisations"
                                class="w-full border-2 border-blue-ycube rounded-lg pl-2 h-10 text-xs">
                        </div>
                    </div>
                </div>

                <div class="flex justify-between">
                    <button class="bg-blue-ycube px-5 py-2 rounded-md text-base font-semibold text-gray-ycube"
                        @click="addBalance"><i class="mdi mdi-plus-circle"></i> Importer une balance de plus</button>
                    <button
                        class="bg-gradient-to-r from-blue-ycube to-green-ycube px-10 py-2 rounded-md uppercase font-bold text-gray-ycube"
                        @click="addMission">Valider</button>
                </div>
            </div>
        </div>
    </div>
</template>
