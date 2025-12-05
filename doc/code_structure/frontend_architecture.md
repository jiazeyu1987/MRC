# 前端架构详细文档

## React + TypeScript 应用架构

### 技术栈概览

MRC 前端采用现代化的 React 技术栈：

```json
{
  "framework": "React 18.2.0",
  "language": "TypeScript",
  "bundler": "Vite 4.4.5",
  "styling": "Tailwind CSS 3.3.0",
  "icons": "Lucide React",
  "state_management": "React Hooks + Context",
  "api_client": "Fetch API"
}
```

### 项目结构分析

```
front/src/
├── App.tsx                 # 根应用组件
├── main.tsx               # React 应用入口
├── MultiRoleDialogSystem.tsx  # 主应用界面 (63KB)
├── LLMTestPage.tsx        # LLM 测试界面
├── api/                   # API 客户端层
│   ├── roleApi.ts         # 角色管理 API
│   ├── flowApi.ts         # 流程模板 API
│   └── sessionApi.ts      # 会话管理 API
├── components/            # 可复用 UI 组件
│   ├── SessionTheater.tsx # 会话剧场组件
│   ├── DebugPanel.tsx     # 调试面板组件
│   ├── StepProgressDisplay.tsx  # 步骤进度显示
│   └── StepVisualization.tsx    # 步骤可视化
├── hooks/                 # 自定义 React Hooks
│   ├── useStepProgress.ts # 步骤进度管理
│   ├── useLLMInteractions.ts # LLM 交互追踪
│   └── useWebSocket.ts    # WebSocket 连接管理
├── types/                 # TypeScript 类型定义
├── utils/                 # 工具函数库
└── theme.tsx              # 主题系统配置
```

## 核心组件架构

### 1. 应用根组件 (App.tsx)

```tsx
function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MultiRoleDialogSystem />} />
          <Route path="/llm-test" element={<LLMTestPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}
```

**设计特点:**
- 单页应用 (SPA) 架构
- React Router 路由管理
- 全局样式和主题应用
- 错误边界和状态管理

### 2. 主应用组件 (MultiRoleDialogSystem.tsx)

这是整个应用的核心组件，包含了完整的多角色对话系统界面：

```tsx
export default function MultiRoleDialogSystem() {
  // 状态管理
  const [activeTab, setActiveTab] = useState('roles');
  const [roles, setRoles] = useState<Role[]>([]);
  const [flows, setFlows] = useState<FlowTemplate[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);

  // API 数据获取
  useEffect(() => {
    fetchRoles();
    fetchFlows();
    fetchSessions();
  }, []);

  // 标签页渲染
  const renderActiveTab = () => {
    switch (activeTab) {
      case 'roles': return <RoleManagement roles={roles} />;
      case 'flows': return <FlowManagement flows={flows} />;
      case 'sessions': return <SessionManagement sessions={sessions} />;
      default: return null;
    }
  };

  return (
    <div className="container mx-auto p-6">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">多角色对话系统</h1>
      </header>

      <div className="bg-white rounded-lg shadow">
        {/* 标签页导航 */}
        <TabNavigation
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />

        {/* 动态内容渲染 */}
        <div className="p-6">
          {renderActiveTab()}
        </div>
      </div>
    </div>
  );
}
```

**核心功能模块:**
- **角色管理**: 创建、编辑、删除虚拟角色
- **流程管理**: 设计和配置对话流程模板
- **会话管理**: 创建和监控对话会话
- **实时监控**: 会话执行状态和进度显示

### 3. API 客户端架构

#### 基础 API 客户端 (api/base.ts)

```typescript
class ApiClient {
  private baseURL: string;

  constructor() {
    // Vite 开发环境代理到后端
    this.baseURL = import.meta.env.VITE_API_BASE_URL || '/api';
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;

    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, { ...defaultOptions, ...options });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        data,
        message: '操作成功'
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : '未知错误'
      };
    }
  }

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    const url = params ? `${endpoint}?${new URLSearchParams(params)}` : endpoint;
    return this.request<T>(url);
  }

  async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }
}
```

#### 角色管理 API (api/roleApi.ts)

```typescript
export const roleApi = {
  // 获取角色列表
  async getRoles(page: number = 1, pageSize: number = 20): Promise<ApiResponse<Role[]>> {
    return apiClient.get<Role[]>('/roles', {
      page: page.toString(),
      page_size: pageSize.toString()
    });
  },

  // 创建角色
  async createRole(roleData: CreateRoleRequest): Promise<ApiResponse<Role>> {
    return apiClient.post<Role>('/roles', roleData);
  },

  // 更新角色
  async updateRole(id: number, roleData: UpdateRoleRequest): Promise<ApiResponse<Role>> {
    return apiClient.put<Role>(`/roles/${id}`, roleData);
  },

  // 删除角色
  async deleteRole(id: number): Promise<ApiResponse<void>> {
    return apiClient.delete<void>(`/roles/${id}`);
  }
};
```

