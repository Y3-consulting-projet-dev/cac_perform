<script setup>
// Paramètres communs à toutes les missions (page C) : CONSULTATION SEULE.
// Toutes les valeurs viennent du serveur (api/src/services/parametres_service.py),
// qui les lit là où le code les définit : aucune valeur recopiée ici.
// Sans authentification, rien n'est modifiable (CLAUDE.md, point de sécurité connu).
import { onMounted, ref } from 'vue'
import { lireParametres } from '@/api/parametres.api'

const parametres = ref(null)
const erreur = ref('')

onMounted(async () => {
  try {
    parametres.value = await lireParametres()
  } catch (e) {
    erreur.value = e.message
  }
})

const MENTION_LECTURE_SEULE = "Modification réservée aux administrateurs, disponible avec l'authentification"

// Catégories de source (parametres_service) : libellé et badge de la charte.
const SOURCES = {
  cahier_des_charges: { libelle: 'Cahier des charges', classe: 'bg-gray-100 text-gray-700' },
  spec_a_confirmer: { libelle: 'Spec à confirmer', classe: 'bg-orange-100 text-orange-700' },
  decision_provisoire: { libelle: 'Décision provisoire', classe: 'bg-orange-100 text-orange-700' },
}

function formaterMontant(valeur) {
  return valeur === null || valeur === undefined ? 'Non défini' : Number(valeur).toLocaleString('fr-FR')
}

// « Étapes 5 à 11 · Calcul des seuils, … » (étapes consécutives, comme la maquette) ou « Étapes 3, 4 · … ».
function groupeEtapes(etapes) {
  const numeros = etapes.map((e) => e.etape)
  const consecutives = numeros.every((n, i) => i === 0 || n === numeros[i - 1] + 1)
  const plage = numeros.length === 1 ? `Étape ${numeros[0]}`
    : numeros.length === 2 ? `Étapes ${numeros[0]} et ${numeros[1]}`
    : consecutives ? `Étapes ${numeros[0]} à ${numeros[numeros.length - 1]}` : `Étapes ${numeros.join(', ')}`
  return `${plage} · ${etapes.map((e) => e.libelle.toLowerCase()).join(', ')}`
}

const CHAMP = 'h-11 w-full text-[15px] px-3 border border-gray-300 rounded-[10px] bg-gray-50 text-gray-800 font-normal cursor-default focus:outline-none'
const CARTE = 'bg-white rounded-[14px] shadow px-[26px] py-[22px] flex flex-col gap-3.5'
const TITRE = 'm-0 text-base font-bold tracking-[0.3px] uppercase text-blue-ycube'
const LIBELLE = 'flex flex-col gap-1.5 text-sm font-semibold'
</script>

