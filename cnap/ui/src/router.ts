import { createRouter, createWebHistory } from 'vue-router'
import Overview from './views/Overview.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: Overview,
    },
    {
      path: '/dashboard',
      component: () => import('./views/Dashboard.vue'),
    },
    {
      path: '/pipelines',
      component: () => import('./views/Pipelines.vue'),
    },
  ],
})
