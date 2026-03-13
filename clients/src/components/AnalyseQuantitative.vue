<script setup>
import { ref, onMounted, inject, watch } from 'vue';

import { useNotyf } from '@/composables/useNotyf';
const axios = inject('axios')
const notyf = useNotyf()

// Facteur du seuil de matérialité (bench * factor %) : déjà géré via bench.factor
// Nouveau : facteurs MANUELS pour
//  - Performance materiality : 50 % à 80 % du seuil de matérialité
//  - Clearly trivial threshold : 1 % à 5 % de la performance materiality
const PERFORMANCE_FACTOR_RANGE = { min: 50, max: 80 }
const TRIVIAL_FACTOR_RANGE = { min: 1, max: 5 }

const FACTOR_RANGES = {
    ebitda: { min: 3, max: 5 },
    expenses: { min: 3, max: 5 },
    profit_before_tax: { min: 5, max: 10 },
    revenue: { min: 0.8, max: 2 },
    total_assets: { min: 1, max: 2 },
    total_equity_net_assets: { min: 1.0, max: 3.0 },
    cash_flows_from_operations: { min: 3.0, max: 5.0 }
}

const listBenchmark = ref([
    {
        id: "ebitda",
        name: "EBITDA",
        balance_value: null,
        factor: null,
        amount_based_on_factor: null,
        performance_materiality: null,
        thresold: null,
        text: "Fourchette de facteur attendue : 3-5 % (peut aller jusqu'a 5 % compte tenu de la taille de l'entite). Consultez le guide de materialite pour plus de details."

    },
    {
        id: "expenses",
        name: "Expenses",
        balance_value: null,
        factor: null,
        amount_based_on_factor: null,
        performance_materiality: null,
        thresold: null,
        text: "Fourchette de facteur attendue : 3-5 % (peut aller jusqu'a 5 % compte tenu de la taille de l'entite). Consultez le guide de materialite pour plus de details."

    },
    {
        id: "profit_before_tax",
        name: "Profit Before Tax",
        balance_value: null,
        factor: null,
        amount_based_on_factor: null,
        performance_materiality: null,
        thresold: null,
        text: "Fourchette de facteur attendue : 5-10%. Voir le guide de materialite pour plus de details."

    },
    {
        id: "revenue",
        name: "Revenue",
        balance_value: null,
        factor: null,
        amount_based_on_factor: null,
        performance_materiality: null,
        thresold: null,
        text: "Fourchette de facteur attendue : 0,8-2 % (peut aller jusqu'a 5 % compte tenu de la taille de l'entite). Consultez le guide de materialite pour plus de details."

    },
    {
        id: "total_assets",
        name: "Total Assets",
        balance_value: null,
        factor: null,
        amount_based_on_factor: null,
        performance_materiality: null,
        thresold: null,
        text: "Fourchette de facteur attendue : 1-2%. Consultez le guide de materialite pour plus de details."

    },
    {
        id: "total_equity_net_assets",
        name: "Total equity / net assets",
        balance_value: null,
        factor: null,
        amount_based_on_factor: null,
        performance_materiality: null,
        thresold: null,
        text: "Fourchette de facteur attendue : 1,0-3,0%."

    },
    {
        id: "cash_flows_from_operations",
        name: "Cash flows from operations",
        balance_value: null,
        factor: null,
        amount_based_on_factor: null,
        performance_materiality: null,
        thresold: null,
        text: "Fourchette de facteur attendue : 3,0-5,0%."

    }
])

const listMaterialities = ref([])

// Une variable qui est utilisé pour maj la liste des seuils de signification quand on enregistre un nouveau
const isValidate = ref(1)

const selectedBench = ref("")
const bench = ref({
    id: "",
    balanceValue: "",
    factor: "",
    performance_factor: "",
    trivial_factor: "",
    amount_based_on_factor: null,
    performance_materiality: null,
    thresold: null,
    text: ""
})

// Recuperer l'id mission dans l'URL
const id_mission = window.location.pathname.split('/')[2]

onMounted(async() =>{
    const result = (await axios.get(`/mission/get_benchmarks/${id_mission}`)).data.response
    
    await getListMaterialities()

    const _keys = Object.keys(result)
    // Remplis la variable listBenchmark avec les benchmarks issus en adressant correctement via la clé id
    listBenchmark.value.forEach(obj => {
        if (_keys.includes(obj.id)) {
            obj.balance_value = result[obj.id]
        }
    })
    console.log(listBenchmark.value)
})

watch(selectedBench, (newValue)=>{
    bench.value.id = newValue
    listBenchmark.value.map(obj => {
        if (obj.id === newValue) {
            bench.value.balanceValue = obj.balance_value
            bench.value.text = obj.text
        }
    })
})

watch(() => bench.value.factor, (newValue) => {
    const factor = parseFloat(newValue)
    const range = FACTOR_RANGES[bench.value.id]
    if (!range || !factor) return
    if (factor < range.min || factor > range.max) {
        notyf.trigger(`Factor out of range for ${bench.value.id}: ${range.min}% to ${range.max}%`, "error")
    }
})

