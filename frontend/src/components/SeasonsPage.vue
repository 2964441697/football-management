<template>
  <DataTable
    :data="seasons"
    :loading="loading"
    :total="total"
    :current-page="currentPage"
    :page-size="pageSize"
    add-text="新增赛季"
    search-placeholder="搜索赛季名称..."
    empty-text="暂无赛季数据"
    empty-hint="点击上方&quot;新增赛季&quot;按钮添加第一个赛季"
    :show-export="true"
    @add="handleAdd"
    @refresh="loadSeasons"
    @export="handleExport"
    @batch-delete="handleBatchDelete"
    @reset-id="handleResetId"
    @search="handleSearch"
    @page-change="handlePageChange"
    @size-change="handleSizeChange"
  >
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column prop="name" label="赛季名称" />
    <el-table-column label="开始日期" width="120">
      <template #default="{ row }">
        {{ formatDate(row.start_date) }}
      </template>
    </el-table-column>
    <el-table-column label="结束日期" width="120">
      <template #default="{ row }">
        {{ formatDate(row.end_date) }}
      </template>
    </el-table-column>
    <el-table-column label="持续天数" width="120">
      <template #default="{ row }">
        {{ getDuration(row.start_date, row.end_date) }}
      </template>
    </el-table-column>
    <el-table-column label="操作" width="150" align="center">
      <template #default="{ row }">
        <el-button link type="primary" size="small" @click="editSeason(row)">编辑</el-button>
        <el-button link type="danger" size="small" @click="deleteSeason(row.id)">删除</el-button>
      </template>
    </el-table-column>

    <template #dialogs>
      <el-dialog :title="editingSeason ? '编辑赛季' : '新增赛季'" v-model="showAddForm" width="500px">
        <el-form :model="formData" label-width="100px" :rules="rules" ref="formRef">
          <el-form-item label="赛季名称" prop="name">
            <el-input v-model="formData.name" placeholder="输入赛季名称，如 2024-2025" />
          </el-form-item>
          <el-form-item label="开始日期" prop="start_date">
            <el-date-picker
              v-model="formData.start_date"
              type="date"
              placeholder="选择开始日期"
              style="width: 100%;"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
          <el-form-item label="结束日期" prop="end_date">
            <el-date-picker
              v-model="formData.end_date"
              type="date"
              placeholder="选择结束日期"
              style="width: 100%;"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAddForm = false">取消</el-button>
          <el-button type="primary" @click="saveSeason">保存</el-button>
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

const seasons = ref([])
const searchName = ref('')
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const showAddForm = ref(false)
const editingSeason = ref(null)
const formRef = ref(null)

const formData = ref({
  name: '',
  start_date: '',
  end_date: ''
})

const rules = {
  name: [
    { required: true, message: '请输入赛季名称', trigger: 'blur' },
    { min: 4, max: 50, message: '长度在 4 到 50 个字符', trigger: 'blur' }
  ],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [
    { required: true, message: '请选择结束日期', trigger: 'change' },
    {
      validator: (rule, value, callback) => {
        if (formData.value.start_date && value) {
          const startDate = new Date(formData.value.start_date)
          const endDate = new Date(value)
          if (endDate <= startDate) {
            callback(new Error('结束日期必须大于开始日期'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

const filteredSeasons = computed(() => {
  let result = seasons.value || []

  if (searchName.value) {
    result = result.filter(s => s.name.includes(searchName.value))
  }

  total.value = result.length

  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return result.slice(start, end)
})

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

function getDuration(startDate, endDate) {
  if (!startDate || !endDate) return '-'
  const start = new Date(startDate)
  const end = new Date(endDate)
  const days = Math.floor((end - start) / (1000 * 60 * 60 * 24))
  return `${days} 天`
}

async function loadSeasons() {
  loading.value = true
  try {
    seasons.value = await endpoints.getSeasons()
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  showAddForm.value = true
  editingSeason.value = null
  formData.value = {
    name: '',
    start_date: '',
    end_date: ''
  }
}

function handleSearch(query) {
  searchName.value = query
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
  const selectedData = seasons.value.filter(s => selected.includes(s.id))
  exportToCSV(selectedData, '赛季数据')
  ElMessage.success('导出成功')
}

async function handleBatchDelete(selected) {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selected.length} 个赛季吗?`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await Promise.all(selected.map(id => endpoints.deleteSeason(id)))
    ElMessage.success('批量删除成功')
    await loadSeasons()
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

    await endpoints.resetSeasonIds()
    ElMessage.success('ID重置成功')
    await loadSeasons()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('重置失败')
    }
  }
}

function editSeason(season) {
  editingSeason.value = season
  formData.value = { ...season }
  showAddForm.value = true
}

async function saveSeason() {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    if (editingSeason.value) {
      await endpoints.updateSeason(editingSeason.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      await endpoints.createSeason(formData.value)
      ElMessage.success('创建成功')
    }
    showAddForm.value = false
    editingSeason.value = null
    await loadSeasons()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('保存失败')
    }
  }
}

async function deleteSeason(id) {
  try {
    await ElMessageBox.confirm('确定删除该赛季吗?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await endpoints.deleteSeason(id)
    ElMessage.success('删除成功')
    await loadSeasons()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadSeasons()
})
</script>

<style scoped>
</style>
