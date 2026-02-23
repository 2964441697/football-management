<template>
  <BackgroundSwitcher>
    <router-view />
  </BackgroundSwitcher>
</template>

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from './stores/user'
import BackgroundSwitcher from './components/BackgroundSwitcher.vue'

const userStore = useUserStore()

onMounted(() => {
  // 初始化用户状态（从本地存储恢复）
  userStore.loadUserFromStorage()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  height: 100%;
  width: 100%;
}

#app {
  height: 100%;
  width: 100%;
}
</style>
