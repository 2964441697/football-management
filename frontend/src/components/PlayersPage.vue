<template>
  <DataTable
    :data="players"
    :loading="loading"
    :total="total"
    :current-page="currentPage"
    :page-size="pageSize"
    :filters="filters"
    add-text="新增球员"
    search-placeholder="搜索球员名称..."
    empty-text="暂无球员数据"
    empty-hint="点击上方&quot;新增球员&quot;按钮添加第一个球员"
    @add="handleAdd"
    @refresh="loadPlayers"
    @export="handleExport"
    @batch-delete="handleBatchDelete"
    @reset-id="handleResetId"
    @search="handleSearch"
    @filter-change="handleFilterChange"
    @page-change="handlePageChange"
    @size-change="handleSizeChange"
  >
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column label="头像" width="80" align="center">
      <template #default="{ row }">
        <el-avatar :size="40" :src="row.avatar" v-lazy-load="getAvatarUrl(row.avatar)">
          <el-icon :size="24"><User /></el-icon>
        </el-avatar>
      </template>
    </el-table-column>
    <el-table-column prop="name" label="球员名称" />
    <el-table-column prop="age" label="年龄" width="80" />
    <el-table-column prop="nationality" label="国籍" width="120" />
    <el-table-column prop="position" label="位置" width="100">
      <template #default="{ row }">
        <el-tag :type="getPositionTagType(row.position)" size="small">{{ row.position }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="height_cm" label="身高" width="100" />
    <el-table-column prop="team_id" label="所属球队" width="120">
      <template #default="{ row }">
        {{ row.team_name || '未分配' }}
      </template>
    </el-table-column>
    <el-table-column label="操作" width="200" align="center">
      <template #default="{ row }">
        <el-button link type="primary" size="small" @click="editPlayer(row)">编辑</el-button>
        <el-button link type="info" size="small" @click="viewStats(row)">统计</el-button>
        <el-button link type="danger" size="small" @click="deletePlayer(row.id)">删除</el-button>
      </template>
    </el-table-column>

    <template #dialogs>
      <el-dialog :title="editingPlayer ? '编辑球员' : '新增球员'" v-model="showAddForm" width="550px" @close="resetForm">
        <div style="text-align: center; margin-bottom: 20px;">
          <el-avatar :size="80" :src="getAvatarUrl(formData.avatar)">
            <el-icon :size="40"><User /></el-icon>
          </el-avatar>
          <div style="margin-top: 10px;">
            <el-upload
              :show-file-list="false"
              :auto-upload="false"
              :on-change="handleAvatarChange"
            >
              <el-button type="primary" size="small">{{ editingPlayer ? '更换头像' : '上传头像' }}</el-button>
            </el-upload>
          </div>
        </div>
        <el-form :model="formData" label-width="100px" :rules="rules" ref="formRef">
          <el-form-item label="球员名称" prop="name">
            <el-input v-model="formData.name" placeholder="输入球员名称" />
          </el-form-item>
          <el-form-item label="年龄" prop="age">
            <el-input-number v-model="formData.age" :min="16" :max="50" />
          </el-form-item>
          <el-form-item label="国籍" prop="nationality">
            <el-input v-model="formData.nationality" placeholder="输入国籍" />
          </el-form-item>
          <el-form-item label="位置" prop="position">
            <el-select v-model="formData.position" placeholder="选择位置" style="width: 100%;">
              <el-option label="门将" value="门将" />
              <el-option label="后卫" value="后卫" />
              <el-option label="中场" value="中场" />
              <el-option label="前锋" value="前锋" />
            </el-select>
          </el-form-item>
          <el-form-item label="身高" prop="height_cm">
            <el-input-number v-model="formData.height_cm" :min="150" :max="220" />
          </el-form-item>
          <el-form-item label="所属球队" prop="team_id">
            <el-select v-model="formData.team_id" placeholder="选择球队" style="width: 100%;" clearable>
              <el-option
                v-for="team in teams"
                :key="team.id"
                :label="team.name"
                :value="team.id"
              />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAddForm = false">取消</el-button>
          <el-button type="primary" @click="savePlayer" :loading="saving">保存</el-button>
        </template>
      </el-dialog>

      <el-dialog title="球员统计" v-model="showStatsDialog" width="600px">
        <el-table :data="playerStats" stripe style="width: 100%">
          <el-table-column prop="season_id" label="赛季" width="80" />
          <el-table-column prop="matches_played" label="出场" width="80" />
          <el-table-column prop="goals" label="进球" width="80" />
          <el-table-column prop="assists" label="助攻" width="80" />
          <el-table-column prop="yellow_cards" label="黄牌" width="80" />
          <el-table-column prop="red_cards" label="红牌" width="80" />
          <el-table-column prop="minutes_played" label="分钟" />
        </el-table>
        <template #footer>
          <el-button @click="showStatsDialog = false">关闭</el-button>
        </template>
      </el-dialog>
    </template>
  </DataTable>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { exportToCSV } from '../utils/helpers'
import endpoints from '../api/endpoints'
import { DataTable } from './common'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000'

const players = ref([])
const teams = ref([])
const loading = ref(false)
const saving = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchName = ref('')
const filterPosition = ref('')
const filterTeam = ref('')

const filters = computed(() => [
  {
    key: 'position',
    placeholder: '筛选位置',
    options: [
      { label: '门将', value: '门将' },
      { label: '后卫', value: '后卫' },
      { label: '中场', value: '中场' },
      { label: '前锋', value: '前锋' }
    ]
  },
  {
    key: 'team',
    placeholder: '筛选球队',
    options: teams.value.map(t => ({ label: t.name, value: t.id }))
  }
])

const showAddForm = ref(false)
const editingPlayer = ref(null)
const formRef = ref(null)
const avatarFile = ref(null)
const showStatsDialog = ref(false)
const playerStats = ref([])

const formData = ref({
  name: '',
  age: 25,
  nationality: '',
  position: '',
  height_cm: 180,
  avatar: '',
  team_id: null
})

const rules = {
  name: [{ required: true, message: '请输入球员名称', trigger: 'blur' }],
  age: [{ required: true, message: '请输入年龄', trigger: 'blur' }],
  position: [{ required: true, message: '请选择位置', trigger: 'change' }],
  height_cm: [{ required: true, message: '请输入身高', trigger: 'blur' }]
}

function getAvatarUrl(avatar) {
  if (!avatar) return ''
  return avatar.startsWith('http') ? avatar : `${BACKEND_URL}${avatar}`
}

function getPositionTagType(position) {
  const typeMap = {
    '门将': 'danger',
    '后卫': 'warning',
    '中场': 'success',
    '前锋': ''
  }
  return typeMap[position] || 'info'
}

async function loadPlayers() {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value
    }

    if (searchName.value) params.name = searchName.value
    if (filterPosition.value) params.position = filterPosition.value
    if (filterTeam.value) params.team_id = filterTeam.value

    const response = await endpoints.getPlayersPaginated(params)

    if (response && response.items) {
      players.value = response.items
      total.value = response.pagination?.total || response.items.length
    } else if (Array.isArray(response)) {
      players.value = response
      total.value = response.length
    } else {
      players.value = []
      total.value = 0
    }
  } catch (e) {
    console.error('加载球员失败:', e)
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function loadTeams() {
  try {
    teams.value = await endpoints.getTeams()
  } catch (e) {
    console.error('加载球队列表失败', e)
  }
}

function handleAdd() {
  showAddForm.value = true
  editingPlayer.value = null
  formData.value = {
    name: '',
    age: 25,
    nationality: '',
    position: '',
    height_cm: 180,
    avatar: '',
    team_id: null
  }
}

function handleSearch(query) {
  searchName.value = query
  currentPage.value = 1
  loadPlayers()
}

function handleFilterChange({ key, value }) {
  if (key === 'position') filterPosition.value = value
  if (key === 'team') filterTeam.value = value
  currentPage.value = 1
  loadPlayers()
}

function handlePageChange(page) {
  currentPage.value = page
  loadPlayers()
}

function handleSizeChange(size) {
  currentPage.value = 1
  pageSize.value = size
  loadPlayers()
}

async function handleExport(selected) {
  const selectedData = players.value.filter(p => selected.includes(p.id))
  exportToCSV(selectedData, '球员数据')
  ElMessage.success('导出成功')
}

async function handleBatchDelete(selected) {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selected.length} 个球员吗?`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await endpoints.batchDeletePlayers(selected)
    ElMessage.success('批量删除成功')
    await loadPlayers()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

async function handleResetId() {
  try {
    await ElMessageBox.confirm('重置ID会重新编号所有数据，确定继续吗?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await endpoints.resetPlayerIds()
    ElMessage.success('ID重置成功')
    await loadPlayers()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('重置失败: ' + (e.data?.error || e.message || '未知错误'))
    }
  }
}

function handleAvatarChange(file) {
  const isImage = file.raw.type.startsWith('image/')
  const isLt2M = file.raw.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过2MB!')
    return
  }

  avatarFile.value = file.raw
  const reader = new FileReader()
  reader.onload = (e) => {
    formData.value.avatar = e.target.result
  }
  reader.readAsDataURL(file.raw)
}

async function uploadPlayerAvatar(playerId) {
  if (!avatarFile.value) return

  const fd = new FormData()
  fd.append('avatar', avatarFile.value)

  if (playerId) {
    fd.append('id', playerId)
  }

  await endpoints.uploadPlayerAvatar(fd)
}

async function viewStats(player) {
  try {
    playerStats.value = await endpoints.getPlayerStats(player.id)
    showStatsDialog.value = true
  } catch (e) {
    ElMessage.error('加载统计失败')
  }
}

function editPlayer(player) {
  editingPlayer.value = player
  formData.value = { ...player }
  avatarFile.value = null
  showAddForm.value = true
}

function resetForm() {
  editingPlayer.value = null
  avatarFile.value = null
  formData.value = {
    name: '',
    age: 25,
    nationality: '',
    position: '',
    height_cm: 180,
    avatar: '',
    team_id: null
  }
}

async function savePlayer() {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    saving.value = true

    if (editingPlayer.value) {
      const updateData = { ...formData.value }
      if (!avatarFile.value && editingPlayer.value.avatar) {
        delete updateData.avatar
      }
      await endpoints.updatePlayer(editingPlayer.value.id, updateData)
      if (avatarFile.value) {
        await uploadPlayerAvatar(editingPlayer.value.id)
      }
      ElMessage.success('更新成功')
    } else {
      const res = await endpoints.createPlayer(formData.value)
      const newPlayerId = res?.id
      if (avatarFile.value && newPlayerId) {
        await uploadPlayerAvatar(newPlayerId)
      }
      ElMessage.success('创建成功')
    }

    showAddForm.value = false
    resetForm()
    await loadPlayers()
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.data?.error || e.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

async function deletePlayer(id) {
  try {
    await ElMessageBox.confirm('确定删除该球员吗?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await endpoints.deletePlayer(id)
    ElMessage.success('删除成功')
    await loadPlayers()
  } catch (e) {
    if (e !== 'cancel') {
      const errorMsg = e.data?.error || e.message || '未知错误'
      console.error('删除球员失败:', e)
      ElMessage.error('删除失败: ' + errorMsg)
    }
  }
}

onMounted(async () => {
  await Promise.all([loadPlayers(), loadTeams()])
})
</script>

<style scoped>
</style>
