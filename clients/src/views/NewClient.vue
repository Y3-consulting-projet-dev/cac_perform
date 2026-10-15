<script setup>
import { ref, inject } from 'vue';
const axios = inject('axios')
import { useNotyf } from '../composables/useNotyf';
import router from '@/router';
import { avertissementNumeroCc } from '@/utils/client';

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
    creation_date: "",
    numero_cc: "",
    capital_social: ""
});

// Champs facultatifs (les clients existants ne les ont pas).
const CHAMPS_FACULTATIFS = new Set(['numero_cc', 'capital_social']);

// Libellés affichés dans les messages d'erreur (mêmes que le formulaire).
const LIBELLES = {
    company_name: 'Client',
    responsable_name: 'Nom et prénom(s) du responsable',
    civility: 'Civilité',
    responsable_function: 'Fonction du responsable',
    RCCM: 'RCCM',
    numero_cc: 'N°CC',
    capital_social: 'Capital social (FCFA)',
    legal_form: 'Forme juridique',
    address: 'Adresse',
    country: 'Pays',
    sector: "Secteur d'activité",
    referentiel: 'Référentiel comptable',
    creation_date: "Date de création de l'entreprise",
};

// Erreurs par champ, affichées sous chaque champ.
const erreurs = ref({});
const enCours = ref(false);

// Mêmes règles que ClientCreateSchema (api/src/schemas/client_schemas.py),
// vérifiées ici pour un message immédiat sans aller-retour serveur.
function validerFormulaire() {
    const e = {};
    for (const [cle, valeur] of Object.entries(field.value)) {
        if (!CHAMPS_FACULTATIFS.has(cle) && !String(valeur || '').trim()) e[cle] = 'Champ obligatoire.';
    }
    for (const cle of ['company_name', 'responsable_name', 'responsable_function', 'RCCM', 'legal_form', 'address', 'country', 'sector']) {
        if (!e[cle] && field.value[cle].trim().length < 2) e[cle] = 'Au moins 2 caractères.';
    }
    const capital = String(field.value.capital_social || '').replace(/[\s\u202f\u00a0]/g, '');
    if (capital && (Number.isNaN(Number(capital)) || Number(capital) < 0)) {
        e.capital_social = 'Nombre positif attendu (ex. 100 000 000).';
    }
    if (!e.creation_date && field.value.creation_date > new Date().toISOString().slice(0, 10)) {
        e.creation_date = 'La date de création ne peut pas être dans le futur.';
    }
    return e;
}

// Messages du serveur (marshmallow, en anglais) -> français.
function traduireErreurServeur(message) {
    if (/Length must be between/.test(message)) return 'Longueur invalide (au moins 2 caractères).';
    if (/Must be one of/.test(message)) return 'Valeur non autorisée.';
    if (/Not a valid date/.test(message)) return 'Date invalide.';
    return message;
}

function resumeErreurs(e) {
    return Object.keys(e).map((cle) => LIBELLES[cle] || cle).join(', ');
}

