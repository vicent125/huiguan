<template>
  <aside class="sidebar">
    <div class="brand">
      <div class="brand__logo">田</div>

      <div>
        <h1>智慧农情</h1>
        <p>SMART AGRICULTURE</p>
      </div>
    </div>

    <nav class="menu">
      <RouterLink
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="menu-item"
      >
        <span class="menu-item__icon">
          {{ item.icon }}
        </span>

        <span>{{ item.name }}</span>

        <span
          v-if="item.badge"
          class="menu-item__badge"
        >
          {{ item.badge }}
        </span>
      </RouterLink>
    </nav>

    <div class="sidebar-footer">
      <span class="status-dot"></span>

      <div>
        <strong>系统运行正常</strong>
        <p>监测设备在线</p>
      </div>
    </div>
  </aside>
</template>

<script setup>
const menuItems = [
  {
    name: '首页总览',
    path: '/',
    icon: '⌂'
  },
  {
    name: '农情监测',
    path: '/monitoring',
    icon: '◉'
  },
  {
    name: '作物管理',
    path: '/crops',
    icon: '♧'
  },
  {
    name: '灌溉决策',
    path: '/irrigation',
    icon: '◌'
  },
  {
    name: '施肥决策',
    path: '/fertilization',
    icon: '◇'
  },
  {
    name: '气象分析',
    path: '/weather',
    icon: '☁'
  },
  {
    name: '预警中心',
    path: '/warnings',
    icon: '!',
    badge: 3
  },
  {
    name: '历史决策',
    path: '/history',
    icon: '▤'
  },
  {
    name: '设备管理',
    path: '/devices',
    icon: '⌘'
  },
  {
    name: '系统设置',
    path: '/settings',
    icon: '⚙'
  }
]
</script>