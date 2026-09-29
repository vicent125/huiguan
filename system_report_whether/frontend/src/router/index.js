import { createRouter, createWebHistory } from 'vue-router'
import Baogaozhongxin from '../views/Baogaozhongxin.vue'
import Tianqifenxi from '../views/Tianqifenxi.vue'
import Xitongguanli from '../views/Xitongguanli.vue'

const routes = [
  { path: '/', redirect: '/baogaozhongxin' },
  { path: '/baogaozhongxin', component: Baogaozhongxin },
  { path: '/xitongguanli', component: Xitongguanli },
  { path: '/tianqifenxi', component: Tianqifenxi }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})
export default router