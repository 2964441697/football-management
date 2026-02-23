<template>
  <div class="settings-container">
    <h2 class="page-title">系统设置</h2>
    
    <el-card class="settings-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="外观" name="appearance">
          <el-form label-width="120px">
            <el-form-item label="主题模式">
              <el-switch
                v-model="isDark"
                active-text="深色"
                inactive-text="浅色"
                @change="toggleTheme"
              />
            </el-form-item>
            <el-form-item label="主题色">
              <el-color-picker v-model="themeColor" @change="changeThemeColor" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="语言" name="language">
          <el-form label-width="120px">
            <el-form-item label="界面语言">
              <el-select v-model="language" @change="changeLanguage">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="数据管理" name="data">
          <el-form label-width="120px">
            <el-form-item label="数据导出">
              <el-button @click="exportAllData">导出全部数据</el-button>
              <span class="hint">导出为CSV格式</span>
            </el-form-item>
            <el-form-item label="清除缓存">
              <el-button type="warning" @click="clearCache">清除本地缓存</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="关于" name="about">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="系统名称">足球管理系统</el-descriptions-item>
            <el-descriptions-item label="版本号">v1.0.0</el-descriptions-item>
            <el-descriptions-item label="前端框架">Vue 3 + Element Plus</el-descriptions-item>
            <el-descriptions-item label="后端框架">Flask + SQLAlchemy</el-descriptions-item>
            <el-descriptions-item label="数据库">MySQL</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import endpoints from '../api/endpoints'

const activeTab = ref('appearance')
const isDark = ref(false)
const themeColor = ref('#667eea')
const language = ref('zh-CN')

function loadSettings() {
  const dark = localStorage.getItem('theme') === 'dark'
  isDark.value = dark
  applyTheme(dark)
  
  const color = localStorage.getItem('themeColor') || '#667eea'
  themeColor.value = color
  document.documentElement.style.setProperty('--primary-color', color)
  
  const lang = localStorage.getItem('language') || 'zh-CN'
  language.value = lang
}

function toggleTheme(val) {
  localStorage.setItem('theme', val ? 'dark' : 'light')
  applyTheme(val)
  ElMessage.success(val ? '已切换为深色模式' : '已切换为浅色模式')
}

function applyTheme(isDark) {
  if (isDark) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

function changeThemeColor(val) {
  if (val) {
    localStorage.setItem('themeColor', val)
    document.documentElement.style.setProperty('--primary-color', val)
    ElMessage.success('主题色已更新')
  }
}

function changeLanguage(val) {
  localStorage.setItem('language', val)
  ElMessage.success('语言切换将在刷新页面后生效')
}

async function exportAllData() {
  try {
    const [teams, players, matches, seasons] = await Promise.all([
      endpoints.getTeams(),
      endpoints.getPlayers(),
      endpoints.getMatches(),
      endpoints.getSeasons()
    ])
    
    const data = { teams, players, matches, seasons }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `football_backup_${new Date().toISOString().slice(0, 10)}.json`
    link.click()
    URL.revokeObjectURL(link.href)
    
    ElMessage.success('数据导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

function clearCache() {
  localStorage.clear()
  ElMessage.success('缓存已清除，请重新登录')
  window.location.reload()
}

onMounted(loadSettings)
</script>

<style scoped>
.settings-container {
  max-width: 800px;
}

.settings-card {
  margin-top: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}

.hint {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}
</style>
