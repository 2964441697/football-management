/**
 * 前端应用入口文件
 * 
 * 初始化Vue应用实例，注册以下插件：
 * - Vue Router：路由管理
 * - Pinia：状态管理
 * - Element Plus：UI组件库
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './styles/global.css'

const app = createApp(App)

// 图片懒加载指令
app.directive('lazy-load', {
    mounted(el, binding) {
        const options = {
            rootMargin: '50px',
            threshold: 0.1
        }
        const loadImage = () => {
            if (binding.value) {
                el.src = binding.value
            }
        }
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        loadImage()
                        observer.unobserve(el)
                    }
                })
            }, options)
            observer.observe(el)
        } else {
            loadImage()
        }
    }
})

app.use(createPinia())
app.use(ElementPlus)
app.use(router)
app.mount('#app')
