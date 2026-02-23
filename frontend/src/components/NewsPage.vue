<template>
  <DataTable
    :data="filteredNews"
    :loading="loading"
    :total="total"
    :current-page="currentPage"
    :page-size="pageSize"
    :filters="filters"
    :selectable="false"
    :show-export="false"
    :show-batch-delete="false"
    add-text="发布新闻"
    search-placeholder="搜索新闻标题..."
    empty-text="暂无新闻"
    empty-hint="点击上方&quot;发布新闻&quot;按钮添加第一条新闻"
    @add="handleAdd"
    @refresh="loadNews"
    @reset-id="handleResetId"
    @search="handleSearch"
    @filter-change="handleFilterChange"
    @page-change="handlePageChange"
    @size-change="handleSizeChange"
  >
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column prop="title" label="标题" />
    <el-table-column prop="category" label="分类" width="100">
      <template #default="{ row }">
        <el-tag :type="getCategoryTagType(row.category)" size="small">{{ row.category }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="published_at" label="发布时间" width="180">
      <template #default="{ row }">
        {{ formatDate(row.published_at) }}
      </template>
    </el-table-column>
    <el-table-column label="操作" width="200" align="center">
      <template #default="{ row }">
        <el-button link type="primary" size="small" @click="viewNews(row)">查看</el-button>
        <el-button link type="primary" size="small" @click="editNews(row)">编辑</el-button>
        <el-button link type="danger" size="small" @click="deleteNews(row.id)">删除</el-button>
      </template>
    </el-table-column>

    <template #dialogs>
      <el-dialog :title="editingNews ? '编辑新闻' : '发布新闻'" v-model="showAddForm" width="700px">
        <el-form :model="formData" label-width="100px" :rules="rules" ref="formRef">
          <el-form-item label="标题" prop="title">
            <el-input v-model="formData.title" placeholder="输入新闻标题" />
          </el-form-item>
          <el-form-item label="分类" prop="category">
            <el-select v-model="formData.category" placeholder="选择分类" style="width: 100%;">
              <el-option label="新闻" value="新闻" />
              <el-option label="公告" value="公告" />
              <el-option label="战报" value="战报" />
              <el-option label="预告" value="预告" />
            </el-select>
          </el-form-item>
          <el-form-item label="封面图片">
            <el-upload
              class="avatar-uploader"
              :show-file-list="false"
              :auto-upload="false"
              :on-change="handleImageChange"
            >
              <img v-if="imageUrl" :src="imageUrl" class="avatar" />
              <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
            </el-upload>
          </el-form-item>
          <el-form-item label="内容" prop="content">
            <el-input v-model="formData.content" type="textarea" :rows="6" placeholder="输入新闻内容" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAddForm = false">取消</el-button>
          <el-button type="primary" @click="saveNews">发布</el-button>
        </template>
      </el-dialog>

      <el-dialog title="新闻详情" v-model="showViewDialog" width="600px">
        <h2>{{ currentNews?.title }}</h2>
        <el-tag :type="getCategoryTagType(currentNews?.category)" style="margin: 10px 0;">{{ currentNews?.category }}</el-tag>
        <p style="color: #999; font-size: 12px; margin-bottom: 20px;">发布时间: {{ formatDate(currentNews?.published_at) }}</p>
        <el-divider />
        <div style="white-space: pre-wrap; line-height: 1.6;">{{ currentNews?.content }}</div>
      </el-dialog>
    </template>
  </DataTable>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import endpoints from '../api/endpoints'
import { DataTable } from './common'

const news = ref([])
const searchTitle = ref('')
const filterCategory = ref('')
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const showAddForm = ref(false)
const showViewDialog = ref(false)
const editingNews = ref(null)
const currentNews = ref(null)
const formRef = ref(null)
const userStore = useUserStore()
const imageUrl = ref('')
const imageFile = ref(null)

const filters = computed(() => [
  {
    key: 'category',
    placeholder: '筛选分类',
    options: [
      { label: '新闻', value: '新闻' },
      { label: '公告', value: '公告' },
      { label: '战报', value: '战报' },
      { label: '预告', value: '预告' }
    ]
  }
])

const formData = ref({
  title: '',
  category: '新闻',
  content: '',
  image: ''
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
}

const filteredNews = computed(() => {
  let result = news.value || []

  if (searchTitle.value) {
    result = result.filter(n => n.title.includes(searchTitle.value))
  }

  if (filterCategory.value) {
    result = result.filter(n => n.category === filterCategory.value)
  }

  total.value = result.length

  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return result.slice(start, end)
})

function getCategoryTagType(category) {
  const typeMap = {
    '新闻': '',
    '公告': 'danger',
    '战报': 'success',
    '预告': 'warning'
  }
  return typeMap[category] || 'info'
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function handleImageChange(file) {
  const isImage = file.raw.type.startsWith('image/')
  const isLt2M = file.raw.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
    return
  }

  imageFile.value = file.raw
  imageUrl.value = URL.createObjectURL(file.raw)
}

async function loadNews() {
  loading.value = true
  try {
    news.value = await endpoints.getNews()
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  showAddForm.value = true
  editingNews.value = null
  formData.value = {
    title: '',
    category: '新闻',
    content: '',
    image: ''
  }
  imageUrl.value = ''
  imageFile.value = null
}

function handleSearch(query) {
  searchTitle.value = query
  currentPage.value = 1
}

function handleFilterChange({ key, value }) {
  if (key === 'category') filterCategory.value = value
  currentPage.value = 1
}

function handlePageChange(page) {
  currentPage.value = page
}

function handleSizeChange(size) {
  currentPage.value = 1
  pageSize.value = size
}

async function handleResetId() {
  try {
    await ElMessageBox.confirm('重置ID会重新编号所有数据，确定继续吗?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await endpoints.resetNewsIds()
    ElMessage.success('ID重置成功')
    await loadNews()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('重置失败')
    }
  }
}

function viewNews(item) {
  currentNews.value = item
  showViewDialog.value = true
}

function editNews(item) {
  editingNews.value = item
  formData.value = { ...item, image: item.image || '' }
  imageUrl.value = item.image || ''
  showAddForm.value = true
}

async function saveNews() {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    let imagePath = formData.value.image
    if (imageFile.value) {
      const formDataObj = new FormData()
      formDataObj.append('file', imageFile.value)
      const uploadRes = await endpoints.uploadImage(formDataObj)
      imagePath = uploadRes.data.path || uploadRes.data.url
    }

    const data = {
      ...formData.value,
      image: imagePath,
      author_id: userStore.user?.id
    }

    if (editingNews.value) {
      await endpoints.updateNews(editingNews.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await endpoints.createNews(data)
      ElMessage.success('发布成功')
    }
    showAddForm.value = false
    editingNews.value = null
    formData.value = { title: '', category: '新闻', content: '', image: '' }
    imageUrl.value = ''
    imageFile.value = null
    await loadNews()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function deleteNews(id) {
  try {
    await ElMessageBox.confirm('确定删除该新闻吗?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await endpoints.deleteNews(id)
    ElMessage.success('删除成功')
    await loadNews()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadNews()
})
</script>

<style scoped>
.avatar-uploader {
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  overflow: hidden;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--el-transition-duration-fast);
}

.avatar-uploader:hover {
  border-color: var(--el-color-primary);
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
}

.avatar {
  width: 120px;
  height: 120px;
  object-fit: cover;
  display: block;
}
</style>
