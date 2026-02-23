<template>
  <div class="profile-container">
    <h2 class="page-title">个人资料</h2>
    
    <el-card class="profile-card">
      <div class="profile-header">
        <el-avatar :size="100" :src="avatarUrl">
          <el-icon :size="60"><User /></el-icon>
        </el-avatar>
        <div class="profile-info">
          <h3>{{ userForm.username }}</h3>
          <p>{{ userForm.email }}</p>
          <el-upload
            class="avatar-uploader"
            :show-file-list="false"
            :auto-upload="true"
            :http-request="handleAvatarUpload"
            :before-upload="beforeAvatarUpload"
          >
            <el-button type="primary" size="small" :loading="uploading">更换头像</el-button>
          </el-upload>
        </div>
      </div>
      
      <el-tabs v-model="activeTab" style="margin-top: 30px;">
        <el-tab-pane label="基本信息" name="info">
          <el-form :model="userForm" label-width="100px" :rules="userRules" ref="userFormRef" style="max-width: 500px;">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="userForm.username" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="userForm.email" />
            </el-form-item>
            <el-form-item label="角色">
              <el-tag>{{ userForm.role }}</el-tag>
            </el-form-item>
            <el-form-item label="注册时间">
              <span>{{ userForm.created_at }}</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveUserInfo" :loading="saving">保存修改</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="修改密码" name="password">
          <el-form :model="passwordForm" label-width="100px" :rules="passwordRules" ref="passwordFormRef" style="max-width: 500px;">
            <el-form-item label="原密码" prop="old_password">
              <el-input v-model="passwordForm.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="passwordForm.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input v-model="passwordForm.confirm_password" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="changePassword" :loading="changingPassword">修改密码</el-button>
              <el-button @click="resetPasswordForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import endpoints from '../api/endpoints'

const userStore = useUserStore()
const activeTab = ref('info')
const saving = ref(false)
const changingPassword = ref(false)
const uploading = ref(false)

const userFormRef = ref(null)
const passwordFormRef = ref(null)

const userForm = ref({
  username: '',
  email: '',
  role: '',
  created_at: '',
  avatar: ''
})

const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const avatarUrl = computed(() => {
  if (userForm.value.avatar) {
    return userForm.value.avatar.startsWith('http') 
      ? userForm.value.avatar 
      : `http://localhost:5000${userForm.value.avatar}`
  }
  return ''
})

const userRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名3-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ]
}

const passwordRules = {
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' }
  ]
}

async function loadUserInfo() {
  if (!userStore.user?.id) return
  
  try {
    const response = await endpoints.getCurrentUser(userStore.user.id)
    userForm.value = response
  } catch (e) {
    ElMessage.error('加载用户信息失败')
  }
}

async function saveUserInfo() {
  if (!userFormRef.value) return
  
  try {
    await userFormRef.value.validate()
    saving.value = true
    
    const response = await endpoints.updateUser({
      id: userStore.user.id,
      username: userForm.value.username,
      email: userForm.value.email
    })
    
    userStore.user.username = response.username
    userStore.user.email = response.email
    localStorage.setItem('user', JSON.stringify(userStore.user))
    
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '保存失败')
  } finally {
    saving.value = false
  }
}

async function changePassword() {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    
    if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
      ElMessage.error('两次输入的密码不一致')
      return
    }
    
    changingPassword.value = true
    
    await endpoints.changePassword({
      id: userStore.user.id,
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password
    })
    
    ElMessage.success('密码修改成功')
    resetPasswordForm()
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '修改失败')
  } finally {
    changingPassword.value = false
  }
}

function resetPasswordForm() {
  passwordForm.value = {
    old_password: '',
    new_password: '',
    confirm_password: ''
  }
}

function beforeAvatarUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  
  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过2MB!')
    return false
  }
  return true
}

async function handleAvatarUpload(options) {
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('id', userStore.user.id)
    formData.append('avatar', options.file)
    
    const response = await endpoints.uploadAvatar(formData)
    userForm.value.avatar = response.avatar
    userStore.user.avatar = response.avatar
    localStorage.setItem('user', JSON.stringify(userStore.user))
    
    ElMessage.success('头像上传成功')
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '上传失败')
  } finally {
    uploading.value = false
  }
}

onMounted(loadUserInfo)
</script>

<style scoped>
.profile-container {
  max-width: 800px;
}

.profile-card {
  margin-top: 20px;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.profile-info h3 {
  margin: 0 0 5px 0;
  font-size: 20px;
}

.profile-info p {
  margin: 0 0 15px 0;
  color: #909399;
}

.avatar-uploader {
  display: inline-block;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}
</style>
