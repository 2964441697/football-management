export function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

export function exportToCSV(data, filename) {
  if (!data || data.length === 0) {
    return
  }

  const headers = Object.keys(data[0])
  const csvContent = [
    headers.join(','),
    ...data.map(row => headers.map(header => {
      const value = row[header]
      const stringValue = value === null || value === undefined ? '' : String(value)
      if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
        return `"${stringValue.replace(/"/g, '""')}"`
      }
      return stringValue
    }).join(','))
  ].join('\n')

  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `${filename}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export function exportToExcel(data, filename) {
  if (!data || data.length === 0) {
    return
  }

  const headers = Object.keys(data[0])
  const workbook = []
  const worksheet = [headers, ...data.map(row => headers.map(header => row[header] ?? ''))]
  
  let csv = '\uFEFF'
  worksheet.forEach(row => {
    csv += row.map(cell => {
      const stringValue = String(cell ?? '')
      if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
        return `"${stringValue.replace(/"/g, '""')}"`
      }
      return stringValue
    }).join(',') + '\n'
  })

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `${filename}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export function formatMoney(amount) {
  if (amount === null || amount === undefined) return '-'
  return `¥${Number(amount).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`
}

export function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

export function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 获取静态资源的完整 URL
 * 用于头像、图片等静态文件
 * @param {string} path - 资源路径 (如 /static/uploads/avatar.jpg)
 * @returns {string} 完整的 URL
 */
export function getStaticUrl(path) {
  if (!path) return ''
  // 如果已经是完整的 URL，直接返回
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  // 从环境变量获取静态资源基础 URL
  const staticBase = import.meta.env.VITE_STATIC_BASE_URL || import.meta.env.VITE_API_BASE_URL || ''
  // 移除 /api 后缀 (如果有的话)
  const baseUrl = staticBase.replace(/\/api\/?$/, '')
  return `${baseUrl}${path}`
}