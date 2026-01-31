import { cn } from '@/lib/utils';

interface RiskScoreProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

export function RiskScore({ 
  score, 
  size = 'md',
  showLabel = true,
  className 
}: RiskScoreProps) {
  const getColor = (s: number) => {
    if (s >= 70) return 'text-emerald-600';
    if (s >= 50) return 'text-amber-600';
    if (s >= 30) return 'text-orange-600';
    return 'text-rose-600';
  };

  const getBgColor = (s: number) => {
    if (s >= 70) return 'bg-emerald-500';
    if (s >= 50) return 'bg-amber-500';
    if (s >= 30) return 'bg-orange-500';
    return 'bg-rose-500';
  };

  const getLabel = (s: number) => {
    if (s >= 70) return '低风险偏好';
    if (s >= 50) return '中等风险';
    if (s >= 30) return '风险上升';
    return '高风险';
  };

  const sizeClasses = {
    sm: { container: 'w-16 h-16', score: 'text-xl', label: 'text-xs' },
    md: { container: 'w-24 h-24', score: 'text-3xl', label: 'text-sm' },
    lg: { container: 'w-32 h-32', score: 'text-4xl', label: 'text-base' }
  };

  const classes = sizeClasses[size];
  const colorClass = getColor(score);
  const bgColorClass = getBgColor(score);

  return (
    <div className={cn("flex flex-col items-center", className)}>
      <div 
        className={cn(
          "relative rounded-full flex items-center justify-center",
          "bg-white border-4 border-slate-200 shadow-sm",
          classes.container
        )}
      >
        {/* Progress ring */}
        <svg 
          className="absolute inset-0 w-full h-full -rotate-90"
          viewBox="0 0 100 100"
        >
          <circle
            cx="50"
            cy="50"
            r="42"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            className="text-slate-200"
          />
          <circle
            cx="50"
            cy="50"
            r="42"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${score * 2.64} 264`}
            className={cn("transition-all duration-500", bgColorClass.replace('bg-', 'text-'))}
          />
        </svg>
        
        {/* Score */}
        <span className={cn("relative font-bold", classes.score, colorClass)}>
          {score}
        </span>
      </div>
      
      {showLabel && (
        <div className="mt-2 text-center">
          <p className={cn("font-medium", classes.label, colorClass)}>
            {getLabel(score)}
          </p>
          <p className="text-xs text-slate-500">Risk Score</p>
        </div>
      )}
    </div>
  );
}

export function RiskScoreBar({ 
  score, 
  className 
}: { 
  score: number;
  className?: string;
}) {
  const getColor = (s: number) => {
    if (s >= 70) return 'from-emerald-500 to-emerald-400';
    if (s >= 50) return 'from-amber-500 to-amber-400';
    if (s >= 30) return 'from-orange-500 to-orange-400';
    return 'from-rose-500 to-rose-400';
  };

  return (
    <div className={cn("w-full", className)}>
      <div className="flex justify-between text-xs text-slate-500 mb-1">
        <span>0</span>
        <span className="font-medium text-slate-700">Risk Score: {score}</span>
        <span>100</span>
      </div>
      <div className="h-3 bg-slate-200 rounded-full overflow-hidden">
        <div 
          className={cn(
            "h-full rounded-full transition-all duration-500 bg-gradient-to-r",
            getColor(score)
          )}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
