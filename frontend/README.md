# 前端应用 (Vue3 + Vite)

## 技术栈

- Vue 3.0+
- Vite 4.0+
- Element Plus 2.0+
- Pinia 2.0+
- Vue Router 4.0+
- Axios 1.0+
- ECharts 5.0+

## 快速开始

### 1. 安装依赖

```powershell
npm install
```

### 2. 启动开发服务器

```powershell
npm run dev
```

前端服务将在 `http://localhost:5173` 运行。

### 3. 构建生产版本

```powershell
npm run build
```

构建产物在 `dist/` 目录。

## 项目结构

```
frontend/
├── src/
│   ├── api/                # API接口封装
│   ├── components/         # Vue组件
│   │   ├── common/         # 公共组件
│   │   ├── Dashboard.vue  # 仪表盘
│   │   ├── TeamsPage.vue  # 球队管理
│   │   ├── PlayersPage.vue # 球员管理
│   │   └── ...            # 其他页面组件
│   ├── views/             # 视图组件
│   ├── router/            # 路由配置
│   ├── utils/             # 工具函数
│   ├── styles/            # 样式文件
│   ├── App.vue            # 根组件
│   └── main.js            # 应用入口
├── public/                # 静态资源
├── vite.config.js         # Vite配置
└── package.json           # 依赖配置
```

## 可用脚本

| 命令 | 说明 |
|------|------|
| `npm run dev` | 启动开发服务器 |
| `npm run build` | 构建生产版本 |
| `npm run preview` | 预览生产构建 |
| `npm run lint` | 运行代码检查 |
| `npm run format` | 格式化代码 |

## 功能特性

### 核心功能

- 用户认证（登录/注册）
- 球队、球员、教练管理
- 比赛和赛事管理
- 合同和转会管理
- 财务管理
- 训练计划管理
- 新闻公告管理
- 数据统计和分析

### UI特性

- 响应式设计
- 主题切换（明亮/暗黑）
- 背景自定义
- 数据表格组件
- 统一的工具栏
- 空状态展示

## 开发说明

### 组件开发

使用Vue 3 Composition API开发组件：

```vue
<template>
  <div>组件内容</div>
</template>

<script setup>
import { ref } from 'vue'

const count = ref(0)
</script>

<style scoped>
/* 组件样式 */
</style>
```

### API调用

使用封装的endpoints调用后端API：

```javascript
import endpoints from '@/api/endpoints'

// 获取球队列表
const teams = await endpoints.getTeams()

// 创建球队
await endpoints.createTeam(data)
```

### 路由配置

路由定义在 `router/index.js` 中：

```javascript
{
  path: '/teams',
  name: 'Teams',
  component: () => import('@/components/TeamsPage.vue'),
  meta: { requiresAuth: true }
}
```

## 环境变量

在 `.env` 文件中配置：

```
VITE_API_BASE_URL=http://localhost:5000/api
VITE_APP_TITLE=足球管理系统
```

## Vite配置

Vite配置在 `vite.config.js` 中：

- API代理到后端
- 路径别名 `@` 指向 `src`
- 构建优化配置

## 公共组件

### DataTable

可复用的数据表格组件，支持：
- 分页
- 搜索
- 筛选
- 选择和批量操作

### TableToolbar

表格工具栏组件，包含：
- 新增/刷新按钮
- 导出/批量删除
- 搜索框
- 筛选器

### EmptyState

空状态展示组件

### BackgroundSwitcher

背景切换组件，支持：
- 内置渐变背景
- 自定义图片URL
- 本地存储偏好

## 开发规范

- 使用Vue 3 Composition API
- 单文件组件结构
- Props和Emits完整声明
- 组件功能单一
- 遵循ESLint规则

## 常见问题

### 依赖安装失败

```powershell
npm cache clean --force
npm install
```

### 开发服务器无法启动

- 检查端口5173是否被占用
- 清除 `node_modules` 重新安装
- 检查Node.js版本（需要16+）

### API请求失败

- 确保后端服务在 `http://localhost:5000` 运行
- 检查浏览器控制台的网络请求
- 验证认证Token是否有效

## 更多文档

- [开发文档](../docs/开发文档.md)
- [API接口文档](../docs/API.md)
- [快速开始指南](../docs/QUICK_START.md)
