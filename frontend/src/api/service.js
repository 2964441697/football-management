/**
 * API服务封装
 * 
 * 使用axios封装HTTP请求，配置统一的基础URL和超时时间
 * 包含请求和响应拦截器统一处理错误和认证
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 从环境变量获取 API 基础 URL
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
    baseURL: API_BASE,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
})

// API 请求缓存
const apiCache = new Map()
const CACHE_DURATION = 5 * 60 * 1000 // 5分钟缓存

const CacheManager = {
    get(key) {
        const cached = apiCache.get(key)
        if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
            return cached.data
        }
        apiCache.delete(key)
        return null
    },
    
    set(key, data) {
        apiCache.set(key, { data, timestamp: Date.now() })
    },
    
    delete(key) {
        apiCache.delete(key)
    },
    
    clear() {
        apiCache.clear()
    }
}

// Token 管理
const TokenManager = {
    getAccessToken() {
        return localStorage.getItem('access_token')
    },
    
    getRefreshToken() {
        return localStorage.getItem('refresh_token')
    },
    
    setTokens(accessToken, refreshToken) {
        if (accessToken) {
            localStorage.setItem('access_token', accessToken)
        }
        if (refreshToken) {
            localStorage.setItem('refresh_token', refreshToken)
        }
    },
    
    clearTokens() {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
    },
    
    isLoggedIn() {
        return !!this.getAccessToken()
    }
}

// 是否正在刷新 token
let isRefreshing = false
// 等待刷新的请求队列
let refreshQueue = []

// Request interceptor - 添加认证token
api.interceptors.request.use(
    config => {
        const token = TokenManager.getAccessToken()
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    error => {
        return Promise.reject(error)
    }
)

// Response interceptor
api.interceptors.response.use(
    response => {
        return response.data
    },
    async error => {
        const { response, config } = error
        
        if (response) {
            const { status, data } = response
            
            // 处理 401 错误 - token 过期
            if (status === 401 && !config._retry) {
                if (data.code === 'TOKEN_INVALID' || data.code === 'TOKEN_EXPIRED') {
                    // 尝试刷新 token
                    if (!isRefreshing) {
                        isRefreshing = true
                        config._retry = true
                        
                        try {
                            const refreshToken = TokenManager.getRefreshToken()
                            if (refreshToken) {
                                const refreshResponse = await axios.post(
                                    `${API_BASE}/auth/refresh`,
                                    { refresh_token: refreshToken },
                                    { headers: { 'Content-Type': 'application/json' } }
                                )
                                
                                const { access_token, refresh_token } = refreshResponse.data
                                TokenManager.setTokens(access_token, refresh_token)
                                
                                // 重试队列中的请求
                                refreshQueue.forEach(cb => cb(access_token))
                                refreshQueue = []
                                
                                // 重试当前请求
                                config.headers.Authorization = `Bearer ${access_token}`
                                return api(config)
                            }
                        } catch (refreshError) {
                            // 刷新失败，清除 token 并跳转登录
                            TokenManager.clearTokens()
                            refreshQueue = []
                            window.location.href = '/login'
                            return Promise.reject(refreshError)
                        } finally {
                            isRefreshing = false
                        }
                    } else {
                        // 正在刷新，加入队列等待
                        return new Promise(resolve => {
                            refreshQueue.push(token => {
                                config.headers.Authorization = `Bearer ${token}`
                                resolve(api(config))
                            })
                        })
                    }
                }
                
                // 未登录或 token 无效
                TokenManager.clearTokens()
                ElMessage.error('登录已过期，请重新登录')
                window.location.href = '/login'
                return Promise.reject({ status, data, message: '未授权' })
            }
            
            // 处理其他错误
            let message = '请求失败'
            
            switch (status) {
                case 400:
                    message = data.error || '请求参数错误'
                    break
                case 403:
                    message = data.error || '权限不足'
                    break
                case 404:
                    message = data.error || '请求的资源不存在'
                    break
                case 500:
                    message = data.error || '服务器内部错误'
                    break
                default:
                    message = data.error || data.message || '网络错误'
            }
            
            ElMessage.error(message)
            return Promise.reject({
                status,
                data,
                message
            })
        }
        
        // 网络错误
        if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
            ElMessage.error('网络连接失败，请检查网络')
        } else if (error.code === 'ECONNABORTED') {
            ElMessage.error('请求超时，请稍后重试')
        } else {
            ElMessage.error('未知错误')
        }
        
        return Promise.reject({ message: error.message })
    }
)

// 通用请求方法
export const request = {
    get(url, params = {}, config = {}) {
        const cacheKey = `${url}?${JSON.stringify(params)}`
        if (config.useCache !== false) {
            const cached = CacheManager.get(cacheKey)
            if (cached) {
                return Promise.resolve(cached)
            }
        }
        return api.get(url, { params, ...config }).then(response => {
            if (config.useCache !== false) {
                CacheManager.set(cacheKey, response)
            }
            return response
        })
    },
    
    post(url, data = {}, config = {}) {
        CacheManager.clear()
        return api.post(url, data, config)
    },
    
    put(url, data = {}, config = {}) {
        CacheManager.clear()
        return api.put(url, data, config)
    },
    
    delete(url, config = {}) {
        CacheManager.clear()
        return api.delete(url, config)
    }
}

// 导出缓存管理器
export { CacheManager }

// 导出 Token 管理器
export { TokenManager }

export default api
