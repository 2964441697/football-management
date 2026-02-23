<template>
  <DataTable
    :data="transfers"
    :loading="loading"
    :total="total"
    :current-page="currentPage"
    :page-size="pageSize"
    :filters="filters"
    add-text="新增转会"
    search-placeholder="搜索球员名称..."
    empty-text="暂无转会数据"
    empty-hint="点击上方&quot;新增转会&quot;按钮添加第一条转会记录"
    @add="handleAdd"
    @refresh="loadTransfers"
    @export="handleExport"
    @batch-delete="handleBatchDelete"
    @reset-id="handleResetId"
    @search="handleSearch"
    @filter-change="handleFilterChange"
    @page-change="handlePageChange"
    @size-change="handleSizeChange"
  >
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column label="球员" width="150">
      <template #default="{ row }">
        {{ row.player_name || '未知' }}
      </template>
    </el-table-column>
    <el-table-column label="从球队" width="150">
      <template #default="{ row }">
        {{ row.from_team_name || '自由转会' }}
      </template>
    </el-table-column>
    <el-table-column label="到球队" width="150">
      <template #default="{ row }">
        {{ row.to_team_name || '未知' }}
      </template>
    </el-table-column>
    <el-table-column label="转会费" width="120">
      <template #default="{ row }">
        {{ formatMoney(row.fee) }}
      </template>
    </el-table-column>
    <el-table-column label="转会日期" width="120">
      <template #default="{ row }">
        {{ formatDate(row.transfer_date) }}
      </template>
    </el-table-column>
    <el-table-column label="操作" width="150" align="center">
      <template #default="{ row }">
        <el-button link type="primary" size="small" @click="editTransfer(row)">编辑</el-button>
        <el-button link type="danger" size="small" @click="deleteTransfer(row.id)">删除</el-button>
      </template>
    </el-table-column>

    <template #dialogs>
      <el-dialog :title="editingTransfer ? '编辑转会' : '新增转会'" v-model="showAddForm" width="600px">
        <el-form :model="formData" label-width="120px" :rules="rules" ref="formRef">
          <el-form-item label="球员" prop="player_id">
            <el-select v-model="formData.player_id" placeholder="选择球员" style="width: 100%;" filterable>
              <el-option
                v-for="player in players"
                :key="player.id"
                :label="`${player.name} (${player.position})`"
                :value="player.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="从球队" prop="from_team_id">
            <el-select v-model="formData.from_team_id" placeholder="选择原球队" style="width: 100%;" clearable>
              <el-option
                v-for="team in teams"
                :key="team.id"
                :label="team.name"
                :value="team.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="到球队" prop="to_team_id">
            <el-select v-model="formData.to_team_id" placeholder="选择转入球队" style="width: 100%;">
              <el-option
                v-for="team in teams"
                :key="team.id"
                :label="team.name"
                :value="team.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="转会费" prop="fee">
            <el-input-number v-model="formData.fee" :min="0" :precision="2" style="width: 100%;" />
          </el-form-item>
          <el-form-item label="转会日期" prop="transfer_date">
            <el-date-picker
              v-model="formData.transfer_date"
              type="date"
              placeholder="选择转会日期"
              style="width: 100%;"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAddForm = false">取消</el-button>
          <el-button type="primary" @click="saveTransfer">保存</el-button>
        </template>
      </el-dialog>
    </template>
  </DataTable>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { exportToCSV } from '../utils/helpers'
import endpoints from '../api/endpoints'
import { DataTable } from './common'

const transfers = ref([])
const teams = ref([])
const players = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchPlayer = ref('')
const filterToTeam = ref('')

const filters = computed(() => [
  {
    key: 'to_team',
    placeholder: '筛选转入球队',
    options: teams.value.map(t => ({ label: t.name, value: t.id }))
  }
])

const showAddForm = ref(false)
const editingTransfer = ref(null)
const formRef = ref(null)

