import { createRouter, createWebHistory } from 'vue-router'

import FeatureView from '../views/FeatureView.vue'
import ChatView from '../views/ChatView.vue'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: FeatureView,
    meta: {
      title: '安全运营控制台',
    },
  },
  {
    path: '/chat',
    name: 'chat',
    component: ChatView,
    meta: {
      title: '智能体对话',
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.afterEach((to) => {
  document.title = to.meta?.title
    ? `${to.meta.title} - Cyber Agent`
    : 'Cyber Agent'
})

export default router