watch(isValidate, async(newValue)=> {
    console.log(newValue)
    await getListMaterialities()
})

async function getListMaterialities() {
    const materialities = (await axios.get(`/mission/get_materiality/${id_mission}`)).data.response.materiality
    console.log(materialities)
    listMaterialities.value = materialities
}

// Calculer les valeurs dépendants du facteur saisi
function updateSelectBenchmark() {
    const factor = parseFloat(bench.value.factor)
    const performanceFactor = parseFloat(bench.value.performance_factor)
    const trivialFactor = parseFloat(bench.value.trivial_factor)
    const balance = Number(bench.value.balanceValue)
    if (!Number.isFinite(factor) || !Number.isFinite(balance)) {
        bench.value.amount_based_on_factor = null
        bench.value.performance_materiality = null
        bench.value.thresold = null
        return
    }
    const range = FACTOR_RANGES[bench.value.id]
    if (range && (factor < range.min || factor > range.max)) {
        return
    }

    // 1. Calcul du seuil de matérialité (Materiality Threshold) à partir du bench et du factor (%)
    bench.value.amount_based_on_factor = Math.round((balance * factor) / 100)

    // 2. Calcul de la performance materiality à partir d'un pourcentage MANUEL (50–80 %)
    if (!Number.isFinite(performanceFactor)) {
        bench.value.performance_materiality = null
        bench.value.thresold = null
        return
    }
    if (
        performanceFactor < PERFORMANCE_FACTOR_RANGE.min ||
        performanceFactor > PERFORMANCE_FACTOR_RANGE.max
    ) {
        notyf.trigger(
            `Le pourcentage de Performance Materiality doit être compris entre ${PERFORMANCE_FACTOR_RANGE.min}% et ${PERFORMANCE_FACTOR_RANGE.max}%`,
            'error'
        )
        return
    }
    bench.value.performance_materiality = Math.round(
        bench.value.amount_based_on_factor * (performanceFactor / 100)
    )

    // 3. Calcul du Clearly Trivial Threshold à partir d'un pourcentage MANUEL (1–5 %) appliqué à la performance materiality
    if (!Number.isFinite(trivialFactor)) {
        bench.value.thresold = null
        return
    }
    if (trivialFactor < TRIVIAL_FACTOR_RANGE.min || trivialFactor > TRIVIAL_FACTOR_RANGE.max) {
        notyf.trigger(
            `Le pourcentage de Clearly Trivial Threshold doit être compris entre ${TRIVIAL_FACTOR_RANGE.min}% et ${TRIVIAL_FACTOR_RANGE.max}%`,
            'error'
        )
        return
    }
    bench.value.thresold = Math.round(
        bench.value.performance_materiality * (trivialFactor / 100)
    )
}

// Calculer seuil de signification et enregistrer dans la BD
async function validerSeuil() {
    const factor = parseFloat(bench.value.factor)
    const range = FACTOR_RANGES[bench.value.id]
    if (range && factor && (factor < range.min || factor > range.max)) {
        notyf.trigger(`Factor out of range for ${bench.value.id}: ${range.min}% to ${range.max}%`, "error")
        return
    }
    updateSelectBenchmark()

    const field = {
        benchmark: bench.value.id,
        materiality : bench.value.amount_based_on_factor,
        performance_materiality : bench.value.performance_materiality,
        trivial_misstatements: bench.value.thresold,
        factor: bench.value.factor,
        performance_factor: bench.value.performance_factor,
        trivial_factor: bench.value.trivial_factor
    }
    const result = (await axios.put(`/mission/save_materiality/${id_mission}`, field)).data.response
    console.log(result)
    if (result === 1) {
        notyf.trigger('Seuil enregsitré avec succès', 'success')
        isValidate.value = isValidate.value + 1
    } else {
        notyf.trigger('Veuillez réessayer', 'error')
    }
}

async function applySeuil(benchmark) {
    const field = {
        "benchmark": benchmark
    }
    const response = await axios.put(`/mission/validate_materiality/${id_mission}`, field)
    if (response.data['response'] === 1) {
        const res = await axios.put(`/mission/quantitative_analysis/${id_mission}`)
        notyf.trigger("Seuil appliqué au grouping avec succès", "success")
        console.log(res.data['response'])
    } else {
        // Ajouter une notification pour dire que ce n'est pas possible
        notyf.trigger("Echec d'application du seuil au grouping", "error")
    }
}
</script>