#### 类型定义 (types/role.ts)

```typescript
export interface Role {
  id: number;
  name: string;
  prompt: string;
  created_at: string;
  updated_at: string;
}

export interface CreateRoleRequest {
  name: string;
  prompt: string;
}

export interface UpdateRoleRequest {
  name?: string;
  prompt?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  pagination?: {
    page: number;
    page_size: number;
    total: number;
    pages: number;
  };
}
```

## 自定义 Hooks 架构

### 1. 步骤进度管理 (useStepProgress.ts)

```typescript
export function useStepProgress(sessionId: number) {
  const [currentStep, setCurrentStep] = useState(0);
  const [totalSteps, setTotalSteps] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  // 获取步骤进度
  const fetchProgress = useCallback(async () => {
    try {
      const response = await sessionApi.getSessionProgress(sessionId);
      if (response.success && response.data) {
        setCurrentStep(response.data.current_step);
        setTotalSteps(response.data.total_steps);
        setIsRunning(response.data.status === 'running');
      }
    } catch (error) {
      console.error('获取进度失败:', error);
    }
  }, [sessionId]);

  // 启动步骤执行
  const runNextStep = useCallback(async () => {
    try {
      const response = await sessionApi.runNextStep(sessionId);
      if (response.success) {
        await fetchProgress(); // 刷新进度
      }
    } catch (error) {
      console.error('执行步骤失败:', error);
    }
  }, [sessionId, fetchProgress]);

  // 初始化
  useEffect(() => {
    fetchProgress();
  }, [fetchProgress]);

  return {
    currentStep,
    totalSteps,
    progress: totalSteps > 0 ? (currentStep / totalSteps) * 100 : 0,
    isRunning,
    runNextStep,
    refreshProgress: fetchProgress
  };
}
```

### 2. LLM 交互追踪 (useLLMInteractions.ts)

```typescript
export function useLLMInteractions() {
  const [interactions, setInteractions] = useState<LLMInteraction[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchInteractions = useCallback(async (filters?: InteractionFilters) => {
    setIsLoading(true);
    try {
      const response = await llmApi.getInteractions(filters);
      if (response.success && response.data) {
        setInteractions(response.data);
      }
    } catch (error) {
      console.error('获取交互记录失败:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const addInteraction = useCallback((interaction: LLMInteraction) => {
    setInteractions(prev => [interaction, ...prev]);
  }, []);

  return {
    interactions,
    isLoading,
    fetchInteractions,
    addInteraction
  };
}
```

### 3. WebSocket 连接管理 (useWebSocket.ts)

```typescript
export function useWebSocket(url: string) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket 连接已建立');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      } catch (error) {
        console.error('解析 WebSocket 消息失败:', error);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket 连接已关闭');
    };

    ws.onerror = (error) => {
      console.error('WebSocket 错误:', error);
    };

    setSocket(ws);

    return () => {
      ws.close();
    };
  }, [url]);

  const sendMessage = useCallback((message: any) => {
    if (socket && isConnected) {
      socket.send(JSON.stringify(message));
    }
  }, [socket, isConnected]);

  return {
    socket,
    isConnected,
    lastMessage,
    sendMessage
  };
}
```

## UI 组件架构

### 1. 会话剧场组件 (SessionTheater.tsx)

```typescript
interface SessionTheaterProps {
  session: Session;
  messages: Message[];
  onSendMessage: (content: string) => void;
  isLoading?: boolean;
}

export function SessionTheater({
  session,
  messages,
  onSendMessage,
  isLoading
}: SessionTheaterProps) {
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* 会话头部信息 */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {session.name}
            </h3>
            <p className="text-sm text-gray-500">
              状态: {getStatusText(session.status)}
            </p>
          </div>
          <StepProgressBar
            current={session.current_step}
            total={session.total_steps}
          />
        </div>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
          />
        ))}
        {isLoading && <LoadingSpinner />}
      </div>

      {/* 消息输入框 */}
      <form onSubmit={handleSubmit} className="bg-white border-t px-6 py-4">
        <div className="flex gap-4">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="输入消息..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            发送
          </button>
        </div>
      </form>
    </div>
  );
}
```

### 2. 步骤进度显示 (StepProgressDisplay.tsx)

