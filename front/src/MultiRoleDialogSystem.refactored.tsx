import React, { useState, useEffect } from 'react';
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

// --- 组件导入 ---
import { Button, Card, Badge, Modal, EmptyState } from './components/common/ui';
import { ThemeProvider } from './contexts/ThemeContext';
import { LLMDebugProvider } from './contexts/LLMDebugContext';
import MultiSelectContextDropdown from './components/flow-management/MultiSelectContextDropdown';
import SimpleLLMDebugPanel from './components/SimpleLLMDebugPanel';

// --- 类型定义 ---
type TabKey = 'roles' | 'flows' | 'sessions' | 'knowledge';

interface FlowStepFormData {
  id?: number;
  role_mapping: string;
  context_strategy: string;
  prompt_template: string;
  termination_condition: string;
  next_step_id?: number;
  is_start: boolean;
}

// --- 主应用组件 ---
const MultiRoleDialogSystem: React.FC = () => {
  // 状态管理
  const [activeTab, setActiveTab] = useState<TabKey>('roles');
  const [roles, setRoles] = useState<Role[]>([]);
  const [flows, setFlows] = useState<FlowTemplate[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedFlow, setSelectedFlow] = useState<FlowTemplate | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [roleFormData, setRoleFormData] = useState<RoleRequest>({
    name: '',
    type: 'custom',
    description: '',
    style: '',
    constraints: '',
    focus_points: []
  });
  const [flowFormData, setFlowFormData] = useState({
    name: '',
    description: ''
  });
  const [flowSteps, setFlowSteps] = useState<FlowStep[]>([]);
  const [editingStep, setEditingStep] = useState<FlowStepFormData | null>(null);
  const [sessionFormData, setSessionFormData] = useState({
    name: '',
    flow_template_id: 0
  });
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [showSessionTheater, setShowSessionTheater] = useState(false);
  const [expandedFlows, setExpandedFlows] = useState<Set<number>>(new Set());
  const [expandedSessions, setExpandedSessions] = useState<Set<number>>(new Set());
  const [debugInfo, setDebugInfo] = useState<any>(null);
  const [showDebugPanel, setShowDebugPanel] = useState(true);

  // 数据加载
  useEffect(() => {
    loadRoles();
    loadFlows();
    loadSessions();
    loadKnowledgeBases();
  }, []);

  const loadRoles = async () => {
    try {
      const data = await roleApi.getRoles();
      setRoles(data);
    } catch (error) {
      handleError(error);
    }
  };

  const loadFlows = async () => {
    try {
      const data = await flowApi.getFlows();
      setFlows(data);
    } catch (error) {
      handleError(error);
    }
  };

  const loadSessions = async () => {
    try {
      const data = await sessionApi.getSessions();
      setSessions(data);
    } catch (error) {
      handleError(error);
    }
  };

  const loadKnowledgeBases = async () => {
    try {
      const data = await knowledgeApi.getKnowledgeBases();
      setKnowledgeBases(data);
    } catch (error) {
      handleError(error);
    }
  };

  // --- 标签页配置 ---
  const tabs = [
    { key: 'roles' as TabKey, label: '角色管理', icon: Users },
    { key: 'flows' as TabKey, label: '流程管理', icon: GitBranch },
    { key: 'sessions' as TabKey, label: '会话管理', icon: MessageSquare },
    { key: 'knowledge' as TabKey, label: '知识库', icon: Database }
  ];

  return (
    <LLMDebugProvider>
      <ThemeProvider>
        <div className="min-h-screen bg-gray-50">
          <div className="flex h-screen">
            {/* Sidebar */}
            <div className="w-64 bg-white shadow-lg">
              <div className="p-6">
                <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                  <Users className="text-blue-600" />
                  多角色对话系统
                </h1>
              </div>

              <nav className="px-4">
                {tabs.map(({ key, label, icon: Icon }) => (
                  <button
                    key={key}
                    onClick={() => setActiveTab(key)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                      activeTab === key
                        ? 'bg-blue-50 text-blue-600 border-l-4 border-blue-600'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    <Icon size={20} />
                    <span className="font-medium">{label}</span>
                  </button>
                ))}
              </nav>

              {/* Theme selector */}
              <div className="absolute bottom-0 w-64 p-4 border-t">
                <div className="text-sm font-medium text-gray-700 mb-2">主题</div>
                <select className="w-full px-3 py-2 border rounded-lg text-sm">
                  <option value="blue">商务蓝</option>
                  <option value="purple">优雅紫</option>
                  <option value="emerald">清新绿</option>
                  <option value="rose">活力红</option>
                  <option value="amber">暖阳橙</option>
                </select>
              </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-hidden">
              <div className="h-full flex flex-col">
                {/* Header */}
                <div className="bg-white shadow-sm border-b px-6 py-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold text-gray-800">
                      {tabs.find(t => t.key === activeTab)?.label}
                    </h2>
                    <div className="flex gap-3">
                      {activeTab === 'roles' && (
                        <Button
                          onClick={() => {
                            setEditingRole(null);
                            setRoleFormData({
                              name: '',
                              type: 'custom',
                              description: '',
                              style: '',
                              constraints: '',
                              focus_points: []
                            });
                            setIsModalOpen(true);
                          }}
                          icon={Plus}
                        >
                          创建角色
                        </Button>
                      )}
                      {activeTab === 'flows' && (
                        <Button
                          onClick={() => {
                            setSelectedFlow(null);
                            setFlowFormData({ name: '', description: '' });
                            setFlowSteps([]);
                            setIsModalOpen(true);
                          }}
                          icon={Plus}
                        >
                          创建流程
                        </Button>
                      )}
                      {activeTab === 'sessions' && (
                        <Button
                          onClick={() => {
                            setSessionFormData({ name: '', flow_template_id: 0 });
                            setIsModalOpen(true);
                          }}
                          icon={Plus}
                        >
                          创建会话
                        </Button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-auto p-6">
                  {/* 角色管理页面 */}
                  {activeTab === 'roles' && (
                    <div>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {roles.map((role) => (
                          <Card key={role.id} title={role.name}>
                            <div className="space-y-2">
                              <p className="text-sm text-gray-600">{role.description}</p>
                              <div className="flex gap-2">
                                <Badge color="blue">{role.type}</Badge>
                                {role.is_builtin && (
                                  <Badge color="gray">内置</Badge>
                                )}
                              </div>
                              <div className="pt-2 border-t flex justify-end gap-2">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {/* 编辑逻辑 */}}
                                  icon={Edit3}
                                >
                                  编辑
                                </Button>
                                {!role.is_builtin && (
                                  <Button
                                    variant="danger"
                                    size="sm"
                                    onClick={() => {/* 删除逻辑 */}}
                                    icon={Trash2}
                                  >
                                    删除
                                  </Button>
                                )}
                              </div>
                            </div>
                          </Card>
                        ))}
                      </div>
                      {roles.length === 0 && (
                        <EmptyState
                          message="还没有创建任何角色"
                          action={
                            <Button
                              onClick={() => {
                                setEditingRole(null);
                                setRoleFormData({
                                  name: '',
                                  type: 'custom',
                                  description: '',
                                  style: '',
                                  constraints: '',
                                  focus_points: []
                                });
                                setIsModalOpen(true);
                              }}
                              icon={Plus}
                            >
                              创建第一个角色
                            </Button>
                          }
                        />
                      )}
                    </div>
                  )}

                  {/* 流程管理页面 */}
                  {activeTab === 'flows' && (
                    <div>
                      <div className="space-y-4">
                        {flows.map((flow) => (
                          <Card key={flow.id}>
                            <div className="flex justify-between items-start">
                              <div>
                                <h3 className="font-semibold text-lg">{flow.name}</h3>
                                <p className="text-gray-600">{flow.description}</p>
                              </div>
                              <div className="flex gap-2">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {/* 编辑逻辑 */}}
                                  icon={Edit3}
                                >
                                  编辑
                                </Button>
                                <Button
                                  variant="danger"
                                  size="sm"
                                  onClick={() => {/* 删除逻辑 */}}
                                  icon={Trash2}
                                >
                                  删除
                                </Button>
                              </div>
                            </div>
                          </Card>
                        ))}
                      </div>
                      {flows.length === 0 && (
                        <EmptyState
                          message="还没有创建任何流程"
                          action={
                            <Button
                              onClick={() => {
                                setSelectedFlow(null);
                                setFlowFormData({ name: '', description: '' });
                                setFlowSteps([]);
                                setIsModalOpen(true);
                              }}
                              icon={Plus}
                            >
                              创建第一个流程
                            </Button>
                          }
                        />
                      )}
                    </div>
                  )}

                  {/* 会话管理页面 */}
                  {activeTab === 'sessions' && (
                    <div>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {sessions.map((session) => (
                          <Card key={session.id} title={session.name}>
                            <div className="space-y-2">
                              <p className="text-sm text-gray-600">
                                流程: {session.flow_template?.name || '未知'}
                              </p>
                              <div className="flex gap-2">
                                <Badge color="green">
                                  {session.status}
                                </Badge>
                              </div>
                              <div className="pt-2 border-t flex justify-end gap-2">
                                <Button
                                  onClick={() => {
                                    setSelectedSession(session);
                                    setShowSessionTheater(true);
                                  }}
                                  icon={Play}
                                >
                                  运行
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {/* 查看详情 */}}
                                  icon={FileText}
                                >
                                  详情
                                </Button>
                              </div>
                            </div>
                          </Card>
                        ))}
                      </div>
                      {sessions.length === 0 && (
                        <EmptyState
                          message="还没有创建任何会话"
                          action={
                            <Button
                              onClick={() => {
                                setSessionFormData({ name: '', flow_template_id: 0 });
                                setIsModalOpen(true);
                              }}
                              icon={Plus}
                            >
                              创建第一个会话
                            </Button>
                          }
                        />
                      )}
                    </div>
                  )}

                  {/* 知识库页面 */}
                  {activeTab === 'knowledge' && (
                    <KnowledgeBaseManagement />
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Debug Panel */}
          {showDebugPanel && (
            <SimpleLLMDebugPanel
              debugInfo={debugInfo}
              onClose={() => setShowDebugPanel(false)}
            />
          )}

          {/* Session Theater Modal */}
          {showSessionTheater && selectedSession && (
            <Modal
              isOpen={showSessionTheater}
              onClose={() => setShowSessionTheater(false)}
              title={`会话剧场 - ${selectedSession.name}`}
              footer={
                <Button onClick={() => setShowSessionTheater(false)}>
                  关闭
                </Button>
              }
            >
              <SessionTheater session={selectedSession} />
            </Modal>
          )}

          {/* Create/Edit Modal - 简化版本 */}
          {isModalOpen && (
            <Modal
              isOpen={isModalOpen}
              onClose={() => setIsModalOpen(false)}
              title={editingRole ? '编辑角色' : '创建角色'}
              footer={
                <div className="flex gap-3">
                  <Button
                    variant="ghost"
                    onClick={() => setIsModalOpen(false)}
                  >
                    取消
                  </Button>
                  <Button
                    onClick={() => {
                      // 保存逻辑
                      setIsModalOpen(false);
                    }}
                    icon={Save}
                  >
                    保存
                  </Button>
                </div>
              }
            >
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    角色名称
                  </label>
                  <input
                    type="text"
                    value={roleFormData.name}
                    onChange={(e) => setRoleFormData({...roleFormData, name: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    描述
                  </label>
                  <textarea
                    value={roleFormData.description}
                    onChange={(e) => setRoleFormData({...roleFormData, description: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg"
                    rows={3}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    类型
                  </label>
                  <select
                    value={roleFormData.type}
                    onChange={(e) => setRoleFormData({...roleFormData, type: e.target.value as any})}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="teacher">老师</option>
                    <option value="student">学生</option>
                    <option value="expert">专家</option>
                    <option value="custom">自定义</option>
                  </select>
                </div>
              </div>
            </Modal>
          )}
        </div>
      </ThemeProvider>
    </LLMDebugProvider>
  );
};

export default MultiRoleDialogSystem;