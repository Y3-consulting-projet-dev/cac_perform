<script setup>
import { ref, inject, onMounted } from 'vue';
import { useNotyf } from '@/composables/useNotyf';
const axios = inject('axios')
const notyf = useNotyf();
const props = defineProps(['grouping'])

const questions = ref([
    "Volume d'activité, complexité et homogénéité des transactions enregistrées, existence de transactions significatives inhabituelles ou anormales dans le COTABD",
    "Changements identifiés dans le COTABD et détermination si un ou de nouveaux risque(s) sont apparus du fait de changement au sein de l'entité ou de son environnement (économique, légal, réglementaire, normatif ou méthodes comptables)",
    "Sensibilité de l'entité aux anomalies issues de fraudes (Si oui, le risque est obligatoirement Significant)",
    "Niveau de complexité des normes, règles, méthodes comptables, notes annexes, estimations ou jugements liées aux comptes ou aux notes annexes",
    "Exposition du COTABD à des pertes (charges ou dépréciations)",
    "Probabilité que des passifs éventuels significatifs (procès, contentieux, litiges etc…) puissent être issus des transactions enregistrées dans le COTABD",
    "Existence de transactions avec des parties liées dans le COTABD",
    "Niveau de contrôle interne et fiabilité des systèmes d'information liés aux comptes"
])

const listQuestions = ref([])
const groupingStats = ref(null)

// Gestion du tooltip pour les questions
const showQuestionTooltip = ref(false);
const selectedQuestion = ref('');
const selectedQuestionText = ref('');
const tooltipPosition = ref({ x: 0, y: 0 });


// Recuperer l'id mission dans l'URL
const id_mission = window.location.pathname.split('/')[2]

// Charger les données de grouping avec l'analyse qualitative
async function loadGroupingWithQualitative() {
    try {
        const { data } = await axios.get(`/mission/grouping_with_qualitative/${id_mission}`);
        if (data.response.ok) {
            // Mettre à jour les données de grouping
            props.grouping = data.response.grouping;
            groupingStats.value = data.response.statistics;
            console.log('Grouping avec analyse qualitative chargé:', data.response);
        }
    } catch (error) {
        console.error('Erreur lors du chargement du grouping:', error);
    }
}

// Charger les données au montage du composant
onMounted(() => {
    loadGroupingWithQualitative();
});

function handleQuestion(compte, indexRow, indexCol, checked) {
    const field = {
        "compte" : compte,
        "significant" : checked,
        // "indexRow" : indexRow,
        "question" : indexCol + 1
    }
    // listQuestions.value.push(field)
    uniqueValue(field)
}

function uniqueValue(group) {
    if (listQuestions.value.length === 0) {
        listQuestions.value.push(group)
    } else {
        // Vérifier si group existe déjà dans la liste
        const existingIndex = listQuestions.value.findIndex(item => item.compte === group.compte && item.question === group.question)

        if (existingIndex !== -1) {
            listQuestions.value[existingIndex] = group
        } else {
            listQuestions.value.push(group)
        }
    }
}

async function validate() {
    try {
        const field = {
            "listGrouping": listQuestions.value
        };
        
        const result = await axios.put(`/mission/qualitative_analysis/${id_mission}`, field);
        
        if (result.data.response.ok) {
            notyf.trigger('Analyse qualitative appliquée avec succès', 'success');
            // Recharger les données après l'application
            await loadGroupingWithQualitative();
        } else {
            notyf.trigger('Erreur lors de l\'application de l\'analyse qualitative', 'error');
        }
    } catch (error) {
        console.error('Erreur lors de l\'analyse qualitative:', error);
        notyf.trigger('Erreur lors de l\'analyse qualitative', 'error');
    }
}

// Fonction pour afficher une question au clic
function showQuestion(questionNumber, event) {
  selectedQuestion.value = `Q${questionNumber}`;
  selectedQuestionText.value = questions.value[questionNumber - 1];
  
  // Positionner le tooltip près du clic
  const rect = event.target.getBoundingClientRect();
  tooltipPosition.value = {
    x: rect.left + rect.width / 2,
    y: rect.bottom + 10
  };
  
  showQuestionTooltip.value = true;
}

// Fonction pour fermer le tooltip
function hideQuestionTooltip() {
  showQuestionTooltip.value = false;
  selectedQuestion.value = '';
  selectedQuestionText.value = '';
}

