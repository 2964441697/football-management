<template>
  <el-container style="height: 100vh">
    <el-drawer v-model="drawerVisible" direction="ltr" :size="200" :with-header="false">
      <Sidebar @close="drawerVisible = false" />
    </el-drawer>
    
    <el-aside v-show="!drawerVisible" class="desktop-aside" width="200px">
      <Sidebar />
    </el-aside>
    
    <el-container>
      <el-header>
        <div class="header-content">
          <div class="header-left">
            <el-button class="mobile-menu-btn" @click="drawerVisible = true" circle>
              <el-icon><Menu /></el-icon>
            </el-button>
            <span class="title">足球管理系统</span>
            <el-autocomplete
              v-model="searchQuery"
              :fetch-suggestions="handleSearch"
              placeholder="搜索球员、球队、新闻..."
              class="global-search"
              :trigger-on-focus="false"
              clearable
              @select="handleSearchSelect"
              @keyup.enter="handleSearchEnter"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
              <template #default="{ item }">
                <div class="search-item" @click="navigateToResult(item)">
                  <el-icon v-if="item.type === 'player'"><User /></el-icon>
                  <el-icon v-else-if="item.type === 'team'"><Trophy /></el-icon>
                  <el-icon v-else-if="item.type === 'news'"><Document /></el-icon>
                  <el-icon v-else-if="item.type === 'competition'"><Medal /></el-icon>
                  <div class="search-item-content">
                    <div class="search-item-name">{{ item.name || item.title }}</div>
                    <div class="search-item-type">{{ getTypeLabel(item.type) }}</div>
                  </div>
                </div>
              </template>
            </el-autocomplete>
          </div>
          <div class="user-info">
            <el-dropdown v-if="userStore.user" @command="handleCommand">
              <div class="user-dropdown">
                <el-avatar :size="32" style="margin-right: 8px;" :src="userAvatar">
                  {{ userStore.user.username.charAt(0).toUpperCase() }}
                </el-avatar>
                <span class="username">{{ userStore.user.username }}</span>
                <el-icon style="margin-left: 4px;"><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                  <el-dropdown-item command="settings">系统设置</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import Sidebar from '../components/Sidebar.vue'
import { ElMessage } from 'element-plus'
import { ArrowDown, Menu, Search, User, Trophy, Document, Medal } from '@element-plus/icons-vue'
import { debounce, getStaticUrl } from '../utils/helpers'
import endpoints from '../api/endpoints'

const router = useRouter()
const userStore = useUserStore()
const drawerVisible = ref(false)
const searchQuery = ref('')
const searchResults = ref([])

const userAvatar = computed(() => {
  return getStaticUrl(userStore.user?.avatar)
})

const handleLogout = () => {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

const handleCommand = (command) => {
  if (command === 'logout') {
    handleLogout()
  } else if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'settings') {
    router.push('/settings')
  }
}

const handleSearch = debounce(async (query, cb) => {
  if (!query || query.length < 1) {
    cb([])
    return
  }
  try {
    const response = await endpoints.globalSearch(query)
    const results = []
    if (response.data.results?.players) {
      response.data.results.players.forEach(p => {
        results.push({ ...p, type: 'player' })
      })
    }
    if (response.data.results?.teams) {
      response.data.results.teams.forEach(t => {
        results.push({ ...t, type: 'team' })
      })
    }
    if (response.data.results?.news) {
      response.data.results.news.forEach(n => {
        results.push({ ...n, type: 'news' })
      })
    }
    if (response.data.results?.competitions) {
      response.data.results.competitions.forEach(c => {
        results.push({ ...c, type: 'competition' })
      })
    }
    searchResults.value = results
    cb(results)
  } catch (e) {
    cb([])
  }
}, 300)

const getTypeLabel = (type) => {
  const labels = {
    player: '球员',
    team: '球队',
    news: '新闻',
    competition: '赛事'
  }
  return labels[type] || type
}

const navigateToResult = (item) => {
  const routes = {
    player: '/players',
    team: '/teams',
    news: '/news',
    competition: '/competitions'
  }
  if (routes[item.type]) {
    router.push(routes[item.type])
  }
}

const handleSearchSelect = (item) => {
  navigateToResult(item)
}

const handleSearchEnter = () => {
  if (searchResults.value.length > 0) {
    navigateToResult(searchResults.value[0])
  }
}
</script>

<style scoped>
.el-container {
  margin: 0;
  padding: 0;
  background: transparent;
}

.el-header {
  background: white;
  color: var(--text-primary);
  padding: 0;
  display: flex;
  align-items: center;
  box-shadow: var(--shadow-light);
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.mobile-menu-btn {
  display: none;
}

.title {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.global-search {
  width: 280px;
  margin-left: 20px;
}

@media (max-width: 1024px) {
  .global-search {
    display: none;
  }
}

.search-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  cursor: pointer;
}

.search-item:hover {
  background-color: #f5f7fa;
  margin: 0 -12px;
  padding: 8px 12px;
}

.search-item-content {
  flex: 1;
}

.search-item-name {
  font-size: 14px;
  color: #303133;
}

.search-item-type {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: var(--transition-base);
}

.user-dropdown:hover {
  background: var(--bg-base);
}

.username {
  display: inline-block;
}

@media (max-width: 768px) {
  .username {
    display: none;
  }
}

@media (max-width: 768px) {
  .mobile-menu-btn {
    display: flex;
  }
  
  .desktop-aside {
    display: none;
  }
}

.el-main {
  background-color: transparent;
  overflow-y: auto;
  padding: 24px;
}

@media (max-width: 768px) {
  .el-main {
    padding: 16px;
  }
}

.el-aside {
  background: transparent;
  overflow-y: auto;
}

.el-drawer {
  background: transparent;
}
</style>
