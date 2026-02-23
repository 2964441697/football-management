<template>
  <div class="data-table">
    <TableToolbar
      :show-add="showAdd"
      :add-text="addText"
      :show-export="showExport"
      :show-batch-delete="showBatchDelete"
      :show-reset-id="showResetId"
      :search-placeholder="searchPlaceholder"
      :filters="filters"
      :selected-count="selectedRows.length"
      :loading="loading"
      @add="handleAdd"
      @refresh="handleRefresh"
      @export="handleExport"
      @batch-delete="handleBatchDelete"
      @reset-id="handleResetId"
      @search="handleSearch"
      @filter-change="handleFilterChange"
    />

    <div v-if="loading" v-loading="true" class="table-loading" />
    <EmptyState
      v-else-if="!data || data.length === 0"
      :text="emptyText"
      :hint="emptyHint"
    />
    <el-table
      v-else
      :data="data"
      stripe
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column v-if="selectable" type="selection" width="55" />
      <slot />
    </el-table>

    <el-pagination
      v-if="showPagination && total > 0"
      v-model:current-page="localCurrentPage"
      v-model:page-size="localPageSize"
      :page-sizes="pageSizes"
      :total="total"
      :layout="paginationLayout"
      class="table-pagination"
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
    />

    <slot name="dialogs" />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import TableToolbar from './TableToolbar.vue'
import EmptyState from './EmptyState.vue'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  selectable: {
    type: Boolean,
    default: true
  },
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
  showPagination: {
    type: Boolean,
    default: true
  },
  searchPlaceholder: {
    type: String,
    default: '搜索...'
  },
  filters: {
    type: Array,
    default: () => []
  },
  emptyText: {
    type: String,
    default: '暂无数据'
  },
  emptyHint: {
    type: String,
    default: ''
  },
  currentPage: {
    type: Number,
    default: 1
  },
  pageSize: {
    type: Number,
    default: 20
  },
  total: {
    type: Number,
    default: 0
  },
  pageSizes: {
    type: Array,
    default: () => [10, 20, 50, 100]
  },
  paginationLayout: {
    type: String,
    default: 'total, sizes, prev, pager, next, jumper'
  }
})

const emit = defineEmits([
  'add',
  'refresh',
  'export',
  'batch-delete',
  'reset-id',
  'search',
  'filter-change',
  'selection-change',
  'page-change',
  'size-change'
])

const selectedRows = ref([])
const localCurrentPage = ref(props.currentPage)
const localPageSize = ref(props.pageSize)

watch(() => props.currentPage, (newVal) => {
  localCurrentPage.value = newVal
})

watch(() => props.pageSize, (newVal) => {
  localPageSize.value = newVal
})

function handleAdd() {
  emit('add')
}

function handleRefresh() {
  emit('refresh')
}

function handleExport() {
  emit('export', selectedRows.value)
}

function handleBatchDelete() {
  emit('batch-delete', selectedRows.value)
}

function handleResetId() {
  emit('reset-id')
}

function handleSearch(query) {
  emit('search', query)
}

function handleFilterChange(filter) {
  emit('filter-change', filter)
}

function handleSelectionChange(selection) {
  selectedRows.value = selection
  emit('selection-change', selection)
}

function handlePageChange(page) {
  localCurrentPage.value = page
  emit('page-change', page)
}

function handleSizeChange(size) {
  localPageSize.value = size
  emit('size-change', size)
}
</script>

<style scoped>
.data-table {
  width: 100%;
}

.table-loading {
  min-height: 400px;
}

.table-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .table-pagination {
    justify-content: center;
  }

  .table-pagination :deep(.el-pagination__sizes),
  .table-pagination :deep(.el-pagination__jump) {
    display: none;
  }
}
</style>
