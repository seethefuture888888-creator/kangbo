import type { LightStatus } from '@/types';
import { cn } from '@/lib/utils';

interface LightIndicatorProps {
  status: LightStatus;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

const statusConfig = {
  green: {
    bg: 'bg-emerald-500',
    glow: 'shadow-emerald-500/50',
    label: '绿',
    labelEn: 'GREEN'
  },
  yellow: {
    bg: 'bg-amber-500',
    glow: 'shadow-amber-500/50',
    label: '黄',
    labelEn: 'YELLOW'
  },
  red: {
    bg: 'bg-rose-500',
    glow: 'shadow-rose-500/50',
    label: '红',
    labelEn: 'RED'
  }
};

const sizeConfig = {
  sm: 'w-3 h-3',
  md: 'w-4 h-4',
  lg: 'w-6 h-6'
};

export function LightIndicator({ 
  status, 
  size = 'md', 
  showLabel = false,
  className 
}: LightIndicatorProps) {
  const config = statusConfig[status];
  const sizeClass = sizeConfig[size];

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div 
        className={cn(
          "rounded-full",
          sizeClass,
          config.bg,
          "shadow-lg",
          config.glow,
          "animate-pulse"
        )}
      />
      {showLabel && (
        <span className={cn("text-xs font-medium", config.bg.replace('bg-', 'text-'))}>
          {config.label}
        </span>
      )}
    </div>
  );
}

export function LightBadge({ 
  status, 
  className 
}: { 
  status: LightStatus; 
  className?: string;
}) {
  const config = statusConfig[status];
  
  return (
    <span 
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
        config.bg.replace('bg-', 'bg-').replace('500', '500/20'),
        config.bg.replace('bg-', 'text-'),
        className
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full mr-1.5", config.bg)} />
      {config.labelEn}
    </span>
  );
}
