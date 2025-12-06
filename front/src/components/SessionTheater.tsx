import React, { useState, useEffect, useRef, useContext } from 'react';
import { ArrowRight, Download, Play, CheckCircle, LogOut, GitBranch, Pause } from 'lucide-react';
import { sessionApi } from '../api/sessionApi';
import { Session, Message } from '../api/sessionApi';
import { useTheme } from '../theme';
import SimpleLLMDebugPanel from './SimpleLLMDebugPanel';
import { LLMDebugContext } from '../MultiRoleDialogSystem';
import { handleError } from '../utils/errorHandler';

interface SessionTheaterProps {
  sessionId: number;
  onExit: () => void;
}

const SessionTheater: React.FC<SessionTheaterProps> = ({ sessionId, onExit }) => {
  const { updateLLMDebugInfo } = useContext(LLMDebugContext);
  const { theme } = useTheme();
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [generating, setGenerating] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto execution states
  const [autoMode, setAutoMode] = useState<boolean>(false);           // 自动/手动模式
  const [autoExecution, setAutoExecution] = useState<boolean>(false);  // 是否正在自动执行
  const executionInterval = 3000;  // 自动执行间隔(毫秒)
  const autoExecutionTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null); // 用于清理定时器的引用

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

  // Auto execution core functions
  const executeNextStepWithAuto = async () => {
    if (!session || generating) return;

    const isFinished = session.status === 'finished';
    if (isFinished) {
      setAutoExecution(false);
      return;
    }

    try {
      await handleNextStep();

      // 检查会话是否已结束
      if (autoMode && session && session.status !== 'finished') {
        const timer = setTimeout(() => {
          executeNextStepWithAuto();
        }, executionInterval);
        autoExecutionTimerRef.current = timer;
      } else {
        setAutoExecution(false);
      }
    } catch (e) {
      setAutoExecution(false);
      console.error("自动执行失败:", e);
      alert("自动执行失败");
    }
  };

  // 开始自动执行
  const startAutoExecution = () => {
    if (!session || session.status === 'finished') return;

    setAutoExecution(true);
    executeNextStepWithAuto();
  };

  // 停止自动执行
  const stopAutoExecution = () => {
    if (autoExecutionTimerRef.current) {
      clearTimeout(autoExecutionTimerRef.current);
      autoExecutionTimerRef.current = null;
    }
    setAutoExecution(false);
  };

  // 切换自动/手动模式
  const toggleAutoMode = () => {
    if (autoMode) {
      // 从自动模式切换到手动模式
      stopAutoExecution();
      setAutoMode(false);
    } else {
      // 从手动模式切换到自动模式
      setAutoMode(true);
      startAutoExecution();
    }
  };

  // 暂停/继续自动执行
  const toggleAutoExecution = () => {
    if (autoExecution) {
      stopAutoExecution();
    } else {
      startAutoExecution();
    }
  };

  // Stop auto execution when session is finished
  useEffect(() => {
    if (session && session.status === 'finished') {
      stopAutoExecution();
    }
  }, [session]);

  // Cleanup auto execution timer on component unmount
  useEffect(() => {
    return () => {
      if (autoExecutionTimerRef.current) {
        clearTimeout(autoExecutionTimerRef.current);
        autoExecutionTimerRef.current = null;
      }
    };
  }, []);

  if (!session) return <div className="p-10 text-center">Loading Theater...</div>;

  const isFinished = session.status === 'finished' || session.status === 'terminated';
  const participants = session.session_roles || [];

  // Badge component
  const Badge = ({ color, children }: { color: string; children: React.ReactNode }) => (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
      color === 'gray' ? 'bg-gray-100 text-gray-600' :
      color === 'green' ? 'bg-green-100 text-green-600' :
      'bg-blue-100 text-blue-600'
    }`}>
      {children}
    </span>
  );

  // Button component
  const Button = ({
    onClick,
    disabled,
    children,
    icon: Icon,
    variant = 'primary',
    size = 'md',
    className = ''
  }: {
    onClick?: () => void;
    disabled?: boolean;
    children: React.ReactNode;
    icon?: any;
    variant?: 'primary' | 'ghost' | 'danger';
    size?: 'sm' | 'md' | 'xs';
    className?: string;
  }) => {
    const baseClasses = 'inline-flex items-center gap-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500';
    const variants = {
      primary: `${theme.primary} text-white hover:${theme.primaryHover} disabled:opacity-50`,
      ghost: 'hover:bg-gray-100 text-gray-600',
      danger: 'bg-red-500 text-white hover:bg-red-600'
    };
    const sizes = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-sm',
      xs: 'px-2 py-1 text-xs'
    };

    return (
      <button
        onClick={onClick}
        disabled={disabled}
        className={`${baseClasses} ${variants[variant]} ${sizes[size]} ${className}`}
      >
        {Icon && <Icon size={16} />}
        {children}
      </button>
    );
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col bg-gray-100 rounded-xl overflow-hidden border border-gray-300 shadow-2xl">
      {/* Header */}
      <div className="bg-white border-b px-6 py-3 flex justify-between items-center shrink-0 z-10">
        <div className="flex items-center gap-4">
          <button onClick={onExit} className="p-2 hover:bg-gray-100 rounded-full">
            <ArrowRight className="rotate-180" />
          </button>
          <div>
            <h2 className="font-bold text-gray-900 flex items-center gap-2">
              {session.topic}
              <Badge color={isFinished ? 'gray' : 'green'}>
                {isFinished ? '已结束' : '进行中'}
              </Badge>
            </h2>
            <div className="text-xs text-gray-500 mt-0.5 flex gap-2">
              <span>Template ID: {session.flow_template_id}</span>
              <span>•</span>
              <span>Round: {session.current_round + 1}</span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" icon={Download}>下载</Button>

          {/* Auto/Manual Mode Toggle */}
          <div className="bg-green-500 text-white px-3 py-1 rounded-lg">
            <span className="text-xs font-bold">DEBUG: {autoMode ? '自动模式' : '手动模式'}</span>
            <button
              onClick={() => {
                console.log('Toggle button clicked! Current mode:', autoMode);
                toggleAutoMode();
              }}
              className="ml-2 bg-white text-green-500 px-2 py-1 rounded text-xs font-bold"
            >
              切换
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 bg-gray-50 border-r p-4 overflow-y-auto hidden md:flex md:flex-col justify-between">
          <div className="space-y-3 flex-1 overflow-y-auto">
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Cast Members</h3>
            {participants.map(p => (
              <div key={p.id} className="bg-white p-3 rounded-lg border shadow-sm flex items-center gap-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm
                  ${p.role_ref.includes('老师') || p.role_ref === 'teacher' ? theme.iconBg : 'bg-green-500'}`}>
                  {p.role_ref[0]?.toUpperCase() || 'R'}
                </div>
                <div>
                  <div className="font-bold text-sm text-gray-900">{p.role_ref}</div>
                  <div className="text-xs text-gray-500">ID: {p.role_id}</div>
                </div>
              </div>
            ))}
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

        {/* Main Theater + Debug Panel */}
        <div className="flex-1 flex">
          {/* Theater Content */}
          <div className="flex-1 bg-white flex flex-col relative">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {messages.length === 0 && (
                <div className="text-center text-gray-400 py-20">
                  <p>舞台已就绪，等待开场...</p>
                </div>
              )}

              {messages.map(msg => {
                 const isTeacher = msg.speaker_role_name?.includes('老师') || false;
                 // Dynamic bubble color for teacher
                 const roleColor = isTeacher ? `${theme.bgSoft} ${theme.text}` : 'bg-gray-100 text-gray-900';
                 return (
                  <div key={msg.id} className={`flex gap-4 max-w-3xl`}>
                    <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center shrink-0 font-bold text-gray-600 text-sm">
                      {msg.speaker_role_name?.[0]?.toUpperCase() || '?'}
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-baseline gap-2">
                        <span className="font-bold text-sm text-gray-900">{msg.speaker_role_name}</span>
                        <span className="text-xs text-gray-400">{new Date(msg.created_at).toLocaleTimeString()}</span>
                        {msg.target_role_name && <span className="text-xs text-gray-400">to {msg.target_role_name}</span>}
                      </div>
                      <div className={`px-4 py-3 rounded-2xl rounded-tl-none ${roleColor} text-sm leading-relaxed shadow-sm`}>
                        {msg.content}
                      </div>
                      <div className="flex gap-2 opacity-0 hover:opacity-100 transition-opacity">
                        <button className={`text-xs ${theme.text} hover:underline flex items-center gap-1`}>
                          <GitBranch size={10} /> 创建分支
                        </button>
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

            {/* Controls */}
            <div className="p-4 border-t bg-white flex items-center justify-between gap-4">
              <div className="text-sm text-gray-500">
                 {!isFinished ? (
                   <>
                     {autoMode ? (
                       <>🤖 自动执行中 (步骤 #{session.current_round + 1})</>
                     ) : (
                       <>下一步: <span className="font-medium text-gray-900">执行步骤 #{session.current_round + 1}</span></>
                     )}
                   </>
                 ) : (
                   <span className="flex items-center gap-1 text-green-600"><CheckCircle size={14}/> 对话流程已结束</span>
                 )}
               </div>

               {/* Dynamic Button Group */}
               <div className="flex gap-2">
                 {!isFinished ? (
                   <>
                     {autoMode ? (
                       // Auto Mode Buttons
                       <>
                         {autoExecution ? (
                           <Button
                             onClick={toggleAutoExecution}
                             className="min-w-[120px]"
                             icon={Pause}
                             variant="secondary"
                           >
                             暂停
                           </Button>
                         ) : (
                           <Button
                             onClick={toggleAutoExecution}
                             className="min-w-[120px]"
                             icon={Play}
                             variant="primary"
                           >
                             继续
                           </Button>
                         )}
                       </>
                     ) : (
                       // Manual Mode Button
                       <Button
                         onClick={handleNextStep}
                         disabled={generating}
                         className="min-w-[140px]"
                         icon={Play}
                       >
                         {generating ? '生成中...' : '执行下一步'}
                       </Button>
                     )}
                   </>
                 ) : (
                   // Finished State - already has end button in sidebar
                   <div className="w-[120px]" />
                 )}
               </div>
             </div>
          </div>

          {/* LLM Debug Panel - uses global context */}
          <SimpleLLMDebugPanel />
        </div>
      </div>
    </div>
  );
};

export default SessionTheater;