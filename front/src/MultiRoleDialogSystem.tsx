import { useState, useEffect, useContext, createContext, useRef, useMemo } from 'react';
import SimpleLLMDebugPanel from './components/SimpleLLMDebugPanel';

// Create LLM Debug Context
const LLMDebugContext = createContext<{
  updateLLMDebugInfo: (debugInfo: any) => void;
}>({
  updateLLMDebugInfo: () => {}
});
import {
  Users,
  GitBranch,
  MessageSquare,
  Play,
  Plus,
  Search,
  Trash2,
  Edit3,
  Save,
  X,
  ChevronRight,
  ChevronDown,
  Download,
  CheckCircle,
  ArrowRight,
  FileText,
  Settings,
  RefreshCw,
  CornerDownLeft,
  Lightbulb,
  LogOut,
  RotateCcw,
  Globe,
  Key,
  FileCheck
} from 'lucide-react';


// --- API和类型导入 ---
import { roleApi } from './api/roleApi';
import { flowApi, FlowTemplate, FlowStep } from './api/flowApi';
import { sessionApi, Session, Message } from './api/sessionApi';
import { Role, RoleRequest } from './types/role';
import { handleError } from './utils/errorHandler';

// --- 主题配置系统 ---

type ThemeKey = 'blue' | 'purple' | 'emerald' | 'rose' | 'amber';

interface ThemeConfig {
  name: string;
  primary: string;       // 按钮背景、Sidebar激活
  primaryHover: string;  // 按钮悬停
  text: string;          // 链接文字、图标颜色
  textHover: string;     // 链接悬停
  bgSoft: string;        // 浅色背景 (Card highlight)
  border: string;        // 边框高亮
  ring: string;          // 输入框Focus
  iconBg: string;        // 圆形图标背景
  badge: string;         // Badge 样式
}

const THEMES: Record<ThemeKey, ThemeConfig> = {
  blue: {
    name: '商务蓝',
    primary: 'bg-blue-600',
    primaryHover: 'hover:bg-blue-700',
    text: 'text-blue-600',
    textHover: 'hover:text-blue-800',
    bgSoft: 'bg-blue-50',
    border: 'border-blue-200',
    ring: 'focus:ring-blue-200',
    iconBg: 'bg-blue-500',
    badge: 'bg-blue-100 text-blue-800'
  },
  purple: {
    name: '优雅紫',
    primary: 'bg-purple-600',
    primaryHover: 'hover:bg-purple-700',
    text: 'text-purple-600',
    textHover: 'hover:text-purple-800',
    bgSoft: 'bg-purple-50',
    border: 'border-purple-200',
    ring: 'focus:ring-purple-200',
    iconBg: 'bg-purple-500',
    badge: 'bg-purple-100 text-purple-800'
  },
  emerald: {
    name: '清新绿',
    primary: 'bg-emerald-600',
    primaryHover: 'hover:bg-emerald-700',
    text: 'text-emerald-600',
    textHover: 'hover:text-emerald-800',
    bgSoft: 'bg-emerald-50',
    border: 'border-emerald-200',
    ring: 'focus:ring-emerald-200',
    iconBg: 'bg-emerald-500',
    badge: 'bg-emerald-100 text-emerald-800'
  },
  rose: {
    name: '活力红',
    primary: 'bg-rose-600',
    primaryHover: 'hover:bg-rose-700',
    text: 'text-rose-600',
    textHover: 'hover:text-rose-800',
    bgSoft: 'bg-rose-50',
    border: 'border-rose-200',
    ring: 'focus:ring-rose-200',
    iconBg: 'bg-rose-500',
    badge: 'bg-rose-100 text-rose-800'
  },
  amber: {
    name: '暖阳橙',
    primary: 'bg-amber-600',
    primaryHover: 'hover:bg-amber-700',
    text: 'text-amber-600',
    textHover: 'hover:text-amber-800',
    bgSoft: 'bg-amber-50',
    border: 'border-amber-200',
    ring: 'focus:ring-amber-200',
    iconBg: 'bg-amber-500',
    badge: 'bg-amber-100 text-amber-800'
  }
};

const ThemeContext = createContext<{
  themeKey: ThemeKey;
  theme: ThemeConfig;
  setThemeKey: (k: ThemeKey) => void;
}>({ 
  themeKey: 'blue', 
  theme: THEMES.blue, 
  setThemeKey: () => {} 
});

const useTheme = () => useContext(ThemeContext);

// --- 类型定义 ---

