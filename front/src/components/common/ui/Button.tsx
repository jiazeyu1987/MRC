import React from 'react';
import { useTheme } from '../../../hooks/useTheme';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  className?: string;
  disabled?: boolean;
  icon?: React.ComponentType<{ size?: number }>;
  size?: 'xs' | 'sm' | 'md';
}

const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  className = '',
  disabled = false,
  icon: Icon,
  size = 'md'
}) => {
  const { theme } = useTheme();

  const baseStyle = "rounded-lg font-medium transition-all flex items-center justify-center gap-2";
  const sizes = {
    xs: "px-2.5 py-1 text-xs",
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2"
  };

  // Dynamic class construction based on theme
  const variants = {
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

export default Button;