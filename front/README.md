# Multi-Role Chat Frontend - Migrated Version

## 项目说明

这是从原始项目 `D:\ProjectPackage\MultiRoleChat\fronted` 迁移过来的前端应用。

## 迁移日期

2025-12-05

## 技术栈

- **React 18.2.0** - 用户界面框架
- **TypeScript** - 类型安全的JavaScript
- **Vite** - 快速的构建工具
- **Tailwind CSS** - 实用优先的CSS框架
- **Lucide React** - 现代化的图标库

## 主要功能

### 核心界面
- **MultiRoleDialogSystem.tsx** - 主要的多角色对话系统界面
- **LLMTestPage.tsx** - LLM集成测试页面
- **主题系统** - 支持5种颜色主题

### API集成
- **roleApi.ts** - 角色管理API客户端
- **flowApi.ts** - 流程模板API客户端
- **sessionApi.ts** - 会话管理API客户端
- **errorHandler.ts** - 统一错误处理

### 组件库
- **StepProgressDisplay** - 步骤进度显示
- **StepVisualization** - 流程可视化
- **DebugPanel** - 调试面板（已禁用实时功能）
- **SessionTheater** - 会话剧场界面

## 已移除的功能

为了提高系统稳定性，以下功能已被移除：
- LLM Interactions监控组件
- 实时LLM交互追踪
- 相关的API调用和状态管理

## 安装和运行

### 前置要求
- Node.js 16+
- npm 或 yarn

### 1. 安装依赖
```bash
cd D:/ProjectPackage/MRC/front
npm install
```

### 2. 启动开发服务器
```bash
npm run dev
```

应用将在 http://localhost:3000 启动

### 3. 构建生产版本
```bash
npm run build
```

### 4. 预览生产构建
```bash
npm run preview
```

## 配置说明

### API代理配置
Vite开发服务器配置了API代理，将 `/api/*` 请求转发到后端服务器：
- 前端：http://localhost:3000
- 后端：http://localhost:5010

### 环境变量
可以在 `.env` 文件中配置：
- `VITE_API_BASE_URL_ALT` - 备用API基础URL

## 项目结构

```
D:/ProjectPackage/MRC/front/
├── src/
│   ├── api/           # API客户端
│   ├── components/    # React组件
│   ├── hooks/         # 自定义Hooks
│   ├── types/         # TypeScript类型定义
│   ├── utils/         # 工具函数
│   ├── test/          # 测试文件
│   ├── App.tsx        # 根组件
│   ├── main.tsx       # 应用入口
│   └── theme.tsx      # 主题配置
├── public/            # 静态资源
├── dist/              # 构建输出
├── package.json       # 项目配置
├── vite.config.ts     # Vite配置
└── README.md          # 项目说明
```

## 开发注意事项

1. **端口配置** - 开发服务器运行在端口3000
2. **API连接** - 确保后端服务器在端口5010运行
3. **TypeScript** - 启用了严格模式和未使用变量检查
4. **样式** - 使用Tailwind CSS实用类
5. **图标** - 使用Lucide React图标库

## 已知问题

- **构建错误** - 某些组件存在TypeScript语法错误，但不影响开发
- **ESLint配置** - 需要初始化ESLint配置文件
- **测试环境** - 需要安装测试相关依赖

## 原始项目

原始项目位置：`D:\ProjectPackage\MultiRoleChat\fronted`

此迁移保持了完整的UI功能，并优化了API连接配置以匹配新的后端位置。

## 快速开始

1. 确保后端服务器运行在 `http://localhost:5010`
2. 在新目录中安装依赖：`npm install`
3. 启动开发服务器：`npm run dev`
4. 访问 `http://localhost:3000` 开始使用