<script setup>
// Fenêtre centrée commune aux écrans V2 (« Commenter » de Fiabilité IPE, mémo
// de sélection…) : modale de la charte (ClientsView), en-tête titre +
// sous-titre + croix. Fermeture par la croix, la touche Échap ou un clic à
// l'extérieur ; à l'ouverture, le focus va au premier champ ou bouton du
// contenu (sinon à la fenêtre elle-même) et revient ensuite à l'élément qui
// l'avait ouverte.
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  titre: { type: String, default: '' },
  sousTitre: { type: String, default: '' },
  libelleFermer: { type: String, default: 'Fermer' },
  largeur: { type: String, default: 'max-w-3xl' },
})
const emit = defineEmits(['fermer'])

const panneau = ref(null)
const contenu = ref(null)
let focusPrecedent = null

function surTouche(e) {
  if (e.key === 'Escape') {
    e.stopPropagation()
    emit('fermer')
  }
}

onMounted(async () => {
  focusPrecedent = document.activeElement
  document.addEventListener('keydown', surTouche)
  await nextTick()
  const premier = contenu.value?.querySelector(
    'textarea:not([disabled]), input:not([disabled]), select:not([disabled]), button:not([disabled]), a[href]')
  ;(premier || panneau.value)?.focus()
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', surTouche)
  if (focusPrecedent && typeof focusPrecedent.focus === 'function') focusPrecedent.focus()
})
</script>

<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="emit('fermer')">
    <section
      ref="panneau"
      role="dialog"
      aria-modal="true"
      :aria-label="props.titre || undefined"
      tabindex="-1"
      :class="['bg-white rounded-2xl w-full p-6 relative max-h-[90vh] overflow-auto flex flex-col gap-4 focus:outline-none', props.largeur]"
    >
      <div class="flex justify-between items-start gap-3">
        <div class="flex flex-col gap-1">
          <h2 class="m-0 text-lg font-bold text-blue-ycube"><slot name="titre">{{ props.titre }}</slot></h2>
          <span v-if="props.sousTitre || $slots['sous-titre']" class="text-sm text-gray-500">
            <slot name="sous-titre">{{ props.sousTitre }}</slot>
          </span>
        </div>
        <button
          type="button"
          class="w-11 h-11 shrink-0 rounded-[10px] bg-[#f5f7fa] text-blue-ycube hover:bg-gray-100 transition flex items-center justify-center"
          :aria-label="props.libelleFermer"
          @click="emit('fermer')"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg>
        </button>
      </div>
      <div ref="contenu" class="flex flex-col gap-4">
        <slot />
      </div>
    </section>
  </div>
</template>
