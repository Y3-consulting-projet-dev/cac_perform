import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import NewClient from '../views/NewClient.vue'
import NewMission from '../views/NewMission.vue'
import GroupingAnalyse from '../views/GroupingAnalyse.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import MissionsView from '@/views/MissionsView.vue'
import ProfileView from '@/views/ProfileView.vue'
import ClientsView from '@/views/ClientsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/connexion',
      name: 'login',
      component: LoginView,
      meta: {
        showHeader: false
      }
    },
    {
      path: '/inscription',
      name: 'register',
      component: RegisterView,
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
        showHeader: true
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
        showHeader: true
      }
    },
    {
      path: '/clients',
      name: 'clients',
      component: ClientsView,
      meta: {
        showHeader: true
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
    }
  ]
})

router.beforeEach((to, from, next) => {
  const publicRoutes = ['login', 'register']
  const isPublic = publicRoutes.includes(to.name)
  const token = sessionStorage.getItem('token')
  if (!isPublic && !token) {
    return next({ name: 'login' })
  }
  next()
})

export default router
