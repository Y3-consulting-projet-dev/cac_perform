<script setup>
import { ref, h, onMounted, watch } from 'vue';
import ActifComponent from './ActifComponent.vue';
import PassifComponent from './PassifComponent.vue';
import PnlComponent from './PnlComponent.vue';
const props = defineProps(['data'])
const selectedValue = ref('')
const componentKey = ref('')
const renderComponent = ref()

function hasEfiValue(row) {
    if (!row || typeof row !== 'object') return false
    const fields = [
        'brut_solde_n',
        'amor_solde_n',
        'net_solde_n',
        'net_solde_n1',
        'solde_n',
        'solde_n1'
    ]
    return fields.some((key) => {
        const val = row[key]
        if (val === null || val === undefined || val === '') return false
        const num = Number(val)
        return !Number.isNaN(num) && num !== 0
    })
}

function filterEfiRows(rows) {
    if (!Array.isArray(rows)) return []
    return rows.filter(hasEfiValue)
}

function showComp(type) {
    let vnode;
    selectedValue.value = type

    // Vérifier que les données existent
    if (!props.data || !props.data.efi) {
        console.warn('⚠️ Données EFI non disponibles');
        renderComponent.value = null;
        componentKey.value = type;
        return;
    }

    if (type === 'actif') {
        const subProps = {
            efiActif: filterEfiRows(props.data?.efi?.actif),
            annee_auditee: props.data?.annee_auditee
        }
        console.log('📊 EfiComponent - Passage à ActifComponent:', subProps);
        console.log('  - efiActif longueur:', subProps.efiActif?.length);
        vnode = h(ActifComponent, subProps)
    } else if (type === 'passif') {
        const subProps = {
            efiPassif: filterEfiRows(props.data?.efi?.passif),
            annee_auditee: props.data.annee_auditee
        }
        console.log('📊 EfiComponent - Passage à PassifComponent:', subProps);
        console.log('  - efiPassif longueur:', subProps.efiPassif?.length);
        if (subProps.efiPassif && subProps.efiPassif.length > 0) {
            console.log('  - Refs passif:', subProps.efiPassif.map(x => x.ref));
        }
        vnode = h(PassifComponent, subProps)
    } else if (type === 'pnl') {
        const subProps = {
            efiPnl: filterEfiRows(props.data?.efi?.pnl),
            annee_auditee: props.data.annee_auditee
        }
        vnode = h(PnlComponent, subProps)
    }
    renderComponent.value = vnode;
    componentKey.value = type;
}

onMounted(()=>{
    console.log('📊 EfiComponent - Données reçues:', props.data)
    // Afficher 'actif' par défaut
    if (props.data && props.data.efi) {
        showComp('actif');
    }
})

// Réagir aux changements de données
watch(() => props.data, (newData) => {
    if (newData && newData.efi && selectedValue.value) {
        showComp(selectedValue.value);
    }
}, { deep: true })
</script>

<template>
    <div class="h-full w-full flex flex-col space-y-2 overflow-auto">
        <div class="min-h-10 flex space-x-3 px-4 pt-2 items-center">
            <button class="w-[250px] h-8 bg-blue-ycube text-white rounded-md shadow-md" :class="{'bg-green-ycube transition-all ease-in-out duration-300': selectedValue === 'actif'}" @click="showComp('actif')">Actifs</button>
            <button class="w-[250px] h-8 bg-blue-ycube text-white rounded-md shadow-md" :class="{'bg-green-ycube transition-all ease-in-out duration-300': selectedValue === 'passif'}" @click="showComp('passif')">Passifs</button>
            <button class="w-[250px] h-8 bg-blue-ycube text-white rounded-md shadow-md" :class="{'bg-green-ycube transition-all ease-in-out duration-300': selectedValue === 'pnl'}" @click="showComp('pnl')">Compte de résultat</button>
        </div>

        <!--  -->
        <div class="flex-auto flex flex-col overflow-visible">
            <div class="w-full flex flex-col overflow-visible">
                <component v-if="renderComponent" :is="renderComponent" :key="componentKey" />
                <div v-else class="flex items-center justify-center h-full">
                    <div class="text-center text-gray-500">
                        <p class="text-lg mb-2">Chargement des états financiers...</p>
                        <p v-if="!props.data || !props.data.efi" class="text-sm">Aucune donnée disponible</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
