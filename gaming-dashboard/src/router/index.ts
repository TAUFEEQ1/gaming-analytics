import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import CompositeMetrics from '@/views/CompositeMetrics.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/composite',
      name: 'composite',
      component: CompositeMetrics
    }
  ]
})

export default router