<template>
    <!-- Liste des seuils de signification -->
    <div class="flex flex-col overflow-auto">
        <h3 class="pt-3 pb-1 pl-0 text-xl font-bold uppercase tracking-wider flex space-x-2 items-center">
            <span>Détermination du seuil de signification</span>
        </h3>
        <div class="overflow-auto flex flex-col space-y-4">
            <!-- <component :is="renderComponent" :key="componentKey" /> -->

            <!-- Calcul du seuil de signification -->
            <div class="mx-auto w-[95%] h-[180px] flex flex-col px-6 pb-6 bg-gray-300 rounded-md">
                <h3 class="pt-3 pb-1 pl-0 text-base font-semibold uppercase tracking-wider">Calcul du seuil</h3>
                <div class="flex space-x-2">
                    <div class="w-[22%]">
                        <label for="" class="font-bold uppercase text-xs">Choisir benchmark</label>
                        <select v-model="selectedBench" name="" id="" class="px-2 border-2 border-blue-ycube w-full h-8">
                            <option value="" disabled>Aucun benchmark choisi</option>
                            <option v-for="bench, index in listBenchmark" :key="index" :value="bench.id">{{ bench.name }}</option>
                        </select>
                        <!-- <div v-if="selectedBench.balance_value" class="px-2 border-2 border-blue-ycube w-full h-8">{{ selectedBench.balance_value }}</div>
                        <div v-else class="px-2 border-2 border-blue-ycube w-full italic h-8">Aucune benchmark choisi</div> -->
                    </div>
                    <div class="w-[22%]">
                        <label for="" class="font-bold uppercase text-xs">Benchmark Balance</label>
                        <div v-if="bench.id" class="px-2 border-2 border-blue-ycube w-full h-8">{{ bench.balanceValue }}</div>
                        <div v-else class="px-2 border-2 border-blue-ycube w-full italic h-8">Aucun benchmark choisi</div>
                    </div>

                    <div class="w-[18%]">
                        <label for="" class="font-bold uppercase text-xs">Factor (%)</label>
                        <input v-model="bench.factor" class="px-2 border-2 border-blue-ycube w-full h-8 placeholder:italic" type="text" placeholder="Enter factor...">
                        <div v-if="bench.id" class="mt-2 text-xs italic"><i class="mdi mdi-information font-bold text-base"></i> {{ bench.text }}</div>
                        <!-- <button @click="console.log(selectedBench)">Test</button> -->
                    </div>

                    <div class="w-[18%]">
                        <label for="" class="font-bold uppercase text-xs">Performance Materiality (%)</label>
                        <input
                            v-model="bench.performance_factor"
                            class="px-2 border-2 border-blue-ycube w-full h-8 placeholder:italic"
                            type="text"
                            placeholder="Entre 50 et 80 %"
                        >
                    </div>

                    <div class="w-[18%]">
                        <label for="" class="font-bold uppercase text-xs">Clearly Trivial (%)</label>
                        <input
                            v-model="bench.trivial_factor"
                            class="px-2 border-2 border-blue-ycube w-full h-8 placeholder:italic"
                            type="text"
                            placeholder="Entre 1 et 5 %"
                        >
                    </div>

                    <div class="w-[10%] flex items-end">
                        <button class="mt-6 py-2 px-8 bg-blue-ycube rounded-md text-xs font-semibold text-white" @click="validerSeuil">Valider</button>
                    </div>
                </div>
            </div>

            <!-- Liste des seuils de signification calculés -->
            <div class="flex flex-col overflow-auto">
                <h3 class="pt-3 pb-1 pl-0 text-base font-semibold uppercase tracking-wider">Liste des seuils de signification</h3>
                <div class="overflow-hidden rounded-xl shadow-xl bg-white border border-gray-100">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-600">
                            <tr>
                                <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">#</th>
                                <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Benchmark</th>
                                <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Factor</th>
                                <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Materiality Threshold</th>
                                <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Materiality Performance</th>
                                <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Seuil inexactitudes</th>
                                <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            <tr v-for="mat, index in listMaterialities" :key="index" class="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-300 group transform hover:scale-[1.01] hover:shadow-md">
                                <td class="px-6 py-4 whitespace-nowrap text-center">
                                    <div class="flex items-center justify-center">
                                        <div class="flex-shrink-0 h-8 w-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-200">
                                            <span class="text-xs font-bold text-white">{{ index + 1 }}</span>
                                        </div>
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div class="text-sm font-medium text-gray-900 group-hover:text-blue-700 transition-colors duration-200">{{ mat.benchmark }}</div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-right">
                                    <div class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">{{ mat.factor }}%</div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-right">
                                    <div class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">{{ mat.materiality.toLocaleString() }}</div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-right">
                                    <div class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">{{ mat.performance_materiality.toLocaleString() }}</div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-right">
                                    <div class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">{{ mat.trivial_misstatements.toLocaleString() }}</div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-center">
                                    <button class="inline-flex items-center px-4 py-2 border border-transparent text-xs font-medium rounded-lg transition-all duration-300 transform hover:scale-105 hover:shadow-lg bg-gradient-to-r from-blue-100 to-blue-200 text-blue-700 hover:from-blue-200 hover:to-blue-300 border border-blue-300" @click="applySeuil(mat.benchmark)">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                        </svg>
                                        Appliquer
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</template>




