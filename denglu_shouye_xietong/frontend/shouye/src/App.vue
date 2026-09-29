<template>
  <div class="app-layout">
    <CeLan />

    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import CeLan from './components/CeLan.vue'
</script>