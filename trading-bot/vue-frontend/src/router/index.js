import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Analysis from '../views/Analysis.vue'
import Logs from '../views/Logs.vue'
import Performance from '../views/Performance.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: Analysis
  },
  {
    path: '/logs',
    name: 'Logs',
    component: Logs
  },
  {
    path: '/performance',
    name: 'Performance',
    component: Performance
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router