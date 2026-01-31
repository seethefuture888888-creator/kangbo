import type { RegimeType } from '@/types';
import { cn } from '@/lib/utils';

interface RegimeBadgeProps {
  regime: RegimeType;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const regimeConfig = {
  A: {
    label: '防守',
    labelEn: 'DEFENSE',
    description: '信用紧缩 + 增长疲软',
    bg: 'bg-rose-500',
    light: 'bg-rose-500',
    border: 'border-rose-500/30',
    text: 'text-rose-500'
  },
  B: {
    label: '复苏进攻',
    labelEn: 'OFFENSE',
    description: '信用宽松 + 增长企稳',
    bg: 'bg-emerald-500',
    light: 'bg-emerald-500',
    border: 'border-emerald-500/30',
    text: 'text-emerald-500'
  },
  C: {
    label: '再通胀/过热',
    labelEn: 'REFLATION',
    description: '通胀上行 + 流动性收紧',
    bg: 'bg-amber-500',
    light: 'bg-amber-500',
    border: 'border-amber-500/30',
    text: 'text-amber-500'
  },
  D: {
    label: '出清/机会',
    labelEn: 'CAPITULATION',
    description: '增长疲软 + 通胀下行',
    bg: 'bg-blue-500',
    light: 'bg-blue-500',
    border: 'border-blue-500/30',
    text: 'text-blue-500'
  }
};

export function RegimeBadge({ 
  regime, 
  showLabel = true,
  size = 'md',
  className 
}: RegimeBadgeProps) {
  const config = regimeConfig[regime];
  
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-1.5'
  };

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div 
        className={cn(
          "flex items-center gap-2 rounded-lg font-bold tracking-wide",
          sizeClasses[size],
          "bg-white border-slate-200 shadow-sm",
          "border",
          config.border,
          config.text
        )}
      >
        <span className={cn("w-2 h-2 rounded-full animate-pulse", config.light)} />
        <span>Regime {regime}</span>
        {showLabel && (
          <span className="opacity-70">· {config.label}</span>
        )}
      </div>
      {showLabel && (
        <span className="text-xs text-slate-500 hidden sm:inline">
          {config.description}
        </span>
      )}
    </div>
  );
}

export function RegimeCard({ 
  regime, 
  className 
}: { 
  regime: RegimeType;
  className?: string;
}) {
  const config = regimeConfig[regime];
  
  return (
    <div 
      className={cn(
        "p-4 rounded-xl border",
        "bg-slate-50",
        config.border,
        className
      )}
    >
      <div className="flex items-center gap-3 mb-2">
        <div className={cn("w-4 h-4 rounded-full", config.light)} />
        <span className={cn("text-2xl font-bold", config.text)}>
          Regime {regime}
        </span>
      </div>
      <p className="text-lg font-medium text-slate-800">{config.label}</p>
      <p className="text-sm text-slate-500 mt-1">{config.description}</p>
    </div>
  );
}
