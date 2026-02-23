import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import endpoints from '../api/endpoints'
import { TokenManager } from '../api/service'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  
  // 角色常量
  const ROLE_ADMIN = 'admin'
  const ROLE_COACH = 'coach'
  const ROLE_VIEWER = 'viewer'

  const ROLE_LABELS = {
    [ROLE_ADMIN]: '管理员',
    [ROLE_COACH]: '教练',
    [ROLE_VIEWER]: '观察者'
  }

  const PERMISSIONS = {
    [ROLE_ADMIN]: ['*'],
    [ROLE_COACH]: ['players', 'training', 'matches', 'seasons', 'competitions'],
    [ROLE_VIEWER]: ['view']
  }

  // 计算属性
  const isLoggedIn = computed(() => TokenManager.isLoggedIn())
  
  const roleLabel = computed(() => {
    if (!user.value) return ''
    return ROLE_LABELS[user.value.role] || user.value.role
  })

  const isAdmin = computed(() => user.value?.role === ROLE_ADMIN)
  const isCoach = computed(() => user.value?.role === ROLE_COACH)
  const isViewer = computed(() => user.value?.role === ROLE_VIEWER)

  // 权限检查
  function hasPermission(permission) {
    if (!user.value) return false
    const perms = PERMISSIONS[user.value.role] || []
    return perms.includes('*') || perms.includes(permission)
  }

  function hasAnyRole(roles) {
    if (!user.value) return false
    return roles.includes(user.value.role)
  }

  // 登录
  async function login(username, password) {
    try {
      const response = await endpoints.login({ username, password })
      user.value = response.user
      return { success: true, user: response.user }
    } catch (error) {
      return { 
        success: false, 
        message: error.data?.error || error.message || '登录失败' 
      }
    }
  }

  // 注册
  async function register(username, email, password, role = 'viewer') {
    try {
      const response = await endpoints.register({ username, email, password, role })
      user.value = response.user
      return { success: true, user: response.user }
    } catch (error) {
      return { 
        success: false, 
        message: error.data?.error || error.message || '注册失败' 
      }
    }
  }

  // 登出
  function logout() {
    user.value = null
    endpoints.logout()
  }

  // 获取当前用户信息
  async function fetchCurrentUser() {
    if (!TokenManager.isLoggedIn()) {
      return null
    }
    
    try {
      const response = await endpoints.getCurrentUser()
      user.value = response
      localStorage.setItem('user', JSON.stringify(response))
      return response
    } catch (error) {
      // token 无效，清除登录状态
      if (error.status === 401) {
        logout()
      }
      return null
    }
  }

  // 更新用户信息
  async function updateUser(data) {
    try {
      const response = await endpoints.updateUser(data)
      user.value = response
      localStorage.setItem('user', JSON.stringify(response))
      return { success: true, user: response }
    } catch (error) {
      return { 
        success: false, 
        message: error.data?.error || error.message || '更新失败' 
      }
    }
  }

  // 修改密码
  async function changePassword(oldPassword, newPassword) {
    try {
      await endpoints.changePassword({ 
        old_password: oldPassword, 
        new_password: newPassword 
      })
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        message: error.data?.error || error.message || '修改密码失败' 
      }
    }
  }

  // 上传头像
  async function uploadAvatar(file) {
    try {
      const formData = new FormData()
      formData.append('avatar', file)
      const response = await endpoints.uploadAvatar(formData)
      if (user.value) {
        user.value.avatar = response.avatar
        localStorage.setItem('user', JSON.stringify(user.value))
      }
      return { success: true, avatar: response.avatar }
    } catch (error) {
      return { 
        success: false, 
        message: error.data?.error || error.message || '上传失败' 
      }
    }
  }

  // 从 localStorage 加载用户信息
  function loadUserFromStorage() {
    const storedUser = localStorage.getItem('user')
    if (storedUser && TokenManager.isLoggedIn()) {
      try {
        user.value = JSON.parse(storedUser)
      } catch (e) {
        localStorage.removeItem('user')
        user.value = null
      }
    } else {
      user.value = null
    }
  }

  // 初始化时加载用户
  loadUserFromStorage()

  return { 
    user, 
    isLoggedIn,
    roleLabel,
    isAdmin,
    isCoach,
    isViewer,
    ROLE_ADMIN,
    ROLE_COACH,
    ROLE_VIEWER,
    ROLE_LABELS,
    hasPermission,
    hasAnyRole,
    login, 
    register, 
    logout,
    fetchCurrentUser,
    updateUser,
    changePassword,
    uploadAvatar,
    loadUserFromStorage 
  }
})
