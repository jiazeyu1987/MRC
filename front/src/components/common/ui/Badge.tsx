import React from 'react';
import { useTheme } from '../../../hooks/useTheme';

interface BadgeProps {
  children: React.ReactNode;
  color?: 'theme' | 'green' | 'gray' | 'red' | 'blue';
  size?: 'sm' | 'md';
}

const Badge: React.FC<BadgeProps> = ({
  children,
  color = 'theme',
  size = 'md'
}) => {
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

export default Badge;