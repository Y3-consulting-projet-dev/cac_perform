<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  getUserProfile,
  updateUserProfile,
  changeUserPassword
} from '@/api/auth.api'

const auth = useAuthStore()

/* ===== USER ===== */
const user = computed(() => auth.user || {})

/* ===== PROFIL ===== */
const form = ref({
  firstname: '',
  lastname: '',
  email: '',
  role: '',
  grade: '',
  departement: ''
})

watch(
  () => auth.user,
  (newUser) => {
    if (newUser) {
      form.value = {
        firstname: newUser.firstname || '',
        lastname: newUser.lastname || '',
        email: newUser.email || '',
        role: newUser.role || '',
        grade: newUser.grade || '',
        departement: newUser.departement || ''
      }
    }
  },
  { immediate: true }
)

const loading = ref(false)
const success = ref('')
const error = ref('')

onMounted(async () => {
  try {
    const { data } = await getUserProfile()
    auth.updateUser(data)
  } catch (e) {
    console.error('Erreur chargement profil', e)
  }
})

async function saveProfile() {
  loading.value = true
  success.value = error.value = ''

  try {
    const { data } = await updateUserProfile(form.value)
    auth.updateUser(data)
    window.location.reload();
    success.value = 'Profil mis à jour avec succès'
  } catch (e) {
    console.error('UPDATE PROFILE ERROR:', e.response?.data || e)
    error.value =
      e.response?.data?.message ||
      JSON.stringify(e.response?.data) ||
      'Erreur lors de la mise à jour'
  } finally {
    loading.value = false
  }
}

/* ===== PASSWORD ===== */
const password = ref({
  old: '',
  new: '',
  confirm: ''
})

const passwordError = ref('')
const passwordSuccess = ref('')

async function updatePassword() {
  passwordError.value = passwordSuccess.value = ''

  if (password.value.new !== password.value.confirm) {
    passwordError.value = 'Les mots de passe ne correspondent pas'
    return
  }

  try {
    await changeUserPassword({
      current_password: password.value.old,
      new_password: password.value.new
    })

    passwordSuccess.value = 'Mot de passe modifié avec succès'
    password.value = { old: '', new: '', confirm: '' }
  } catch (e) {
    passwordError.value =
      e.response?.data?.message || 'Mot de passe incorrect'
  }
}
</script>

<template>
  <div class="flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-10">

    <!-- TITLE -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-800">Mon profil</h1>
      <p class="text-sm text-gray-500">
        Consultez et modifiez vos informations
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">

      <!-- PROFIL CARD -->
      <div class="bg-white rounded-xl shadow p-6 flex flex-col items-center text-center">
        <div class="w-24 h-24 rounded-full bg-green-ycube text-white text-3xl flex items-center justify-center mb-4">
          {{ user.firstname?.[0] }}{{ user.lastname?.[0] }}
        </div>

        <h2 class="text-lg font-semibold">
          {{ user.firstname }} {{ user.lastname }}
        </h2>
        <p class="text-sm text-gray-500">{{ user.role }} — {{ user.grade }}</p>

        <div class="mt-6 w-full text-left space-y-2 text-sm">
          <p><strong>Email :</strong> {{ user.email }}</p>
          <p><strong>Département :</strong> {{ user.departement }}</p>
        </div>
      </div>

      <!-- EDIT PROFILE -->
      <div class="lg:col-span-2 space-y-8">

        <!-- INFOS -->
        <div class="bg-white rounded-xl shadow p-6">
          <h3 class="text-lg font-semibold mb-4">Informations personnelles</h3>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="uppercase font-semibold text-[#022a41]">Prénom</label>
              <input v-model="form.firstname" placeholder="Prénom"
                class="w-full mt-2 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-ycube" />
            </div>
            <div>
              <label class="uppercase font-semibold text-[#022a41]">Nom</label>
              <input v-model="form.lastname" placeholder="Nom"
                class="w-full mt-2 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-ycube" />
            </div>
            <div>
              <label class="uppercase font-semibold text-[#022a41]">Email</label>
              <input v-model="form.email" placeholder="Email"
                class="w-full mt-2 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-ycube" />
            </div>
            <div>
              <label class="uppercase font-semibold text-[#022a41]">Rôle</label>
              <select v-model="form.role" placeholder="Rôle"
                class="w-full mt-2 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-ycube">
                <option disabled value="">Choisir</option>
                <option>Administrateur</option>
                <option>Manager</option>
                <option>Auditeur Senior</option>
                <option>Auditeur</option>
                <option>Stagiaire</option>
              </select>
            </div>
            <div>
              <label class="uppercase font-semibold text-[#022a41]">Grade</label>
              <select v-model="form.grade" placeholder="Grade"
                class="w-full mt-2 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-ycube">
                <option disabled value="">Choisir</option>
                <option>Junior</option>
                <option>Confirmé</option>
                <option>Senior</option>
                <option>Expert</option>
                <option>Directeur</option>
              </select>
            </div>
            <div>
              <label class="uppercase font-semibold text-[#022a41]">Département</label>
              <select v-model="form.departement" placeholder="Grade"
                class="w-full mt-2 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-ycube">
                <option disabled value="">Choisir</option>
                <option>Audit</option>
                <option>Conseil</option>
                <option>Expertise Comptable</option>
                <option>Juridique</option>
                <option>Administration</option>
              </select>
            </div>
          </div>

          <div class="mt-6 flex justify-end">
            <button @click="saveProfile" :disabled="loading"
              class="bg-green-ycube text-white px-6 py-2 rounded-lg font-semibold hover:bg-green-700 transition">
              {{ loading ? 'Enregistrement...' : 'Enregistrer' }}
            </button>
          </div>

          <p v-if="success" class="text-green-600 text-sm mt-3">
            {{ success }}
          </p>
          <p v-if="error" class="text-red-600 text-sm mt-3">
            {{ error }}
          </p>

        </div>

        <!-- PASSWORD -->
        <div class="bg-white rounded-xl shadow p-6">
          <h3 class="text-lg font-semibold mb-4">Sécurité</h3>

          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <input v-model="password.old" type="password" placeholder="Mot de passe actuel"
              class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-ycube" />
            <input v-model="password.new" type="password" placeholder="Nouveau mot de passe"
              class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-ycube" />
            <input v-model="password.confirm" type="password" placeholder="Confirmer"
              class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-ycube" />
          </div>

          <div class="mt-6 flex justify-end">
            <button @click="updatePassword"
              class="bg-blue-ycube text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 transition">
              Modifier le mot de passe
            </button>
          </div>

          <p v-if="passwordSuccess" class="text-green-600 text-sm mt-3">
            {{ passwordSuccess }}
          </p>
          <p v-if="passwordError" class="text-red-600 text-sm mt-3">
            {{ passwordError }}
          </p>

        </div>

      </div>
    </div>
  </div>
</template>
