import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: React.ReactNode;
  actions?: React.ReactNode;
}

const Card: React.FC<CardProps> = ({
  children,
  className = '',
  title,
  actions
}) => (
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

export default Card;