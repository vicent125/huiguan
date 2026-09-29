<template>
  <div class="app-layout">
    <CeLan />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import CeLan from '../components/CeLan.vue'
</script>

<style scoped>
.app-layout {
  display:flex;
  width:100vw;
  height:100vh;
  overflow:hidden;
}
.main-content {
  flex:1;
  overflow-y:auto;
  background:#f5f7f9;
}
</style>