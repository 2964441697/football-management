<template>
  <div class="auth-page">
    <div class="auth-left">
      <div class="brand-content">
        <img src="/football.png" alt="足球" class="brand-logo" />
        <h1 class="brand-title">足球管理系统</h1>
        <p class="brand-subtitle">专业、高效的足球俱乐部管理平台</p>
      </div>
    </div>
    <div class="auth-right">
      <div class="login-card">
        <h2>欢迎回来</h2>
        <el-tabs v-model="activeTab" class="auth-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form :model="loginForm">
              <el-form-item label="用户名">
                <el-input v-model="loginForm.username" placeholder="请输入用户名" />
              </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="loginForm.password" type="password" show-password placeholder="请输入密码" />
            </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleLogin" :loading="loginLoading" style="width: 100%;">登录</el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form :model="registerForm">
              <el-form-item label="用户名">
                <el-input v-model="registerForm.username" placeholder="请输入用户名" />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="registerForm.email" type="email" placeholder="请输入邮箱" />
              </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="registerForm.password" type="password" show-password placeholder="请输入密码" />
              <div v-if="registerForm.password" class="password-strength">
                <div class="strength-bar">
                  <div 
                    class="strength-fill" 
                    :style="{ width: (passwordStrength.score / 5 * 100) + '%', backgroundColor: passwordStrength.color }"
                  ></div>
                </div>
                <span class="strength-text" :style="{ color: passwordStrength.color }">{{ passwordStrength.text }}</span>
              </div>
            </el-form-item>
            <el-form-item label="确认密码">
              <el-input v-model="registerForm.confirmPassword" type="password" show-password placeholder="请确认密码" />
            </el-form-item>
            <el-form-item label="角色">
              <el-select v-model="registerForm.role" placeholder="请选择角色" style="width: 100%;">
                <el-option label="管理员" value="admin" />
                <el-option label="教练" value="coach" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleRegister" :loading="registerLoading" style="width: 100%;">注册</el-button>
            </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const activeTab = ref('login')
const loginLoading = ref(false)
const registerLoading = ref(false)

const loginForm = ref({
  username: '',
  password: ''
})

const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: 'coach'
})

// 密码强度检查
const passwordStrength = computed(() => {
  const password = registerForm.value.password
  if (!password) return { score: 0, text: '', color: '' }
  
  let score = 0
  const checks = {
    length: password.length >= 8,
    lowercase: /[a-z]/.test(password),
    uppercase: /[A-Z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
  }
  
  score = Object.values(checks).filter(Boolean).length
  
  if (score <= 2) return { score, text: '弱', color: '#F56C6C' }
  if (score <= 3) return { score, text: '中', color: '#E6A23C' }
  if (score <= 4) return { score, text: '强', color: '#67C23A' }
  return { score, text: '非常强', color: '#409EFF' }
})

// 密码验证规则
function validatePassword(password) {
  const errors = []
  if (password.length < 8) {
    errors.push('密码至少需要8个字符')
  }
  if (!/[a-zA-Z]/.test(password)) {
    errors.push('密码需要包含字母')
  }
  if (!/[0-9]/.test(password)) {
    errors.push('密码需要包含数字')
  }
  return errors
}

async function handleLogin() {
  if (!loginForm.value.username || !loginForm.value.password) {
    ElMessage.error('请填写用户名和密码')
    return
  }

  loginLoading.value = true
  try {
    const result = await userStore.login(loginForm.value.username, loginForm.value.password)
    if (result && result.success) {
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      ElMessage.error(result?.message || '登录失败')
    }
  } finally {
    loginLoading.value = false
  }
}

async function handleRegister() {
  const { username, email, password, confirmPassword, role } = registerForm.value

  if (!username || !email || !password) {
    ElMessage.error('请填写所有字段')
    return
  }

  // 密码强度验证
  const passwordErrors = validatePassword(password)
  if (passwordErrors.length > 0) {
    ElMessage.error(passwordErrors[0])
    return
  }

  if (password !== confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }

  // 邮箱格式验证
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) {
    ElMessage.error('请输入有效的邮箱地址')
    return
  }

  registerLoading.value = true
  try {
    const result = await userStore.register(username, email, password, role)
    if (result && result.success) {
      ElMessage.success('注册成功')
      router.push('/')
    } else {
      ElMessage.error(result?.message || '注册失败')
    }
  } finally {
    registerLoading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  min-height: 100vh;
  width: 100%;
  position: relative;
}

.auth-left {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 45%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.brand-content {
  text-align: center;
  color: white;
}

.brand-logo {
  width: 100px;
  height: 100px;
  margin-bottom: 30px;
  filter: drop-shadow(0 4px 20px rgba(0,0,0,0.4));
  animation: float 3s ease-in-out infinite;
  border-radius: 50%;
  object-fit: cover;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.brand-title {
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  font-size: 48px;
  font-weight: 900;
  margin-bottom: 20px;
  text-shadow: 0 4px 30px rgba(0,0,0,0.4);
  letter-spacing: 8px;
  background: linear-gradient(135deg, #fff 0%, #f0f0f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-subtitle {
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  font-size: 20px;
  opacity: 0.85;
  letter-spacing: 4px;
  font-weight: 300;
}

.auth-right {
  position: absolute;
  right: 8%;
  top: 50%;
  transform: translateY(-50%);
  width: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
}

.login-card {
  width: 100%;
}

.login-card h2 {
  text-align: center;
  margin-bottom: 32px;
  color: #333;
  font-size: 26px;
  font-weight: 600;
  letter-spacing: 2px;
}

.auth-tabs :deep(.el-form-item) {
  margin-bottom: 20px;
}

.auth-tabs :deep(.el-input__wrapper) {
  padding: 10px;
}

.auth-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background: #e0e0e0;
}

.auth-tabs :deep(.el-tabs__item) {
  font-size: 16px;
  padding: 0 20px;
}

@media (max-width: 900px) {
  .auth-left {
    width: 100%;
    position: relative;
    padding: 60px 20px 40px;
  }
  
  .brand-logo {
    width: 80px;
    height: 80px;
  }
  
  .brand-title {
    font-size: 32px;
    letter-spacing: 4px;
  }
  
  .auth-right {
    position: relative;
    right: auto;
    top: auto;
    transform: none;
    width: 100%;
    margin: 20px;
    padding: 30px 20px;
  }
}

.password-strength {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.strength-bar {
  flex: 1;
  height: 4px;
  background: #e0e0e0;
  border-radius: 2px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  transition: width 0.3s, background-color 0.3s;
  border-radius: 2px;
}

.strength-text {
  font-size: 12px;
  min-width: 50px;
}
</style>
