import React from 'react';
import { X } from 'lucide-react';

interface LLMDebugEntry {
  role_name: string;
  step_description: string;
  step_type: string;
  prompt: string;
  response: string;
  timestamp: string;
  context_summary: string;
}

interface SimpleLLMDebugPanelProps {
  debugInfo?: LLMDebugEntry;
  showDebugPanel?: boolean;
  onClose?: () => void;
}

export const SimpleLLMDebugPanel: React.FC<SimpleLLMDebugPanelProps> = ({
  debugInfo,
  showDebugPanel = true,
  onClose
}) => {
  return (
    <div className={`w-80 bg-white border-l border-gray-200 p-4 h-screen overflow-y-auto fixed right-0 top-0 z-40 transition-all duration-300 ${
      showDebugPanel ? 'translate-x-0' : 'translate-x-full'
    }`}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">LLM调试面板</h3>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
            title="关闭调试面板"
          >
            <X size={18} className="text-gray-500" />
          </button>
        )}
      </div>

      {!debugInfo ? (
        <div className="text-sm text-gray-500">
          <div className="bg-gray-50 p-3 rounded border border-gray-200">
            <p className="font-medium mb-2">等待LLM调用...</p>
            <p className="text-xs">当前无调试信息</p>
            <p className="text-xs mt-1">时间: {new Date().toLocaleTimeString()}</p>
          </div>
        </div>
      ) : (
        <div className="space-y-3 text-sm">
          <div className="bg-green-50 p-2 rounded border border-green-200">
            <p className="font-medium text-green-700">✅ LLM调试信息</p>
          </div>

          <div>
            <span className="font-medium text-gray-600">角色:</span>
            <span className="ml-2 text-gray-800">{debugInfo.role_name}</span>
          </div>

          <div>
            <span className="font-medium text-gray-600">步骤:</span>
            <span className="ml-2 text-gray-800">{debugInfo.step_description}</span>
          </div>

          <div>
            <span className="font-medium text-gray-600">时间:</span>
            <span className="ml-2 text-gray-500 text-xs">
              {new Date(debugInfo.timestamp).toLocaleString()}
            </span>
          </div>

          <div>
            <div className="font-medium text-gray-600 mb-1">提示词:</div>
            <div className="bg-gray-50 p-2 rounded text-xs text-gray-700 max-h-32 overflow-y-auto border border-gray-200">
              {debugInfo.prompt}
            </div>
          </div>

          <div>
            <div className="font-medium text-gray-600 mb-1">LLM响应:</div>
            <div className="bg-blue-50 p-2 rounded text-xs text-gray-700 max-h-32 overflow-y-auto border border-blue-200">
              {debugInfo.response}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SimpleLLMDebugPanel;