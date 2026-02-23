<template>
  <div>
    <div style="margin-bottom: 20px; display: flex; gap: 10px; align-items: center;">
      <el-button type="primary" @click="showAddForm = true">+ 新增球队</el-button>
      <el-button @click="loadTeams">刷新</el-button>
      <el-button type="success" :disabled="selectedTeams.length === 0" @click="exportSelected">导出选中</el-button>
      <el-button type="danger" :disabled="selectedTeams.length === 0" @click="batchDelete">批量删除</el-button>
      <el-button type="warning" @click="resetIds" :disabled="total === 0">重置ID</el-button>
      <el-input v-model="searchName" placeholder="搜索球队名称..." style="width: 300px;" @input="handleSearch" clearable />
    </div>

    <div v-if="loading" v-loading="true" style="min-height: 400px;"></div>
    <EmptyState 
      v-else-if="teams.length === 0" 
      text="暂无球队数据"
      hint="点击上方&quot;新增球队&quot;按钮添加第一个球队"
    />
    <el-table v-else :data="teams" stripe style="width: 100%" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="球队名称" />
      <el-table-column prop="home_stadium" label="主场" />
      <el-table-column prop="founded_year" label="成立年份" width="100" />
      <el-table-column prop="budget" label="预算">
        <template #default="{ row }">
          {{ row.budget ? `¥${Number(row.budget).toLocaleString()}` : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" align="center">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="editTeam(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="deleteTeam(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Add/Edit Form Dialog -->
    <el-dialog :title="editingTeam ? '编辑球队' : '新增球队'" v-model="showAddForm" width="500px">
      <el-form :model="formData" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="球队名称" prop="name">
          <el-input v-model="formData.name" placeholder="输入球队名称" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="主场" prop="home_stadium">
          <el-input v-model="formData.home_stadium" placeholder="输入主场" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="成立年份" prop="founded_year">
          <el-input-number v-model="formData.founded_year" :min="1800" :max="new Date().getFullYear()" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="预算" prop="budget">
          <el-input-number v-model="formData.budget" :min="0" :precision="2" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddForm = false">取消</el-button>
        <el-button type="primary" @click="saveTeam">保存</el-button>
      </template>
    </el-dialog>

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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { debounce, exportToCSV } from '../utils/helpers'
import endpoints from '../api/endpoints'
import EmptyState from './common/EmptyState.vue'

const teams = ref([])
const searchName = ref('')
const loading = ref(false)
const showAddForm = ref(false)
const editingTeam = ref(null)
const formRef = ref(null)
const selectedTeams = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const formData = ref({
  name: '',
  home_stadium: '',
  founded_year: new Date().getFullYear(),
  budget: 0
})

const rules = {
  name: [
    { required: true, message: '请输入球队名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  home_stadium: [
    { required: true, message: '请输入主场', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  founded_year: [
    { required: true, message: '请选择成立年份', trigger: 'blur' },
    { type: 'number', min: 1800, max: new Date().getFullYear(), message: `年份范围 1800-${new Date().getFullYear()}`, trigger: 'blur' }
  ],
  budget: [
    { required: true, message: '请输入预算', trigger: 'blur' },
    { type: 'number', min: 0, message: '预算不能为负数', trigger: 'blur' }
  ]
}

// 使用后端分页加载数据
async function loadTeams() {
  loading.value = true
  try {
    const result = await endpoints.getTeamsPaginated({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchName.value
    })
    
    if (result.items !== undefined) {
      teams.value = result.items
      total.value = result.total
    } else {
      // 兼容旧格式
      teams.value = result
      total.value = result.length
    }
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

// 搜索防抖
const handleSearch = debounce(() => {
  currentPage.value = 1
  loadTeams()
}, 300)

function handleSizeChange() {
  currentPage.value = 1
  loadTeams()
}

function handleCurrentChange() {
  loadTeams()
}

function handleSelectionChange(selection) {
  selectedTeams.value = selection.map(row => row.id)
}

function exportSelected() {
  const selectedData = teams.value.filter(t => selectedTeams.value.includes(t.id))
  exportToCSV(selectedData, '球队数据')
  ElMessage.success('导出成功')
}

async function batchDelete() {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedTeams.value.length} 个球队吗?`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await Promise.all(selectedTeams.value.map(id => endpoints.deleteTeam(id)))
    ElMessage.success('批量删除成功')
    selectedTeams.value = []
    await loadTeams()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('批量删除失败')
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
    
    await endpoints.resetTeamIds()
    ElMessage.success('ID重置成功')
    await loadTeams()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('重置失败')
    }
  }
}

function editTeam(team) {
  editingTeam.value = team
  formData.value = { ...team }
  showAddForm.value = true
}

async function saveTeam() {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    if (editingTeam.value) {
      await endpoints.updateTeam(editingTeam.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      await endpoints.createTeam(formData.value)
      ElMessage.success('创建成功')
    }
    showAddForm.value = false
    editingTeam.value = null
    formData.value = { name: '', home_stadium: '', founded_year: new Date().getFullYear(), budget: 0 }
    await loadTeams()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('保存失败')
    }
  }
}

async function deleteTeam(id) {
  try {
    await ElMessageBox.confirm('确定删除该球队吗?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await endpoints.deleteTeam(id)
    ElMessage.success('删除成功')
    await loadTeams()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(loadTeams)
</script>