// Multi-select dropdown component
const MultiSelectContextDropdown: React.FC<{
  value: string | string[];
  onChange: (value: string | string[]) => void;
  roles: Role[];
  className?: string;
}> = ({ value, onChange, roles, className = "" }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Convert value to array for handling (support both strings and JSON arrays)
  const selectedValues = useMemo(() => {
    if (Array.isArray(value)) {
      return value;
    }

    if (!value) {
      return [];
    }

    // Try to parse as JSON array (for multi-role selections)
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed : [value];
    } catch {
      // If not valid JSON, treat as single string value
      return [value];
    }
  }, [value]);

  // Options available
  const systemOptions = [
    { value: 'all', label: '全部历史', type: 'system' },
    { value: '__TOPIC__', label: '预设议题', type: 'system' }
  ];

  const roleOptions = roles.map(role => ({
    value: role.name,
    label: role.name,
    type: 'role'
  }));

  const allOptions = [...systemOptions, ...roleOptions];

  const handleToggle = (optionValue: string) => {
    let newSelectedValues: string[];

    if (optionValue === 'all' || optionValue === '__TOPIC__') {
      // System options are single-select
      newSelectedValues = [optionValue];
    } else {
      // Role options are multi-select
      if (selectedValues.includes(optionValue)) {
        newSelectedValues = selectedValues.filter(v => v !== optionValue);
      } else {
        // Remove system options when selecting roles
        newSelectedValues = selectedValues.filter(v => !['all', '__TOPIC__'].includes(v));
        newSelectedValues.push(optionValue);
      }
    }

    // Convert to appropriate format for backend
    let result: string | string[];
    if (newSelectedValues.length === 0) {
      result = '';
    } else if (newSelectedValues.length === 1 && ['all', '__TOPIC__'].includes(newSelectedValues[0])) {
      // System options remain as single strings
      result = newSelectedValues[0];
    } else {
      // Multiple roles get serialized as JSON array for backend
      result = JSON.stringify(newSelectedValues);
    }

    onChange(result);
  };

  const handleRemove = (optionValue: string) => {
    handleToggle(optionValue);
  };

  const getDisplayText = () => {
    if (selectedValues.length === 0) return '选择上下文策略';

    if (selectedValues.length === 1) {
      const option = allOptions.find(o => o.value === selectedValues[0]);
      return option ? option.label : selectedValues[0];
    }

    return `已选择 ${selectedValues.length} 项`;
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <div
        className={`w-full border rounded px-2 py-1 text-sm cursor-pointer min-h-[32px] flex items-center justify-between ${className}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="truncate">{getDisplayText()}</span>
        <ChevronDown size={16} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </div>

      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border rounded shadow-lg max-h-60 overflow-auto">
          {allOptions.map((option) => (
            <div
              key={option.value}
              className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer"
              onClick={() => handleToggle(option.value)}
            >
              <input
                type="checkbox"
                checked={selectedValues.includes(option.value)}
                onChange={() => {}}
                className="mr-2"
              />
              <span className="text-sm">{option.label}</span>
              {option.type === 'role' && (
                <span className="ml-2 text-xs text-gray-400">(角色)</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Selected items display */}
      {selectedValues.length > 1 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {selectedValues.map((selectedValue) => {
            const option = allOptions.find(o => o.value === selectedValue);
            return (
              <span
                key={selectedValue}
                className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
              >
                {option ? option.label : selectedValue}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemove(selectedValue);
                  }}
                  className="hover:text-blue-600"
                >
                  ×
                </button>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
};

// Session and Message types are now imported from sessionApi

// Mock API removed - now using real roleApi

// --- UI Components ---

const Button = ({ children, onClick, variant = 'primary', className = '', disabled = false, icon: Icon, size = 'md' }: any) => {
  const { theme } = useTheme();
  
  const baseStyle = "rounded-lg font-medium transition-all flex items-center justify-center gap-2";
  const sizes: any = {
    xs: "px-2.5 py-1 text-xs",
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2"
  };
  
  // Dynamic class construction based on theme
  const variants: any = {
    primary: `${theme.primary} text-white ${theme.primaryHover} disabled:bg-gray-300`,
    secondary: "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:bg-gray-100",
    danger: "bg-red-50 text-red-600 hover:bg-red-100",
    ghost: "text-gray-600 hover:bg-gray-100",
  };

  return (
    <button 
      onClick={onClick} 
      disabled={disabled}
      className={`${baseStyle} ${sizes[size]} ${variants[variant]} ${className}`}
    >
      {Icon && <Icon size={size === 'sm' || size === 'xs' ? 14 : 18} />}
      {children}
    </button>
  );
};

const Card = ({ children, className = '', title, actions }: any) => (
  <div className={`bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden ${className}`}>
    {(title || actions) && (
      <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
        <h3 className="font-semibold text-gray-800">{title}</h3>
        <div className="flex gap-2">{actions}</div>
      </div>
    )}
    <div className="p-6">{children}</div>
  </div>
);

const Badge = ({ children, color = 'theme' }: any) => {
  const { theme } = useTheme();
  
  // Custom theme badge or semantic colors
  let colorClass = "";
  if (color === 'theme') colorClass = theme.badge;
  else if (color === 'green') colorClass = "bg-green-100 text-green-800";
  else if (color === 'gray') colorClass = "bg-gray-100 text-gray-800";
  else if (color === 'red') colorClass = "bg-red-100 text-red-800";
  else colorClass = "bg-blue-100 text-blue-800"; // fallback

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>
      {children}
    </span>
  );
};

const Modal = ({ isOpen, onClose, title, children, footer }: any) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl animate-in fade-in zoom-in duration-200">
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <h3 className="text-lg font-bold">{title}</h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded"><X size={20} /></button>
        </div>
        <div className="p-6 overflow-y-auto flex-1">{children}</div>
        {footer && <div className="px-6 py-4 border-t bg-gray-50 rounded-b-xl flex justify-end gap-3">{footer}</div>}
      </div>
    </div>
  );
};

const EmptyState = ({ message, action }: any) => (
  <div className="flex flex-col items-center justify-center py-16 text-gray-500">
    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
      <Search size={24} className="text-gray-400" />
    </div>
    <p className="mb-4">{message}</p>
    {action}
  </div>
);

// --- Pages ---

// 1. Role Management
const RoleManagement = () => {
  const { theme } = useTheme();
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Partial<Role>>({});
  const [saving, setSaving] = useState(false);

  const fetchRoles = async () => {
    try {
      setLoading(true);
      const response = await roleApi.getRoles();
      setRoles(response.items);
    } catch (error: any) {
      console.error('获取角色列表失败:', error);
      alert(error.message || '获取角色列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  const handleSave = async () => {
    try {
      if (!editingRole.name || !editingRole.prompt) {
        alert("请填写角色名称和提示词");
        return;
      }

      setSaving(true);

      const roleData: RoleRequest = {
        name: editingRole.name!,
        prompt: editingRole.prompt!
      };

      if (editingRole.id) {
        // 更新现有角色
        await roleApi.updateRole(editingRole.id, roleData);
      } else {
        // 创建新角色
        await roleApi.createRole(roleData);
      }

      setIsModalOpen(false);
      setEditingRole({});
      await fetchRoles(); // 重新获取列表
    } catch (error: any) {
      console.error('保存角色失败:', error);
      alert(error.message || '保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (confirm(`确认删除角色"${name}"吗？`)) {
      try {
        await roleApi.deleteRole(id);
        await fetchRoles(); // 重新获取列表
      } catch (error: any) {
        console.error('删除角色失败:', error);
        alert(error.message || '删除失败');
      }
    }
  };

  const openEditModal = (role: Role) => {
    setEditingRole(role);
    setIsModalOpen(true);
  };

  const openCreateModal = () => {
    setEditingRole({});
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingRole({});
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">角色管理</h1>
          <p className="text-gray-500 text-sm mt-1">创建角色并定义其核心 Prompt</p>
        </div>
        <Button onClick={openCreateModal} icon={Plus} disabled={loading}>新建角色</Button>
      </div>

      {loading ? (
        <div className="flex justify-center py-10">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {roles.map(role => (
            <Card key={role.id} className={`hover:shadow-md transition-shadow hover:border-${theme.name === '商务蓝' ? 'blue' : 'gray'}-300`}>
              <div className="flex justify-between items-center h-full">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${theme.iconBg}`}>
                    {role.name[0]}
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900">{role.name}</h3>
                    <p className="text-xs text-gray-500">
                      创建于 {new Date(role.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => openEditModal(role)}
                    className={`p-2 text-gray-400 ${theme.textHover} hover:bg-gray-50 rounded-full transition-colors`}
                    title="编辑角色"
                  >
                    <Edit3 size={18} />
                  </button>
                  <button
                    onClick={() => handleDelete(role.id, role.name)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
                    title="删除角色"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            </Card>
          ))}
          {roles.length === 0 && (
            <div className="col-span-full py-10">
              <EmptyState message="暂无角色，请点击右上角新建" />
            </div>
          )}
        </div>
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingRole.id ? "编辑角色" : "新建角色"}
        footer={
          <>
            <Button variant="secondary" onClick={closeModal} disabled={saving}>
              取消
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? '保存中...' : '保存'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              角色名称 <span className="text-red-500">*</span>
            </label>
            <input
              className={`w-full border rounded-lg px-3 py-2 ${theme.ring}`}
              value={editingRole.name || ''}
              onChange={e => setEditingRole({...editingRole, name: e.target.value})}
              placeholder="请输入唯一角色名称"
              disabled={saving}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              角色提示词 (Prompt) <span className="text-red-500">*</span>
            </label>
            <textarea
              className={`w-full border rounded-lg px-3 py-2 h-40 ${theme.ring}`}
              value={editingRole.prompt || ''}
              onChange={e => setEditingRole({...editingRole, prompt: e.target.value})}
              placeholder="请输入角色的设定、风格、行为准则等提示词..."
              disabled={saving}
            />
            <p className="text-xs text-gray-500 mt-1">
              提示词用于定义角色的性格、专业背景、说话风格等特征
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
};

