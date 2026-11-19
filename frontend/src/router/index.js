import { createRouter, createWebHistory } from 'vue-router'

import Dashboard from '../views/Dashboard.vue'
import Resume from '../views/Resume.vue'
import Interview from '../views/Interview.vue'
import Report from '../views/Report.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/resume',
    name: 'Resume',
    component: Resume
  },
  {
    path: '/interview/:sessionId?',
    name: 'Interview',
    component: Interview
  },
  {
    path: '/report/:sessionId?',
    name: 'Report',
    component: Report
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router