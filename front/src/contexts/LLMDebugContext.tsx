import React, { createContext, ReactNode } from 'react';

interface LLMDebugInfo {
  request?: any;
  response?: any;
  metadata?: any;
  timestamp?: number;
}

interface LLMDebugContextValue {
  updateLLMDebugInfo: (debugInfo: LLMDebugInfo) => void;
  showDebugPanel: boolean;
  setShowDebugPanel: (show: boolean) => void;
}

const LLMDebugContext = createContext<LLMDebugContextValue>({
  updateLLMDebugInfo: () => {},
  showDebugPanel: true,
  setShowDebugPanel: () => {}
});

interface LLMDebugProviderProps {
  children: ReactNode;
}

export const LLMDebugProvider: React.FC<LLMDebugProviderProps> = ({ children }) => {
  // For now, keeping the existing implementation
  // This would need to be connected to actual state management
  const contextValue: LLMDebugContextValue = {
    updateLLMDebugInfo: () => {},
    showDebugPanel: true,
    setShowDebugPanel: () => {}
  };

  return (
    <LLMDebugContext.Provider value={contextValue}>
      {children}
    </LLMDebugContext.Provider>
  );
};

export { LLMDebugContext };