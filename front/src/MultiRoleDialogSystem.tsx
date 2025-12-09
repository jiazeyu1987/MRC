import { useState, useEffect, useContext, createContext, useRef, useMemo } from 'react';
import SimpleLLMDebugPanel from './components/SimpleLLMDebugPanel';

// Create LLM Debug Context
export const LLMDebugContext = createContext<{
  updateLLMDebugInfo: (debugInfo: any) => void;
  showDebugPanel: boolean;
  setShowDebugPanel: (show: boolean) => void;
}>({
  updateLLMDebugInfo: () => {},
  showDebugPanel: true,
  setShowDebugPanel: () => {}
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
  FileCheck,
  Pause,
  AlertTriangle,
  Database
} from 'lucide-react';


// --- API和类型导入 ---
import { roleApi } from './api/roleApi';
import { flowApi, FlowTemplate, FlowStep } from './api/flowApi';
import { sessionApi, Session, Message } from './api/sessionApi';
import { Role, RoleRequest, RoleKnowledgeBase } from './types/role';
import { KnowledgeBase } from './types/knowledge';
import { knowledgeApi } from './api/knowledgeApi';
import { handleError } from './utils/errorHandler';
import SessionTheater from './components/SessionTheater';
import KnowledgeBaseManagement from './components/KnowledgeBaseManagement';

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

    // All options are now multi-select
    if (selectedValues.includes(optionValue)) {
      newSelectedValues = selectedValues.filter(v => v !== optionValue);
    } else {
      newSelectedValues = [...selectedValues, optionValue];
    }

    // Convert to appropriate format for backend
    let result: string | string[];
    if (newSelectedValues.length === 0) {
      result = '';
    } else if (newSelectedValues.length === 1) {
      // Single option remains as single string
      result = newSelectedValues[0];
    } else {
      // Multiple options get serialized as JSON array for backend
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

const Badge = ({ children, color = 'theme', size = 'md' }: any) => {
  const { theme } = useTheme();

  // Custom theme badge or semantic colors
  let colorClass = "";
  if (color === 'theme') colorClass = theme.badge;
  else if (color === 'green') colorClass = "bg-green-100 text-green-800";
  else if (color === 'gray') colorClass = "bg-gray-100 text-gray-800";
  else if (color === 'red') colorClass = "bg-red-100 text-red-800";
  else colorClass = "bg-blue-100 text-blue-800"; // fallback

  // Size classes
  const sizeClasses = {
    sm: "px-1.5 py-0.5 text-xs",
    md: "px-2 py-0.5 text-xs"
  };

  return (
    <span className={`${sizeClasses[size] || sizeClasses.md} rounded font-medium ${colorClass}`}>
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

// --- Components ---

// Knowledge Base Selector Component for Role Management
const KnowledgeBaseSelector: React.FC<{
  selectedAssociations: Array<{
    knowledge_base_id: number;
    priority: number;
    filtering_rules?: {
      enabled: boolean;
      confidence_threshold?: number;
      document_types?: string[];
      keywords?: string[];
    };
  }>;
  onChange: (associations: Array<{
    knowledge_base_id: number;
    priority: number;
    filtering_rules?: {
      enabled: boolean;
      confidence_threshold?: number;
      document_types?: string[];
      keywords?: string[];
    };
  }>) => void;
  knowledgeBases: KnowledgeBase[];
  className?: string;
}> = ({ selectedAssociations, onChange, knowledgeBases, className = '' }) => {
  const { theme } = useTheme();
  const [expandedAssociation, setExpandedAssociation] = useState<number | null>(null);

  const addAssociation = () => {
    const usedIds = selectedAssociations.map(a => a.knowledge_base_id);
    const availableKB = knowledgeBases.find(kb => !usedIds.includes(kb.id));

    if (availableKB) {
      const newAssociations = [
        ...selectedAssociations,
        {
          knowledge_base_id: availableKB.id,
          priority: Math.max(...selectedAssociations.map(a => a.priority), 0) + 1,
          filtering_rules: {
            enabled: false,
            confidence_threshold: 0.7,
            document_types: [],
            keywords: []
          }
        }
      ];
      onChange(newAssociations);
    }
  };

  const updateAssociation = (index: number, field: string, value: any) => {
    const newAssociations = [...selectedAssociations];
    if (field === 'filtering_rules') {
      newAssociations[index] = {
        ...newAssociations[index],
        filtering_rules: { ...newAssociations[index].filtering_rules, ...value }
      };
    } else {
      newAssociations[index] = { ...newAssociations[index], [field]: value };
    }
    onChange(newAssociations);
  };

  const removeAssociation = (index: number) => {
    const newAssociations = selectedAssociations.filter((_, i) => i !== index);
    // Re-order priorities
    const reorderedAssociations = newAssociations.map((assoc, i) => ({
      ...assoc,
      priority: i + 1
    }));
    onChange(reorderedAssociations);
  };

  const moveAssociation = (fromIndex: number, toIndex: number) => {
    const newAssociations = [...selectedAssociations];
    const [moved] = newAssociations.splice(fromIndex, 1);
    newAssociations.splice(toIndex, 0, moved);

    // Re-order priorities based on new positions
    const reorderedAssociations = newAssociations.map((assoc, i) => ({
      ...assoc,
      priority: i + 1
    }));
    onChange(reorderedAssociations);
  };

  const getKnowledgeBaseName = (kbId: number) => {
    const kb = knowledgeBases.find(k => k.id === kbId);
    return kb ? kb.name : `Knowledge Base #${kbId}`;
  };

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex justify-between items-center">
        <label className="block text-sm font-medium text-gray-700">
          <Database className="inline-block w-4 h-4 mr-1" />
          关联知识库
        </label>
        <Button
          size="sm"
          onClick={addAssociation}
          disabled={selectedAssociations.length >= knowledgeBases.length}
          icon={Plus}
        >
          添加知识库
        </Button>
      </div>

      {selectedAssociations.length === 0 ? (
        <div className="text-center py-4 border-2 border-dashed border-gray-200 rounded-lg text-gray-500">
          <Database className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          <p className="text-sm">暂无关联知识库</p>
          <p className="text-xs mt-1">点击上方按钮添加知识库关联</p>
        </div>
      ) : (
        <div className="space-y-2">
          {selectedAssociations
            .sort((a, b) => a.priority - b.priority)
            .map((association, index) => {
              const isExpanded = expandedAssociation === index;
              const kb = knowledgeBases.find(k => k.id === association.knowledge_base_id);

              return (
                <div key={index} className={`border rounded-lg p-3 ${theme.bgSoft} ${theme.border}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      <div className="flex items-center gap-2">
                        <Database className={`w-4 h-4 ${theme.text}`} />
                        <span className="font-medium text-sm">
                          {getKnowledgeBaseName(association.knowledge_base_id)}
                        </span>
                        <Badge color="theme" size="sm">
                          优先级: {association.priority}
                        </Badge>
                        {kb?.status === 'active' ? (
                          <Badge color="green" size="sm">活跃</Badge>
                        ) : (
                          <Badge color="gray" size="sm">离线</Badge>
                        )}
                      </div>

                      {kb && (
                        <div className="text-xs text-gray-500">
                          {kb.document_count} 文档 · {(kb.total_size / 1024 / 1024).toFixed(1)}MB
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => moveAssociation(index, Math.max(0, index - 1))}
                        disabled={index === 0}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                        title="上移"
                      >
                        <ChevronDown className="w-4 h-4 rotate-180" />
                      </button>
                      <button
                        onClick={() => moveAssociation(index, Math.min(selectedAssociations.length - 1, index + 1))}
                        disabled={index === selectedAssociations.length - 1}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                        title="下移"
                      >
                        <ChevronDown className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setExpandedAssociation(isExpanded ? null : index)}
                        className={`p-1 ${isExpanded ? theme.text : 'text-gray-400'} hover:text-gray-600`}
                        title={isExpanded ? '收起详情' : '展开详情'}
                      >
                        <Settings className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => removeAssociation(index)}
                        className="p-1 text-gray-400 hover:text-red-600"
                        title="移除关联"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="mt-3 space-y-3 border-t pt-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">
                            知识库
                          </label>
                          <select
                            className={`w-full border rounded px-2 py-1 text-sm ${theme.ring}`}
                            value={association.knowledge_base_id}
                            onChange={(e) => updateAssociation(index, 'knowledge_base_id', Number(e.target.value))}
                          >
                            <option value="">选择知识库...</option>
                            {knowledgeBases
                              .filter(kb => !selectedAssociations.some(a => a.knowledge_base_id === kb.id) || kb.id === association.knowledge_base_id)
                              .map(kb => (
                                <option key={kb.id} value={kb.id}>
                                  {kb.name} ({kb.document_count} 文档)
                                </option>
                              ))
                            }
                          </select>
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">
                            优先级
                          </label>
                          <input
                            type="number"
                            min="1"
                            className={`w-full border rounded px-2 py-1 text-sm ${theme.ring}`}
                            value={association.priority}
                            onChange={(e) => updateAssociation(index, 'priority', Number(e.target.value))}
                          />
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <input
                            type="checkbox"
                            id={`filtering-enabled-${index}`}
                            checked={association.filtering_rules?.enabled || false}
                            onChange={(e) => updateAssociation(index, 'filtering_rules', { enabled: e.target.checked })}
                            className="rounded"
                          />
                          <label htmlFor={`filtering-enabled-${index}`} className="text-sm font-medium text-gray-700">
                            启用过滤规则
                          </label>
                        </div>

                        {association.filtering_rules?.enabled && (
                          <div className="space-y-2 pl-6">
                            <div>
                              <label className="block text-xs font-medium text-gray-600 mb-1">
                                置信度阈值 (0-1)
                              </label>
                              <input
                                type="number"
                                min="0"
                                max="1"
                                step="0.1"
                                className={`w-full border rounded px-2 py-1 text-sm ${theme.ring}`}
                                value={association.filtering_rules?.confidence_threshold || 0.7}
                                onChange={(e) => updateAssociation(index, 'filtering_rules', {
                                  confidence_threshold: Number(e.target.value)
                                })}
                              />
                            </div>

                            <div>
                              <label className="block text-xs font-medium text-gray-600 mb-1">
                                关键词 (逗号分隔)
                              </label>
                              <input
                                type="text"
                                placeholder="例如：物理,数学,科学"
                                className={`w-full border rounded px-2 py-1 text-sm ${theme.ring}`}
                                value={association.filtering_rules?.keywords?.join(', ') || ''}
                                onChange={(e) => updateAssociation(index, 'filtering_rules', {
                                  keywords: e.target.value ? e.target.value.split(',').map(k => k.trim()).filter(k => k) : []
                                })}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
        </div>
      )}
    </div>
  );
};

// --- Pages ---

// 1. Role Management
const RoleManagement = () => {
  const { theme } = useTheme();
  const [roles, setRoles] = useState<Role[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Partial<Role> & { knowledge_base_associations?: any[] }>({});
  const [saving, setSaving] = useState(false);

  const fetchKnowledgeBases = async () => {
    try {
      const response = await knowledgeApi.getKnowledgeBases({ page_size: 100 });
      setKnowledgeBases(response.knowledge_bases);
    } catch (error: any) {
      console.error('获取知识库列表失败:', error);
      // 不显示错误消息，因为这是辅助功能
      setKnowledgeBases([]);
    }
  };

  const fetchRoles = async () => {
    try {
      setLoading(true);
      const [rolesResponse] = await Promise.all([
        roleApi.getRoles(),
        fetchKnowledgeBases()
      ]);
      setRoles(rolesResponse.items);
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
        prompt: editingRole.prompt!,
        knowledge_base_associations: editingRole.knowledge_base_associations
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

  const handleDeleteAllRoles = async () => {
    try {
      // 第一步：获取删除统计信息
      const stats = await roleApi.getDeletionStatistics();

      if (stats.total_roles === 0) {
        alert('当前没有角色可以删除');
        return;
      }

      if (stats.deletable_roles === 0) {
        alert(`找到 ${stats.total_roles} 个角色，但所有角色都在被使用，无法删除`);
        return;
      }

      // 第二步：显示统计信息并要求确认
      const confirmMessage = `找到 ${stats.total_roles} 个角色：\n` +
        `• 可以删除：${stats.deletable_roles} 个\n` +
        `• 正在使用：${stats.used_roles} 个\n\n` +
        `只有未被使用的角色才会被删除，是否继续？`;

      if (!confirm(confirmMessage)) {
        return;
      }

      // 第三步：最终确认
      const finalConfirm = prompt('请输入 "删除所有角色" 来确认批量删除操作：');
      if (finalConfirm !== '删除所有角色') {
        alert('确认文本不正确，操作已取消');
        return;
      }

      // 执行批量删除
      const result = await roleApi.deleteAllRoles('', true);

      // 显示结果
      let message = `批量删除完成！\n` +
        `• 成功删除：${result.deleted_roles} 个角色`;

      if (result.skipped_roles.length > 0) {
        message += `\n• 跳过删除：${result.skipped_roles.length} 个角色`;
      }

      if (result.errors.length > 0) {
        message += `\n• 错误：${result.errors.length} 个`;
        console.error('删除错误:', result.errors);
      }

      alert(message);

      // 重新获取角色列表
      await fetchRoles();

    } catch (error: any) {
      console.error('批量删除角色失败:', error);
      alert(error.message || '批量删除失败');
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
        <div className="flex gap-2">
          <button
            onClick={handleDeleteAllRoles}
            disabled={loading || roles.length === 0}
            className={`px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2 text-sm font-medium`}
            title="删除所有未被使用的角色"
          >
            <Trash2 size={16} />
            删除所有角色
          </button>
          <Button onClick={openCreateModal} icon={Plus} disabled={loading}>新建角色</Button>
        </div>
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
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-gray-900">{role.name}</h3>
                      {role.knowledge_bases && role.knowledge_bases.length > 0 && (
                        <div className="flex items-center gap-1">
                          <Database className="w-3 h-3 text-blue-500" />
                          <span className="text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded-full">
                            {role.knowledge_bases.length} KB
                          </span>
                        </div>
                      )}
                    </div>
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

          {/* Knowledge Base Association */}
          <div>
            <KnowledgeBaseSelector
              selectedAssociations={editingRole.knowledge_base_associations || []}
              onChange={(associations) => setEditingRole({...editingRole, knowledge_base_associations: associations})}
              knowledgeBases={knowledgeBases}
            />
            <p className="text-xs text-gray-500 mt-1">
              关联知识库后，角色在对话中可以检索和使用相关知识库的信息
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
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([]);
  const [expandedLogicStep, setExpandedLogicStep] = useState<number | null>(null);

  useEffect(() => {
    // 加载角色和知识库数据
    roleApi.getRoles().then(res => setRoles(res.items));

    // 加载知识库数据
    knowledgeApi.getKnowledgeBases({ page: 1, page_size: 100 }).then(res => {
      setKnowledgeBases(res.knowledge_bases || []);
    }).catch(err => {
      console.error('Failed to load knowledge bases:', err);
    });
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
      context_scope: 'all',
      knowledge_base_config: {
        enabled: false,
        knowledge_base_ids: [],
        retrieval_params: {
          top_k: 5,
          similarity_threshold: 0.7,
          max_context_length: 2000
        }
      }
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

  const updateKnowledgeBaseConfig = (index: number, field: string, value: any) => {
    const newSteps = [...steps];
    const currentKBConfig = newSteps[index].knowledge_base_config || {
      enabled: false,
      knowledge_base_ids: [],
      retrieval_params: {
        top_k: 5,
        similarity_threshold: 0.7,
        max_context_length: 2000
      }
    };

    if (field === 'enabled') {
      currentKBConfig.enabled = value;
    } else if (field === 'knowledge_base_ids') {
      currentKBConfig.knowledge_base_ids = value;
    } else if (field === 'retrieval_params') {
      currentKBConfig.retrieval_params = { ...currentKBConfig.retrieval_params, ...value };
    }

    newSteps[index].knowledge_base_config = currentKBConfig;
    setSteps(newSteps);
  };

  const toggleKnowledgeBaseSelection = (index: number, kbId: string) => {
    const newSteps = [...steps];
    const currentKBConfig = newSteps[index].knowledge_base_config || {
      enabled: false,
      knowledge_base_ids: [],
      retrieval_params: {
        top_k: 5,
        similarity_threshold: 0.7,
        max_context_length: 2000
      }
    };

    const kbIds = currentKBConfig.knowledge_base_ids || [];
    const isSelected = kbIds.includes(kbId);

    currentKBConfig.knowledge_base_ids = isSelected
      ? kbIds.filter(id => id !== kbId)
      : [...kbIds, kbId];

    newSteps[index].knowledge_base_config = currentKBConfig;
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

                    {/* Knowledge Base Configuration */}
                    <div className="border-t border-gray-200 pt-4 mt-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center">
                          <Database className="w-5 h-5 text-gray-600 mr-2" />
                          <h4 className="text-sm font-medium text-gray-900">知识库配置</h4>
                        </div>
                        <button
                          onClick={() => updateKnowledgeBaseConfig(index, 'enabled', !step.knowledge_base_config?.enabled)}
                          className={`px-3 py-1 text-xs font-medium rounded-full ${
                            step.knowledge_base_config?.enabled
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {step.knowledge_base_config?.enabled ? '已启用' : '已禁用'}
                        </button>
                      </div>

                      {step.knowledge_base_config?.enabled && (
                        <div className="space-y-3">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              选择知识库
                            </label>
                            {knowledgeBases.length === 0 ? (
                              <p className="text-gray-500 text-sm">暂无可用知识库</p>
                            ) : (
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-32 overflow-y-auto">
                                {knowledgeBases.map((kb) => (
                                  <label
                                    key={kb.id}
                                    className="flex items-center p-2 border border-gray-200 rounded hover:bg-gray-50 cursor-pointer"
                                  >
                                    <input
                                      type="checkbox"
                                      checked={step.knowledge_base_config?.knowledge_base_ids?.includes(kb.id.toString()) || false}
                                      onChange={() => toggleKnowledgeBaseSelection(index, kb.id.toString())}
                                      className="mr-2 rounded text-blue-500 focus:ring-blue-500"
                                    />
                                    <div>
                                      <div className="text-sm font-medium text-gray-900">{kb.name}</div>
                                      <div className="text-xs text-gray-500">
                                        {kb.document_count || 0} 个文档
                                      </div>
                                    </div>
                                  </label>
                                ))}
                              </div>
                            )}
                          </div>

                          <div className="grid grid-cols-3 gap-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                Top K 结果
                              </label>
                              <input
                                type="number"
                                min="1"
                                max="20"
                                value={step.knowledge_base_config?.retrieval_params?.top_k || 5}
                                onChange={(e) => updateKnowledgeBaseConfig(index, 'retrieval_params', {
                                  top_k: parseInt(e.target.value) || 5
                                })}
                                className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                              />
                            </div>

                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                相似度阈值
                              </label>
                              <input
                                type="number"
                                min="0"
                                max="1"
                                step="0.1"
                                value={step.knowledge_base_config?.retrieval_params?.similarity_threshold || 0.7}
                                onChange={(e) => updateKnowledgeBaseConfig(index, 'retrieval_params', {
                                  similarity_threshold: parseFloat(e.target.value) || 0.7
                                })}
                                className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                              />
                            </div>

                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                最大上下文长度
                              </label>
                              <input
                                type="number"
                                min="100"
                                max="10000"
                                step="100"
                                value={step.knowledge_base_config?.retrieval_params?.max_context_length || 2000}
                                onChange={(e) => updateKnowledgeBaseConfig(index, 'retrieval_params', {
                                  max_context_length: parseInt(e.target.value) || 2000
                                })}
                                className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                              />
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
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
      // Load sessions from API
      const loadSessions = async () => {
        try {
          const sessionsData = await sessionApi.getSessions({ page_size: 50 });
          setSessions(sessionsData.items);
        } catch (error) {
          handleError(error);
          setSessions([]); // Fallback to empty list on error
        }
      };
      loadSessions();
    }
  }, [view]);

  // Delete single session
  const handleDeleteSession = async (sessionId: number, topic: string) => {
    // 显示确认对话框
    const confirmed = window.confirm(`确定要删除会话 "${topic}" 吗？\n\n此操作不可恢复，将删除会话及其所有消息数据。`);

    if (!confirmed) {
      return;
    }

    try {
      await sessionApi.deleteSession(sessionId);

      // 显示成功消息
      alert('会话删除成功！');

      // 重新加载会话列表
      const sessionsData = await sessionApi.getSessions({ page_size: 50 });
      setSessions(sessionsData.items);

    } catch (error) {
      console.error('删除会话失败:', error);
      alert(`删除失败: ${(error as Error).message || '删除会话时发生错误'}`);
    }
  };

  // Delete all sessions
  const handleDeleteAllSessions = async () => {
    if (sessions.length === 0) {
      alert('当前没有会话可以删除。');
      return;
    }

    // 显示确认对话框
    const confirmed = window.confirm(
      `确定要删除所有会话吗？\n\n当前共有 ${sessions.length} 个会话。此操作不可恢复，将删除所有会话及其消息数据。`
    );

    if (!confirmed) {
      return;
    }

    // 二次确认
    const finalConfirmation = window.confirm(
      '请再次确认：真的要删除所有会话吗？\n\n正在运行的会话不会被删除。输入"确定"继续，输入"取消"停止操作。'
    );

    if (!finalConfirmation) {
      return;
    }

    try {
      // 先获取删除统计信息
      const stats = await sessionApi.getDeletionStatistics();

      // 显示详细确认信息
      const detailedConfirm = window.confirm(
        `删除确认：\n` +
        `• 总会话数: ${stats.total_sessions}\n` +
        `• 可删除会话: ${stats.deletable_sessions}\n` +
        `• 运行中会话（不会被删除）: ${stats.running_sessions}\n\n` +
        `确认继续删除操作吗？`
      );

      if (!detailedConfirm) {
        return;
      }

      // 执行批量删除
      const result = await sessionApi.deleteAllSessions('', true);

      // 显示成功消息
      alert(`批量删除成功！\n已删除 ${result.deleted_sessions} 个会话，跳过 ${result.skipped_sessions} 个运行中的会话。`);

      // 重新加载会话列表
      const sessionsData = await sessionApi.getSessions({ page_size: 50 });
      setSessions(sessionsData.items);

    } catch (error) {
      console.error('批量删除会话失败:', error);
      alert(`批量删除失败: ${(error as Error).message || '批量删除会话时发生错误'}`);
    }
  };

  // Force delete single session
  const handleForceDeleteSession = async (sessionId: number, topic: string) => {
    // 显示强制删除警告对话框
    const confirmed = window.confirm(
      `⚠️ 强制删除警告 ⚠️\n\n` +
      `您确定要强制删除正在运行的会话 "${topic}" 吗？\n\n` +
      `这将会：\n` +
      `• 立即终止正在进行的对话流程\n` +
      `• 删除会话及其所有消息数据\n` +
      `• 可能导致部分对话内容丢失\n\n` +
      `此操作不可恢复，请谨慎操作！`
    );

    if (!confirmed) {
      return;
    }

    // 二次确认
    const finalConfirmation = window.confirm(
      `最后确认：\n\n` +
      `真的要强制删除会话 "${topic}" 吗？\n\n` +
      `此操作将中断正在运行的AI对话，确认继续吗？`
    );

    if (!finalConfirmation) {
      return;
    }

    try {
      await sessionApi.forceDeleteSession(sessionId);

      // 显示成功消息
      alert('✅ 强制删除成功！会话已终止并删除。');

      // 重新加载会话列表
      const sessionsData = await sessionApi.getSessions({ page_size: 50 });
      setSessions(sessionsData.items);

    } catch (error) {
      console.error('强制删除会话失败:', error);
      alert(`❌ 强制删除失败: ${(error as Error).message || '强制删除会话时发生错误'}`);
    }
  };

  // Force delete all sessions
  const handleForceDeleteAllSessions = async () => {
    if (sessions.length === 0) {
      alert('当前没有会话可以删除。');
      return;
    }

    // 先获取统计信息
    const stats = await sessionApi.getDeletionStatistics();

    // 显示强制删除警告对话框
    const confirmed = window.confirm(
      `⚠️ 强制删除所有会话警告 ⚠️\n\n` +
      `您确定要强制删除所有会话吗？\n\n` +
      `统计信息：\n` +
      `• 总会话数: ${stats.total_sessions}\n` +
      `• 正在运行: ${stats.running_sessions}\n` +
      `• 可正常删除: ${stats.deletable_sessions}\n\n` +
      `这将会：\n` +
      `• 终止所有正在运行的对话流程\n` +
      `• 删除所有会话及其消息数据\n` +
      `• 可能导致部分对话内容丢失\n\n` +
      `此操作不可恢复，请极度谨慎！`
    );

    if (!confirmed) {
      return;
    }

    // 二次确认
    const finalConfirmation = window.confirm(
      `最后确认：\n\n` +
      `真的要强制删除所有 ${stats.total_sessions} 个会话吗？\n\n` +
      `其中包括 ${stats.running_sessions} 个正在运行的会话！\n\n` +
      `此操作将中断所有正在运行的AI对话，确认继续吗？`
    );

    if (!finalConfirmation) {
      return;
    }

    // 三次确认 - 要求输入特殊文本
    const typedConfirmation = window.prompt(
      `为了防止误操作，请输入以下文本以确认强制删除：\n\n` +
      `输入: "我确认强制删除所有会话"\n\n` +
      `（注意：区分大小写）`
    );

    if (typedConfirmation !== "我确认强制删除所有会话") {
      alert('❌ 确认文本不正确，操作已取消。');
      return;
    }

    try {
      // 执行强制批量删除
      const result = await sessionApi.forceDeleteAllSessions('', true);

      // 显示成功消息
      alert(
        `✅ 强制批量删除成功！\n\n` +
        `操作结果：\n` +
        `• 总删除: ${result.deleted_sessions} 个会话\n` +
        `• 强制删除运行中: ${result.force_deleted_sessions} 个会话\n` +
        `• 跳过: ${result.skipped_sessions} 个会话` +
        (result.errors.length > 0 ? `\n• 错误: ${result.errors.length} 个` : '')
      );

      // 重新加载会话列表
      const sessionsData = await sessionApi.getSessions({ page_size: 50 });
      setSessions(sessionsData.items);

    } catch (error) {
      console.error('强制批量删除会话失败:', error);
      alert(`❌ 强制批量删除失败: ${(error as Error).message || '强制批量删除会话时发生错误'}`);
    }
  };

  if (view === 'create') {
    return <SessionCreator
      onCancel={() => setView('list')}
      onSuccess={(id: number) => {
        setActiveSessionId(id);
        setView('theater');
        // Refresh sessions list when returning to list view
        const refreshSessions = async () => {
          try {
            const sessionsData = await sessionApi.getSessions({ page_size: 50 });
            setSessions(sessionsData.items);
          } catch (error) {
            handleError(error);
          }
        };
        refreshSessions();
      }}
    />;
  }

  if (view === 'theater' && activeSessionId) {
    return <SessionTheater
      sessionId={activeSessionId}
      onExit={() => {
        setView('list');
        setActiveSessionId(null);
        // Refresh sessions list when exiting theater
        const refreshSessions = async () => {
          try {
            const sessionsData = await sessionApi.getSessions({ page_size: 50 });
            setSessions(sessionsData.items);
          } catch (error) {
            handleError(error);
          }
        };
        refreshSessions();
      }}
    />;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">会话管理</h1>
          <p className="text-gray-500 text-sm mt-1">创建并执行多角色对话剧场</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleForceDeleteAllSessions}
            variant="danger"
            icon={AlertTriangle}
            disabled={sessions.length === 0}
            className="bg-orange-600 hover:bg-orange-700"
          >
            强制删除所有
          </Button>
          <Button
            onClick={handleDeleteAllSessions}
            variant="danger"
            icon={Trash2}
            disabled={sessions.length === 0}
          >
            删除所有
          </Button>
          <Button onClick={() => setView('create')} icon={Plus}>新建会话</Button>
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
                  <div className="flex items-center gap-2 justify-end">
                    {s.status !== 'running' && (
                      <button
                        onClick={() => handleDeleteSession(s.id, s.topic)}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
                        title="删除会话"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                    {s.status === 'running' && (
                      <button
                        onClick={() => handleForceDeleteSession(s.id, s.topic)}
                        className="p-2 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-full transition-colors"
                        title="强制删除会话（危险操作）"
                      >
                        <AlertTriangle size={16} />
                      </button>
                    )}
                    <button onClick={() => { setActiveSessionId(s.id); setView('theater'); }} className={`${theme.text} ${theme.textHover} font-medium text-sm flex items-center gap-1`}>
                      {s.status === 'finished' ? '回放' : '进入剧场'} <ChevronRight size={14} />
                    </button>
                  </div>
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
                  <span key={ref} className={`px-3 py-1 rounded-full text-xs font-medium ${theme.primary} text-white`}>
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


// 4. History Page
const HistoryPage = ({ onPlayback }: any) => {
  const { theme } = useTheme();
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    // Load finished sessions from API for history
    const loadHistorySessions = async () => {
      try {
        const sessionsData = await sessionApi.getSessions({
          status: 'finished,terminated',
          page_size: 50
        });
        setSessions(sessionsData.items);
      } catch (error) {
        handleError(error);
        setSessions([]); // Fallback to empty list on error
      }
    };
    loadHistorySessions();
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
  const { showDebugPanel, setShowDebugPanel } = useContext(LLMDebugContext);

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
            <div className="flex items-center justify-between">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  LLM调试面板
                </label>
                <p className="text-xs text-gray-500">显示/隐藏右侧的LLM调试信息面板</p>
              </div>
              <button
                onClick={() => setShowDebugPanel(!showDebugPanel)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  showDebugPanel ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    showDebugPanel ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
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
  const [knowledgeTabRefresh, setKnowledgeTabRefresh] = useState<number>(0);

  // State for Theme
  const [themeKey, setThemeKey] = useState<ThemeKey>('blue');
  const theme = THEMES[themeKey];

  // Handle tab switching with manual refresh for knowledge tab
  const handleTabSwitch = (tab: string) => {
    setActiveTab(tab);
    if (tab === 'knowledge') {
      // Trigger refresh for knowledge base tab
      setKnowledgeTabRefresh(prev => prev + 1);
    }
  };

  // Global LLM Debug State
  const [globalLLMDebugInfo, setGlobalLLMDebugInfo] = useState<any>(null);

  // Debug Panel Visibility State
  const [showDebugPanel, setShowDebugPanel] = useState<boolean>(true);

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
      case 'knowledge': return <KnowledgeBaseManagement manualRefresh={knowledgeTabRefresh > 0} />;
      case 'history': return <HistoryPage onPlayback={handlePlayback} />;
      case 'settings': return <SettingsPage />;
      default: return <RoleManagement />;
    }
  };

  return (
    <ThemeContext.Provider value={{ themeKey, theme, setThemeKey }}>
      <LLMDebugContext.Provider value={{
        updateLLMDebugInfo: updateGlobalLLMDebugInfo,
        showDebugPanel: showDebugPanel,
        setShowDebugPanel: setShowDebugPanel
      }}>
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
            <NavItem icon={Users} label="角色管理" active={activeTab === 'roles'} onClick={() => handleTabSwitch('roles')} />
            <NavItem icon={GitBranch} label="流程模板" active={activeTab === 'flows'} onClick={() => handleTabSwitch('flows')} />
            <NavItem icon={Play} label="会话剧场" active={activeTab === 'sessions'} onClick={() => handleTabSwitch('sessions')} />
            <NavItem icon={Database} label="知识库" active={activeTab === 'knowledge'} onClick={() => handleTabSwitch('knowledge')} />
            <div className="pt-4 mt-4 border-t border-slate-700">
              <NavItem icon={FileText} label="历史记录" active={activeTab === 'history'} onClick={() => handleTabSwitch('history')} />
              <NavItem icon={Settings} label="系统设置" active={activeTab === 'settings'} onClick={() => handleTabSwitch('settings')} />
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
        <div className={`flex-1 overflow-y-auto transition-all duration-300 ${showDebugPanel ? 'mr-80' : ''}`}>
          <div className={`${showDebugPanel ? 'max-w-[calc(100vw-320px)]' : 'max-w-full'} mx-auto p-8 transition-all duration-300`}>
            {renderContent()}
          </div>
        </div>
      </div>

        {/* 全局LLM调试面板 - 始终渲染但根据状态显示/隐藏 */}
        <SimpleLLMDebugPanel
          debugInfo={globalLLMDebugInfo}
          showDebugPanel={showDebugPanel}
          onClose={() => setShowDebugPanel(false)}
        />
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