```typescript
interface StepProgressDisplayProps {
  currentStep: number;
  totalSteps: number;
  steps: FlowStep[];
  isRunning: boolean;
}

export function StepProgressDisplay({
  currentStep,
  totalSteps,
  steps,
  isRunning
}: StepProgressDisplayProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-lg font-medium text-gray-900">执行进度</h4>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
          isRunning
            ? 'bg-green-100 text-green-800'
            : 'bg-gray-100 text-gray-800'
        }`}>
          {isRunning ? '执行中' : '已暂停'}
        </span>
      </div>

      {/* 进度条 */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>步骤 {currentStep + 1} / {totalSteps}</span>
          <span>{Math.round((currentStep / totalSteps) * 100)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${(currentStep / totalSteps) * 100}%` }}
          />
        </div>
      </div>

      {/* 步骤列表 */}
      <div className="space-y-2">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className={`flex items-center p-3 rounded-lg border ${
              index === currentStep
                ? 'border-blue-500 bg-blue-50'
                : index < currentStep
                ? 'border-green-500 bg-green-50'
                : 'border-gray-200 bg-white'
            }`}
          >
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium mr-3 ${
              index < currentStep
                ? 'bg-green-500 text-white'
                : index === currentStep
                ? 'bg-blue-500 text-white'
                : 'bg-gray-300 text-gray-600'
            }`}>
              {index < currentStep ? '✓' : index + 1}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">
                {step.description}
              </p>
              <p className="text-xs text-gray-500">
                角色: {step.speaker_role_ref} → {step.target_role_ref}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## 主题系统架构

### 主题配置 (theme.tsx)

```typescript
export interface Theme {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: {
      primary: string;
      secondary: string;
      muted: string;
    };
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      md: string;
      lg: string;
      xl: string;
    };
  };
}

export const themes: Record<string, Theme> = {
  blue: {
    colors: {
      primary: '#3B82F6',
      secondary: '#6366F1',
      accent: '#10B981',
      background: '#F9FAFB',
      surface: '#FFFFFF',
      text: {
        primary: '#111827',
        secondary: '#6B7280',
        muted: '#9CA3AF'
      }
    },
    spacing: {
      xs: '0.5rem',
      sm: '1rem',
      md: '1.5rem',
      lg: '2rem',
      xl: '3rem'
    },
    typography: {
      fontFamily: 'Inter, system-ui, sans-serif',
      fontSize: {
        xs: '0.75rem',
        sm: '0.875rem',
        md: '1rem',
        lg: '1.125rem',
        xl: '1.25rem'
      }
    }
  },
  purple: {
    // ... 紫色主题配置
  },
  emerald: {
    // ... 绿色主题配置
  },
  rose: {
    // ... 玫红色主题配置
  },
  amber: {
    // ... 琥珀色主题配置
  }
};

export const useTheme = (themeName: string = 'blue') => {
  const theme = themes[themeName] || themes.blue;

  const applyTheme = () => {
    // 应用主题到 CSS 变量
    Object.entries(theme.colors).forEach(([key, value]) => {
      const cssVar = `--color-${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`;
      document.documentElement.style.setProperty(cssVar, value);
    });
  };

  useEffect(() => {
    applyTheme();
  }, [theme]);

  return { theme, applyTheme };
};
```

## 构建和部署配置

### Vite 配置 (vite.config.ts)

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5010',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['lucide-react', 'clsx', 'tailwind-merge'],
          api: ['./src/api/roleApi.ts', './src/api/flowApi.ts', './src/api/sessionApi.ts']
        }
      }
    }
  }
});
```

### TypeScript 配置 (tsconfig.json)

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@/components/*": ["src/components/*"],
      "@/hooks/*": ["src/hooks/*"],
      "@/types/*": ["src/types/*"],
      "@/utils/*": ["src/utils/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

## 性能优化策略

### 1. 代码分割

```typescript
// 路由级别的代码分割
import { lazy } from 'react';

const MultiRoleDialogSystem = lazy(() => import('./MultiRoleDialogSystem'));
const LLMTestPage = lazy(() => import('./LLMTestPage'));

// 组件级别的代码分割
const DebugPanel = lazy(() => import('./components/DebugPanel'));
```

### 2. 状态优化

```typescript
// 使用 useMemo 优化计算密集型操作
const filteredRoles = useMemo(() => {
  return roles.filter(role =>
    role.name.toLowerCase().includes(searchTerm.toLowerCase())
  );
}, [roles, searchTerm]);

// 使用 useCallback 避免不必要的重渲染
const handleRoleCreate = useCallback(async (roleData: CreateRoleRequest) => {
  const response = await roleApi.createRole(roleData);
  if (response.success) {
    setRoles(prev => [...prev, response.data!]);
  }
}, []);
```

### 3. 数据获取优化

```typescript
// SWR 模式的数据获取
export function useRoles() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const fetchRoles = async () => {
      try {
        setLoading(true);
        const response = await roleApi.getRoles();
        if (!cancelled && response.success) {
          setRoles(response.data || []);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : '获取角色失败');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchRoles();

    return () => {
      cancelled = true;
    };
  }, []);

  const refetch = () => fetchRoles();

  return { roles, loading, error, refetch };
}
```

## 错误处理和日志

### 错误边界 (ErrorBoundary.tsx)

```typescript
export class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('React Error Boundary caught an error:', error, errorInfo);
    // 发送错误日志到监控服务
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              应用出现错误
            </h2>
            <p className="text-gray-600 mb-4">
              请刷新页面重试，或联系技术支持。
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              刷新页面
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

这个前端架构设计确保了应用的可维护性、可扩展性和良好的用户体验，同时提供了强大的 TypeScript 类型安全和性能优化。