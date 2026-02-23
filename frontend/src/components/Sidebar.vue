<template>
  <el-menu
    active-text-color="#fff"
    background-color="transparent"
    class="el-menu-vertical-demo"
    default-active="1"
    text-color="rgba(255, 255, 255, 0.7)"
    @open="handleOpen"
    @close="handleClose"
    router
  >
    <div class="menu-logo">
      <img src="/football.png" alt="足球" class="logo-img" />
      <span class="logo-text">{{ roleLabel }}</span>
    </div>
    
    <el-menu-item index="/dashboard">
      <el-icon><HomeFilled /></el-icon>
      <span>数据概览</span>
    </el-menu-item>
    
    <el-menu-item v-if="userStore.hasPermission('teams')" index="/teams">
      <el-icon><UserFilled /></el-icon>
      <span>球队管理</span>
    </el-menu-item>
    
    <el-menu-item v-if="userStore.hasPermission('players')" index="/players">
      <el-icon><User /></el-icon>
      <span>球员管理</span>
    </el-menu-item>
    
    <el-menu-item v-if="userStore.hasPermission('coaches')" index="/coaches">
      <el-icon><Grid /></el-icon>
      <span>教练管理</span>
    </el-menu-item>
    
    <el-menu-item v-if="userStore.hasPermission('matches')" index="/matches">
      <el-icon><Trophy /></el-icon>
      <span>比赛管理</span>
    </el-menu-item>
    
    <el-menu-item v-if="userStore.hasPermission('seasons')" index="/seasons">
      <el-icon><Calendar /></el-icon>
      <span>赛季管理</span>
    </el-menu-item>
    
    <el-menu-item v-if="userStore.hasPermission('competitions')" index="/competitions">
      <el-icon><Medal /></el-icon>
      <span>赛事管理</span>
    </el-menu-item>
    
    <el-menu-item v-if="userStore.hasPermission('transfers')" index="/transfers">
      <el-icon><Promotion /></el-icon>
      <span>转会管理</span>
    </el-menu-item>
    
    <el-menu-item v-if="userStore.hasPermission('contracts')" index="/contracts">
      <el-icon><Document /></el-icon>
      <span>合同管理</span>
    </el-menu-item>
    
    <el-sub-menu v-if="userStore.isAdmin" index="management">
      <template #title>
        <el-icon><Management /></el-icon>
        <span>综合管理</span>
      </template>
      <el-menu-item v-if="userStore.hasPermission('news')" index="/news">
        <el-icon><Bell /></el-icon>
        <span>新闻公告</span>
      </el-menu-item>
      <el-menu-item v-if="userStore.hasPermission('finances')" index="/finances">
        <el-icon><Money /></el-icon>
        <span>财务管理</span>
      </el-menu-item>
      <el-menu-item v-if="userStore.hasPermission('training')" index="/training-plans">
        <el-icon><Aim /></el-icon>
        <span>训练计划</span>
      </el-menu-item>
    </el-sub-menu>
    
    <el-menu-item v-if="userStore.hasPermission('profile')" index="/profile">
      <el-icon><User /></el-icon>
      <span>个人资料</span>
    </el-menu-item>
    
    <el-menu-item v-if="userStore.isAdmin" index="/settings">
      <el-icon><Setting /></el-icon>
      <span>系统设置</span>
    </el-menu-item>
    
    <div class="drawer-close-btn" @click="closeDrawer">
      <el-icon><Close /></el-icon>
    </div>
  </el-menu>
</template>

<script setup>
import { computed } from 'vue'
import { HomeFilled, User, UserFilled, Trophy, Calendar, Promotion, Close, Medal, Document, Money, Management, Bell, Grid, Setting, Aim } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'

const emit = defineEmits(['close'])
const userStore = useUserStore()

const roleLabel = computed(() => {
  return userStore.roleLabel
})

const handleOpen = (key, keyPath) => {
  // console.log(key, keyPath)
}
const handleClose = (key, keyPath) => {
  // console.log(key, keyPath)
}

const closeDrawer = () => {
  emit('close')
}
</script>

<style scoped>
.el-menu-vertical-demo {
  height: 100%;
  min-height: 100vh;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
}

.menu-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 24px 20px;
  margin-bottom: 12px;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: white;
}

.football-icon {
  width: 36px;
  height: 36px;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
}

.logo-img {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 50%;
}

.el-menu-item {
  margin: 4px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.el-menu-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.el-menu-item.is-active {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  font-weight: 600;
}

.el-menu-item .el-icon {
  margin-right: 8px;
}

.drawer-close-btn {
  display: none;
  position: absolute;
  top: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition-base);
}

.drawer-close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

@media (max-width: 768px) {
  .drawer-close-btn {
    display: flex;
  }
  
  .menu-logo {
    padding-right: 60px;
  }
}
</style>
