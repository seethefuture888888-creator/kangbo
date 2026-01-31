import type { ActionType } from '@/types';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ActionBadgeProps {
  action: ActionType;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

const actionConfig = {
  ADD: {
    label: '加仓',
    labelEn: 'ADD',
    bg: 'bg-emerald-500/20',
    text: 'text-emerald-400',
    border: 'border-emerald-500/30',
    icon: TrendingUp,
    iconColor: 'text-emerald-400'
  },
  REDUCE: {
    label: '减仓',
    labelEn: 'REDUCE',
    bg: 'bg-rose-500/20',
    text: 'text-rose-400',
    border: 'border-rose-500/30',
    icon: TrendingDown,
    iconColor: 'text-rose-400'
  },
  HOLD: {
    label: '观望',
    labelEn: 'HOLD',
    bg: 'bg-amber-500/20',
    text: 'text-amber-400',
    border: 'border-amber-500/30',
    icon: Minus,
    iconColor: 'text-amber-400'
  }
};

export function ActionBadge({ 
  action, 
  size = 'md',
  showIcon = true,
  className 
}: ActionBadgeProps) {
  const config = actionConfig[action];
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-sm px-3 py-1 gap-1.5',
    lg: 'text-base px-4 py-1.5 gap-2'
  };

  const iconSizes = {
    sm: 12,
    md: 14,
    lg: 18
  };

  return (
    <span 
      className={cn(
        "inline-flex items-center rounded-lg font-semibold border",
        sizeClasses[size],
        config.bg,
        config.text,
        config.border,
        className
      )}
    >
      {showIcon && <Icon size={iconSizes[size]} className={config.iconColor} />}
      <span>{config.labelEn}</span>
      <span className="opacity-70">· {config.label}</span>
    </span>
  );
}

export function ActionButton({ 
  action, 
  onClick,
  disabled = false,
  className 
}: { 
  action: ActionType;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}) {
  const config = actionConfig[action];
  const Icon = config.icon;

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all",
        "border",
        config.bg,
        config.text,
        config.border,
        "hover:opacity-80 active:scale-95",
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
    >
      <Icon size={16} />
      <span>{config.label}</span>
    </button>
  );
}
