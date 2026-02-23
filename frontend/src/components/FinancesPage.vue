<template>
  <div>
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value" style="color: #67C23A;">¥{{ (summary.total_income || 0).toLocaleString() }}</div>
          <div class="stat-label">总收入</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value" style="color: #F56C6C;">¥{{ (summary.total_expense || 0).toLocaleString() }}</div>
          <div class="stat-label">总支出</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value" :style="{ color: summary.balance >= 0 ? '#67C23A' : '#F56C6C' }">
            ¥{{ (summary.balance || 0).toLocaleString() }}
          </div>
          <div class="stat-label">结余</div>
        </el-card>
      </el-col>
    </el-row>

    <DataTable
      :data="finances"
      :loading="loading"
      :total="total"
      :current-page="currentPage"
      :page-size="pageSize"
      :filters="filters"
      add-text="添加记录"
      empty-text="暂无财务记录"
      empty-hint="点击上方&quot;添加记录&quot;按钮添加第一条记录"
      :show-export="true"
      @add="handleAdd"
      @refresh="loadFinances"
      @export="handleExport"
      @batch-delete="handleBatchDelete"
      @reset-id="handleResetId"
      @filter-change="handleFilterChange"
      @page-change="handlePageChange"
      @size-change="handleSizeChange"
    >
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="category" label="分类" width="120">
        <template #default="{ row }">
          <el-tag :type="getAmountTagType(row.amount)" size="small">{{ row.category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="amount" label="金额" width="150">
        <template #default="{ row }">
          <span :style="{ color: row.amount >= 0 ? '#67C23A' : '#F56C6C', fontWeight: 'bold' }">
            {{ row.amount >= 0 ? '+' : '' }}{{ row.amount.toLocaleString() }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="team_id" label="球队" width="150">
        <template #default="{ row }">
          {{ row.team_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="record_date" label="日期" width="120" />
      <el-table-column prop="note" label="备注" show-overflow-tooltip />
      <el-table-column label="操作" width="150" align="center">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="editFinance(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="deleteFinance(row.id)">删除</el-button>
        </template>
      </el-table-column>

      <template #dialogs>
        <el-dialog :title="editingFinance ? '编辑记录' : '添加记录'" v-model="showAddForm" width="500px">
          <el-form :model="formData" label-width="100px" :rules="rules" ref="formRef">
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
            <el-form-item label="分类" prop="category">
              <el-select v-model="formData.category" placeholder="选择分类" style="width: 100%;">
                <el-option label="转会收入" value="转会收入" />
                <el-option label="转会支出" value="转会支出" />
                <el-option label="薪资支出" value="薪资支出" />
                <el-option label="奖金收入" value="奖金收入" />
                <el-option label="赞助费" value="赞助费" />
                <el-option label="门票收入" value="门票收入" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
            <el-form-item label="金额" prop="amount">
              <el-input-number v-model="formData.amount" :precision="2" style="width: 100%;" />
            </el-form-item>
            <el-form-item label="日期" prop="record_date">
              <el-date-picker
                v-model="formData.record_date"
                type="date"
                placeholder="选择日期"
                style="width: 100%;"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            <el-form-item label="备注" prop="note">
              <el-input v-model="formData.note" type="textarea" :rows="3" placeholder="输入备注" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showAddForm = false">取消</el-button>
            <el-button type="primary" @click="saveFinance">保存</el-button>
          </template>
        </el-dialog>
      </template>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { exportToCSV } from '../utils/helpers'
import endpoints from '../api/endpoints'
import { DataTable } from './common'

const finances = ref([])
const teams = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterCategory = ref('')
const filterTeam = ref(null)

const filters = computed(() => [
  {
    key: 'category',
    placeholder: '筛选分类',
    options: [
      { label: '转会收入', value: '转会收入' },
      { label: '转会支出', value: '转会支出' },
      { label: '薪资支出', value: '薪资支出' },
      { label: '奖金收入', value: '奖金收入' },
      { label: '赞助费', value: '赞助费' },
      { label: '门票收入', value: '门票收入' },
      { label: '其他', value: '其他' }
    ]
  },
  {
    key: 'team',
    placeholder: '筛选球队',
    options: teams.value.map(t => ({ label: t.name, value: t.id }))
  }
])

const showAddForm = ref(false)
const editingFinance = ref(null)
const formRef = ref(null)

const formData = ref({
  team_id: null,
  category: '其他',
  amount: 0,
  record_date: '',
  note: ''
})

const summary = ref({
  total_income: 0,
  total_expense: 0,
  balance: 0
})

const rules = {
  team_id: [{ required: true, message: '请选择球队', trigger: 'change' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  amount: [
    { required: true, message: '请输入金额', trigger: 'blur' },
    { type: 'number', message: '请输入有效的数字', trigger: 'blur' }
  ]
}

function getAmountTagType(amount) {
  return amount >= 0 ? 'success' : 'danger'
}

async function loadFinances() {
  loading.value = true
  try {
    const financesData = await endpoints.getFinancesPaginated({
      page: currentPage.value,
      per_page: pageSize.value,
      category: filterCategory.value,
      team_id: filterTeam.value
    })

    if (financesData && financesData.items) {
      finances.value = financesData.items
      total.value = financesData.pagination?.total || financesData.items.length
    } else {
      finances.value = financesData || []
      total.value = financesData?.length || 0
    }

    summary.value = {
      total_income: finances.value.reduce((sum, f) => f.amount > 0 ? sum + f.amount : sum, 0),
      total_expense: finances.value.reduce((sum, f) => f.amount < 0 ? sum + Math.abs(f.amount) : sum, 0),
      balance: finances.value.reduce((sum, f) => sum + f.amount, 0)
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
  editingFinance.value = null
  formData.value = {
    team_id: null,
    category: '其他',
    amount: 0,
    record_date: '',
    note: ''
  }
}

function handleFilterChange({ key, value }) {
  if (key === 'category') filterCategory.value = value
  if (key === 'team') filterTeam.value = value
  currentPage.value = 1
  loadFinances()
}

function handlePageChange(page) {
  currentPage.value = page
  loadFinances()
}

function handleSizeChange(size) {
  currentPage.value = 1
  pageSize.value = size
  loadFinances()
}

async function handleExport(selected) {
  const selectedData = finances.value.filter(f => selected.includes(f.id))
  exportToCSV(selectedData, '财务数据')
  ElMessage.success('导出成功')
}

async function handleBatchDelete(selected) {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selected.length} 条记录吗?`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await endpoints.batchDeleteFinances({ ids: selected })
    ElMessage.success('批量删除成功')
    await loadFinances()
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

    await endpoints.resetFinanceIds()
    ElMessage.success('ID重置成功')
    await loadFinances()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('重置失败')
    }
  }
}

function editFinance(finance) {
  editingFinance.value = finance
  formData.value = { ...finance }
  showAddForm.value = true
}

async function saveFinance() {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    if (editingFinance.value) {
      await endpoints.updateFinance(editingFinance.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      await endpoints.createFinance(formData.value)
      ElMessage.success('创建成功')
    }
    showAddForm.value = false
    editingFinance.value = null
    await loadFinances()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('保存失败')
    }
  }
}

async function deleteFinance(id) {
  try {
    await ElMessageBox.confirm('确定删除该记录吗?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await endpoints.deleteFinance(id)
    ElMessage.success('删除成功')
    await loadFinances()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(async () => {
  await Promise.all([loadFinances(), loadTeams()])
})
</script>

<style scoped>
.stat-card {
  text-align: center;
  padding: 20px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}
</style>