// Fonction pour ajouter un nouveau client
async function addClient() {
    if (enCours.value) return;
    erreurs.value = validerFormulaire();
    if (Object.keys(erreurs.value).length) {
        notyf.trigger(`Champ(s) à corriger : ${resumeErreurs(erreurs.value)}`, 'error', { duration: 6000 });
        return;
    }

    enCours.value = true;
    try {
        const { data } = await axios.post('/client/nouveau_client/', field.value);
        if (!data || data.response === 'error' || data.response === 'Failed') {
            throw { response: { data } };
        }
        notyf.trigger(`Client « ${field.value.company_name.trim()} » créé avec succès`, 'success', { duration: 4000 });
        router.back();
    } catch (err) {
        const donnees = err?.response?.data;
        if (donnees?.errors) {
            // Champ refusé par le serveur : message sous le champ concerné.
            erreurs.value = Object.fromEntries(
                Object.entries(donnees.errors).map(([cle, msgs]) => [cle, traduireErreurServeur([].concat(msgs)[0])]),
            );
            notyf.trigger(`Champ(s) refusé(s) par le serveur : ${resumeErreurs(erreurs.value)}`, 'error', { duration: 6000 });
        } else if (donnees?.message) {
            const message = donnees.message.includes('existe déjà')
                ? `Un client nommé « ${field.value.company_name.trim()} » existe déjà.`
                : donnees.message;
            notyf.trigger(message, 'error', { duration: 6000 });
        } else {
            notyf.trigger(`Création impossible : serveur injoignable ou erreur inattendue (${err?.message || 'raison inconnue'}).`, 'error', { duration: 6000 });
        }
    } finally {
        enCours.value = false;
    }
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
                        <input v-model="field.company_name" type="text" :class="erreurs['company_name'] ? 'border-red-500' : 'border-blue-ycube'" class="w-full border-2 rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                        <p v-if="erreurs.company_name" class="text-xs text-red-600 mt-1">{{ erreurs.company_name }}</p>
                    </div>
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Nom et Prénom(s) du responsable</label>
                        <input v-model="field.responsable_name" type="text" :class="erreurs['responsable_name'] ? 'border-red-500' : 'border-blue-ycube'" class="w-full border-2 rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                        <p v-if="erreurs.responsable_name" class="text-xs text-red-600 mt-1">{{ erreurs.responsable_name }}</p>
                    </div>
                </div>

                <div class="flex space-x-6">
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Civilité</label>
                        <select v-model="field.civility" name="" id="" :class="erreurs['civility'] ? 'border-red-500' : 'border-blue-ycube'" class="w-full border-2 rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                            <option value="" disabled>Choisir</option>
                            <option value="M">M</option>
                            <option value="Mme">Mme</option>
                            <option value="Mlle">Mlle</option>
                        </select>
                        <p v-if="erreurs.civility" class="text-xs text-red-600 mt-1">{{ erreurs.civility }}</p>
                    </div>
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Fonction du responsable</label>
                        <input v-model="field.responsable_function" type="text" :class="erreurs['responsable_function'] ? 'border-red-500' : 'border-blue-ycube'" class="w-full border-2 rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                        <p v-if="erreurs.responsable_function" class="text-xs text-red-600 mt-1">{{ erreurs.responsable_function }}</p>
                    </div>
                </div>

                <div class="flex space-x-6">
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">RCCM</label>
                        <input v-model="field.RCCM" type="text" :class="erreurs['RCCM'] ? 'border-red-500' : 'border-blue-ycube'" class="w-full border-2 rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                        <p v-if="erreurs.RCCM" class="text-xs text-red-600 mt-1">{{ erreurs.RCCM }}</p>
                    </div>
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Forme juridique</label>
                        <input v-model="field.legal_form" type="text" :class="erreurs['legal_form'] ? 'border-red-500' : 'border-blue-ycube'" class="w-full border-2 rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                        <p v-if="erreurs.legal_form" class="text-xs text-red-600 mt-1">{{ erreurs.legal_form }}</p>
                    </div>
                </div>

                <div class="flex space-x-6">
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Adresse</label>
                        <input v-model="field.address" type="text" :class="erreurs['address'] ? 'border-red-500' : 'border-blue-ycube'" class="w-full border-2 rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                        <p v-if="erreurs.address" class="text-xs text-red-600 mt-1">{{ erreurs.address }}</p>
                    </div>
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Pays</label>
                        <input v-model="field.country" type="text" :class="erreurs['country'] ? 'border-red-500' : 'border-blue-ycube'" class="w-full border-2 rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                        <p v-if="erreurs.country" class="text-xs text-red-600 mt-1">{{ erreurs.country }}</p>
                    </div>
                </div>

                <div class="flex space-x-6">
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">secteur d'activité</label>
                        <input v-model="field.sector" type="text" :class="erreurs['sector'] ? 'border-red-500' : 'border-blue-ycube'" class="w-full border-2 rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                        <p v-if="erreurs.sector" class="text-xs text-red-600 mt-1">{{ erreurs.sector }}</p>
                    </div>
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Référentiel comptable</label>
                        <select v-model="field.referentiel" name="" id="" :class="erreurs['referentiel'] ? 'border-red-500' : 'border-blue-ycube'" class="w-full border-2 rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                            <option value="" disabled>Choisir un référentiel</option>
                            <option value="SYSCOHADA">SYSCOHADA</option>
                        </select>
                        <p v-if="erreurs.referentiel" class="text-xs text-red-600 mt-1">{{ erreurs.referentiel }}</p>
                    </div>
                </div>

                <div class="flex space-x-6">
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">N°CC <span class="normal-case font-normal text-gray-500">(facultatif)</span></label>
                        <input v-model="field.numero_cc" type="text" placeholder="ex. 1512345 A" class="w-full border-2 border-blue-ycube rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                        <p v-if="avertissementNumeroCc(field.numero_cc)" class="text-xs text-orange-600 mt-1">{{ avertissementNumeroCc(field.numero_cc) }}</p>
                    </div>
                    <div class="w-1/2">
                        <label for="" class="text-xs uppercase font-bold">Capital social (FCFA) <span class="normal-case font-normal text-gray-500">(facultatif)</span></label>
                        <input v-model="field.capital_social" type="text" inputmode="numeric" placeholder="ex. 100 000 000" :class="erreurs['capital_social'] ? 'border-red-500' : 'border-blue-ycube'" class="w-full border-2 rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                        <p v-if="erreurs.capital_social" class="text-xs text-red-600 mt-1">{{ erreurs.capital_social }}</p>
                    </div>
                </div>

                <div class="w-1/2">
                    <label for="" class="text-xs uppercase font-bold">Date de création de l'entreprise</label>
                    <input v-model="field.creation_date" type="date" :class="erreurs['creation_date'] ? 'border-red-500' : 'border-blue-ycube'" class="w-full border-2 rounded-lg pl-2 focus:outline-none focus:ring-0 h-10">
                        <p v-if="erreurs.creation_date" class="text-xs text-red-600 mt-1">{{ erreurs.creation_date }}</p>
                </div>
            </div>

            <div class="flex justify-end">
                <button class="bg-gradient-to-r from-blue-ycube to-green-ycube px-10 py-2 rounded-md uppercase font-bold text-gray-ycube disabled:opacity-50 disabled:cursor-not-allowed" :disabled="enCours" @click="addClient">{{ enCours ? 'Création...' : 'Valider' }}</button>
            </div>
        </div>
    </div>
  </div>
</template>
