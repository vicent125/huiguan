<template>
  <div class="app-shell">
    <el-menu :default-active="$route.path" mode="horizontal" router class="app-nav">
      <el-menu-item index="/tianqifenxi">天气分析</el-menu-item>
      <el-menu-item index="/baogaozhongxin">报告中心</el-menu-item>
      <el-menu-item index="/xitongguanli">系统管理</el-menu-item>
    </el-menu>
    <router-view />
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.app-nav {
  position: sticky;
  top: 0;
  z-index: 20;
  justify-content: center;
}
</style>
