<template>
    <div>
        <div class="bg-root" :style="bgStyle">
            <div class="bg-overlay" />
        </div>

        <div class="app-content">
            <slot />
        </div>

        <div class="switcher">
            <button class="toggle" @click="togglePanel">背景</button>
            <div class="panel" v-if="showPanel">
                <div class="option" v-for="(opt, idx) in optionsList" :key="idx" @click="selectOption(opt)">
                    <div class="preview" :style="getPreviewStyle(opt)"></div>
                    <span class="label">{{ opt.name }}</span>
                </div>
                
                <div class="upload-section" v-if="isAdmin">
                    <input type="file" ref="fileInputRef" accept="image/*" style="display:none" @change="onFileChange" />
                    <button class="upload-btn" @click="triggerUpload" :disabled="uploading">
                        {{ uploading ? '上传中...' : '+ 添加背景' }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '../api/service'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const STORAGE_KEY = 'app:bgOption'

const defaultOptions = []

const customOptions = ref([])
const showPanel = ref(false)
const fileInputRef = ref(null)
const currentBg = ref(null)
const uploading = ref(false)

const isAdmin = computed(() => userStore.isAdmin)

const optionsList = computed(() => {
    const list = []
    defaultOptions.forEach(opt => {
        if (opt && opt.id) list.push({ ...opt })
    })
    customOptions.value.forEach(opt => {
        if (opt && opt.id) list.push({ ...opt })
    })
    return list
})

function togglePanel() {
    showPanel.value = !showPanel.value
}

function selectOption(opt) {
    if (!opt || !opt.value) return
    currentBg.value = { ...opt }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(opt))
    showPanel.value = false
}

function getPreviewStyle(opt) {
    if (!opt || !opt.value) return {}
    if (opt.type === 'image') {
        return { backgroundImage: `url(${opt.value})`, backgroundSize: 'cover', backgroundPosition: 'center' }
    }
    return { backgroundImage: opt.value }
}

const bgStyle = computed(() => {
    if (!currentBg.value || !currentBg.value.value) {
        return { backgroundImage: defaultOptions[0]?.value ? `url(${defaultOptions[0].value})` : 'none' }
    }
    const val = currentBg.value.value
    if (currentBg.value.type === 'image') {
        return { backgroundImage: `url(${val})`, backgroundSize: 'cover', backgroundPosition: 'center center' }
    }
    return { backgroundImage: val }
})

function triggerUpload() {
    fileInputRef.value?.click()
}

async function onFileChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    
    if (!file.type.startsWith('image/')) {
        alert('请选择图片文件')
        return
    }
    
    if (file.size > 5 * 1024 * 1024) {
        alert('图片大小不能超过5MB')
        return
    }
    
    uploading.value = true
    
    try {
        const formData = new FormData()
        formData.append('background', file)
        formData.append('id', userStore.user?.id)
        
        const newBg = await api.post('/auth/backgrounds/upload', formData)
        
        customOptions.value = [...customOptions.value, newBg]
        currentBg.value = { ...newBg }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(newBg))
        
        alert('上传成功')
        showPanel.value = false
    } catch (err) {
        alert(err.response?.data?.error || '上传失败')
    } finally {
        uploading.value = false
        e.target.value = ''
    }
}

async function loadCustomBackgrounds() {
    try {
        const list = await api.get('/auth/backgrounds')
        if (Array.isArray(list)) {
            customOptions.value = list
        }
    } catch (err) {
        console.log('加载背景列表失败')
    }
}

function initBackground() {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
        try {
            const parsed = JSON.parse(saved)
            currentBg.value = { ...parsed }
            return
        } catch (e) {}
    }
    if (optionsList.value.length > 0) {
        currentBg.value = { ...optionsList.value[0] }
    }
}

onMounted(async () => {
    await loadCustomBackgrounds()
    initBackground()
})
</script>

<style scoped>
.bg-root {
    position: fixed;
    inset: 0;
    z-index: 0;
    overflow: hidden;
}

.bg-root .bg-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.15);
    backdrop-filter: blur(4px);
}

.app-content {
    position: relative;
    z-index: 1;
    min-height: 100vh;
}

.switcher {
    position: fixed;
    right: 18px;
    bottom: 18px;
    z-index: 2;
}

.switcher .toggle {
    background: rgba(0, 0, 0, 0.6);
    color: #fff;
    border: none;
    padding: 8px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
}

.switcher .panel {
    position: absolute;
    bottom: 50px;
    right: 0;
    background: rgba(255, 255, 255, 0.95);
    padding: 12px;
    border-radius: 8px;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
    width: 200px;
    max-height: 280px;
    overflow-y: auto;
}

.option {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;
}

.option:hover {
    background: rgba(0, 0, 0, 0.05);
}

.preview {
    width: 50px;
    height: 32px;
    border-radius: 4px;
    background-size: cover;
    background-position: center;
    border: 1px solid #ddd;
    flex-shrink: 0;
}

.label {
    font-size: 13px;
    color: #333;
}

.upload-section {
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #eee;
}

.upload-btn {
    width: 100%;
    padding: 8px;
    background: #f5f5f5;
    border: 1px dashed #ccc;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    color: #666;
}

.upload-btn:hover:not(:disabled) {
    background: #eee;
    border-color: #999;
}

.upload-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}
</style>