// 2. Flow Templates
const FlowManagement = () => {
  const { theme } = useTheme();
  const [flows, setFlows] = useState<FlowTemplate[]>([]);
  const [editingFlow, setEditingFlow] = useState<Partial<FlowTemplate> | null>(null);

  useEffect(() => {
    // 加载流程模板列表
    fetchFlows();
  }, []); 

  const handleCreate = () => {
    setEditingFlow({ name: "新对话流程", topic: "", is_active: true, steps: [] });
  };

  const handleEdit = async (flow: FlowTemplate) => {
    try {
      // 从后端获取完整模板详情（包含步骤等配置）
      const fullFlow = await flowApi.getFlow(flow.id);
      setEditingFlow(fullFlow as Partial<FlowTemplate>);
    } catch (error) {
      console.error('获取流程模板详情失败:', error);
      alert((error as Error).message || '获取模板详情失败');
    }
  }

  const fetchFlows = async () => {
    try {
      const result = await flowApi.getFlows();
      setFlows(result.items as FlowTemplate[]);
    } catch (error) {
      console.error('获取流程模板失败:', error);
    }
  };

  const handleClearAll = async () => {
    // 显示确认对话框
    const confirmed = window.confirm(
      `确定要删除所有 ${flows.length} 个流程模板吗？\n\n此操作不可恢复，将删除所有模板和相关的步骤数据。`
    );

    if (!confirmed) {
      return;
    }

    // 二次确认
    const finalConfirmation = window.confirm(
      '请再次确认：真的要删除所有流程模板吗？\n\n输入"确定"继续，输入"取消"停止操作。'
    );

    if (!finalConfirmation) {
      return;
    }

    try {
      // 调用API删除所有模板
      const result = await flowApi.clearAllFlows();

      // 显示成功消息
      alert(`删除成功！\n已删除 ${result.deleted_templates} 个模板和 ${result.deleted_steps} 个步骤。`);

      // 重新加载模板列表
      await fetchFlows();

    } catch (error) {
      console.error('删除所有模板失败:', error);
      alert(`删除失败: ${(error as Error).message || '删除所有模板时发生错误'}`);
    }
  };

  // 日志格式化函数
  const formatTemplateForLog = (flow: any) => {
    const timestamp = new Date().toISOString();

    console.log(`=== 模板保存开始 [${timestamp}] ===`);

    // 基本模板信息
    console.log('模板基本信息：');
    console.log(`- ID: ${flow.id || '新模板'}`);
    console.log(`- 名称: "${flow.name || '未命名模板'}"`);
    console.log(`- 主题: "${flow.topic || '无主题'}"`);
    console.log(`- 状态: ${flow.is_active ? 'active' : 'inactive'}`);
    console.log(`- 步骤数量: ${flow.steps?.length || 0}`);

    // 详细步骤信息
    if (flow.steps && flow.steps.length > 0) {
      console.log('\n模板步骤详情：');
      flow.steps.forEach((step: any, index: number) => {
        console.log(`步骤 ${index + 1}:`);
        console.log(`  - 顺序: ${step.order}`);
        console.log(`  - 说话角色: ${step.speaker_role_ref}`);
        console.log(`  - 目标角色: ${step.target_role_ref || '无'}`);
        console.log(`  - 任务类型: ${step.task_type}`);
        console.log(`  - 上下文范围: ${step.context_scope}`);
        console.log(`  - 上下文参数: ${JSON.stringify(step.context_param || {})}`);
        console.log(`  - 逻辑配置: ${JSON.stringify(step.logic_config || {})}`);
        console.log(`  - 描述: ${step.description || '无描述'}`);

        if (step.next_step_id) {
          console.log(`  - 下一步ID: ${step.next_step_id}`);
        }

        // 添加分隔符
        if (index < flow.steps.length - 1) {
          console.log('');
        }
      });
    }

    // 完整数据快照
    console.log('\n完整数据快照：');
    console.log(JSON.stringify(flow, null, 2));

    console.log(`=== 模板保存完成 ===`);
  };

  if (editingFlow) {
    return <FlowEditor flow={editingFlow} onSave={async (flow: any) => {
      // 保存前详细日志记录
      formatTemplateForLog(flow);

      try {
        console.log("开始调用后端API保存模板...");

        // 判断是新建还是更新
        const isUpdate = flow.id && flow.id > 0;

        // normalize steps for API: strip frontend-only id and flow_template_id fields
        const normalizedSteps = (flow.steps || []).map((step: any) => {
          const { id, flow_template_id, ...rest } = step;
          return rest;
        });

        let result;
        if (isUpdate) {
          console.log(`更新现有模板，ID: ${flow.id}`);
          result = await flowApi.updateFlow(flow.id, {
            name: flow.name,
            topic: flow.topic,
            type: flow.type || 'teaching',
            description: flow.description,
            version: flow.version,
            is_active: flow.is_active,
            termination_config: flow.termination_config,
            steps: normalizedSteps
          });
        } else {
          console.log("创建新模板");
          result = await flowApi.createFlow({
            name: flow.name,
            topic: flow.topic,
            type: flow.type || 'teaching',
            description: flow.description,
            version: flow.version,
            is_active: flow.is_active,
            termination_config: flow.termination_config,
            steps: normalizedSteps
          });
        }

        console.log("API调用成功，返回结果:", result);

        // 刷新模板列表
        await fetchFlows();

        setEditingFlow(null);
      } catch (error) {
        console.error("保存模板失败:", error);
        alert(`保存模板失败: ${(error as Error).message || '未知错误'}`);
      }
    }} onCancel={() => setEditingFlow(null)} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">流程模板</h1>
          <p className="text-gray-500 text-sm mt-1">设计对话的SOP（标准作业程序）</p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={handleClearAll}
            variant="danger"
            icon={Trash2}
            disabled={flows.length === 0}
          >
            删除所有
          </Button>
          <Button onClick={handleCreate} icon={Plus}>新建模板</Button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">模板名称</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">议题</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">步骤数</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">状态</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600 text-right">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {flows.map(flow => (
              <tr key={flow.id} className="hover:bg-gray-50/50">
                <td className="px-6 py-4 font-medium text-gray-900">{flow.name}</td>
                <td className="px-6 py-4 text-gray-600 max-w-xs truncate">{flow.topic || '-'}</td>
                <td className="px-6 py-4 text-gray-600">{flow.steps?.length || 0}</td>
                <td className="px-6 py-4">
                  <Badge color={flow.is_active ? 'green' : 'gray'}>{flow.is_active ? '启用' : '禁用'}</Badge>
                </td>
                <td className="px-6 py-4 text-right">
                  <button onClick={() => handleEdit(flow)} className={`${theme.text} ${theme.textHover} font-medium text-sm`}>编辑</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {flows.length === 0 && <EmptyState message="暂无流程模板" />}
      </div>
    </div>
  );
};

