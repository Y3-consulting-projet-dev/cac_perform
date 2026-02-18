<template>
  <div class="w-screen h-screen bg-gradient-to-r from-blue-ycube to-green-ycube flex">

    <!-- COLONNE GAUCHE -->
    <div class="w-1/2 flex flex-col justify-center items-center text-white px-10">
      <img src="/src/assets/logo.png" alt="" class="w-40 mb-6">
      <h1 class="text-3xl font-bold">Bienvenue sur Outil CAC PREFORM</h1>
      <img src="/src/assets/logo5.png" alt="" class="w-80 my-8">
      <h3 class="text-xl tracking-wide text-center">
        Accordez à votre espace de travail en un clic
      </h3>
    </div>

    <!-- COLONNE DROITE -->
    <main class="w-1/2 flex flex-col justify-center items-center bg-white rounded-l-3xl px-10">
      <h1 class="uppercase font-bold tracking-widest text-3xl text-green-ycube-2 mb-8">
        Connexion
      </h1>

      <div class="flex flex-col space-y-6 w-full max-w-md">
        <div class="flex flex-col space-y-2">
          <label class="uppercase font-semibold text-[#022a41]">Email</label>
          <input
            type="text"
            v-model="email"
            placeholder="Saisir l'email..."
            class="p-3 w-full border-2 border-[#022a41] rounded-xl bg-transparent text-[#022a41] placeholder:italic focus:outline-none"
          />
        </div>

        <div class="flex flex-col space-y-2">
          <label class="uppercase font-semibold text-[#022a41]">Mot de passe</label>
          <div class="relative">
            <input
              :type="showPassword ? 'text' : 'password'"
              v-model="password"
              placeholder="........"
              class="p-3 w-full border-2 border-[#022a41] rounded-xl bg-transparent text-[#022a41] placeholder:font-bold placeholder:text-2xl focus:outline-none pr-20"
            />
            <button
              type="button"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-sm font-semibold text-[#022a41] hover:opacity-80"
              @click="showPassword = !showPassword"
            >
              <FontAwesomeIcon v-if="showPassword" :icon="['fas', 'eye-slash']" class="text-[#01986b]" />
              <FontAwesomeIcon v-else :icon="['fas', 'eye']" class="text-[#01986b]" />
            </button>
          </div>
        </div>
      </div>

      <p v-if="errorMessage" class="mt-4 text-sm text-red-500">
        {{ errorMessage }}
      </p>

      <button
        @click="login"
        :disabled="isLoading"
        class="mt-10 px-10 py-3 bg-green-ycube-2 rounded-full uppercase text-white font-bold hover:bg-green-ycube active:bg-green-ycube-2 disabled:opacity-60 disabled:cursor-not-allowed inline-flex items-center gap-2"
      >
        <span v-if="isLoading" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
        <span>{{ isLoading ? 'Connexion...' : 'Se connecter' }}</span>
      </button>

      <p class="mt-6 text-sm text-gray-600">
        Pas encore de compte ?
        <span @click="router.push('/inscription')" class="text-blue-ycube cursor-pointer font-semibold">
          S'inscrire
        </span>
      </p>
    </main>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useNotyf } from '@/composables/useNotyf'
import router from '@/router'
import { login as loginApi } from '@/api/auth.api'

const notyf = useNotyf()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const errorMessage = ref('')
const isLoading = ref(false)

async function login() {
  try {
    errorMessage.value = ''
    if (isLoading.value) return

    if (!email.value || !password.value) {
      errorMessage.value = "Veuillez renseigner l'email et le mot de passe"
      notyf.trigger(errorMessage.value, "warning")
      return
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailPattern.test(email.value)) {
      errorMessage.value = "Format d'email invalide."
      notyf.trigger(errorMessage.value, "warning")
      return
    }

    const payload = {
      email: email.value,
      password: password.value,
    }

    isLoading.value = true
    const user = await loginApi(payload)

    if (user) {
      notyf.trigger("Connexion rÃ©ussie", "success")
      router.push('/')
    } else {
      errorMessage.value = "Identifiants invalides"
      notyf.trigger(errorMessage.value, "error")
    }
  } catch (e) {
    console.error(e)
    const apiMessage = e?.response?.data?.message || e?.message
    errorMessage.value = apiMessage || "Identifiants invalides"
    notyf.trigger(errorMessage.value, "error")
  } finally {
    isLoading.value = false
  }
}
</script>
