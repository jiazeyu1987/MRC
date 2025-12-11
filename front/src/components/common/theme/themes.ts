export type ThemeKey = 'blue' | 'purple' | 'emerald' | 'rose' | 'amber';

export interface ThemeConfig {
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

export const THEMES: Record<ThemeKey, ThemeConfig> = {
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