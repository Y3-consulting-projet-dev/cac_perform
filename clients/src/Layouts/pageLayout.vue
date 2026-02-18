<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Header from '@/components/Header.vue'

const route = useRoute()

// Affiche le Header si la route définit `meta.showHeader === true`
// Sinon, par défaut on affiche le header sur la page 'home'.
const showHeader = computed(() => {
  if (route.meta?.showHeader !== undefined) {
    return route.meta.showHeader
  }
  return true
})
</script>

<template>
  <div class="h-screen flex flex-col bg-[#f5f7fa]">
    
    <!-- HEADER FIXE -->
    <Header v-if="showHeader" class="shrink-0" />

    <!-- ZONE APP -->
    <div class="flex flex-1 overflow-hidden">
      <slot />
    </div>

  </div>
</template>
