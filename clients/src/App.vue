<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import router from '@/router'
import pageLayout from './Layouts/pageLayout.vue'

const hasToken = computed(() => typeof sessionStorage !== 'undefined' && !!sessionStorage.getItem('token'))
const isPageLoading = ref(false)

function logout() {
  sessionStorage.removeItem('token')
  router.push('/connexion')
}

const startLoading = () => { isPageLoading.value = true }
const stopLoading = () => { isPageLoading.value = false }

const removeBefore = router.beforeEach((to, from, next) => {
  startLoading()
  next()
})
const removeAfter = router.afterEach(() => {
  stopLoading()
})
const removeError = router.onError(() => {
  stopLoading()
})

onBeforeUnmount(() => {
  removeBefore()
  removeAfter()
  removeError()
})
</script>

<template>
  <pageLayout>
    <router-view />
    <div
      v-if="isPageLoading"
      class="fixed inset-0 z-9999 flex items-center justify-center bg-black/20"
    >
      <div class="flex items-center gap-3 rounded-xl bg-white px-6 py-4 shadow-lg">
        <span class="h-5 w-5 animate-spin rounded-full border-2 border-green-ycube-2 border-t-transparent"></span>
        <span class="text-sm font-semibold text-[#022a41]">Chargement...</span>
      </div>
    </div>
  </pageLayout>
</template>
