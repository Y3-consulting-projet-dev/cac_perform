<script setup>
// Étape 3, Contrôle de cohérence — vue « Contrôle arithmétique ». AFFICHAGE
// seulement : la synthèse et les deux contrôles (équilibre, formule) viennent du rapport V1
// (/cors/mission/controle_coherence, api/src/model.py, inchangé) ; les pistes
// d'analyse (lignes de forme sous-total, comptes où ouverture + mouvements ≠
// solde final) et la liste des comptes viennent d'une lecture V2
// (GET /api/v1/missions/<id>/balance-generale/pistes-coherence), qui applique
// les règles du service de balance générale V2 sans rien modifier.
import { computed, ref, watch } from 'vue'
import { lirePistesCoherence } from '@/api/imports.api'
import { formatMontant, formatSens } from '@/utils/lectureFichierComplementaire'

const props = defineProps({ missionId: String, annee: String, rapport: Object })
const emit = defineEmits(['ouvrir-ecran'])

const pistesParAnnee = ref(null)
const erreurPistes = ref('')
const listeOuverte = ref(false)
const recherche = ref('')
const tri = ref({ cle: 'compte', sens: 1 })

watch(() => props.missionId, async (id) => {
  pistesParAnnee.value = null
  erreurPistes.value = ''
  if (!id) return
  try {
    pistesParAnnee.value = await lirePistesCoherence(id)
  } catch (e) {
    erreurPistes.value = e.message
  }
}, { immediate: true })

const pistes = computed(() => (pistesParAnnee.value || []).find((p) => p.annee === String(props.annee)) || null)
const debits = computed(() => Number(props.rapport?.total_debits ?? props.rapport?.verification_equilibre?.total_debits ?? 0))
const credits = computed(() => Number(props.rapport?.total_credits ?? props.rapport?.verification_equilibre?.total_credits ?? 0))
const ecart = computed(() => debits.value - credits.value)
const equilibree = computed(() => props.rapport?.equilibre_global === true)
const formule = computed(() => props.rapport?.verification_formule || null)

const phraseSynthese = computed(() => {
  if (equilibree.value) return `Balance équilibrée : ${formatMontant(debits.value)} FCFA au débit comme au crédit.`
  const montant = formatMontant(Math.abs(ecart.value))
  return `Balance déséquilibrée : ${montant} FCFA de ${ecart.value < 0 ? 'crédit' : 'débit'} en trop.`
})

// Les textes du rapport V1 portent des montants au format anglais (1,388,434,386) :
// réécrits au format français pour l'affichage, sans toucher au calcul.
const enFrancais = (texte) => String(texte || '').replace(/-?\d{1,3}(?:,\d{3})+(?:\.\d+)?/g, (m) => formatMontant(Number(m.replace(/,/g, ''))))
const montantDuMessage = (message, etiquette) => {
  const m = String(message || '').match(new RegExp(`${etiquette}\\s*:\\s*(-?[\\d,.]+)`))
  return m ? Number(m[1].replace(/,/g, '')) : null
}

// Comptes en erreur du second contrôle : erreurs « arithmetique » du rapport V1,
// lues dans leur message (model.py, inchangé).
const comptesFormuleEnErreur = computed(() => (props.rapport?.erreurs || [])
  .filter((e) => e.type === 'arithmetique')
  .map((e) => ({
    numero_compte: e.numero_compte,
    libelle: (String(e.message || '').match(/Libellé\s*:\s*(.*)/) || [])[1]?.trim() || '',
    attendu: montantDuMessage(e.message, 'Solde attendu'),
    reel: montantDuMessage(e.message, 'Solde réel'),
    ecart: montantDuMessage(e.message, 'ÉCART DÉTECTÉ'),
  })))

// Une fois les lignes de forme sous-total retirées (règle V2) : écart du solde final.
const ecartHorsSousTotaux = computed(() => pistes.value?.equilibre_hors_sous_totaux?.paires?.solde_final?.ecart ?? null)

