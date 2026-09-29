import { createRouter, createWebHistory } from 'vue-router'

import Yucefenxi from '../views/Yucefenxi.vue'
import Shuifeijuece from '../views/Shuifeijuece.vue'

const routes = [
  {
    path: '/',
    redirect: '/yucefenxi'
  },
  {
    path: '/yucefenxi',
    name: 'yucefenxi',
    component: Yucefenxi
  },
  {
    path: '/shuifeijuece',
    name: 'shuifeijuece',
    component: Shuifeijuece
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router