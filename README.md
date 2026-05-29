# 光影甄选 (Photo Pick)

专业摄影选片工具 —— 高效浏览、评分、筛选和导出照片。

## 功能特性

- **照片导入**：扫描指定文件夹，自动读取 EXIF 信息（相机、镜头、光圈、ISO、快门等）
- **缩略图生成**：后台自动生成小（300px）和大（1920px）两种缩略图，WebSocket 实时通知前端
- **三种浏览模式**：网格视图、单张查看器、双图对比
- **评分标记**：1-5 星评分、彩色标签（红/黄/绿/蓝/紫）、入选/淘汰状态
- **筛选过滤**：按星级、状态、颜色标签组合筛选
- **连拍分组**：基于拍摄时间自动检测连拍序列
- **质量分析**：模糊检测（拉普拉斯算子）、曝光分析（直方图）、闭眼检测
- **批量导出**：支持复制/移动、按条件筛选、子文件夹分组、文件重命名模板
- **文件夹浏览器**：可视化选择导入/导出路径（支持 Windows 磁盘驱动器列表）
- **键盘快捷键**：全键盘操作支持
- **实时更新**：WebSocket 推送缩略图就绪、导入进度、导出进度等事件

## 技术栈

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.5 | UI 框架（Composition API + `<script setup>`） |
| TypeScript | ~5.6 | 类型安全 |
| Vite | ^6.0 | 构建工具 + 开发服务器 |
| Pinia | ^2.3 | 状态管理 |
| Vue Router | ^4.5 | 路由 |
| Tailwind CSS | ^3.4 | 样式（自定义奶油暖白主题） |
| Axios | ^1.7 | HTTP 客户端 |
| @vueuse/core | ^11.3 | Vue 工具集 |
| @tanstack/vue-virtual | ^3.11 | 虚拟列表（大量照片性能优化） |

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | >=0.115 | Web 框架 |
| Uvicorn | - | ASGI 服务器 |
| SQLAlchemy 2.0 | - | ORM（异步模式） |
| aiosqlite | - | SQLite 异步驱动 |
| Pillow | - | 图像处理 / 缩略图生成 |
| OpenCV (headless) | - | 图像质量分析 |
| ExifRead | - | EXIF 元数据读取 |
| imagehash | - | 图像相似度哈希 |
| Pydantic | - | 数据验证 / 配置管理 |

## 项目结构

```
photo-pick/
├── README.md
├── scripts/
│   ├── dev.bat              # 一键启动前后端开发服务器
│   └── stop.bat             # 停止所有服务
├── data/
│   ├── db/                  # SQLite 数据库文件
│   └── cache/               # 缩略图缓存
├── backend/
│   ├── pyproject.toml       # Python 项目配置
│   ├── requirements.txt     # 依赖锁定
│   └── app/
│       ├── main.py          # FastAPI 应用入口
│       ├── config.py        # 配置项（pydantic-settings）
│       ├── models/          # SQLAlchemy ORM 模型
│       ├── schemas/         # Pydantic 请求/响应模型
│       ├── api/             # API 路由层
│       │   ├── sessions.py  # 会话管理
│       │   ├── photos.py    # 照片列表 / 缩略图
│       │   ├── marks.py     # 评分 / 标记
│       │   ├── groups.py    # 连拍分组
│       │   ├── analysis.py  # 质量分析
│       │   ├── export.py    # 导出
│       │   ├── filesystem.py# 文件夹浏览
│       │   └── ws.py        # WebSocket
│       ├── services/        # 业务逻辑层
│       │   ├── import_service.py     # 照片导入
│       │   ├── thumbnail_service.py  # 缩略图生成
│       │   ├── grouping_service.py   # 连拍分组
│       │   └── ws_manager.py         # WebSocket 管理
│       ├── analysis/        # 图像分析模块
│       │   ├── blur_detector.py      # 模糊检测
│       │   ├── exposure_analyzer.py  # 曝光分析
│       │   └── eye_detector.py       # 闭眼检测
│       └── utils/
└── frontend/
    ├── package.json
    ├── vite.config.ts       # Vite 配置（API 代理）
    ├── tailwind.config.js   # Tailwind 主题配置
    └── src/
        ├── main.ts          # Vue 应用入口
        ├── App.vue
        ├── router/          # 路由配置
        ├── api/             # API 接口封装
        ├── types/           # TypeScript 类型定义
        ├── stores/          # Pinia 状态管理
        ├── composables/     # 组合式函数
        ├── views/           # 页面视图
        ├── components/      # UI 组件
        │   ├── grid/        # 网格视图组件
        │   ├── viewer/      # 查看器组件
        │   ├── compare/     # 对比视图组件
        │   ├── layout/      # 布局组件（筛选面板）
        │   ├── export/      # 导出弹窗
        │   └── common/      # 通用组件（文件夹选择器）
        └── styles/          # 全局样式
```