<template>
  <!-- Disposition de la maquette docs/maquettes/7_Parametres.html (sans « Droits par profil ») ;
       couleurs et police de la charte (CLAUDE.md, section charte d'interface). -->
  <div class="h-full w-full overflow-y-auto bg-[#f5f7fa] text-gray-800">
    <div class="p-7 flex flex-col gap-5">

      <!-- En-tête -->
      <section class="bg-white rounded-[14px] shadow px-7 py-6 flex flex-col gap-1.5 text-center items-center">
        <h1 class="m-0 text-[26px] font-bold text-blue-ycube">Paramètres</h1>
        <p class="m-0 text-gray-500">Réglages communs à toutes les missions · réservé aux administrateurs</p>
        <span class="mt-1 px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700">{{ MENTION_LECTURE_SEULE }}</span>
      </section>

      <p v-if="erreur" class="m-0 px-4 py-3 rounded-[10px] bg-red-100 text-red-700 text-sm">{{ erreur }}</p>

      <template v-if="parametres">
        <!-- État du verrou IPE -->
        <section class="bg-orange-100 rounded-[14px] px-6 py-[18px] flex items-center justify-between gap-4 flex-wrap">
          <div class="flex flex-col gap-1">
            <strong class="text-orange-700">Verrou IPE : {{ parametres.verrou.actif ? 'activé' : 'désactivé' }}</strong>
            <span class="text-sm text-orange-700">{{ parametres.verrou.source.reference }}.</span>
            <span class="text-[13px] text-orange-700">
              Variable d'environnement {{ parametres.verrou.variable }} · {{ SOURCES[parametres.verrou.source.categorie].libelle }}
            </span>
          </div>
          <button
            type="button"
            disabled
            :title="MENTION_LECTURE_SEULE"
            class="h-11 px-[18px] rounded-[10px] bg-orange-200 text-orange-700 text-[13px] font-bold opacity-70 cursor-not-allowed"
          >
            {{ parametres.verrou.actif ? 'Désactiver le verrou' : 'Activer le verrou' }}
          </button>
        </section>

        <div class="grid grid-cols-1 xl:grid-cols-2 gap-5">
          <!-- Rapprochements IPE -->
          <section :class="CARTE">
            <h2 :class="TITRE">Rapprochements IPE</h2>
            <div class="grid grid-cols-3 gap-2.5">
              <label v-for="r in parametres.rapprochements.racines" :key="r.libelle" :class="LIBELLE">{{ r.libelle }}
                <input :value="r.valeur" readonly :title="MENTION_LECTURE_SEULE" :class="CHAMP" />
              </label>
              <label :class="LIBELLE">{{ parametres.rapprochements.immobilisations.libelle }}
                <input :value="parametres.rapprochements.immobilisations.valeur" readonly :title="MENTION_LECTURE_SEULE" :class="CHAMP" />
              </label>
            </div>
            <div class="grid grid-cols-2 gap-2.5">
              <label v-for="s in parametres.rapprochements.seuils" :key="s.libelle" :class="LIBELLE">{{ s.libelle }}
                <input :value="s.applique ? formaterMontant(s.valeur) : 'Non appliqué'" readonly :title="MENTION_LECTURE_SEULE"
                       :class="[CHAMP, s.applique ? '' : 'text-gray-500 italic']" />
                <span class="text-xs font-normal text-gray-500">
                  Cahier des charges §2.4 : {{ formaterMontant(s.propose) }} {{ s.propose_unite }} par défaut · non appliqué
                </span>
              </label>
            </div>
            <p class="m-0 text-[13px] text-gray-500 flex flex-wrap items-center gap-2">
              <span :class="['px-3 py-1 rounded-full text-xs font-semibold', SOURCES[parametres.rapprochements.racines_source.categorie].classe]">
                {{ SOURCES[parametres.rapprochements.racines_source.categorie].libelle }}
              </span>
              Racines clients et fournisseurs : {{ parametres.rapprochements.racines_source.reference }}
            </p>
            <p class="m-0 text-[13px] text-gray-500 flex flex-wrap items-center gap-2">
              <span :class="['px-3 py-1 rounded-full text-xs font-semibold', SOURCES[parametres.rapprochements.immobilisations_source.categorie].classe]">
                {{ SOURCES[parametres.rapprochements.immobilisations_source.categorie].libelle }}
              </span>
              Immobilisations : {{ parametres.rapprochements.immobilisations.detail }} ·
              {{ parametres.rapprochements.immobilisations.exclusion }} · {{ parametres.rapprochements.immobilisations_source.reference }}
            </p>
            <p class="m-0 text-[13px] text-gray-500 flex flex-wrap items-center gap-2">
              <span :class="['px-3 py-1 rounded-full text-xs font-semibold', SOURCES[parametres.rapprochements.seuils_source.categorie].classe]">
                {{ SOURCES[parametres.rapprochements.seuils_source.categorie].libelle }}
              </span>
              {{ parametres.rapprochements.seuils_source.reference }}
            </p>
          </section>

          <!-- Causes d'écart -->
          <section :class="CARTE">
            <h2 :class="TITRE">Causes d'écart</h2>
            <ul class="list-none m-0 p-0 flex flex-wrap gap-2">
              <li v-for="c in parametres.causes_ecart.valeurs" :key="c"
                  class="px-3 py-2 rounded-full bg-blue-ycube/10 text-blue-ycube font-semibold text-sm">{{ c }}</li>
            </ul>
            <p class="m-0 text-[13px] text-gray-500 flex flex-wrap items-center gap-2">
              <span :class="['px-3 py-1 rounded-full text-xs font-semibold', SOURCES[parametres.causes_ecart.source.categorie].classe]">
                {{ SOURCES[parametres.causes_ecart.source.categorie].libelle }}
              </span>
              {{ parametres.causes_ecart.source.reference }}
            </p>
          </section>

          <!-- Circularisation -->
          <section :class="CARTE">
            <h2 :class="TITRE">Circularisation</h2>
            <div class="grid grid-cols-4 gap-2.5">
              <label v-for="c in parametres.circularisation.cadence" :key="c.libelle" :class="LIBELLE">{{ c.libelle }}
                <input :value="c.valeur" readonly :title="MENTION_LECTURE_SEULE" :class="CHAMP" />
              </label>
            </div>
            <p class="m-0 text-[13px] text-gray-500 flex flex-wrap items-center gap-2">
              <span :class="['px-3 py-1 rounded-full text-xs font-semibold', SOURCES[parametres.circularisation.source.categorie].classe]">
                {{ SOURCES[parametres.circularisation.source.categorie].libelle }}
              </span>
              {{ parametres.circularisation.source.reference }}
            </p>
          </section>

          <!-- Étapes bloquées par le verrou -->
          <section :class="CARTE">
            <h2 :class="TITRE">Étapes bloquées par le verrou</h2>
            <ul class="list-none m-0 p-0 flex flex-col gap-2 text-[15px]">
              <li class="flex items-start gap-2.5 text-gray-500">
                <input type="checkbox" disabled :title="MENTION_LECTURE_SEULE" class="mt-0.5 shrink-0 w-[18px] h-[18px]" />
                <span>{{ groupeEtapes(parametres.etapes_verrou.non_bloquees) }}</span>
              </li>
              <li class="flex items-start gap-2.5">
                <input type="checkbox" checked disabled :title="MENTION_LECTURE_SEULE" class="mt-0.5 shrink-0 w-[18px] h-[18px] accent-blue-ycube" />
                <span>{{ groupeEtapes(parametres.etapes_verrou.bloquees) }}</span>
              </li>
              <li class="flex items-center gap-2.5 text-gray-500">
                <input type="checkbox" disabled :title="MENTION_LECTURE_SEULE" class="w-[18px] h-[18px]" />
                Circularisation · sélection, courriers, suivi (modules à venir)
              </li>
            </ul>
            <p class="m-0 text-[13px] text-gray-500 flex flex-wrap items-center gap-2">
              <span :class="['px-3 py-1 rounded-full text-xs font-semibold', SOURCES[parametres.etapes_verrou.source.categorie].classe]">
                {{ SOURCES[parametres.etapes_verrou.source.categorie].libelle }}
              </span>
              {{ parametres.etapes_verrou.source.reference }}
            </p>
          </section>
        </div>
      </template>
    </div>
  </div>
</template>