const formData = ref({
  player_id: null,
  from_team_id: null,
  to_team_id: null,
  fee: 0,
  transfer_date: ''
})

const rules = {
  player_id: [{ required: true, message: '请选择球员', trigger: 'change' }],
  to_team_id: [{ required: true, message: '请选择转入球队', trigger: 'change' }],
  fee: [
    { required: true, message: '请输入转会费', trigger: 'blur' },
    { type: 'number', min: 0, message: '转会费不能为负数', trigger: 'blur' }
  ],
  transfer_date: [{ required: true, message: '请选择转会日期', trigger: 'change' }]
}

const filteredTransfers = computed(() => {
  let result = transfers.value || []

  if (searchPlayer.value) {
    result = result.filter(t => {
      const player = players.value.find(p => p.id === t.player_id)
      return player && player.name.includes(searchPlayer.value)
    })
  }

  if (filterToTeam.value) {
    result = result.filter(t => t.to_team_id === filterToTeam.value)
  }

  total.value = result.length

  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return result.slice(start, end)
})

function getPlayerName(playerId) {
  const player = players.value.find(p => p.id === playerId)
  return player ? player.name : '未知'
}

function getTeamName(teamId) {
  const team = teams.value.find(t => t.id === teamId)
  return team ? team.name : '自由转会'
}

function formatMoney(amount) {
  if (amount === null || amount === undefined) return '-'
  return `¥${Number(amount).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

async function loadTransfers() {
  loading.value = true
  try {
    transfers.value = await endpoints.getTransfers()
  } catch (e) {
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

async function loadPlayers() {
  try {
    players.value = await endpoints.getPlayers()
  } catch (e) {
    console.error('加载球员列表失败', e)
  }
}

function handleAdd() {
  showAddForm.value = true
  editingTransfer.value = null
  formData.value = {
    player_id: null,
    from_team_id: null,
    to_team_id: null,
    fee: 0,
    transfer_date: ''
  }
}

function handleSearch(query) {
  searchPlayer.value = query
  currentPage.value = 1
}

function handleFilterChange({ key, value }) {
  if (key === 'to_team') filterToTeam.value = value
  currentPage.value = 1
}

function handlePageChange(page) {
  currentPage.value = page
}

function handleSizeChange(size) {
  currentPage.value = 1
  pageSize.value = size
}

async function handleExport(selected) {
  const selectedData = transfers.value.filter(t => selected.includes(t.id))
  exportToCSV(selectedData, '转会数据')
  ElMessage.success('导出成功')
}

async function handleBatchDelete(selected) {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selected.length} 条转会记录吗?`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await Promise.all(selected.map(id => endpoints.deleteTransfer(id)))
    ElMessage.success('批量删除成功')
    await loadTransfers()
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

    await endpoints.resetTransferIds()
    ElMessage.success('ID重置成功')
    await loadTransfers()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('重置失败')
    }
  }
}

function editTransfer(transfer) {
  editingTransfer.value = transfer
  formData.value = { ...transfer }
  showAddForm.value = true
}

async function saveTransfer() {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    if (editingTransfer.value) {
      await endpoints.updateTransfer(editingTransfer.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      await endpoints.createTransfer(formData.value)
      ElMessage.success('创建成功')
    }
    showAddForm.value = false
    editingTransfer.value = null
    await loadTransfers()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('保存失败')
    }
  }
}

async function deleteTransfer(id) {
  try {
    await ElMessageBox.confirm('确定删除该转会记录吗?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await endpoints.deleteTransfer(id)
    ElMessage.success('删除成功')
    await loadTransfers()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

watch(() => formData.value.player_id, (newPlayerId) => {
  if (newPlayerId) {
    const player = players.value.find(p => p.id === newPlayerId)
    if (player && player.team_id) {
      formData.value.from_team_id = player.team_id
    }
  }
})

onMounted(async () => {
  await Promise.all([loadTransfers(), loadTeams(), loadPlayers()])
})
</script>

<style scoped>
</style>
