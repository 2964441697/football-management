<template>
  <DataTable
    :data="competitions"
    :loading="loading"
    :total="total"
    :current-page="currentPage"
    :page-size="pageSize"
    :filters="filters"
    add-text="新增赛事"
    search-placeholder="搜索赛事名称..."
    empty-text="暂无赛事数据"
    empty-hint="点击上方&quot;新增赛事&quot;按钮添加第一个赛事"
    :show-export="true"
    @add="handleAdd"
    @refresh="loadCompetitions"
    @export="handleExport"
    @batch-delete="handleBatchDelete"
    @reset-id="handleResetId"
    @search="handleSearch"
    @filter-change="handleFilterChange"
    @page-change="handlePageChange"
    @size-change="handleSizeChange"
  >
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column prop="name" label="赛事名称" />
    <el-table-column prop="type" label="类型" width="120">
      <template #default="{ row }">
        <el-tag :type="getTypeTagType(row.type)" size="small">{{ row.type }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="season_id" label="赛季" width="120">
      <template #default="{ row }">
        {{ getSeasonName(row.season_id) }}
      </template>
    </el-table-column>
    <el-table-column label="操作" width="150" align="center">
      <template #default="{ row }">
        <el-button link type="primary" size="small" @click="editCompetition(row)">编辑</el-button>
        <el-button link type="danger" size="small" @click="deleteCompetition(row.id)">删除</el-button>
      </template>
    </el-table-column>

    <template #dialogs>
      <el-dialog :title="editingCompetition ? '编辑赛事' : '新增赛事'" v-model="showAddForm" width="500px">
        <el-form :model="formData" label-width="100px" :rules="rules" ref="formRef">
          <el-form-item label="赛事名称" prop="name">
            <el-input v-model="formData.name" placeholder="输入赛事名称" />
          </el-form-item>
          <el-form-item label="类型" prop="type">
            <el-select v-model="formData.type" placeholder="选择类型" style="width: 100%;">
              <el-option label="联赛" value="联赛" />
              <el-option label="杯赛" value="杯赛" />
              <el-option label="锦标赛" value="锦标赛" />
              <el-option label="友谊赛" value="友谊赛" />
            </el-select>
          </el-form-item>
          <el-form-item label="赛季" prop="season_id">
            <el-select v-model="formData.season_id" placeholder="选择赛季" style="width: 100%;" clearable>
              <el-option
                v-for="season in seasons"
                :key="season.id"
                :label="season.name"
                :value="season.id"
              />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAddForm = false">取消</el-button>
          <el-button type="primary" @click="saveCompetition">保存</el-button>
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

const competitions = ref([])
const seasons = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchName = ref('')
const filterType = ref('')

const filters = computed(() => [
  {
    key: 'type',
    placeholder: '筛选类型',
    options: [
      { label: '联赛', value: '联赛' },
      { label: '杯赛', value: '杯赛' },
      { label: '锦标赛', value: '锦标赛' },
      { label: '友谊赛', value: '友谊赛' }
    ]
  }
])

const showAddForm = ref(false)
const editingCompetition = ref(null)
const formRef = ref(null)

const formData = ref({
  name: '',
  type: '联赛',
  season_id: null
})

const rules = {
  name: [
    { required: true, message: '请输入赛事名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

function getTypeTagType(type) {
  const typeMap = {
    '联赛': '',
    '杯赛': 'danger',
    '锦标赛': 'success',
    '友谊赛': 'warning'
  }
  return typeMap[type] || 'info'
}

function getSeasonName(seasonId) {
  const season = seasons.value.find(s => s.id === seasonId)
  return season ? season.name : '-'
}

async function loadCompetitions() {
  loading.value = true
  try {
    const competitionsData = await endpoints.getCompetitions()

    const result = competitionsData || []
    if (searchName.value) {
      result = result.filter(c => c.name.includes(searchName.value))
    }

    if (filterType.value) {
      result = result.filter(c => c.type === filterType.value)
    }

    total.value = result.length
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    competitions.value = result.slice(start, end)
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
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
  editingCompetition.value = null
  formData.value = {
    name: '',
    type: '联赛',
    season_id: null
  }
}

function handleSearch(query) {
  searchName.value = query
  currentPage.value = 1
  loadCompetitions()
}

function handleFilterChange({ key, value }) {
  if (key === 'type') filterType.value = value
  currentPage.value = 1
  loadCompetitions()
}

function handlePageChange(page) {
  currentPage.value = page
  loadCompetitions()
}

function handleSizeChange(size) {
  currentPage.value = 1
  pageSize.value = size
  loadCompetitions()
}

async function handleExport(selected) {
  const selectedData = competitions.value.filter(c => selected.includes(c.id))
  exportToCSV(selectedData, '赛事数据')
  ElMessage.success('导出成功')
}

async function handleBatchDelete(selected) {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selected.length} 个赛事吗?`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await Promise.all(selected.map(id => endpoints.deleteCompetition(id)))
    ElMessage.success('批量删除成功')
    await loadCompetitions()
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

    await endpoints.resetCompetitionIds()
    ElMessage.success('ID重置成功')
    await loadCompetitions()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('重置失败')
    }
  }
}

function editCompetition(competition) {
  editingCompetition.value = competition
  formData.value = { ...competition }
  showAddForm.value = true
}

async function saveCompetition() {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    if (editingCompetition.value) {
      await endpoints.updateCompetition(editingCompetition.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      await endpoints.createCompetition(formData.value)
      ElMessage.success('创建成功')
    }
    showAddForm.value = false
    editingCompetition.value = null
    await loadCompetitions()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('保存失败')
    }
  }
}

async function deleteCompetition(id) {
  try {
    await ElMessageBox.confirm('确定删除该赛事吗?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await endpoints.deleteCompetition(id)
    ElMessage.success('删除成功')
    await loadCompetitions()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(async () => {
  await Promise.all([loadCompetitions(), loadSeasons()])
})
</script>

<style scoped>
</style>
