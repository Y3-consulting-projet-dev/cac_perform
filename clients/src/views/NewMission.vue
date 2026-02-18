<script setup>
import { ref, onMounted } from 'vue';
import router from '@/router';
import { uploadFile } from '@/utils/uploadFile';
import { useNotyf } from '../composables/useNotyf';

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
        class="h-screen w-screen bg-gradient-to-r from-blue-ycube to-green-ycube flex overflow-auto items-center justify-center">
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
    <input v-model="field.date_debut_mandat" type="date" class="input" />
  </div>

  <div class="w-1/2">
    <label class="text-xs uppercase font-bold">Fin du mandat</label>
    <input v-model="field.date_fin_mandat" type="date" class="input" />
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
