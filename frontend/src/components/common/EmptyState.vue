<template>
  <div class="empty-state">
    <el-icon :size="iconSize" :color="iconColor">
      <component :is="icon" />
    </el-icon>
    <div class="empty-state-text">{{ text }}</div>
    <div v-if="hint" class="empty-state-hint">{{ hint }}</div>
    <slot name="action"></slot>
  </div>
</template>

<script setup>
import { FolderOpened } from '@element-plus/icons-vue'

defineProps({
  icon: {
    type: Object,
    default: () => FolderOpened
  },
  iconSize: {
    type: Number,
    default: 64
  },
  iconColor: {
    type: String,
    default: '#C0C4CC'
  },
  text: {
    type: String,
    default: '暂无数据'
  },
  hint: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-state-text {
  font-size: 16px;
  margin-top: 16px;
  color: #606266;
}

.empty-state-hint {
  font-size: 14px;
  margin-top: 8px;
  color: #909399;
}
</style>