</script>

<template>
    <!-- Tableau grouping principal -->
    <div class="flex flex-col overflow-auto">
        <h3 class="pt-3 pb-1 pl-0 text-xl font-semibold uppercase tracking-wider">Questionnaire pour déterminer les comptes significatifs</h3>
        
        <!-- Statistiques de l'analyse qualitative -->
        <div v-if="groupingStats" class="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 class="text-lg font-semibold text-blue-800 mb-2">Résultats de l'analyse qualitative</h4>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-white p-3 rounded border">
                    <div class="text-xs text-gray-600">Total comptes</div>
                    <div class="text-lg font-bold text-blue-600">{{ groupingStats.total_accounts }}</div>
                </div>
                <div class="bg-white p-3 rounded border">
                    <div class="text-xs text-gray-600">Comptes significatifs</div>
                    <div class="text-lg font-bold text-red-600">{{ groupingStats.significant_accounts }}</div>
                </div>
                <div class="bg-white p-3 rounded border">
                    <div class="text-xs text-gray-600">Comptes non significatifs</div>
                    <div class="text-lg font-bold text-green-600">{{ groupingStats.non_significant_accounts }}</div>
                </div>
                <div class="bg-white p-3 rounded border">
                    <div class="text-xs text-gray-600">Pourcentage significatifs</div>
                    <div class="text-lg font-bold text-purple-600">{{ groupingStats.percentage_significant.toFixed(1) }}%</div>
                </div>
            </div>
        </div>
        <div class="overflow-hidden rounded-xl shadow-xl bg-white border border-gray-100">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-600">
                    <tr>
                        <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">#</th>
                        <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors" v-for="q, index in questions" :key="index" @click="showQuestion(index + 1, $event)" :title="'Cliquer pour voir la question complète'">{{ q }}</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="group, indexRow in props.grouping" :key="indexRow" class="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-300 group transform hover:scale-[1.01] hover:shadow-md" :class="group.significant ? 'bg-red-50' : 'bg-white'">
                        <td class="px-6 py-4 whitespace-nowrap text-center">
                            <div class="flex items-center justify-center space-x-2">
                                <div class="flex-shrink-0 h-8 w-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-200">
                                    <span class="text-xs font-bold text-white">{{ group.compte }}</span>
                                </div>
                                <span v-if="group.significant" class="inline-flex px-2 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-red-100 to-red-200 text-red-800 border border-red-300">
                                    <span class="w-2 h-2 rounded-full mr-1 bg-red-500"></span>
                                    SIGNIFICATIF
                                </span>
                            </div>
                        </td>
                        <td class="px-6 py-4 text-center" v-for="q, indexCol in questions" :key="indexCol">
                            <label :for="'check'+indexRow.toString()+indexCol.toString()" class="w-full h-12 flex items-center justify-center cursor-pointer">
                                <input :id="'check'+indexRow.toString()+indexCol.toString()" class="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 transform group-hover:scale-110 transition-all duration-200" type="checkbox" @change="(e) => handleQuestion(group.compte, indexRow, indexCol, e.target.checked)">
                            </label>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        <button class=" mt-2 mx-6 mb-2 py-2 bg-blue-ycube rounded-md text-base font-semibold text-white" @click="validate">Valider</button>
    </div>

    <!-- Tooltip pour afficher les questions -->
    <div 
      v-if="showQuestionTooltip" 
      class="fixed z-50 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-md"
      :style="{
        left: tooltipPosition.x + 'px',
        top: tooltipPosition.y + 'px',
        transform: 'translateX(-50%)'
      }"
      @click.stop
    >
      <div class="flex justify-between items-start mb-2">
        <h4 class="text-lg font-bold text-blue-800">{{ selectedQuestion }}</h4>
        <button 
          @click="hideQuestionTooltip"
          class="text-gray-500 hover:text-gray-700 text-xl font-bold ml-2"
        >
          ×
        </button>
      </div>
      <div class="bg-blue-50 border-l-4 border-blue-400 p-3 rounded">
        <p class="text-sm text-gray-700 leading-relaxed">{{ selectedQuestionText }}</p>
      </div>
    </div>

    <!-- Overlay pour fermer le tooltip en cliquant ailleurs -->
    <div 
      v-if="showQuestionTooltip" 
      class="fixed inset-0 z-40" 
      @click="hideQuestionTooltip"
    ></div>

</template>
