<template>
  <div class="w-screen h-screen bg-gradient-to-r from-blue-ycube to-green-ycube flex">

    <!-- COLONNE GAUCHE -->
    <div class="w-1/2 flex flex-col justify-center items-center text-white px-10">
      <img src="/src/assets/logo.png" alt="" class="w-40 mb-6">
      <h1 class="text-3xl font-bold">Bienvenue sur Outil CAC PREFORM</h1>
      <img src="/src/assets/logo5.png" alt="" class="w-80 my-8">
      <h3 class="text-xl tracking-wide text-center">
        Accédez à votre espace de travail en un clic
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
          <input
            type="password"
            v-model="password"
            placeholder="Saisir le mot de passe..."
            class="p-3 w-full border-2 border-[#022a41] rounded-xl bg-transparent text-[#022a41] placeholder:italic focus:outline-none"
          />
        </div>
      </div>

      <button
        @click="login"
        class="mt-10 px-10 py-3 bg-green-ycube-2 rounded-full uppercase text-white font-bold hover:bg-green-ycube active:bg-green-ycube-2"
      >
        Se connecter
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

async function login() {
  try {
    if (!email.value || !password.value) {
      notyf.trigger("Veuillez renseigner l'email et le mot de passe", "warning")
      return
    }

    const payload = {
      email: email.value,
      password: password.value,
    }

    const user = await loginApi(payload)

    if (user) {
      notyf.trigger("Connexion réussie", "success")
      router.push('/')
    } else {
      notyf.trigger("Identifiants invalides", "error")
    }
  } catch (e) {
    console.error(e)
    notyf.trigger("Identifiants invalides", "error")
  }
}
</script>
