<template>
  <DataTable
    :data="filteredPlans"
    :loading="loading"
    :total="total"
    :current-page="currentPage"
    :page-size="pageSize"
    :filters="filters"
    add-text="添加训练计划"
    empty-text="暂无训练计划"
    empty-hint="点击上方&quot;添加训练计划&quot;按钮添加第一个计划"
    :show-export="true"
    @add="handleAdd"
    @refresh="loadTrainingPlans"
    @export="handleExport"
    @batch-delete="handleBatchDelete"
    @reset-id="handleResetId"
    @filter-change="handleFilterChange"
    @page-change="handlePageChange"
    @size-change="handleSizeChange"
  >
    <template #default>
      <el-timeline>
        <el-timeline-item
          v-for="plan in filteredPlans"
          :key="plan.id"
          :timestamp="plan.training_date"
          :type="isPast(plan.training_date) ? '' : 'success'"
          placement="top"
        >
          <el-card shadow="hover">
            <div style="display: flex; justify-content: space-between; align-items: start;">
              <div>
                <h4>{{ plan.title }} <el-tag v-if="plan.team_name" size="small" style="margin-left: 10px">{{ plan.team_name }}</el-tag></h4>
                <p style="color: #666; margin: 8px 0;">
                  <el-icon><Timer /></el-icon>
                  {{ plan.duration_minutes }}分钟 |
                  <el-icon><Location /></el-icon>
                  {{ plan.location || '未指定场地' }}
                </p>
                <p style="color: #999; font-size: 12px;">{{ plan.content }}</p>
              </div>
              <div>
                <el-button link type="primary" size="small" @click="editPlan(plan)">编辑</el-button>
                <el-button link type="danger" size="small" @click="deletePlan(plan.id)">删除</el-button>
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </template>

    <template #dialogs>
      <el-dialog :title="editingPlan ? '编辑训练计划' : '添加训练计划'" v-model="showAddForm" width="550px">
        <el-form :model="formData" label-width="100px" :rules="rules" ref="formRef">
          <el-form-item label="标题" prop="title">
            <el-input v-model="formData.title" placeholder="输入训练标题" />
          </el-form-item>
          <el-form-item label="球队" prop="team_id">
            <el-select v-model="formData.team_id" placeholder="选择球队" style="width: 100%;" clearable>
              <el-option
                v-for="team in teams"
                :key="team.id"
                :label="team.name"
                :value="team.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="训练日期" prop="training_date">
            <el-date-picker v-model="formData.training_date" type="date" placeholder="选择日期" style="width: 100%;" value-format="YYYY-MM-DD" />
          </el-form-item>
          <el-form-item label="时长" prop="duration_minutes">
            <el-input-number v-model="formData.duration_minutes" :min="15" :max="300" :step="15" />
            <span style="margin-left: 10px;">分钟</span>
          </el-form-item>
          <el-form-item label="场地" prop="location">
            <el-input v-model="formData.location" placeholder="输入训练场地" />
          </el-form-item>
          <el-form-item label="内容" prop="content">
            <el-input v-model="formData.content" type="textarea" :rows="4" placeholder="输入训练内容" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAddForm = false">取消</el-button>
          <el-button type="primary" @click="savePlan">保存</el-button>
        </template>
      </el-dialog>
    </template>
  </DataTable>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Timer, Location } from '@element-plus/icons-vue'
import { exportToCSV } from '../utils/helpers'
import endpoints from '../api/endpoints'
import { DataTable } from './common'

const trainingPlans = ref([])
const teams = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const selectedTeam = ref(null)
const filterTeam = ref(null)

const filters = computed(() => [
  {
    key: 'team',
    placeholder: '筛选球队',
    options: teams.value.map(t => ({ label: t.name, value: t.id }))
  }
])

const showAddForm = ref(false)
const editingPlan = ref(null)
const formRef = ref(null)

const formData = ref({
  team_id: null,
  title: '',
  training_date: '',
  duration_minutes: 90,
  location: '',
  content: ''
})

const rules = {
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  training_date: [{ required: true, message: '请选择训练日期', trigger: 'change' }],
  duration_minutes: [
    { required: true, message: '请输入时长', trigger: 'blur' },
    { type: 'number', min: 15, max: 300, message: '时长在 15-300 分钟之间', trigger: 'blur' }
  ]
}

const filteredPlans = computed(() => {
  let result = trainingPlans.value || []

  if (filterTeam.value) {
    result = result.filter(p => p.team_id === filterTeam.value)
  }

  total.value = result.length

  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return result.slice(start, end)
})

function isPast(dateStr) {
  if (!dateStr) return false
  const date = new Date(dateStr)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date < today
}

async function loadTrainingPlans() {
  loading.value = true
  try {
    trainingPlans.value = await endpoints.getTrainingPlans()

    if (selectedTeam.value) {
      trainingPlans.value = await endpoints.getTrainingPlansByTeam(selectedTeam.value)
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
  editingPlan.value = null
  formData.value = {
    team_id: null,
    title: '',
    training_date: '',
    duration_minutes: 90,
    location: '',
    content: ''
  }
}

async function loadUpcoming() {
  try {
    trainingPlans.value = await endpoints.getUpcomingTrainingPlans()
    selectedTeam.value = null
  } catch (e) {
    ElMessage.error('加载失败')
  }
}

function handleFilterChange({ key, value }) {
  if (key === 'team') filterTeam.value = value
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
  const selectedData = trainingPlans.value.filter(p => selected.includes(p.id))
  exportToCSV(selectedData, '训练计划')
  ElMessage.success('导出成功')
}

async function handleBatchDelete(selected) {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selected.length} 个计划吗?`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await Promise.all(selected.map(id => endpoints.deleteTrainingPlan(id)))
    ElMessage.success('批量删除成功')
    await loadTrainingPlans()
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

    await endpoints.resetTrainingPlanIds()
    ElMessage.success('ID重置成功')
    await loadTrainingPlans()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('重置失败')
    }
  }
}

function editPlan(plan) {
  editingPlan.value = plan
  formData.value = { ...plan }
  showAddForm.value = true
}

async function savePlan() {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    if (editingPlan.value) {
      await endpoints.updateTrainingPlan(editingPlan.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      await endpoints.createTrainingPlan(formData.value)
      ElMessage.success('创建成功')
    }
    showAddForm.value = false
    editingPlan.value = null
    await loadTrainingPlans()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('保存失败')
    }
  }
}

async function deletePlan(id) {
  try {
    await ElMessageBox.confirm('确定删除该训练计划吗?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await endpoints.deleteTrainingPlan(id)
    ElMessage.success('删除成功')
    await loadTrainingPlans()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(async () => {
  await Promise.all([loadTrainingPlans(), loadTeams()])
})
</script>

<style scoped>
</style>
