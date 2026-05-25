/**
 * 路由配置 - 首页（会话管理）和浏览页（照片选片）
 */
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
    },
    {
      path: '/browse/:sessionId',
      name: 'browse',
      component: () => import('../views/BrowseView.vue'),
    },
  ],
})

export default router
