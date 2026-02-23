<template>
  <DataTable
    :data="coaches"
    :loading="loading"
    :total="total"
    :current-page="currentPage"
    :page-size="pageSize"
    :filters="filters"
    add-text="新增教练"
    search-placeholder="搜索教练名称..."
    empty-text="暂无教练数据"
    empty-hint="点击上方&quot;新增教练&quot;按钮添加第一个教练"
    :show-export="false"
    @add="handleAdd"
    @refresh="loadCoaches"
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
        <el-avatar :size="40" v-lazy-load="getAvatarUrl(row.avatar)">
          <el-icon :size="24"><User /></el-icon>
        </el-avatar>
      </template>
    </el-table-column>
    <el-table-column prop="name" label="教练名称" />
    <el-table-column prop="nationality" label="国籍" width="120" />
    <el-table-column prop="date_of_birth" label="出生日期" width="120" />
    <el-table-column prop="role" label="角色" width="120">
      <template #default="{ row }">
        <el-tag :type="getRoleTagType(row.role)" size="small">{{ row.role }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="team_id" label="所属球队" width="150">
      <template #default="{ row }">
        {{ getTeamName(row.team_id) }}
      </template>
    </el-table-column>
    <el-table-column prop="salary" label="薪资" width="100">
      <template #default="{ row }">
        {{ row.salary ? `¥${row.salary.toLocaleString()}` : '-' }}
      </template>
    </el-table-column>
    <el-table-column label="操作" width="150" align="center">
      <template #default="{ row }">
        <el-button link type="primary" size="small" @click="editCoach(row)">编辑</el-button>
        <el-button link type="danger" size="small" @click="deleteCoach(row.id)">删除</el-button>
      </template>
    </el-table-column>

    <template #dialogs>
      <el-dialog :title="editingCoach ? '编辑教练' : '新增教练'" v-model="showAddForm" width="600px">
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
              <el-button type="primary" size="small">{{ editingCoach ? '更换头像' : '上传头像' }}</el-button>
            </el-upload>
          </div>
        </div>
        <el-form :model="formData" label-width="100px" :rules="rules" ref="formRef">
          <el-form-item label="教练名称" prop="name">
            <el-input v-model="formData.name" placeholder="输入教练名称" />
          </el-form-item>
          <el-form-item label="国籍" prop="nationality">
            <el-input v-model="formData.nationality" placeholder="输入国籍" />
          </el-form-item>
          <el-form-item label="出生日期" prop="date_of_birth">
            <el-date-picker v-model="formData.date_of_birth" type="date" placeholder="选择出生日期" style="width: 100%;" />
          </el-form-item>
          <el-form-item label="角色" prop="role">
            <el-select v-model="formData.role" placeholder="选择角色" style="width: 100%;">
              <el-option label="主教练" value="主教练" />
              <el-option label="助理教练" value="助理教练" />
              <el-option label="守门员教练" value="守门员教练" />
              <el-option label="体能教练" value="体能教练" />
              <el-option label="技术分析师" value="技术分析师" />
            </el-select>
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
          <el-form-item label="入职日期" prop="hire_date">
            <el-date-picker v-model="formData.hire_date" type="date" placeholder="选择入职日期" style="width: 100%;" />
          </el-form-item>
          <el-form-item label="薪资" prop="salary">
            <el-input-number v-model="formData.salary" :min="0" :precision="2" :step="10000" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAddForm = false">取消</el-button>
          <el-button type="primary" @click="saveCoach">保存</el-button>
        </template>
      </el-dialog>
    </template>
  </DataTable>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { getStaticUrl } from '../utils/helpers'
import endpoints from '../api/endpoints'
import { DataTable } from './common'

const coaches = ref([])
const teams = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchName = ref('')
const filterRole = ref('')

const filters = computed(() => [
  {
    key: 'role',
    placeholder: '筛选角色',
    options: [
      { label: '主教练', value: '主教练' },
      { label: '助理教练', value: '助理教练' },
      { label: '守门员教练', value: '守门员教练' },
      { label: '体能教练', value: '体能教练' }
    ]
  }
])

const showAddForm = ref(false)
const editingCoach = ref(null)
const formRef = ref(null)
const avatarFile = ref(null)

const formData = ref({
  name: '',
  nationality: '',
  date_of_birth: null,
  role: '主教练',
  avatar: '',
  team_id: null,
  hire_date: null,
  salary: 0
})

const rules = {
  name: [{ required: true, message: '请输入教练名称', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

function getAvatarUrl(avatar) {
  return getStaticUrl(avatar)
}

function getRoleTagType(role) {
  const typeMap = {
    '主教练': 'danger',
    '助理教练': 'warning',
    '守门员教练': 'success',
    '体能教练': '',
    '技术分析师': 'info'
  }
  return typeMap[role] || 'info'
}

function getTeamName(teamId) {
  const team = teams.value.find(t => t.id === teamId)
  return team ? team.name : '未分配'
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

async function uploadCoachAvatar(coachId) {
  if (!avatarFile.value) return

  const fd = new FormData()
  fd.append('avatar', avatarFile.value)

  if (coachId) {
    fd.append('id', coachId)
  }

  await endpoints.uploadCoachAvatar(fd)
}

async function loadCoaches() {
  loading.value = true
  try {
    const result = await endpoints.getCoachesPaginated({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchName.value,
      role: filterRole.value
    })

    if (result.items !== undefined) {
      coaches.value = result.items
      total.value = result.total
    } else {
      coaches.value = result
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

function handleAdd() {
  showAddForm.value = true
  editingCoach.value = null
  avatarFile.value = null
  formData.value = {
    name: '',
    nationality: '',
    date_of_birth: null,
    role: '主教练',
    avatar: '',
    team_id: null,
    hire_date: null,
    salary: 0
  }
}

function handleSearch(query) {
  searchName.value = query
  currentPage.value = 1
  loadCoaches()
}

function handleFilterChange({ key, value }) {
  if (key === 'role') filterRole.value = value
  currentPage.value = 1
  loadCoaches()
}

function handlePageChange(page) {
  currentPage.value = page
  loadCoaches()
}

function handleSizeChange(size) {
  currentPage.value = 1
  pageSize.value = size
  loadCoaches()
}

async function handleBatchDelete(selected) {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selected.length} 个教练吗?`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await Promise.all(selected.map(id => endpoints.deleteCoach(id)))
    ElMessage.success('批量删除成功')
    await loadCoaches()
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

    await endpoints.resetCoachIds()
    ElMessage.success('ID重置成功')
    await loadCoaches()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('重置失败')
    }
  }
}

function editCoach(coach) {
  editingCoach.value = coach
  formData.value = {
    ...coach,
    date_of_birth: coach.date_of_birth ? new Date(coach.date_of_birth) : null,
    hire_date: coach.hire_date ? new Date(coach.hire_date) : null
  }
  showAddForm.value = true
}

async function saveCoach() {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    const data = {
      ...formData.value,
      date_of_birth: formData.value.date_of_birth ? formData.value.date_of_birth.toISOString().split('T')[0] : null,
      hire_date: formData.value.hire_date ? formData.value.hire_date.toISOString().split('T')[0] : null
    }

    if (editingCoach.value) {
      await endpoints.updateCoach(editingCoach.value.id, data)
      if (avatarFile.value) {
        await uploadCoachAvatar(editingCoach.value.id)
      }
      ElMessage.success('更新成功')
    } else {
      const res = await endpoints.createCoach(data)
      if (avatarFile.value) {
        await uploadCoachAvatar(res.id || res)
      }
      ElMessage.success('创建成功')
    }
    showAddForm.value = false
    editingCoach.value = null
    avatarFile.value = null
    await loadCoaches()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function deleteCoach(id) {
  try {
    await ElMessageBox.confirm('确定删除该教练吗?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await endpoints.deleteCoach(id)
    ElMessage.success('删除成功')
    await loadCoaches()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(async () => {
  await Promise.all([loadCoaches(), loadTeams()])
})
</script>

<style scoped>
</style>