// --- Liste complète : recherche et tri ------------------------------------------
const numerosSousTotaux = computed(() => new Set((pistes.value?.sous_totaux || []).map((s) => s.numero_compte)))
const net = (d, c) => (Number(d) || 0) - (Number(c) || 0)
const COLONNES = [
  { cle: 'compte', titre: 'Compte', valeur: (l) => l.numero_compte || '—', tri: (l) => l.numero_compte || '' },
  { cle: 'libelle', titre: 'Libellé', valeur: (l) => l.libelle || '—', tri: (l) => (l.libelle || '').toLowerCase(), large: true },
  { cle: 'ouverture', titre: "Solde d'ouverture", valeur: (l) => formatSens(l.debit_initial, l.credit_initial), tri: (l) => net(l.debit_initial, l.credit_initial), montant: true },
  { cle: 'mouvements', titre: 'Mouvements', valeur: (l) => formatSens(l.debit_mvt, l.credit_mvt), tri: (l) => net(l.debit_mvt, l.credit_mvt), montant: true,
    infobulle: (l) => `Débit ${formatMontant(l.debit_mvt)} — Crédit ${formatMontant(l.credit_mvt)}` },
  { cle: 'final', titre: 'Solde final', valeur: (l) => formatSens(l.debit_fin, l.credit_fin), tri: (l) => net(l.debit_fin, l.credit_fin), montant: true },
]
const lignesAffichees = computed(() => {
  const q = recherche.value.trim().toLowerCase()
  const colonne = COLONNES.find((c) => c.cle === tri.value.cle)
  return (pistes.value?.lignes || [])
    .filter((l) => !q || `${l.numero_compte} ${l.libelle}`.toLowerCase().includes(q))
    .slice()
    .sort((a, b) => {
      const va = colonne.tri(a), vb = colonne.tri(b)
      return (va < vb ? -1 : va > vb ? 1 : 0) * tri.value.sens
    })
})
function trier(cle) {
  tri.value = tri.value.cle === cle ? { cle, sens: -tri.value.sens } : { cle, sens: 1 }
}

const CARTE = 'bg-white rounded-xl shadow p-6 flex flex-col gap-4'
const TITRE = 'm-0 font-semibold text-sm uppercase text-blue-ycube'
</script>

