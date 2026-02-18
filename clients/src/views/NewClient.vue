<script setup>
import { ref, inject } from 'vue';
const axios = inject('axios')
import { useNotyf } from '../composables/useNotyf';
import router from '@/router';

const notyf = useNotyf();

const field = ref({
    company_name: "",
    sector: "",
    address: "",
    referentiel: "",
    legal_form: "",
    responsable_name: "",
    civility: "",
    responsable_function: "",
    RCCM: "",
    country: "",
    creation_date: ""
});

// Fonction pour ajouter un nouveau client
async function addClient() {
    const result = (await axios.post('/client/nouveau_client/', field.value)).data.response
    console.log(result)
    if (result !== 'Failed') {
        notyf.trigger('Ajouté avec succès', 'success')
    }
    router.back();
}

// Fonction pour retourner à la home page
function back() {
    router.back();
}
</script>

<template>
  <div class="w-screen bg-gradient-to-r from-blue-ycube to-green-ycube flex overflow-auto items-center justify-center">
    <div class="flex flex-col bg-white px-6 py-6 w-[60%] mt-40 mb-20 rounded-md shadow-lg overflow-auto">
        <div class="flex">
            <button class="px-6 py-2 rounded-md bg-gray-ycube-1" @click="back">Retour</button>
        </div>
        <div class="flex flex-col space-y-5">
            <h1 class="text-justifyfont-bold text-blue-ycube text-xl">Saisir les informations du nouveau client</h1>
            <div class="flex-auto flex flex-col space-y-4">
                <div class="flex space-x-6">
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Client</label>
                        <input v-model="field.company_name" type="text" class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                    </div>
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Nom et Prénom(s) du responsable</label>
                        <input v-model="field.responsable_name" type="text" class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                    </div>
                </div>

                <div class="flex space-x-6">
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Civilité</label>
                        <select v-model="field.civility" name="" id="" class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                            <option value="" disabled>Choisir</option>
                            <option value="M">M</option>
                            <option value="Mme">Mme</option>
                            <option value="Mlle">Mlle</option>
                        </select>
                    </div>
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Fonction du responsable</label>
                        <input v-model="field.responsable_function" type="text" class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                    </div>
                </div>

                <div class="flex space-x-6">
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">N°CC</label>
                        <input v-model="field.RCCM" type="text" class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                    </div>
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Forme juridique</label>
                        <input v-model="field.legal_form" type="text" class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                    </div>
                </div>

                <div class="flex space-x-6">
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Adresse</label>
                        <input v-model="field.address" type="text" class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                    </div>
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Pays</label>
                        <input v-model="field.country" type="text" class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                    </div>
                </div>

                <div class="flex space-x-6">
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">secteur d'activité</label>
                        <input v-model="field.sector" type="text" class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                    </div>
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Référentiel comptable</label>
                        <select v-model="field.referentiel" name="" id="" class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                            <option value="" disabled>Choisir un référentiel</option>
                            <option value="SYSCOHADA">SYSCOHADA</option>
                        </select>
                    </div>
                </div>

                <div class="w-1/2">
                    <label for="" class="text-xs uppercase font-bold">Date de création de l'entreprise</label>
                    <input v-model="field.creation_date" type="date" class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                </div>
            </div>

            <div class="flex justify-end">
                <button class="bg-gradient-to-r from-blue-ycube to-green-ycube px-10 py-2 rounded-md uppercase font-bold text-gray-ycube" @click="addClient">Valider</button>
            </div>
        </div>
    </div>
  </div>
</template>
