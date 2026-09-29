<template>
  <div class="module-page">
    <header class="page-header">
      <div>
        <span>SMART AGRICULTURE SYSTEM</span>
        <h1>{{ route.meta.title }}</h1>
        <p>该板块已成功接入 Vue Router。</p>
      </div>

      <RouterLink
        to="/"
        class="back-button"
      >
        返回首页
      </RouterLink>
    </header>

    <section class="module-placeholder">
      <div class="module-placeholder__icon">
        {{ pageIcon }}
      </div>

      <h2>{{ route.meta.title }}</h2>

      <p>
        后续可以在这里继续添加监测数据、信息表格、操作按钮和管理功能。
      </p>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const icons = {
  monitoring: '◉',
  crops: '♧',
  irrigation: '◌',
  fertilization: '◇',
  weather: '☁',
  warnings: '!',
  history: '▤',
  devices: '⌘',
  settings: '⚙'
}

const pageIcon = computed(() => {
  return icons[route.name] || '◇'
})
</script>