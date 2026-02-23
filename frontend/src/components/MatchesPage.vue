<template>
  <DataTable
    :data="matches"
    :loading="loading"
    :total="total"
    :current-page="currentPage"
    :page-size="pageSize"
    :filters="filters"
    add-text="新增比赛"
    search-placeholder="搜索场地..."
    empty-text="暂无比赛数据"
    empty-hint="点击上方&quot;新增比赛&quot;按钮添加第一场比赛"
    @add="handleAdd"
    @refresh="loadMatches"
    @export="handleExport"
    @batch-delete="handleBatchDelete"
    @reset-id="handleResetId"
    @search="handleSearch"
    @filter-change="handleFilterChange"
    @page-change="handlePageChange"
    @size-change="handleSizeChange"
  >
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column label="赛季" width="150">
      <template #default="{ row }">
        {{ row.season_name || '未知' }}
      </template>
    </el-table-column>
    <el-table-column label="主队" width="150">
      <template #default="{ row }">
        {{ row.home_team_name || '未知' }}
      </template>
    </el-table-column>
    <el-table-column label="客队" width="150">
      <template #default="{ row }">
        {{ row.away_team_name || '未知' }}
      </template>
    </el-table-column>
    <el-table-column label="开始时间" width="180">
      <template #default="{ row }">
        {{ formatDateTime(row.start_time) }}
      </template>
    </el-table-column>
    <el-table-column prop="venue" label="场地" />
    <el-table-column label="操作" width="150" align="center">
      <template #default="{ row }">
        <el-button link type="primary" size="small" @click="editMatch(row)">编辑</el-button>
        <el-button link type="danger" size="small" @click="deleteMatch(row.id)">删除</el-button>
      </template>
    </el-table-column>

    <template #dialogs>
      <el-dialog :title="editingMatch ? '编辑比赛' : '新增比赛'" v-model="showAddForm" width="600px">
        <el-form :model="formData" label-width="100px" :rules="rules" ref="formRef">
          <el-form-item label="赛季" prop="season_id">
            <el-select v-model="formData.season_id" placeholder="选择赛季" style="width: 100%;">
              <el-option
                v-for="season in seasons"
                :key="season.id"
                :label="season.name"
                :value="season.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="主队" prop="home_team_id">
            <el-select v-model="formData.home_team_id" placeholder="选择主队" style="width: 100%;">
              <el-option
                v-for="team in teams"
                :key="team.id"
                :label="team.name"
                :value="team.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="客队" prop="away_team_id">
            <el-select v-model="formData.away_team_id" placeholder="选择客队" style="width: 100%;">
              <el-option
                v-for="team in teams"
                :key="team.id"
                :label="team.name"
                :value="team.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="开始时间" prop="start_time">
            <el-date-picker
              v-model="formData.start_time"
              type="datetime"
              placeholder="选择日期时间"
              style="width: 100%;"
              value-format="YYYY-MM-DDTHH:mm:ss"
            />
          </el-form-item>
          <el-form-item label="场地" prop="venue">
            <el-input v-model="formData.venue" placeholder="输入场地" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAddForm = false">取消</el-button>
          <el-button type="primary" @click="saveMatch">保存</el-button>
        </template>
      </el-dialog>
    </template>
  </DataTable>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { exportToCSV } from '../utils/helpers'
import endpoints from '../api/endpoints'
import { DataTable } from './common'

const matches = ref([])
const teams = ref([])
const seasons = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchVenue = ref('')
const filterSeason = ref('')

const filters = computed(() => [
  {
    key: 'season',
    placeholder: '筛选赛季',
    options: seasons.value.map(s => ({ label: s.name, value: s.id }))
  }
])

const showAddForm = ref(false)
const editingMatch = ref(null)
const formRef = ref(null)

const formData = ref({
  season_id: null,
  home_team_id: null,
  away_team_id: null,
  start_time: '',
  venue: ''
})

const rules = {
  season_id: [{ required: true, message: '请选择赛季', trigger: 'change' }],
  home_team_id: [{ required: true, message: '请选择主队', trigger: 'change' }],
  away_team_id: [{ required: true, message: '请选择客队', trigger: 'change' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  venue: [
    { required: true, message: '请输入场地', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

function formatDateTime(dateTime) {
  if (!dateTime) return ''
  const date = new Date(dateTime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function loadMatches() {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value
    }

    if (filterSeason.value) {
      params.season_id = filterSeason.value
    }
    if (searchVenue.value) {
      params.venue = searchVenue.value
    }

    const result = await endpoints.getMatchesPaginated(params)

    if (result.items !== undefined) {
      matches.value = result.items
      total.value = result.total
    } else {
      matches.value = result
      total.value = result.length
    }
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

async function loadSeasons() {
  try {
    seasons.value = await endpoints.getSeasons()
  } catch (e) {
    console.error('加载赛季列表失败', e)
  }
}

function handleAdd() {
  showAddForm.value = true
  editingMatch.value = null
  formData.value = {
    season_id: null,
    home_team_id: null,
    away_team_id: null,
    start_time: '',
    venue: ''
  }
}

function handleSearch(query) {
  searchVenue.value = query
  currentPage.value = 1
  loadMatches()
}

function handleFilterChange({ key, value }) {
  if (key === 'season') filterSeason.value = value
  currentPage.value = 1
  loadMatches()
}

function handlePageChange(page) {
  currentPage.value = page
  loadMatches()
}

function handleSizeChange(size) {
  currentPage.value = 1
  pageSize.value = size
  loadMatches()
}

async function handleExport(selected) {
  const selectedData = matches.value.filter(m => selected.includes(m.id))
  exportToCSV(selectedData, '比赛数据')
  ElMessage.success('导出成功')
}

async function handleBatchDelete(selected) {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selected.length} 场比赛吗?`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await Promise.all(selected.map(id => endpoints.deleteMatch(id)))
    ElMessage.success('批量删除成功')
    await loadMatches()
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

    await endpoints.resetMatchIds()
    ElMessage.success('ID重置成功')
    await loadMatches()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('重置失败')
    }
  }
}

function editMatch(match) {
  editingMatch.value = match
  formData.value = { ...match }
  showAddForm.value = true
}

async function saveMatch() {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    if (editingMatch.value) {
      await endpoints.updateMatch(editingMatch.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      await endpoints.createMatch(formData.value)
      ElMessage.success('创建成功')
    }
    showAddForm.value = false
    editingMatch.value = null
    await loadMatches()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('保存失败')
    }
  }
}

async function deleteMatch(id) {
  try {
    await ElMessageBox.confirm('确定删除该比赛吗?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await endpoints.deleteMatch(id)
    ElMessage.success('删除成功')
    await loadMatches()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(async () => {
  await Promise.all([loadMatches(), loadTeams(), loadSeasons()])
})
</script>

<style scoped>
</style>
