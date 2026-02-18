<template>
  <div class="w-screen min-h-screen bg-gradient-to-r from-blue-ycube to-green-ycube flex">

    <!-- COLONNE GAUCHE -->
    <div class="w-[45%] min-w-[240px] flex flex-col justify-center items-center text-white px-6 py-10">
      <img src="/src/assets/logo.png" alt="" class="w-40 mb-6">
      <h1 class="text-3xl font-bold text-center">
        Rejoignez CAC PERFORM
      </h1>
      <img src="/src/assets/logo5.png" alt="" class="w-80 my-8">
      <h3 class="text-xl tracking-wide text-center">
        Créez votre compte en quelques secondes
      </h3>
    </div>

    <!-- COLONNE DROITE -->
    <main class="w-[55%] min-w-[300px] flex flex-col justify-start items-center bg-white rounded-l-3xl px-6 py-10 overflow-y-auto">
      <h1 class="uppercase font-bold tracking-widest text-3xl text-green-ycube-2 mb-8">
        Inscription
      </h1>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-2xl">

        <!-- Prénom -->
        <div>
          <label class="uppercase font-semibold text-[#022a41]">Prénom</label>
          <input v-model="form.firstname" type="text" placeholder="Verane"
            class="p-3 w-full border-2 border-[#022a41] rounded-xl bg-transparent
         text-[#022a41] focus:outline-none placeholder:italic" />
        </div>

        <!-- Nom -->
        <div>
          <label class="uppercase font-semibold text-[#022a41]">Nom</label>
          <input v-model="form.lastname" type="text" placeholder="N'Gouan"
            class="p-3 w-full border-2 border-[#022a41] rounded-xl bg-transparent
         text-[#022a41] focus:outline-none placeholder:italic" />
        </div>

        <!-- Email -->
        <div class="md:col-span-2">
          <label class="uppercase font-semibold text-[#022a41]">Email</label>
          <input v-model="form.email" type="email" placeholder="verane@ycube.ci"
            class="p-3 w-full border-2 border-[#022a41] rounded-xl bg-transparent
         text-[#022a41] focus:outline-none placeholder:italic" />
        </div>

        <!-- Mot de passe -->
        <div>
          <label class="uppercase font-semibold text-[#022a41]">Mot de passe</label>
          <input v-model="form.password" type="password" placeholder="........" class="p-3 w-full border-2 border-[#022a41] rounded-xl bg-transparent
         text-[#022a41] focus:outline-none placeholder:font-bold placeholder:text-2xl" />
        </div>

        <!-- Confirmation -->
        <div>
          <label class="uppercase font-semibold text-[#022a41]">Confirmation</label>
          <input v-model="confirmPassword" type="password" placeholder="........" class="p-3 w-full border-2 border-[#022a41] rounded-xl bg-transparent
         text-[#022a41] focus:outline-none placeholder:font-bold placeholder:text-2xl" />
        </div>

        <!-- Département -->
        <div>
          <label class="uppercase font-semibold text-[#022a41]">Département</label>
          <select v-model="form.departement" class="p-3 w-full border-2 border-[#022a41] rounded-xl bg-transparent
         text-[#022a41] focus:outline-none">
            <option disabled value="">Choisir</option>
            <option>Audit</option>
            <option>Conseil</option>
            <option>Expertise Comptable</option>
            <option>Juridique</option>
            <option>Administration</option>
          </select>
        </div>

        <!-- Rôle -->
        <div>
          <label class="uppercase font-semibold text-[#022a41]">Rôle</label>
          <select v-model="form.role" class="p-3 w-full border-2 border-[#022a41] rounded-xl bg-transparent
         text-[#022a41] focus:outline-none">
            <option disabled value="">Choisir</option>
            <option>Administrateur</option>
            <option>Manager</option>
            <option>Auditeur Senior</option>
            <option>Auditeur</option>
            <option>Stagiaire</option>
          </select>
        </div>

        <!-- Grade -->
        <div class="md:col-span-2">
          <label class="uppercase font-semibold text-[#022a41]">Grade</label>
          <select v-model="form.grade" class="p-3 w-full border-2 border-[#022a41] rounded-xl bg-transparent
         text-[#022a41] focus:outline-none">
            <option disabled value="">Choisir</option>
            <option>Junior</option>
            <option>Confirmé</option>
            <option>Senior</option>
            <option>Expert</option>
            <option>Directeur</option>
          </select>
        </div>
      </div>

      <!-- ERREUR -->
      <p v-if="errorMessage" class="text-red-500 mt-4 text-sm">
        {{ errorMessage }}
      </p>

      <!-- BOUTON -->
      <button
        @click="register"
        class="mt-8 px-10 py-3 bg-green-ycube-2 rounded-full uppercase text-white font-bold hover:bg-green-ycube active:bg-green-ycube-2"
      >
        Créer un compte
      </button>

      <!-- Lien -->
      <p class="mt-6 text-sm text-gray-600">
        Déjà un compte ?
        <span @click="router.push('/connexion')" class="text-blue-ycube cursor-pointer font-semibold">
          Se connecter
        </span>
      </p>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import router from '@/router'
import { useNotyf } from '@/composables/useNotyf'
import { register as registerApi } from '@/api/auth.api'

const notyf = useNotyf()

const form = ref({
  email: '',
  password: '',
  firstname: '',
  lastname: '',
  departement: '',
  role: '',
  grade: '',
})

const confirmPassword = ref('')
const errorMessage = ref('')

async function register() {
  errorMessage.value = ''

  if (!Object.values(form.value).every(Boolean)) {
    errorMessage.value = 'Veuillez remplir tous les champs'
    return
  }

  if (form.value.password !== confirmPassword.value) {
    errorMessage.value = 'Les mots de passe ne correspondent pas'
    return
  }

  try {
    await registerApi(form.value)
    notyf.trigger('Compte créé avec succès', 'success')
    router.push('/connexion')
  } catch (e) {
    errorMessage.value = 'Erreur lors de la création du compte'
  }
}
</script>