<template>
  <div class="@container flex flex-col gap-5">
    <!-- 1. Synthèse en une phrase -->
    <p :class="['m-0 px-5 py-4 rounded-xl text-base font-semibold', equilibree ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700']">
      {{ phraseSynthese }}
    </p>

    <!-- 2. Premier contrôle arithmétique : vérification de l'équilibre (rapport V1) -->
    <section v-if="rapport?.verification_equilibre" :class="CARTE">
      <div class="flex items-center justify-between gap-3 flex-wrap">
        <h3 :class="TITRE">Premier contrôle arithmétique : vérification de l'équilibre</h3>
        <span :class="['px-3 py-1 rounded-full text-xs font-semibold', equilibree ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700']">
          {{ equilibree ? 'Équilibrée' : 'Déséquilibrée' }}
        </span>
      </div>
      <div class="grid grid-cols-1 @3xl:grid-cols-2 gap-3">
        <div class="border border-gray-200 rounded-lg px-4 py-3 flex flex-col gap-1">
          <span class="text-gray-500 text-sm">Total des débits</span>
          <span class="font-semibold text-gray-800 font-mono">{{ formatMontant(debits) }} FCFA</span>
        </div>
        <div class="border border-gray-200 rounded-lg px-4 py-3 flex flex-col gap-1">
          <span class="text-gray-500 text-sm">Total des crédits</span>
          <span class="font-semibold text-gray-800 font-mono">{{ formatMontant(credits) }} FCFA</span>
        </div>
        <div v-if="!equilibree" class="border border-red-300 bg-red-50 rounded-lg px-4 py-3 flex flex-col gap-1 @3xl:col-span-2">
          <span class="text-gray-500 text-sm">Écart détecté</span>
          <span class="font-semibold text-red-700 font-mono">{{ formatMontant(Math.abs(ecart)) }} FCFA de {{ ecart < 0 ? 'crédit' : 'débit' }} en trop</span>
        </div>
      </div>
      <p class="m-0 text-sm">
        <span class="text-gray-500">Nombre de comptes analysés :</span>
        <span class="ml-1 font-semibold text-gray-800">{{ rapport.verification_equilibre.nb_comptes_analyses }}</span>
      </p>
      <p v-if="rapport.verification_equilibre.explication"
         :class="['m-0 px-4 py-3 rounded-lg text-sm', equilibree ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700']">
        <strong>Explication :</strong> {{ enFrancais(rapport.verification_equilibre.explication) }}
      </p>
      <p class="m-0 px-4 py-3 rounded-lg text-sm bg-gray-100 text-gray-700">
        <strong>Comment vérifier manuellement :</strong> additionnez toutes les valeurs de la colonne « Débit fin » de tous
        les comptes, puis toutes les valeurs de la colonne « Crédit fin ». Les deux totaux doivent être identiques.
      </p>
    </section>

    <!-- 3. Second contrôle arithmétique : vérification de la formule (rapport V1) -->
    <section v-if="formule" :class="CARTE">
      <div class="flex items-center justify-between gap-3 flex-wrap">
        <h3 :class="TITRE">Second contrôle arithmétique : vérification de la formule</h3>
        <span :class="['px-3 py-1 rounded-full text-xs font-semibold', formule.nb_comptes_erreur > 0 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700']">
          {{ formule.nb_comptes_erreur > 0 ? 'Formule non respectée' : 'Formule respectée' }}
        </span>
      </div>
      <p class="m-0 text-sm text-gray-700"><strong>Formule vérifiée :</strong> solde de clôture = solde d'ouverture + mouvements de la période.</p>
      <p v-if="formule.explication" class="m-0 text-sm text-gray-500">{{ enFrancais(formule.explication) }}</p>
      <div class="grid grid-cols-1 @3xl:grid-cols-3 gap-3">
        <div class="border border-gray-200 rounded-lg px-4 py-3 flex flex-col gap-1">
          <span class="text-gray-500 text-sm">Comptes vérifiés</span>
          <span class="font-semibold text-gray-800">{{ formule.nb_comptes_verifies }}</span>
        </div>
        <div class="border border-gray-200 rounded-lg px-4 py-3 flex flex-col gap-1">
          <span class="text-gray-500 text-sm">Formule respectée</span>
          <span class="font-semibold text-green-700">{{ formule.nb_comptes_ok }}</span>
        </div>
        <div :class="['border rounded-lg px-4 py-3 flex flex-col gap-1', formule.nb_comptes_erreur > 0 ? 'border-red-300 bg-red-50' : 'border-gray-200']">
          <span class="text-gray-500 text-sm">Formule non respectée</span>
          <span :class="['font-semibold', formule.nb_comptes_erreur > 0 ? 'text-red-700' : 'text-gray-800']">{{ formule.nb_comptes_erreur }}</span>
        </div>
      </div>
      <template v-if="comptesFormuleEnErreur.length">
        <p class="m-0 text-sm text-gray-500">Comptes en erreur : écart entre le solde de clôture attendu et le solde réel.</p>
        <table class="min-w-full text-sm">
          <thead class="bg-blue-ycube text-white h-12 text-left">
            <tr>
              <th class="px-3">Compte</th>
              <th class="px-3">Libellé</th>
              <th class="px-3 text-right">Solde attendu</th>
              <th class="px-3 text-right">Solde réel</th>
              <th class="px-3 text-right">Écart</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="e in comptesFormuleEnErreur" :key="e.numero_compte" class="h-12 border-b hover:bg-gray-50">
              <td class="px-3 font-mono">{{ e.numero_compte }}</td>
              <td class="px-3">{{ e.libelle || '—' }}</td>
              <td class="px-3 text-right font-mono whitespace-nowrap">{{ e.attendu === null ? '—' : formatSens(Math.max(e.attendu, 0), Math.max(-e.attendu, 0)) }}</td>
              <td class="px-3 text-right font-mono whitespace-nowrap">{{ e.reel === null ? '—' : formatSens(Math.max(e.reel, 0), Math.max(-e.reel, 0)) }}</td>
              <td class="px-3 text-right font-mono whitespace-nowrap font-semibold text-red-700">{{ e.ecart === null ? '—' : formatMontant(e.ecart) }}</td>
            </tr>
          </tbody>
        </table>
        <span class="text-xs text-gray-500">D = solde débiteur, C = solde créditeur. Écart en valeur absolue (FCFA).</span>
      </template>
    </section>

    <!-- 4. Sous-totaux détectés : la balance fausse le contrôle -->
    <p v-if="pistes?.sous_totaux?.length" class="m-0 px-5 py-4 rounded-xl bg-orange-100 text-orange-700 text-sm">
      Cette balance contient des lignes de sous-total qui faussent le contrôle. Remplacez-la par l'import V2
      depuis Fichiers complémentaires.
      <button type="button" class="font-semibold underline" @click="emit('ouvrir-ecran', 'fichiers_complementaires')">
        Ouvrir Fichiers complémentaires
      </button>
    </p>

    <!-- Pistes d'analyse : lignes de forme sous-total (règle de l'import V2) -->
    <section :class="CARTE">
      <h3 :class="TITRE">Pistes d'analyse</h3>
      <p v-if="erreurPistes" class="m-0 px-4 py-3 rounded-lg bg-red-100 text-red-700 text-sm">{{ erreurPistes }}</p>
      <p v-else-if="!pistes" class="m-0 text-sm text-gray-500">Chargement…</p>
      <div v-else class="flex flex-col gap-2">
        <div class="flex items-center gap-2 flex-wrap">
          <strong class="text-sm text-gray-800">Lignes qui ressemblent à des sous-totaux</strong>
          <span :class="['px-3 py-1 rounded-full text-xs font-semibold', pistes.sous_totaux.length ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-700']">
            {{ pistes.sous_totaux.length }}
          </span>
        </div>
        <p class="m-0 text-xs text-gray-500">
          Numéro préfixe d'autres comptes de la balance et montants égaux à leur somme (règle de l'import V2) :
          ces lignes sont comptées deux fois dans les totaux.
          <template v-if="pistes.sous_totaux.length && ecartHorsSousTotaux !== null">
            Sans elles, l'écart du solde final serait de {{ formatMontant(Math.abs(ecartHorsSousTotaux)) }} FCFA.
          </template>
        </p>
        <table v-if="pistes.sous_totaux.length" class="min-w-full text-sm">
          <thead class="bg-blue-ycube text-white h-10 text-left">
            <tr><th class="px-3">Compte</th><th class="px-3">Libellé</th><th class="px-3 text-right">Comptes résumés</th></tr>
          </thead>
          <tbody>
            <tr v-for="s in pistes.sous_totaux" :key="s.numero_compte" class="h-10 border-b hover:bg-gray-50">
              <td class="px-3 font-mono">{{ s.numero_compte }}</td>
              <td class="px-3">{{ s.libelle || '—' }}</td>
              <td class="px-3 text-right">{{ s.nb_comptes_detail }}</td>
            </tr>
          </tbody>
        </table>
        <p v-if="pistes.ambigus.length" class="m-0 text-xs text-orange-700">
          {{ pistes.ambigus.length }} autre(s) ligne(s) ont la forme d'un sous-total sans correspondre à leurs comptes :
          {{ pistes.ambigus.map((a) => a.numero_compte).join(', ') }}.
        </p>
      </div>
    </section>

    <!-- 5. Liste complète, repliée -->
    <section v-if="pistes" :class="CARTE">
      <button type="button" class="self-start font-semibold text-blue-ycube flex items-center gap-2 hover:underline" :aria-expanded="listeOuverte"
              @click="listeOuverte = !listeOuverte">
        <i :class="['fa-solid', listeOuverte ? 'fa-chevron-up' : 'fa-chevron-down']" aria-hidden="true"></i>
        {{ listeOuverte ? 'Masquer les comptes' : 'Afficher tous les comptes' }} ({{ pistes.nb_lignes }})
      </button>
      <template v-if="listeOuverte">
        <input v-model="recherche" type="search" aria-label="Rechercher un compte" placeholder="Rechercher un compte (numéro ou libellé)"
               class="h-10 px-3 text-sm border border-gray-300 rounded-lg w-full max-w-md focus:outline-none focus:ring-2 focus:ring-blue-ycube" />
        <div class="max-h-96 overflow-y-auto border rounded-lg">
          <table class="w-full text-xs">
            <thead class="bg-blue-ycube text-white text-left sticky top-0">
              <tr class="h-10">
                <th v-for="col in COLONNES" :key="col.cle" class="px-2" :class="col.montant ? 'text-right whitespace-nowrap' : ''"
                    :aria-sort="tri.cle === col.cle ? (tri.sens > 0 ? 'ascending' : 'descending') : 'none'">
                  <button type="button" class="font-semibold inline-flex items-center gap-1 hover:underline" @click="trier(col.cle)">
                    {{ col.titre }}
                    <i v-if="tri.cle === col.cle" :class="['fa-solid text-[10px]', tri.sens > 0 ? 'fa-arrow-up' : 'fa-arrow-down']" aria-hidden="true"></i>
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(ligne, i) in lignesAffichees" :key="i" class="border-b hover:bg-gray-50"
                  :class="numerosSousTotaux.has(ligne.numero_compte) ? 'bg-orange-50' : ''">
                <td v-for="col in COLONNES" :key="col.cle" class="px-2 py-1.5"
                    :class="col.montant ? 'text-right font-mono whitespace-nowrap' : (col.large ? 'break-words' : 'whitespace-nowrap')"
                    :title="col.infobulle ? col.infobulle(ligne) : null">
                  {{ col.valeur(ligne) }}
                  <span v-if="col.cle === 'libelle' && numerosSousTotaux.has(ligne.numero_compte)"
                        class="ml-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-orange-100 text-orange-700">sous-total</span>
                </td>
              </tr>
              <tr v-if="!lignesAffichees.length"><td :colspan="COLONNES.length" class="px-2 py-3 text-center text-gray-500">Aucun compte ne correspond.</td></tr>
            </tbody>
          </table>
        </div>
        <span class="text-xs text-gray-500">D = solde débiteur, C = solde créditeur.</span>
      </template>
    </section>
  </div>
</template>
