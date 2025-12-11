import React from 'react';
import { Search } from 'lucide-react';

interface EmptyStateProps {
  message: React.ReactNode;
  action?: React.ReactNode;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  message,
  action
}) => (
  <div className="flex flex-col items-center justify-center py-16 text-gray-500">
    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
      <Search size={24} className="text-gray-400" />
    </div>
    <p className="mb-4">{message}</p>
    {action}
  </div>
);

export default EmptyState;