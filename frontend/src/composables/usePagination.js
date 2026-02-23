import { ref, computed, watch } from 'vue'
import { debounce } from '../utils/helpers'

/**
 * 分页和搜索 composable
 * @param {Function} fetchFn - 获取数据的函数，接收 { page, pageSize, search, ...filters } 参数
 * @param {Object} options - 配置选项
 * @param {number} options.defaultPageSize - 默认每页条数，默认 20
 * @param {number} options.debounceMs - 搜索防抖时间，默认 300ms
 * @param {boolean} options.immediate - 是否立即加载，默认 true
 */
export function usePagination(fetchFn, options = {}) {
  const {
    defaultPageSize = 20,
    debounceMs = 300,
    immediate = true
  } = options

  // 分页状态
  const currentPage = ref(1)
  const pageSize = ref(defaultPageSize)
  const total = ref(0)
  const loading = ref(false)
  
  // 数据
  const data = ref([])
  
  // 搜索和筛选
  const searchQuery = ref('')
  const filters = ref({})

  // 加载数据
  async function loadData() {
    loading.value = true
    try {
      const result = await fetchFn({
        page: currentPage.value,
        pageSize: pageSize.value,
        search: searchQuery.value,
        ...filters.value
      })
      
      // 支持两种返回格式
      if (result.items !== undefined) {
        data.value = result.items
        total.value = result.total
      } else if (Array.isArray(result)) {
        data.value = result
        total.value = result.length
      } else {
        data.value = result.data || []
        total.value = result.total || result.data?.length || 0
      }
    } catch (error) {
      console.error('加载数据失败:', error)
      data.value = []
      total.value = 0
    } finally {
      loading.value = false
    }
  }

  // 防抖搜索
  const debouncedLoad = debounce(() => {
    currentPage.value = 1
    loadData()
  }, debounceMs)

  // 搜索处理
  function handleSearch(query) {
    if (query !== undefined) {
      searchQuery.value = query
    }
    debouncedLoad()
  }

  // 筛选处理
  function handleFilter(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
    currentPage.value = 1
    loadData()
  }

  // 清除筛选
  function clearFilters() {
    filters.value = {}
    searchQuery.value = ''
    currentPage.value = 1
    loadData()
  }

  // 分页变更
  function handleSizeChange(size) {
    pageSize.value = size
    currentPage.value = 1
    loadData()
  }

  function handleCurrentChange(page) {
    currentPage.value = page
    loadData()
  }

  // 刷新当前页
  function refresh() {
    loadData()
  }

  // 重置到第一页并刷新
  function reset() {
    currentPage.value = 1
    searchQuery.value = ''
    filters.value = {}
    loadData()
  }

  // 计算属性
  const isEmpty = computed(() => data.value.length === 0 && !loading.value)
  const hasData = computed(() => data.value.length > 0)
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

  // 立即加载
  if (immediate) {
    loadData()
  }

  return {
    // 状态
    data,
    loading,
    currentPage,
    pageSize,
    total,
    searchQuery,
    filters,
    
    // 计算属性
    isEmpty,
    hasData,
    totalPages,
    
    // 方法
    loadData,
    handleSearch,
    handleFilter,
    clearFilters,
    handleSizeChange,
    handleCurrentChange,
    refresh,
    reset
  }
}

export default usePagination
