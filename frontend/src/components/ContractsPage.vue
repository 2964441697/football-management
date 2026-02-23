<template>
  <div>
    <div style="margin-bottom: 20px; display: flex; gap: 10px; align-items: center;">
      <el-button type="primary" @click="showAddForm = true">+ 新增合同</el-button>
      <el-button @click="loadContracts">刷新</el-button>
      <el-button type="warning" @click="resetIds" :disabled="contracts.length === 0">重置ID</el-button>
      <el-button type="warning" @click="loadExpiring">即将到期</el-button>
      <el-select v-model="selectedTeamId" placeholder="筛选球队" clearable style="width: 200px;" @change="loadContracts">
        <el-option
          v-for="team in teams"
          :key="team.id"
          :label="team.name"
          :value="team.id"
        />
      </el-select>
    </div>

    <div v-if="loading" v-loading="true" style="min-height: 400px;"></div>
    <div v-else-if="filteredContracts.length === 0" class="empty-state">
      <el-icon :size="64" color="#C0C4CC"><FolderOpened /></el-icon>
      <div class="empty-state-text">暂无合同</div>
      <div class="empty-state-hint">点击上方"新增合同"按钮添加第一个合同</div>
    </div>
    <el-table v-else :data="filteredContracts" stripe style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="球员" width="150">
        <template #default="{ row }">
          {{ row.player_name || '未知' }}
        </template>
      </el-table-column>
      <el-table-column label="球队" width="150">
        <template #default="{ row }">
          {{ row.team_name || '未知' }}
        </template>
      </el-table-column>
      <el-table-column prop="start_date" label="开始日期" width="120" />
      <el-table-column prop="end_date" label="结束日期" width="120">
        <template #default="{ row }">
          <span :style="{ color: isExpiringSoon(row.end_date) ? '#F56C6C' : 'inherit' }">
            {{ row.end_date }}
          </span>
          <el-tag v-if="isExpiringSoon(row.end_date)" type="warning" size="small" style="margin-left: 5px;">即将到期</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="salary" label="年薪" width="120">
        <template #default="{ row }">
          ¥{{ (row.salary || 0).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column prop="release_clause" label="违约金" width="120">
        <template #default="{ row }">
          {{ row.release_clause ? `¥${row.release_clause.toLocaleString()}` : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="editContract(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="deleteContract(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[10, 20, 50, 100]"
      :total="total"
      layout="total, sizes, prev, pager, next, jumper"
      style="margin-top: 20px; justify-content: flex-end;"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />

    <el-dialog :title="editingContract ? '编辑合同' : '新增合同'" v-model="showAddForm" width="550px">
      <el-form :model="formData" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="球员" prop="player_id">
          <el-select v-model="formData.player_id" placeholder="选择球员" style="width: 100%;" filterable>
            <el-option
              v-for="player in players"
              :key="player.id"
              :label="player.name"
              :value="player.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="球队" prop="team_id">
          <el-select v-model="formData.team_id" placeholder="选择球队" style="width: 100%;">
            <el-option
              v-for="team in teams"
              :key="team.id"
              :label="team.name"
              :value="team.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker v-model="formData.start_date" type="date" placeholder="选择开始日期" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="结束日期" prop="end_date">
          <el-date-picker v-model="formData.end_date" type="date" placeholder="选择结束日期" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="年薪" prop="salary">
          <el-input-number v-model="formData.salary" :min="0" :precision="2" :step="100000" />
        </el-form-item>
        <el-form-item label="违约金" prop="release_clause">
          <el-input-number v-model="formData.release_clause" :min="0" :precision="2" :step="1000000" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddForm = false">取消</el-button>
        <el-button type="primary" @click="saveContract">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { FolderOpened } from '@element-plus/icons-vue'
import { debounce } from '../utils/helpers'
import endpoints from '../api/endpoints'

const contracts = ref([])
const players = ref([])
const teams = ref([])
const selectedTeamId = ref(null)
const loading = ref(false)
const showAddForm = ref(false)
const editingContract = ref(null)
const formRef = ref(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const formData = ref({
  player_id: null,
  team_id: null,
  start_date: new Date(),
  end_date: new Date(new Date().setFullYear(new Date().getFullYear() + 1)),
  salary: 0,
  release_clause: null
})

const rules = {
  player_id: [{ required: true, message: '请选择球员', trigger: 'change' }],
  team_id: [{ required: true, message: '请选择球队', trigger: 'change' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }]
}

const filteredContracts = computed(() => {
  const contractsArray = contracts.value || []
  total.value = contractsArray.length
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return contractsArray.slice(start, end)
})

function isExpiringSoon(dateStr) {
  if (!dateStr) return false
  const endDate = new Date(dateStr)
  const now = new Date()
  const thirtyDaysLater = new Date(now.setDate(now.getDate() + 30))
  return endDate <= thirtyDaysLater && endDate >= new Date()
}

function getPlayerName(playerId) {
  const player = players.value.find(p => p.id === playerId)
  return player ? player.name : '-'
}

function getTeamName(teamId) {
  const team = teams.value.find(t => t.id === teamId)
  return team ? team.name : '-'
}

async function loadContracts() {
  loading.value = true
  try {
    if (selectedTeamId.value) {
      const allContracts = await endpoints.getContracts()
      contracts.value = allContracts.filter(c => c.team_id === selectedTeamId.value)
    } else {
      contracts.value = await endpoints.getContracts()
    }
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function loadExpiring() {
  loading.value = true
  try {
    contracts.value = await endpoints.getExpiringContracts()
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function loadPlayersAndTeams() {
  try {
    const [playersData, teamsData] = await Promise.all([
      endpoints.getPlayers(),
      endpoints.getTeams()
    ])
    players.value = playersData
    teams.value = teamsData
  } catch (e) {
    console.error('加载数据失败', e)
  }
}

function handleSizeChange() {
  currentPage.value = 1
}

function handleCurrentChange() {}

function editContract(contract) {
  editingContract.value = contract
  formData.value = {
    ...contract,
    start_date: contract.start_date ? new Date(contract.start_date) : new Date(),
    end_date: contract.end_date ? new Date(contract.end_date) : new Date()
  }
  showAddForm.value = true
}

async function saveContract() {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    const data = {
      ...formData.value,
      start_date: formData.value.start_date ? formData.value.start_date.toISOString().split('T')[0] : null,
      end_date: formData.value.end_date ? formData.value.end_date.toISOString().split('T')[0] : null
    }

    if (editingContract.value) {
      await endpoints.updateContract(editingContract.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await endpoints.createContract(data)
      ElMessage.success('创建成功')
    }
    showAddForm.value = false
    editingContract.value = null
    formData.value = {
      player_id: null,
      team_id: null,
      start_date: new Date(),
      end_date: new Date(new Date().setFullYear(new Date().getFullYear() + 1)),
      salary: 0,
      release_clause: null
    }
    await loadContracts()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function deleteContract(id) {
  try {
    await ElMessageBox.confirm('确定删除该合同吗?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await endpoints.deleteContract(id)
    ElMessage.success('删除成功')
    await loadContracts()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function resetIds() {
  try {
    await ElMessageBox.confirm('重置ID会重新编号所有数据，确定继续吗?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await endpoints.resetContractIds()
    ElMessage.success('ID重置成功')
    await loadContracts()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('重置失败')
    }
  }
}

onMounted(async () => {
  await Promise.all([loadContracts(), loadPlayersAndTeams()])
})
</script>
