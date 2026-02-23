<!--
  Dashboard.vue - 仪表盘页面组件

  功能：
  - 展示系统统计概览（球队、球员、比赛、赛季数量）
  - 显示最近的5支球队列表
  - 提供快捷导航到各管理模块
-->
<template>
  <div>
    <h2 class="page-title">数据概览</h2>
    <el-row :gutter="20" style="margin-bottom: 30px;">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <el-icon :size="48" color="#667eea"><UserFilled /></el-icon>
          <div class="stat-value">{{ stats.teams }}</div>
          <div class="stat-label">球队总数</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <el-icon :size="48" color="#764ba2"><User /></el-icon>
          <div class="stat-value">{{ stats.players }}</div>
          <div class="stat-label">球员总数</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <el-icon :size="48" color="#67C23A"><Trophy /></el-icon>
          <div class="stat-value">{{ stats.matches }}</div>
          <div class="stat-label">比赛场数</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <el-icon :size="48" color="#E6A23C"><Calendar /></el-icon>
          <div class="stat-value">{{ stats.seasons }}</div>
          <div class="stat-label">赛季数</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-bottom: 30px;">
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="stat-card">
          <el-icon :size="48" color="#F56C6C"><Money /></el-icon>
          <div class="stat-value" style="font-size: 28px;">{{ formatMoney(stats.total_income) }}</div>
          <div class="stat-label">总收入</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="stat-card">
          <el-icon :size="48" color="#909399"><Money /></el-icon>
          <div class="stat-value" style="font-size: 28px;">{{ formatMoney(stats.total_expense) }}</div>
          <div class="stat-label">总支出</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="8">
        <el-card class="stat-card">
          <el-icon :size="48" :color="stats.balance >= 0 ? '#67C23A' : '#F56C6C'"><Wallet /></el-icon>
          <div class="stat-value" style="font-size: 28px;">{{ formatMoney(stats.balance) }}</div>
          <div class="stat-label">结余</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>球员位置分布</span>
            </div>
          </template>
          <div ref="positionChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>财务概况</span>
            </div>
          </template>
          <div ref="financeChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <h3 class="section-title" style="margin-top: 30px;">最近球队</h3>
    <el-card>
      <div v-if="recentTeams.length === 0" class="empty-state">
        <el-icon :size="64" color="#C0C4CC"><FolderOpened /></el-icon>
        <div class="empty-state-text">暂无球队数据</div>
        <div class="empty-state-hint">点击上方"球队管理"开始添加球队</div>
      </div>
      <el-table v-else :data="recentTeams" stripe style="width: 100%">
        <el-table-column prop="name" label="球队名称">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 10px;">
              <el-avatar v-if="row.logo" :src="row.logo" :size="32" />
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="home_stadium" label="主场" />
        <el-table-column prop="founded_year" label="成立年份" width="120">
          <template #default="{ row }">
            <span class="badge badge-primary">{{ row.founded_year }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="budget" label="预算" width="150">
          <template #default="{ row }">
            {{ formatMoney(row.budget) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { UserFilled, User, Trophy, Calendar, FolderOpened, Money, Wallet } from '@element-plus/icons-vue'
import { formatMoney } from '../utils/helpers'
import endpoints from '../api/endpoints'
import * as echarts from 'echarts'

const stats = ref({
  teams: 0,
  players: 0,
  matches: 0,
  seasons: 0,
  total_income: 0,
  total_expense: 0,
  balance: 0,
  players_by_position: {},
  finances_by_category: {}
})
const recentTeams = ref([])
const positionChartRef = ref(null)
const financeChartRef = ref(null)
let positionChart = null
let financeChart = null

async function loadStats() {
  try {
    const dashboardStats = await endpoints.getDashboardStats()
    stats.value = {
      ...dashboardStats,
      teams: dashboardStats.teams || 0,
      players: dashboardStats.players || 0,
      matches: dashboardStats.matches || 0,
      seasons: dashboardStats.seasons || 0,
      total_income: dashboardStats.total_income || 0,
      total_expense: dashboardStats.total_expense || 0,
      balance: dashboardStats.balance || 0,
      players_by_position: dashboardStats.players_by_position || {},
      finances_by_category: dashboardStats.finances_by_category || {}
    }
    updateCharts()
    const teams = await endpoints.getTeams()
    recentTeams.value = teams.slice(0, 5)
  } catch (e) {
    console.error('加载统计数据失败', e)
  }
}

function updateCharts() {
  nextTick(() => {
    if (positionChartRef.value) {
      if (!positionChart) {
        positionChart = echarts.init(positionChartRef.value)
      }
      const positionData = Object.entries(stats.value.players_by_position).map(([name, value]) => ({ name, value }))
      positionChart.setOption({
        tooltip: { trigger: 'item' },
        legend: { orient: 'vertical', left: 'left' },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
          label: { show: false },
          emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
          data: positionData.length > 0 ? positionData : [{ name: '暂无数据', value: 1 }],
          color: ['#67C23A', '#E6A23C', '#409EFF', '#F56C6C', '#909399']
        }]
      })
    }

    if (financeChartRef.value) {
      if (!financeChart) {
        financeChart = echarts.init(financeChartRef.value)
      }
      const income = stats.value.total_income || 0
      const expense = stats.value.total_expense || 0
      financeChart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        legend: { bottom: 0 },
        grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
        xAxis: { type: 'category', data: ['收入', '支出', '结余'] },
        yAxis: { type: 'value' },
        series: [{
          name: '金额',
          type: 'bar',
          data: [
            { value: income, itemStyle: { color: '#67C23A' } },
            { value: expense, itemStyle: { color: '#F56C6C' } },
            { value: stats.value.balance, itemStyle: { color: stats.value.balance >= 0 ? '#409EFF' : '#F56C6C' } }
          ],
          barWidth: '50%',
          label: { show: true, position: 'top', formatter: (params) => formatMoney(params.value) }
        }]
      })
    }
  })
}

function handleResize() {
  positionChart?.resize()
  financeChart?.resize()
}

onMounted(async () => {
  await loadStats()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  positionChart?.dispose()
  financeChart?.dispose()
})
</script>

<style scoped>
.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-primary);
}

.stat-card {
  text-align: center;
  padding: 30px 20px;
}

@media (max-width: 768px) {
  .stat-card {
    padding: 20px 10px;
  }
}

.stat-value {
  font-size: 48px;
  font-weight: 700;
  margin: 16px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

@media (max-width: 768px) {
  .stat-value {
    font-size: 32px;
  }
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.el-icon {
  margin-bottom: 8px;
}
</style>
