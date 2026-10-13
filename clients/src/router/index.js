import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import NewClient from '../views/NewClient.vue'
import NewMission from '../views/NewMission.vue'
import GroupingAnalyse from '../views/GroupingAnalyse.vue'
import LoginView from '@/views/LoginView.vue'
import MissionsView from '@/views/MissionsView.vue'
import ProfileView from '@/views/ProfileView.vue'
import ClientsView from '@/views/ClientsView.vue'
import HelpView from '@/views/HelpView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/bienvenue',
      name: 'landing',
      component: () => import('@/views/LandingView.vue'),
      meta: {
        showHeader: false
      }
    },
    {
      path: '/connexion',
      name: 'login',
      component: LoginView,
      meta: {
        showHeader: false
      }
    },
    {
  path: '/profile',
  name: 'profile',
  component: () => import('@/views/ProfileView.vue'),
  meta: {
        showHeader: true
      }
},

    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: {
        showHeader: false
      }
    },
    {
      path: '/client/:clientId',
      name: 'clientSpace',
      component: () => import('../views/ClientSpace.vue'),
      meta: {
        showHeader: true
      },
      props: true
    },
    {
      path: '/newClient',
      name: 'newClient',
      component: NewClient,
      meta: {
        showHeader: true
      }
    },
    {
      path: '/newMission/:clientId',
      name: 'newMission',
      component: NewMission,
      meta: {
        showHeader: true
      },
      props: true
    },
    {
      path: '/missions',
      name: 'missions',
      component: MissionsView,
      meta: {
        showHeader: false
      }
    },
    {
      path: '/clients',
      name: 'clients',
      component: ClientsView,
      meta: {
        showHeader: false
      }
    },
    {
      path: '/grouping-analyse/:missionId',
      name: 'groupingAnalyse',
      component: GroupingAnalyse,
      meta: {
        showHeader: true
      },
      props: true
    },
    {
      // Fichiers complémentaires s'affiche dans GroupingAnalyse, sous la barre
      // latérale bleue : l'ancienne adresse y redirige pour garder la barre visible.
      path: '/grouping-analyse/:missionId/fichiers-complementaires',
      name: 'fichiersComplementaires',
      redirect: (to) => ({
        path: `/grouping-analyse/${to.params.missionId}`,
        query: { step: 'fichiers_complementaires' },
      }),
    },
    {
      // Fiabilité IPE s'affiche dans GroupingAnalyse, sous la barre latérale
      // bleue : l'ancienne adresse y redirige pour garder la barre visible.
      path: '/grouping-analyse/:missionId/fiabilite-ipe',
      name: 'fiabiliteIpe',
      redirect: (to) => ({
        path: `/grouping-analyse/${to.params.missionId}`,
        query: { step: 'fiabilite_ipe' },
      }),
    },
    {
      path: '/aide',
      name: 'help',
      component: HelpView,
      meta: {
        showHeader: true
      }
    }
  ]
})

router.beforeEach((to, from, next) => {
  const publicRoutes = ['login', 'landing']
  const isPublic = publicRoutes.includes(to.name)
  const token = sessionStorage.getItem('token')
  if (!isPublic && !token) {
    return next({ name: 'login' })
  }
  if (to.path === '/inscription') {
    return next({ name: 'login' })
  }
  next()
})

export default router