// Flow Editor Sub-component
const FlowEditor = ({ flow, onSave, onCancel }: any) => {
  const { theme } = useTheme();
  const [data, setData] = useState(flow);
  const [steps, setSteps] = useState<FlowStep[]>(flow.steps || []);
  const [roles, setRoles] = useState<Role[]>([]);
  const [expandedLogicStep, setExpandedLogicStep] = useState<number | null>(null);

  useEffect(() => {
    roleApi.getRoles().then(res => setRoles(res.items));
  }, []);

  // 当外部传入的 flow 发生变化（例如从后端重新加载模板详情时），同步更新本地表单和步骤状态
  useEffect(() => {
    setData(flow);
    setSteps(flow.steps || []);
  }, [flow]);

  const addStep = () => {
    const newStep: FlowStep = {
      id: Date.now(),
      flow_template_id: data.id || 0, // 临时ID，保存时由后端分配
      order: steps.length + 1,
      speaker_role_ref: roles[0]?.name || '',
      task_type: 'ask_question',
      context_scope: 'all'
    };
    setSteps([...steps, newStep]);
  };

  const updateStep = (index: number, field: string, value: any) => {
    const newSteps = [...steps];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setSteps(newSteps);
  };

  
  const updateLogicConfig = (index: number, field: string, value: any) => {
    const newSteps = [...steps];
    const currentLogic = newSteps[index].logic_config || {};
    newSteps[index].logic_config = { ...currentLogic, [field]: value };
    setSteps(newSteps);
  };

  const deleteStep = (index: number) => {
    const newSteps = steps.filter((_, i) => i !== index).map((s, i) => ({ ...s, order: i + 1 }));
    setSteps(newSteps);
  };

  return (
    <div className="space-y-6 animate-in slide-in-from-right duration-300">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={onCancel} className="p-2 hover:bg-gray-100 rounded-full"><ArrowRight className="rotate-180" /></button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{data.id ? '编辑模板' : '新建模板'}</h1>
        </div>
        <div className="ml-auto flex gap-3">
          <Button variant="secondary" onClick={onCancel}>取消</Button>
          <Button onClick={() => onSave({ ...data, steps })} icon={Save}>保存模板</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="基本信息" className="h-fit">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">模板名称</label>
              <input className={`w-full border rounded-lg px-3 py-2 ${theme.ring}`} value={data.name} onChange={e => setData({...data, name: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                <Lightbulb size={14} className="text-yellow-500"/> 预设议题 (Topic)
              </label>
              <textarea 
                className={`w-full border rounded-lg px-3 py-2 bg-yellow-50/50 border-yellow-200 focus:ring-yellow-200 h-48`}
                placeholder="例如：动量守恒的适用条件..."
                value={data.topic || ''} 
                onChange={e => setData({...data, topic: e.target.value})} 
              />
              <p className="text-xs text-gray-500 mt-1">若填写，会话的第一位发言者将针对此议题开场。</p>
            </div>
          </div>
        </Card>

        <div className="lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="font-bold text-gray-800">流程步骤 ({steps.length})</h3>
            <Button size="sm" onClick={addStep} icon={Plus}>添加步骤</Button>
          </div>
          
          <div className="space-y-3">
            {steps.map((step, index) => {
              const isLogicExpanded = expandedLogicStep === index;
              const hasLoopLogic = step.logic_config?.exit_condition || step.logic_config?.max_loops;
              const hasNextStep = step.logic_config?.next_step_order;

              return (
              <div key={step.id} className="bg-white border border-gray-200 rounded-lg p-4 relative group hover:border-gray-300 transition-colors">
                <div className="flex items-start gap-4">
                  <div className="relative shrink-0 mt-1">
                    <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center font-bold text-gray-500">
                      {index + 1}
                    </div>
                    {/* 循环逻辑指示器 */}
                    <div className="absolute -top-1 -right-1 flex gap-0.5">
                      {hasNextStep && (
                        <div
                          className="w-3 h-3 bg-blue-500 rounded-full border border-white cursor-help"
                          title={`跳转逻辑: 执行完后跳转到 Step ${step.logic_config?.next_step_order}`}
                        >
                          <span className="sr-only">跳转逻辑</span>
                        </div>
                      )}
                      {step.logic_config?.max_loops && (
                        <div
                          className="w-3 h-3 bg-orange-500 rounded-full border border-white cursor-help"
                          title={`循环限制: 最大重复 ${step.logic_config.max_loops} 次${step.logic_config.exit_condition ? ' 或满足结束条件' : ''}`}
                        >
                          <span className="sr-only">最大循环次数</span>
                        </div>
                      )}
                      {step.logic_config?.exit_condition && (
                        <div
                          className="w-3 h-3 bg-green-500 rounded-full border border-white cursor-help"
                          title={`结束条件: "${step.logic_config.exit_condition}"${step.logic_config.max_loops ? ` (最多${step.logic_config.max_loops}次循环)` : ''}`}
                        >
                          <span className="sr-only">循环结束条件</span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex-1 space-y-3">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <label className="text-xs text-gray-500 block mb-1">发言者 (Speaker)</label>
                        <select 
                          className={`w-full border rounded px-2 py-1 text-sm ${theme.bgSoft} font-medium ${theme.text} ${theme.ring}`}
                          value={step.speaker_role_ref}
                          onChange={e => updateStep(index, 'speaker_role_ref', e.target.value)}
                        >
                          <option value="">选择角色...</option>
                          {roles.map(r => <option key={r.id} value={r.name}>{r.name}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-gray-500 block mb-1">任务类型</label>
                        <select 
                          className={`w-full border rounded px-2 py-1 text-sm ${theme.ring}`}
                          value={step.task_type}
                          onChange={e => updateStep(index, 'task_type', e.target.value)}
                        >
                          <option value="ask_question">提问</option>
                          <option value="answer_question">回答</option>
                          <option value="review_answer">点评</option>
                          <option value="question">质询</option>
                          <option value="summarize">总结</option>
                          <option value="evaluate">评估</option>
                          <option value="suggest">建议</option>
                          <option value="challenge">挑战</option>
                          <option value="support">支持</option>
                          <option value="conclude">结束</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-gray-500 block mb-1">对象 (Target)</label>
                        <select 
                          className={`w-full border rounded px-2 py-1 text-sm bg-gray-50 ${theme.ring}`}
                          value={step.target_role_ref || ''}
                          onChange={e => updateStep(index, 'target_role_ref', e.target.value)}
                        >
                          <option value="">(无对象/系统)</option>
                          <option value="__TOPIC__">预设议题 (Topic)</option>
                          {roles.map(r => <option key={r.id} value={r.name}>{r.name}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-gray-500 block mb-1">上下文策略</label>
                        <MultiSelectContextDropdown
                          value={step.context_scope}
                          onChange={(value) => updateStep(index, 'context_scope', value)}
                          roles={roles}
                          className={theme.ring}
                        />
                      </div>
                    </div>

                    {/* 紧凑的循环信息显示 */}
                    {(hasNextStep || hasLoopLogic) && !isLogicExpanded && (
                      <div className="flex flex-wrap items-center gap-2 text-xs">
                        {hasNextStep && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-md">
                            <CornerDownLeft size={10} />
                            跳转至 Step {step.logic_config?.next_step_order}
                          </span>
                        )}
                        {step.logic_config?.max_loops && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-orange-50 text-orange-700 border border-orange-200 rounded-md">
                            <RefreshCw size={10} />
                            最大 {step.logic_config.max_loops} 次
                          </span>
                        )}
                        {step.logic_config?.exit_condition && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-50 text-green-700 border border-green-200 rounded-md max-w-xs truncate" title={step.logic_config.exit_condition}>
                            <FileCheck size={10} />
                            结束条件: {step.logic_config.exit_condition}
                          </span>
                        )}
                      </div>
                    )}

                    <div className="flex items-center gap-2 text-xs">
                       <button 
                         onClick={() => setExpandedLogicStep(isLogicExpanded ? null : index)}
                         className={`flex items-center gap-1 px-2 py-1 rounded border transition-colors ${
                           isLogicExpanded 
                             ? `${theme.bgSoft} ${theme.border} ${theme.text}` 
                             : step.logic_config?.next_step_order ? `${theme.bgSoft} ${theme.border} ${theme.text}` : 'bg-gray-50 border-gray-200 text-gray-500'
                         }`}
                       >
                         <Settings size={12} />
                         {isLogicExpanded ? '收起流转配置' : '流转逻辑配置'}
                         {step.logic_config?.next_step_order && !isLogicExpanded && (
                           <span className="ml-1 font-bold">→ 跳转至 Step {step.logic_config.next_step_order}</span>
                         )}
                       </button>
                    </div>

                    {isLogicExpanded && (
                      <div className={`p-3 rounded border ${theme.bgSoft} ${theme.border} grid grid-cols-1 md:grid-cols-3 gap-4 animate-in fade-in slide-in-from-top-2 duration-200`}>
                        <div>
                           <label className={`text-xs font-bold ${theme.text} block mb-1 flex items-center gap-1`}>
                             <CornerDownLeft size={12}/> 跳转逻辑 (Next Step)
                           </label>
                           <select 
                             className={`w-full border ${theme.border} rounded px-2 py-1 text-sm`}
                             value={step.logic_config?.next_step_order || ''}
                             onChange={e => updateLogicConfig(index, 'next_step_order', e.target.value ? Number(e.target.value) : undefined)}
                           >
                             <option value="">默认 (继续下一步)</option>
                             {steps.map(s => (
                               <option key={s.id} value={s.order}>Step {s.order} ({s.speaker_role_ref})</option>
                             ))}
                           </select>
                        </div>
                        <div>
                           <label className={`text-xs font-bold ${theme.text} block mb-1 flex items-center gap-1`}>
                             <FileText size={12}/> 循环结束条件
                           </label>
                           <input 
                             className={`w-full border ${theme.border} rounded px-2 py-1 text-sm`}
                             placeholder="例如：学生回答正确"
                             value={step.logic_config?.exit_condition || ''}
                             onChange={e => updateLogicConfig(index, 'exit_condition', e.target.value)}
                           />
                        </div>
                        <div>
                           <label className={`text-xs font-bold ${theme.text} block mb-1 flex items-center gap-1`}>
                             <RefreshCw size={12}/> 最大循环次数
                           </label>
                           <input 
                             type="number"
                             className={`w-full border ${theme.border} rounded px-2 py-1 text-sm`}
                             placeholder="例如：3"
                             value={step.logic_config?.max_loops || ''}
                             onChange={e => updateLogicConfig(index, 'max_loops', e.target.value ? Number(e.target.value) : undefined)}
                           />
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <button onClick={() => deleteStep(index)} className="p-2 text-gray-300 hover:text-red-500 transition-colors">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            )})}
            {steps.length === 0 && <div className="text-center py-10 text-gray-400 border-2 border-dashed border-gray-200 rounded-lg">暂无步骤，请点击添加</div>}
          </div>
        </div>
      </div>
    </div>
  );
};

// 3. Session Management & Theater
const SessionManagement = ({ onPlayback }: any) => {
  const { theme } = useTheme();
  const [view, setView] = useState<'list' | 'create' | 'theater'>('list');
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);

  useEffect(() => {
    if (onPlayback) {
      setActiveSessionId(onPlayback);
      setView('theater');
    }
  }, [onPlayback]);

  useEffect(() => {
    if (view === 'list') {
      // TODO: Replace with real API when available
      setSessions([]); // Temporary empty sessions
    }
  }, [view]);

  if (view === 'create') {
    return <SessionCreator onCancel={() => setView('list')} onSuccess={(id: number) => { setActiveSessionId(id); setView('theater'); }} />;
  }

  if (view === 'theater' && activeSessionId) {
    return <SessionTheater sessionId={activeSessionId} onExit={() => { setView('list'); setActiveSessionId(null); }} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">会话管理</h1>
          <p className="text-gray-500 text-sm mt-1">创建并执行多角色对话剧场</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setView('create')} icon={Plus}>新建会话</Button>
          <Button onClick={() => { setActiveSessionId(999); setView('theater'); }} variant="ghost" size="sm">
            🔴 测试调试面板
          </Button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">主题</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">模板</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">状态</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">创建时间</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600 text-right">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sessions.map(s => (
              <tr key={s.id} className="hover:bg-gray-50/50">
                <td className="px-6 py-4 font-medium text-gray-900">{s.topic}</td>
                <td className="px-6 py-4 text-gray-600">Template #{s.flow_template_id}</td>
                <td className="px-6 py-4">
                  <Badge color={s.status === 'running' ? 'green' : s.status === 'finished' ? 'gray' : 'theme'}>
                    {s.status === 'running' ? '进行中' : s.status === 'finished' ? '已结束' : '未开始'}
                  </Badge>
                </td>
                <td className="px-6 py-4 text-gray-500 text-sm">{new Date(s.created_at).toLocaleDateString()}</td>
                <td className="px-6 py-4 text-right">
                  <button onClick={() => { setActiveSessionId(s.id); setView('theater'); }} className={`${theme.text} ${theme.textHover} font-medium text-sm flex items-center gap-1 justify-end ml-auto`}>
                    {s.status === 'finished' ? '回放' : '进入剧场'} <ChevronRight size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {sessions.length === 0 && <EmptyState message="暂无会话记录" />}
      </div>
    </div>
  );
};

const SessionCreator = ({ onCancel, onSuccess }: any) => {
  const { theme } = useTheme();
  const [formData, setFormData] = useState({ topic: '', flow_template_id: '', role_mappings: [] as any[] });
  const [flows, setFlows] = useState<FlowTemplate[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [requiredRoles, setRequiredRoles] = useState<string[]>([]);
  const [needsRoleMapping, setNeedsRoleMapping] = useState(true); // 新增：是否需要角色映射

  useEffect(() => {
    // 加载流程模板列表
    flowApi.getFlows().then(res => {
      setFlows(res.items);
    }).catch(error => {
      handleError(error, false); // 不显示用户消息，只记录错误
      setFlows([]); // 失败时设置为空数组
    });
    roleApi.getRoles().then(res => setRoles(res.items));
  }, []);

  useEffect(() => {
    if (formData.flow_template_id && flows.length > 0) {
      const flow = flows.find(f => f.id === Number(formData.flow_template_id));
      if (flow) {
        const refs = Array.from(new Set((flow.steps || []).map(s => s.speaker_role_ref).filter(Boolean)));
        setRequiredRoles(refs);
        if (flow.topic) setFormData(prev => ({ ...prev, topic: flow.topic || '' }));

        // 检查是否是无需角色映射的流程
        // 如果流程类型包含"simple"或"business_discussion"，则无需角色映射
        const needsMapping = !flow.type?.includes('simple') &&
                           !flow.type?.includes('business_discussion') &&
                           refs.length > 0;
        setNeedsRoleMapping(needsMapping);

        if (needsMapping) {
          setFormData(prev => ({
            ...prev,
            role_mappings: refs.map(ref => {
              const matchedRole = roles.find(r => r.name === ref);
              return { role_ref: ref, role_id: matchedRole ? matchedRole.id : '' };
            })
          }));
        } else {
          // 无需角色映射的流程
          setFormData(prev => ({ ...prev, role_mappings: [] }));
        }
      }
    }
  }, [formData.flow_template_id, flows, roles]);

  const updateMapping = (ref: string, roleId: string) => {
    setFormData(prev => ({
      ...prev,
      role_mappings: prev.role_mappings.map(m => m.role_ref === ref ? { ...m, role_id: roleId } : m)
    }));
  };

  const handleCreate = async () => {
    // 验证必填字段
    if (!formData.topic || !formData.flow_template_id) {
      alert("请填写完整信息");
      return;
    }

    // 如果需要角色映射，验证角色映射是否完整
    if (needsRoleMapping && formData.role_mappings.some(m => !m.role_id)) {
      alert("请完成所有角色映射");
      return;
    }

    try {
      // 构建请求数据
      let requestData: any = {
        topic: formData.topic,
        flow_template_id: Number(formData.flow_template_id)
      };

      // 只有在需要角色映射时才包含role_mappings
      if (needsRoleMapping && formData.role_mappings.length > 0) {
        const role_mappings = formData.role_mappings.reduce((acc, mapping) => {
          acc[mapping.role_ref] = Number(mapping.role_id);
          return acc;
        }, {} as Record<string, number>);
        requestData.role_mappings = role_mappings;
      }
      // 如果不需要角色映射，不传role_mappings字段（后端会处理为null）

      console.log('Creating session with data:', requestData);
      console.log('Needs role mapping:', needsRoleMapping);

      const sessionData = await sessionApi.createSession(requestData);
      console.log('Session created successfully:', sessionData);

      // 自动启动会话
      try {
        const startedSession = await sessionApi.startSession(sessionData.id);
        console.log('Session started successfully:', startedSession);
        onSuccess(sessionData.id);
      } catch (startError) {
        console.error('Failed to start session:', startError);
        handleError(startError);
      }
    } catch (error) {
      console.error('Session creation failed:', error);
      handleError(error);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6 py-6">
      <div className="flex items-center gap-4 border-b pb-4">
        <button onClick={onCancel} className="p-2 hover:bg-gray-100 rounded-full"><ArrowRight className="rotate-180" /></button>
        <h1 className="text-2xl font-bold text-gray-900">发起新会话</h1>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">会话主题</label>
          <input className={`w-full border rounded-lg px-3 py-2 ${theme.ring}`} placeholder="例如：高中物理-动量守恒教学" value={formData.topic} onChange={e => setFormData({...formData, topic: e.target.value})} />
          <p className="text-xs text-gray-500 mt-1">若所选模板包含预设议题，此处会自动填充。</p>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">选择流程模板</label>
          <select className={`w-full border rounded-lg px-3 py-2 ${theme.ring}`} value={formData.flow_template_id} onChange={e => setFormData({...formData, flow_template_id: e.target.value})}>
            <option value="">请选择...</option>
            {flows.map(f => <option key={f.id} value={f.id}>{f.name} ({(f.steps || []).length}步)</option>)}
          </select>
        </div>

        {needsRoleMapping && requiredRoles.length > 0 && (
          <div className={`p-4 rounded-lg border ${theme.bgSoft} ${theme.border}`}>
            <h3 className={`font-bold ${theme.text} mb-3 flex items-center gap-2`}><Users size={18}/> 角色映射 (Casting)</h3>
            <div className="space-y-3">
              {requiredRoles.map(ref => (
                <div key={ref} className="flex items-center gap-4">
                  <div className={`w-24 text-sm font-medium ${theme.text} text-right`}>
                    {ref} <span className="opacity-50">→</span>
                  </div>
                  <select
                    className={`flex-1 border rounded px-3 py-2 text-sm ${theme.ring}`}
                    value={formData.role_mappings.find(m => m.role_ref === ref)?.role_id || ''}
                    onChange={e => updateMapping(ref, e.target.value)}
                  >
                    <option value="">选择扮演该角色的实例...</option>
                    {roles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
                  </select>
                </div>
              ))}
            </div>
            <p className={`text-xs ${theme.text} mt-2 opacity-70`}>* 系统已尝试根据名称自动匹配角色</p>
          </div>
        )}

        {!needsRoleMapping && requiredRoles.length > 0 && (
          <div className={`p-4 rounded-lg border ${theme.bgSoft} ${theme.border}`}>
            <h3 className={`font-bold ${theme.text} mb-3 flex items-center gap-2`}><CheckCircle size={18}/> 自动角色配置</h3>
            <div className="space-y-2">
              <p className={`text-sm ${theme.text} opacity-80`}>
                此流程将自动使用以下角色参与讨论：
              </p>
              <div className="flex flex-wrap gap-2">
                {requiredRoles.map(ref => (
                  <span key={ref} className={`px-3 py-1 rounded-full text-xs font-medium ${theme.bgPrimary} ${theme.textPrimary}`}>
                    {ref}
                  </span>
                ))}
              </div>
              <p className={`text-xs ${theme.text} mt-2 opacity-70`}>* 系统将自动匹配对应的角色配置</p>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-3 pt-4">
          <Button variant="secondary" onClick={onCancel}>取消</Button>
          <Button onClick={handleCreate} disabled={!formData.topic}>创建并进入</Button>
        </div>
      </div>
    </div>
  );
};

const SessionTheater = ({ sessionId, onExit }: any) => {
  const { updateLLMDebugInfo } = useContext(LLMDebugContext);
  const { theme } = useTheme();
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [generating, setGenerating] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadData = async () => {
    try {
      // 加载会话详情
      const sessionData = await sessionApi.getSession(sessionId);
      setSession(sessionData);

      // 加载会话消息
      const messagesData = await sessionApi.getMessages(sessionId, { page_size: 100 });
      setMessages(messagesData.items);
    } catch (error) {
      handleError(error);
    }
  };

  useEffect(() => { loadData(); }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, generating]);

  const handleNextStep = async () => {
    if (!session) return;
    setGenerating(true);
    try {
      // 调用真实的API执行下一步
      const result = await sessionApi.executeNextStep(session.id);

      // 添加新消息到消息列表
      if (result.message) {
        setMessages(prev => [...prev, result.message]);
      }

      // 更新全局LLM调试信息
      if (result.llm_debug && updateLLMDebugInfo) {
        updateLLMDebugInfo(result.llm_debug);
      }

      // 更新会话状态（如果后端返回了更新的会话信息）
      if (result.execution_info) {
        // 检查会话是否已完成
        if (result.execution_info.is_finished) {
          setSession(prev => prev ? {
            ...prev,
            status: 'finished',
            updated_at: new Date().toISOString()
          } : null);
        }
      }

    } catch (error) {
      handleError(error);
    } finally {
      setGenerating(false);
    }
  };

  const handleFinish = async () => {
    if (!session) return;

    if (confirm("确定要结束当前会话吗？")) {
      try {
        await sessionApi.terminateSession(session.id);
        setSession(prev => prev ? {
          ...prev,
          status: 'finished',
          updated_at: new Date().toISOString()
        } : null);
      } catch (error) {
        handleError(error);
      }
    }
  };

  if (!session) return <div className="p-10 text-center">Loading Theater...</div>;

  const isFinished = session.status === 'finished' || session.status === 'terminated';

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col bg-gray-100 rounded-xl overflow-hidden border border-gray-300 shadow-2xl">
      <div className="bg-white border-b px-6 py-3 flex justify-between items-center shrink-0 z-10">
        <div className="flex items-center gap-4">
          <button onClick={onExit} className="p-2 hover:bg-gray-100 rounded-full"><ArrowRight className="rotate-180" /></button>
          <div>
            <h2 className="font-bold text-gray-900 flex items-center gap-2">
              {session.topic} 
              <Badge color={isFinished ? 'gray' : 'green'}>{isFinished ? '已结束' : '进行中'}</Badge>
            </h2>
            <div className="text-xs text-gray-500 mt-0.5 flex gap-2">
              <span>Template ID: {session.flow_template_id}</span>
              <span>•</span>
              <span>Round: {session.current_round + 1}</span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" icon={Download} />
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-64 bg-gray-50 border-r p-4 overflow-y-auto hidden md:flex md:flex-col justify-between">
          <div className="space-y-3 flex-1 overflow-y-auto">
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Cast Members</h3>
            {/* TODO: 显示会话角色信息 */}
            <div className="text-sm text-gray-500">
              会话角色信息将在此处显示
            </div>
          </div>

          <div className="pt-4 border-t mt-4 shrink-0">
             {!isFinished && (
               <Button
                 variant="danger"
                 size="xs"
                 onClick={handleFinish}
                 icon={LogOut}
                 className="w-full justify-center"
               >
                 结束会话
               </Button>
             )}
          </div>
        </div>

        <div className="flex-1 flex">
          <div className="flex-1 bg-white flex flex-col relative">
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.length === 0 && (
              <div className="text-center text-gray-400 py-20">
                <p>舞台已就绪，等待开场...</p>
              </div>
            )}
            
            {messages.map(msg => {
               // 简化的角色判断逻辑，可以根据需要扩展
               const isTeacher = msg.speaker_role_name?.includes('老师') || false;
               // Dynamic bubble color for teacher
               const roleColor = isTeacher ? `${theme.bgSoft} ${theme.text}` : 'bg-gray-100 text-gray-900';
               return (
                <div key={msg.id} className={`flex gap-4 max-w-3xl`}>
                  <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center shrink-0 font-bold text-gray-600 text-sm">
                    {msg.speaker_role_name?.[0] || '?'}
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-baseline gap-2">
                      <span className="font-bold text-sm text-gray-900">{msg.speaker_role_name || '未知角色'}</span>
                      <span className="text-xs text-gray-400">{new Date(msg.created_at).toLocaleTimeString()}</span>
                      {msg.target_role_name && <span className="text-xs text-gray-400">to {msg.target_role_name}</span>}
                    </div>
                    <div className={`px-4 py-3 rounded-2xl rounded-tl-none ${roleColor} text-sm leading-relaxed shadow-sm`}>
                      {msg.content}
                    </div>
                    <div className="flex gap-2 opacity-0 hover:opacity-100 transition-opacity">
                      <button className={`text-xs ${theme.text} hover:underline flex items-center gap-1`}><GitBranch size={10} /> 创建分支</button>
                    </div>
                  </div>
                </div>
               );
            })}
            
            {generating && (
              <div className="flex gap-4 max-w-3xl">
                <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center shrink-0 animate-pulse">...</div>
                <div className="space-y-1">
                  <div className="h-4 w-20 bg-gray-100 rounded animate-pulse"/>
                  <div className="h-10 w-48 bg-gray-100 rounded-2xl rounded-tl-none animate-pulse"/>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 border-t bg-white flex items-center justify-between gap-4">
             <div className="text-sm text-gray-500">
                {!isFinished ? (
                   <>下一步: <span className="font-medium text-gray-900">执行步骤 #{session.current_round + 1}</span></>
                ) : (
                   <span className="flex items-center gap-1 text-green-600"><CheckCircle size={14}/> 对话流程已结束</span>
                )}
             </div>
             <Button 
               onClick={handleNextStep} 
               disabled={isFinished || generating} 
               className="min-w-[140px]"
               icon={Play}
             >
               {generating ? '生成中...' : '执行下一步'}
                        </Button>
          </div>
        </div>
      </div>

        </div>
    </div>
  );
};

// 4. History Page
const HistoryPage = ({ onPlayback }: any) => {
  const { theme } = useTheme();
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    // TODO: Replace with real API when available
    setSessions([]); // Temporary empty sessions
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">历史记录</h1>
          <p className="text-gray-500 text-sm mt-1">查看已结束的对话存档</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">主题</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">模板</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">结束时间</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600 text-right">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sessions.map(s => (
              <tr key={s.id} className="hover:bg-gray-50/50">
                <td className="px-6 py-4 font-medium text-gray-900">{s.topic}</td>
                <td className="px-6 py-4 text-gray-600">Template #{s.flow_template_id}</td>
                <td className="px-6 py-4 text-gray-500 text-sm">{new Date(s.updated_at).toLocaleString()}</td>
                <td className="px-6 py-4 text-right">
                  <button onClick={() => onPlayback(s.id)} className={`${theme.text} ${theme.textHover} font-medium text-sm flex items-center gap-1 justify-end ml-auto`}>
                    回放 <ChevronRight size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {sessions.length === 0 && <EmptyState message="暂无历史记录" />}
      </div>
    </div>
  );
};

// 5. Settings Page (Updated with Theme Switcher)
const SettingsPage = () => {
  const { themeKey, setThemeKey } = useTheme();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">系统设置</h1>
          <p className="text-gray-500 text-sm mt-1">配置系统参数与偏好</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 max-w-2xl">
        {/* Theme Settings */}
        <Card title="主题外观">
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {Object.keys(THEMES).map((key) => {
                const k = key as ThemeKey;
                const t = THEMES[k];
                return (
                  <button
                    key={k}
                    onClick={() => setThemeKey(k)}
                    className={`flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-all ${
                      themeKey === k ? `${t.border} ${t.bgSoft}` : 'border-transparent hover:bg-gray-50'
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-full ${t.primary} shadow-sm`}></div>
                    <span className="text-xs font-medium text-gray-700">{t.name}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </Card>

        <Card title="基础设置">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-2">
                <Globe size={16} /> 界面语言
              </label>
              <select className="w-full border rounded-lg px-3 py-2 bg-gray-50">
                <option>简体中文</option>
                <option>English</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-2">
                <Key size={16} /> LLM API Key
              </label>
              <input type="password" className="w-full border rounded-lg px-3 py-2" placeholder="sk-........................" />
              <p className="text-xs text-gray-500 mt-1">用于连接大模型服务的密钥</p>
            </div>
          </div>
        </Card>

        <Card title="数据管理">
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-red-50 border border-red-100 rounded-lg">
              <div>
                <h4 className="font-bold text-red-800 text-sm">重置所有数据</h4>
                <p className="text-xs text-red-600 mt-1">这将清空所有角色、模板和历史记录，不可恢复。</p>
              </div>
              <Button variant="danger" size="sm" icon={RotateCcw}>立即重置</Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

// --- Main App ---
const App = () => {
  const [activeTab, setActiveTab] = useState('roles');
  const [playbackSessionId, setPlaybackSessionId] = useState<number | null>(null);

  // State for Theme
  const [themeKey, setThemeKey] = useState<ThemeKey>('blue');
  const theme = THEMES[themeKey];

  // Global LLM Debug State
  const [globalLLMDebugInfo, setGlobalLLMDebugInfo] = useState<any>(null);

  // Global function to update LLM debug info
  const updateGlobalLLMDebugInfo = (debugInfo: any) => {
    setGlobalLLMDebugInfo(debugInfo);
  };

  const handlePlayback = (id: number) => {
    setPlaybackSessionId(id);
    setActiveTab('sessions');
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'roles': return <RoleManagement />;
      case 'flows': return <FlowManagement />;
      case 'sessions': return <SessionManagement onPlayback={playbackSessionId} />;
      case 'history': return <HistoryPage onPlayback={handlePlayback} />;
      case 'settings': return <SettingsPage />;
      default: return <RoleManagement />;
    }
  };

  return (
    <ThemeContext.Provider value={{ themeKey, theme, setThemeKey }}>
      <LLMDebugContext.Provider value={{ updateLLMDebugInfo: updateGlobalLLMDebugInfo }}>
      <div className="flex h-screen w-full bg-gray-100 text-gray-900 font-sans">
        <div className="w-64 bg-slate-900 text-white flex flex-col shrink-0 transition-colors">
          <div className="p-6">
            <div className="flex items-center gap-3 font-bold text-xl tracking-tight">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${theme.iconBg} text-white`}>
                <MessageSquare size={18} />
              </div>
              MultiRole
            </div>
            <div className="text-xs text-slate-400 mt-1">多角色对话仿真系统</div>
          </div>
          <nav className="flex-1 px-4 space-y-2">
            <NavItem icon={Users} label="角色管理" active={activeTab === 'roles'} onClick={() => setActiveTab('roles')} />
            <NavItem icon={GitBranch} label="流程模板" active={activeTab === 'flows'} onClick={() => setActiveTab('flows')} />
            <NavItem icon={Play} label="会话剧场" active={activeTab === 'sessions'} onClick={() => setActiveTab('sessions')} />
            <div className="pt-4 mt-4 border-t border-slate-700">
              <NavItem icon={FileText} label="历史记录" active={activeTab === 'history'} onClick={() => setActiveTab('history')} />
              <NavItem icon={Settings} label="系统设置" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
            </div>
          </nav>
          <div className="p-4 bg-slate-800 m-4 rounded-lg">
            <div className="text-xs text-slate-400 mb-2">当前状态</div>
            <div className="flex items-center gap-2 text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              Mock Server Online
            </div>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-6xl mx-auto p-8">
            {renderContent()}
          </div>
        </div>
      </div>

        {/* 全局LLM调试面板 - 在所有页面都可见 */}
        <SimpleLLMDebugPanel debugInfo={globalLLMDebugInfo} />
      </LLMDebugContext.Provider>
    </ThemeContext.Provider>
  );
};

const NavItem = ({ icon: Icon, label, active, onClick }: any) => {
  const { theme } = useTheme();
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all
        ${active ? `${theme.primary} text-white shadow-lg shadow-blue-900/20` : 'text-slate-300 hover:bg-slate-800 hover:text-white'}`}
    >
      <Icon size={18} />
      {label}
    </button>
  );
};

export default App;
