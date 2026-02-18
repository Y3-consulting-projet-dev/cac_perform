<script setup>
import { computed } from 'vue'
import router from '@/router'
import pageLayout from './Layouts/pageLayout.vue'

const hasToken = computed(() => typeof sessionStorage !== 'undefined' && !!sessionStorage.getItem('token'))

function logout() {
  sessionStorage.removeItem('token')
  router.push('/connexion')
}
</script>

<template>
  <pageLayout>
    <router-view />
  </pageLayout>
</template>
