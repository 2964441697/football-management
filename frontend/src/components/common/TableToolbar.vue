<template>
  <div class="table-toolbar">
    <div class="toolbar-left">
      <el-button
        v-if="showAdd"
        type="primary"
        @click="$emit('add')"
      >
        <el-icon><Plus /></el-icon>
        {{ addText }}
      </el-button>
      <el-button @click="$emit('refresh')">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
      <el-button
        v-if="showExport"
        type="success"
        :disabled="selectedCount === 0"
        @click="$emit('export')"
      >
        <el-icon><Download /></el-icon>
        导出选中
      </el-button>
      <el-button
        v-if="showBatchDelete"
        type="danger"
        :disabled="selectedCount === 0"
        @click="$emit('batch-delete')"
      >
        <el-icon><Delete /></el-icon>
        批量删除
      </el-button>
      <el-button
        v-if="showResetId"
        type="warning"
        :disabled="loading"
        @click="$emit('reset-id')"
      >
        <el-icon><RefreshRight /></el-icon>
        重置ID
      </el-button>
    </div>

    <div class="toolbar-right">
      <el-input
        v-if="searchPlaceholder"
        v-model="searchValue"
        :placeholder="searchPlaceholder"
        class="search-input"
        clearable
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select
        v-for="filter in filters"
        :key="filter.key"
        v-model="filterValues[filter.key]"
        :placeholder="filter.placeholder"
        class="filter-select"
        clearable
        @change="handleFilterChange(filter.key, $event)"
      >
        <el-option
          v-for="option in filter.options"
          :key="option.value"
          :label="option.label"
          :value="option.value"
        />
      </el-select>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { Plus, Refresh, Download, Delete, RefreshRight, Search } from '@element-plus/icons-vue'
import { debounce } from '../../utils/helpers'

const props = defineProps({
  showAdd: {
    type: Boolean,
    default: true
  },
  addText: {
    type: String,
    default: '新增'
  },
  showExport: {
    type: Boolean,
    default: true
  },
  showBatchDelete: {
    type: Boolean,
    default: true
  },
  showResetId: {
    type: Boolean,
    default: true
  },
  searchPlaceholder: {
    type: String,
    default: ''
  },
  filters: {
    type: Array,
    default: () => []
  },
  selectedCount: {
    type: Number,
    default: 0
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['add', 'refresh', 'export', 'batch-delete', 'reset-id', 'search', 'filter-change'])

const searchValue = ref('')
const filterValues = reactive({})

const debouncedSearch = debounce((value) => {
  emit('search', value)
}, 300)

function handleSearch(value) {
  debouncedSearch(value)
}

function handleFilterChange(key, value) {
  emit('filter-change', { key, value })
}
</script>

<style scoped>
.table-toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: white;
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-light);
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.toolbar-right {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-left: auto;
  flex-wrap: wrap;
}

.search-input {
  width: 300px;
}

.filter-select {
  width: 200px;
}

@media (max-width: 768px) {
  .table-toolbar {
    padding: 12px;
    gap: 8px;
  }

  .toolbar-left,
  .toolbar-right {
    width: 100%;
    margin-left: 0;
  }

  .toolbar-right {
    order: 2;
  }

  .search-input,
  .filter-select {
    width: 100%;
  }
}
</style>
