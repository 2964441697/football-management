# 足球管理系统

现代化的高校足球俱乐部管理系统，提供球队、球员、比赛、财务等核心数据的高效管理和分析功能。

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端 | Flask + SQLAlchemy + MySQL |
| 前端 | Vue 3 + Vite + Element Plus |
| 认证 | JWT |
| 数据库 | MySQL 8.0+ |

## 功能特性

- 用户认证与权限管理
- 球队、球员、教练信息管理
- 比赛与赛事管理
- 合同与转会管理
- 财务管理
- 训练计划管理
- 新闻公告发布
- 数据统计与分析

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.9+
- MySQL 8.0+

### 1. 克隆项目

```bash
git clone <repository-url>
cd football-management
```

### 2. 配置数据库

```bash
# 方式1：直接导入 SQL 文件（推荐）
mysql -u root -p < db/football_db.sql

# 方式2：手动创建数据库
mysql -u root -p -e "CREATE DATABASE football_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
```

### 3. 后端启动

```bash
cd backend

# 创建虚拟环境（可选）
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\Activate
# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install Flask-Limiter

# 启动服务
python app.py
```

后端地址: http://localhost:5000

### 4. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端地址: http://localhost:5173

### 5. 测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 教练 | coach | coach123 |

## 项目结构

```
football-management/
├── backend/                 # Flask 后端
│   ├── api/                # API 路由模块
│   ├── utils/              # 工具模块
│   ├── scripts/            # 数据库优化脚本
│   ├── static/             # 静态资源
│   ├── app.py              # 应用入口
│   ├── config.py           # 配置文件
│   ├── models.py           # 数据模型
│   └── requirements.txt    # Python 依赖
│
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/            # API 服务
│   │   ├── components/     # Vue 组件
│   │   ├── views/          # 页面视图
│   │   ├── router/         # 路由
│   │   ├── stores/         # 状态管理
│   │   └── utils/          # 工具函数
│   └── package.json        # Node 依赖
│
└── db/                     # 数据库脚本
    └── football_db.sql    # 数据库初始化文件
```

## API 端点

| 模块 | 前缀 | 说明 |
|------|------|------|
| 认证 | `/api/auth` | 登录注册 |
| 球队 | `/api/teams` | 球队管理 |
| 球员 | `/api/players` | 球员管理 |
| 教练 | `/api/coaches` | 教练管理 |
| 比赛 | `/api/matches` | 比赛管理 |
| 赛季 | `/api/seasons` | 赛季管理 |
| 赛事 | `/api/competitions` | 赛事管理 |
| 合同 | `/api/contracts` | 合同管理 |
| 转会 | `/api/transfers` | 转会管理 |
| 财务 | `/api/finances` | 财务管理 |
| 训练 | `/api/training-plans` | 训练计划 |
| 新闻 | `/api/news` | 新闻管理 |
| 统计 | `/api/stats` | 数据统计 |

## 环境变量

在 `backend/.env` 中配置：

```env
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/football_db
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
FLASK_ENV=development
```

## 性能优化

项目已包含以下优化：

- **数据库索引**：复合索引提升查询性能
- **关联预加载**：使用 `lazy='joined'` 避免 N+1 查询
- **API 缓存**：前端 GET 请求 5 分钟缓存
- **速率限制**：默认 200次/天，50次/小时
- **图片懒加载**：前端图片按需加载

如需为现有数据库添加索引：

```bash
cd backend
python scripts/optimize_db.py
```

## 部署

### 生产环境

1. 设置 `FLASK_ENV=production`
2. 使用 Gunicorn 运行后端
3. 构建前端: `npm run build`
4. 配置 Nginx 反向代理

## 许可证

MIT License
