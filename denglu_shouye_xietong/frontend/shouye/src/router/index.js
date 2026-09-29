import { createRouter, createWebHistory } from 'vue-router'
import Shouye from '../views/Shouye.vue'
import Mokuai from '../views/Mokuai.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: Shouye,
    meta: {
      title: '首页总览'
    }
  },
  {
    path: '/monitoring',
    name: 'monitoring',
    component: Mokuai,
    meta: {
      title: '农情监测'
    }
  },
  {
    path: '/crops',
    name: 'crops',
    component: Mokuai,
    meta: {
      title: '作物管理'
    }
  },
  {
    path: '/irrigation',
    name: 'irrigation',
    component: Mokuai,
    meta: {
      title: '灌溉决策'
    }
  },
  {
    path: '/fertilization',
    name: 'fertilization',
    component: Mokuai,
    meta: {
      title: '施肥决策'
    }
  },
  {
    path: '/weather',
    name: 'weather',
    component: Mokuai,
    meta: {
      title: '气象分析'
    }
  },
  {
    path: '/warnings',
    name: 'warnings',
    component: Mokuai,
    meta: {
      title: '预警中心'
    }
  },
  {
    path: '/history',
    name: 'history',
    component: Mokuai,
    meta: {
      title: '历史决策'
    }
  },
  {
    path: '/devices',
    name: 'devices',
    component: Mokuai,
    meta: {
      title: '设备管理'
    }
  },
  {
    path: '/settings',
    name: 'settings',
    component: Mokuai,
    meta: {
      title: '系统设置'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.afterEach((to) => {
  document.title = `${to.meta.title || '智慧农业'} - 智慧农情系统`
})

export default router