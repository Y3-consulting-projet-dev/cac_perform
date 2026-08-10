<script setup>
import { ref } from 'vue'
import router from '@/router'

const mobileMenuOpen = ref(false)

const features = [
  {
    icon: 'fa-users',
    title: 'Gestion des clients',
    description: "Créez et centralisez vos dossiers clients pour retrouver en un clic l'historique complet de chaque mandat."
  },
  {
    icon: 'fa-clipboard-check',
    title: 'Missions d’audit',
    description: 'Initialisez vos missions de commissariat aux comptes et suivez leur avancement de bout en bout.'
  },
  {
    icon: 'fa-file-import',
    title: 'Import des balances N / N-1',
    description: "Importez directement vos balances comptables et laissez l'outil préparer l'analyse."
  },
  {
    icon: 'fa-layer-group',
    title: 'Groupings automatisés',
    description: 'Réalisez vos regroupements de comptes (actif, passif, résultat) sans ressaisie manuelle.'
  },
  {
    icon: 'fa-file-invoice',
    title: 'États financiers provisoires',
    description: 'Générez automatiquement vos états financiers provisoires prêts à être revus.'
  },
  {
    icon: 'fa-chart-line',
    title: 'Analyse des variations',
    description: 'Visualisez instantanément les variations entre exercices et repérez les écarts significatifs.'
  },
  {
    icon: 'fa-bullseye',
    title: 'Comptes significatifs',
    description: "Identifiez automatiquement les comptes significatifs à prioriser dans votre programme de travail.",
  },
  {
    icon: 'fa-route',
    title: 'Pistes d’audit',
    description: 'Obtenez des pistes d’audit générées automatiquement pour orienter vos diligences.'
  },
]

const steps = [
  {
    number: '01',
    title: 'Créez votre dossier client',
    description: "Renseignez les informations de l'entité et initialisez une nouvelle mission d'audit en quelques secondes."
  },
  {
    number: '02',
    title: 'Importez vos balances',
    description: 'Chargez les balances N et N-1 : CAC Perform structure et contrôle vos données automatiquement.'
  },
  {
    number: '03',
    title: 'Analysez et concluez',
    description: 'Groupings, variations, comptes significatifs et pistes d’audit sont générés pour accélérer vos travaux.'
  },
]

const trustPoints = [
  {
    icon: 'fa-lock',
    title: 'Confidentialité des données',
    description: 'Vos dossiers clients et balances comptables restent strictement confidentiels.'
  },
  {
    icon: 'fa-scale-balanced',
    title: 'Conforme aux normes d’audit',
    description: 'Des méthodes d’analyse alignées sur les référentiels de commissariat aux comptes.'
  },
  {
    icon: 'fa-users-gear',
    title: 'Conçu avec des auditeurs',
    description: 'Développé par le cabinet Y3 Audit & Conseils, pour des auditeurs, avec des auditeurs.'
  },
]

function goToLogin() {
  router.push('/connexion')
}
</script>