## 快速开始

### 环境要求

- **Node.js** >= 18
- **Python** >= 3.11
- **pnpm** 或 npm

### 安装

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
pnpm install   # 或 npm install
```

### 启动开发服务器

```bash
# 方式一：使用脚本一键启动
scripts/dev.bat

# 方式二：手动分别启动
# 终端 1 - 后端（端口 8000）
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 终端 2 - 前端（端口 5173）
cd frontend
npm run dev
```

访问 `http://localhost:5173` 即可使用。

### 生产构建

```bash
cd frontend
pnpm build     # 输出到 dist/
```

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/sessions` | 导入文件夹创建会话 |
| GET | `/api/sessions` | 获取会话列表 |
| GET | `/api/sessions/{id}` | 获取会话详情 |
| DELETE | `/api/sessions/{id}` | 删除会话 |
| GET | `/api/sessions/{id}/photos` | 获取照片列表（支持分页、筛选） |
| GET | `/api/photos/{id}/thumbnail/{size}` | 获取缩略图（sm/lg） |
| GET | `/api/photos/{id}/full` | 获取原图 |
| PATCH | `/api/photos/{id}/marks` | 更新评分/标记 |
| PATCH | `/api/photos/batch/marks` | 批量更新标记 |
| POST | `/api/sessions/{id}/groups/detect` | 自动检测连拍分组 |
| POST | `/api/sessions/{id}/analyze` | 启动质量分析 |
| POST | `/api/sessions/{id}/export` | 启动导出任务 |
| GET | `/api/filesystem/browse` | 浏览文件系统目录 |
| WS | `/ws/{session_id}` | WebSocket 实时推送 |

## 键盘快捷键

| 按键 | 功能 |
|------|------|
| `←` / `k` | 上一张 |
| `→` / `j` | 下一张 |
| `1` - `5` | 设置星级 |
| `0` | 清除星级 |
| `6` / `7` / `8` / `9` | 颜色标签：红/黄/绿/蓝 |
| `P` | 标记入选 |
| `X` | 标记淘汰 |
| `U` | 取消标记 |
| `Space` / `Z` | 切换缩放（查看器模式） |
| `Enter` / `F` | 进入查看器模式 |
| `G` | 进入网格模式 |
| `C` | 进入对比模式 |
| `Esc` | 返回上一层视图 |
| `PageUp` / `PageDown` | 翻页 |
| `Ctrl+E` | 打开导出弹窗 |

## 配置说明

后端配置通过环境变量或 `.env` 文件设置，前缀为 `PHOTO_PICK_`：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `PHOTO_PICK_DATA_DIR` | `../data` | 数据存储根目录 |
| `PHOTO_PICK_THUMBNAIL_SM_SIZE` | `300` | 小缩略图宽度（px） |
| `PHOTO_PICK_THUMBNAIL_LG_SIZE` | `1920` | 大缩略图宽度（px） |
| `PHOTO_PICK_THUMBNAIL_WORKERS` | `4` | 缩略图生成线程数 |
| `PHOTO_PICK_GROUPING_TIME_THRESHOLD_SECONDS` | `2.0` | 连拍分组时间阈值（秒） |

## WebSocket 事件

| 事件类型 | 数据 | 说明 |
|----------|------|------|
| `import_progress` | `{ current, total }` | 导入进度 |
| `import_complete` | `{}` | 导入完成 |
| `thumbnail_ready` | `{ photo_id }` | 单张缩略图就绪 |
| `thumbnail_progress` | `{ current, total }` | 缩略图生成进度 |
| `analysis_complete` | `{ photo_id }` | 单张分析完成 |
| `export_progress` | `{ current, total }` | 导出进度 |

## 许可证

私有项目，仅供内部使用。