<template>
  <div class="landing-page w-full min-h-screen bg-white text-[#022a41] overflow-y-auto">

    <!-- NAVBAR -->
    <header class="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-gray-100">
      <div class="max-w-7xl mx-auto px-6 lg:px-10 h-20 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <img src="../assets/logo.png" alt="CAC Perform" class="h-10" />
          <span class="text-lg font-bold tracking-wide text-blue-ycube">CAC PERFORM</span>
        </div>

        <nav class="hidden md:flex items-center gap-8 text-sm font-semibold text-slate-700">
          <a href="#fonctionnalites" class="rounded hover:text-blue-ycube transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-ycube focus-visible:ring-offset-2">Fonctionnalités</a>
          <a href="#comment-ca-marche" class="rounded hover:text-blue-ycube transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-ycube focus-visible:ring-offset-2">Comment ça marche</a>
          <a href="#contact" class="rounded hover:text-blue-ycube transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-ycube focus-visible:ring-offset-2">Contact</a>
        </nav>

        <div class="hidden md:flex items-center gap-4">
          <button
            @click="goToLogin"
            class="px-5 py-2.5 rounded-full bg-green-ycube-2 text-white font-semibold hover:bg-green-ycube transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-ycube focus-visible:ring-offset-2"
          >
            Se connecter
          </button>
        </div>

        <button
          class="md:hidden text-2xl text-blue-ycube focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-ycube focus-visible:ring-offset-2 rounded"
          :aria-expanded="mobileMenuOpen"
          aria-label="Ouvrir le menu"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          <i class="fa-solid" :class="mobileMenuOpen ? 'fa-xmark' : 'fa-bars'" aria-hidden="true"></i>
        </button>
      </div>

      <div v-if="mobileMenuOpen" class="md:hidden border-t border-gray-100 px-6 py-4 flex flex-col gap-4 bg-white">
        <a href="#fonctionnalites" class="font-semibold text-slate-700 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-ycube" @click="mobileMenuOpen = false">Fonctionnalités</a>
        <a href="#comment-ca-marche" class="font-semibold text-slate-700 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-ycube" @click="mobileMenuOpen = false">Comment ça marche</a>
        <a href="#contact" class="font-semibold text-slate-700 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-ycube" @click="mobileMenuOpen = false">Contact</a>
        <button
          @click="goToLogin"
          class="mt-2 px-5 py-2.5 rounded-full bg-green-ycube-2 text-white font-semibold hover:bg-green-ycube transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-ycube focus-visible:ring-offset-2"
        >
          Se connecter
        </button>
      </div>
    </header>

    <!-- HERO -->
    <section class="relative bg-gradient-to-br from-blue-ycube to-blue-ycube-3 text-white overflow-hidden">
      <div class="max-w-7xl mx-auto px-6 lg:px-10 py-20 lg:py-28 grid lg:grid-cols-2 gap-12 items-center">
        <div>
          <span class="inline-block px-4 py-1.5 rounded-full bg-white/10 text-sm font-semibold tracking-wide mb-6">
            Conçu par Y3 Audit &amp; Conseils
          </span>
          <h1 class="text-4xl lg:text-5xl font-extrabold leading-tight mb-6">
            L’analyse préliminaire de vos missions de CAC, automatisée.
          </h1>
          <p class="text-lg text-blue-100 mb-8 max-w-xl">
            CAC Perform assiste les auditeurs dans leurs missions de commissariat aux comptes :
            import des balances, groupings, états financiers provisoires et pistes d’audit générés
            automatiquement.
          </p>
          <div class="flex flex-wrap gap-4">
            <button
              @click="goToLogin"
              class="px-8 py-3.5 rounded-full bg-green-ycube-2 text-white font-bold hover:bg-green-ycube transition shadow-lg shadow-black/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-blue-ycube"
            >
              Se connecter
            </button>
            <a
              href="#fonctionnalites"
              class="px-8 py-3.5 rounded-full border-2 border-white/40 font-bold hover:bg-white/10 transition text-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-blue-ycube"
            >
              Découvrir les fonctionnalités
            </a>
          </div>
        </div>

        <div class="relative flex justify-center">
          <div class="absolute inset-0 bg-green-ycube-2/20 blur-3xl rounded-full"></div>
          <img src="../assets/logo5.png" alt="CAC Perform" class="relative w-full max-w-md drop-shadow-2xl" />
        </div>
      </div>
    </section>

    <!-- TRUST BAR -->
    <section class="bg-white border-b border-gray-100">
      <div class="max-w-7xl mx-auto px-6 lg:px-10 py-12 grid sm:grid-cols-3 gap-8">
        <div v-for="point in trustPoints" :key="point.title" class="flex items-start gap-4">
          <div class="w-11 h-11 shrink-0 rounded-full bg-blue-ycube/10 flex items-center justify-center">
            <i :class="['fa-solid', point.icon, 'text-blue-ycube']" aria-hidden="true"></i>
          </div>
          <div>
            <h3 class="font-bold text-sm text-[#022a41]">{{ point.title }}</h3>
            <p class="text-sm text-gray-600 mt-1 leading-relaxed">{{ point.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- FEATURES -->
    <section id="fonctionnalites" class="py-20 lg:py-28 bg-gray-ycube/40">
      <div class="max-w-7xl mx-auto px-6 lg:px-10">
        <div class="max-w-2xl mx-auto text-center mb-16">
          <h2 class="text-3xl lg:text-4xl font-extrabold text-blue-ycube mb-4">
            Tout ce dont vous avez besoin pour vos missions d’audit
          </h2>
          <p class="text-gray-600 text-lg">
            De la création du dossier client à la production des pistes d’audit, CAC Perform couvre
            l’ensemble de votre analyse préliminaire.
          </p>
        </div>

        <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div
            v-for="feature in features"
            :key="feature.title"
            class="bg-white rounded-2xl shadow p-6 hover:shadow-lg hover:-translate-y-1 transition"
          >
            <div class="w-12 h-12 rounded-xl bg-blue-ycube/10 flex items-center justify-center mb-5">
              <i :class="['fa-solid', feature.icon, 'text-xl text-blue-ycube']" aria-hidden="true"></i>
            </div>
            <h3 class="font-bold text-lg mb-2 text-[#022a41]">{{ feature.title }}</h3>
            <p class="text-sm text-gray-600 leading-relaxed">{{ feature.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- HOW IT WORKS -->
    <section id="comment-ca-marche" class="py-20 lg:py-28">
      <div class="max-w-7xl mx-auto px-6 lg:px-10">
        <div class="max-w-2xl mx-auto text-center mb-16">
          <h2 class="text-3xl lg:text-4xl font-extrabold text-blue-ycube mb-4">
            Comment ça marche
          </h2>
          <p class="text-gray-600 text-lg">
            Trois étapes suffisent pour transformer une balance en dossier d’audit structuré.
          </p>
        </div>

        <div class="grid md:grid-cols-3 gap-10">
          <div v-for="step in steps" :key="step.number" class="relative text-center md:text-left">
            <span class="text-5xl font-extrabold text-green-ycube-2/40">{{ step.number }}</span>
            <h3 class="text-xl font-bold mt-2 mb-3 text-[#022a41]">{{ step.title }}</h3>
            <p class="text-gray-600 leading-relaxed">{{ step.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA BANNER -->
    <section class="py-16 bg-gradient-to-r from-green-ycube-2 to-green-ycube">
      <div class="max-w-4xl mx-auto px-6 text-center text-white">
        <h2 class="text-2xl lg:text-3xl font-extrabold mb-4">
          Prêt à accélérer vos missions de commissariat aux comptes ?
        </h2>
        <p class="text-white/90 mb-8">
          Connectez-vous à votre espace CAC Perform pour reprendre vos dossiers en cours.
        </p>
        <button
          @click="goToLogin"
          class="px-8 py-3.5 rounded-full bg-white text-green-ycube font-bold hover:bg-gray-100 transition shadow-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-green-ycube"
        >
          Se connecter
        </button>
      </div>
    </section>

    <!-- FOOTER -->
    <footer id="contact" class="bg-blue-ycube text-white/80 py-12">
      <div class="max-w-7xl mx-auto px-6 lg:px-10 flex flex-col md:flex-row justify-between gap-8">
        <div class="flex items-center gap-3">
          <img src="../assets/logo.png" alt="CAC Perform" class="h-9" />
          <span class="font-bold text-white">CAC PERFORM</span>
        </div>

        <div class="text-sm space-y-1">
          <p class="text-white font-semibold">Besoin d’aide ?</p>
          <p>
            <a href="mailto:axelhamilton02@gmail.com" class="hover:text-white transition">
              axelhamilton02@gmail.com
            </a>
          </p>
          <p>Cabinet Y3 Audit &amp; Conseils</p>
        </div>
      </div>

      <div class="max-w-7xl mx-auto px-6 lg:px-10 mt-8 pt-6 border-t border-white/10 text-xs text-white/50">
        © {{ new Date().getFullYear() }} CAC Perform — Y3 Audit &amp; Conseils. Tous droits réservés.
      </div>
    </footer>

  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,600;0,700;0,800;1,400&display=swap');

.landing-page {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}

@media (prefers-reduced-motion: reduce) {
  .landing-page * {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
  }

  .landing-page .hover\:-translate-y-1:hover {
    transform: none !important;
  }
}
</style>
