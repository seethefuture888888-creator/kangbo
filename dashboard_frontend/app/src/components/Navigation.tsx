import { cn } from '@/lib/utils';
import { LayoutDashboard, TrendingUp, BarChart3, RefreshCw } from 'lucide-react';

interface NavigationProps {
  currentView: 'daily' | 'asset' | 'weekly';
  onViewChange: (view: 'daily' | 'asset' | 'weekly') => void;
  className?: string;
}

const navItems = [
  { id: 'daily' as const, label: 'Daily 总览', icon: LayoutDashboard },
  { id: 'asset' as const, label: '资产详情', icon: TrendingUp },
  { id: 'weekly' as const, label: 'Weekly 康波', icon: BarChart3 }
];

export function Navigation({ currentView, onViewChange, className }: NavigationProps) {
  return (
    <nav className={cn("flex items-center gap-1 p-1 bg-slate-900/80 rounded-xl border border-slate-800", className)}>
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = currentView === item.id;
        
        return (
          <button
            key={item.id}
            onClick={() => onViewChange(item.id)}
            className={cn(
              "flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all",
              "hover:bg-slate-800",
              isActive && "bg-slate-800 text-slate-100",
              !isActive && "text-slate-400 hover:text-slate-200"
            )}
          >
            <Icon size={16} className={isActive ? "text-blue-400" : ""} />
            <span>{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}

export function Header({ 
  date, 
  dataAsOf,
  onRefresh,
  lastUpdatedAt,
  loading,
  className 
}: { 
  date: string;
  dataAsOf: string;
  onRefresh?: () => void;
  lastUpdatedAt?: string;
  loading?: boolean;
  className?: string;
}) {
  return (
    <header className={cn("flex items-center justify-between py-4", className)}>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-100">
              投资决策仪表盘
            </h1>
            <p className="text-xs text-slate-400">
              Investment Decision Dashboard
            </p>
          </div>
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        {lastUpdatedAt != null && (
          <p className="text-xs text-slate-500">
            更新于: {lastUpdatedAt}
          </p>
        )}
        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            disabled={loading}
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all",
              "bg-slate-800 hover:bg-slate-700 text-slate-200 disabled:opacity-50 disabled:cursor-not-allowed"
            )}
            title="刷新数据"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            <span>{loading ? '刷新中…' : '刷新'}</span>
          </button>
        )}
        <div className="text-right">
          <p className="text-sm font-medium text-slate-200">{date}</p>
          <p className="text-xs text-slate-500">
            数据截止: {dataAsOf}
          </p>
        </div>
      </div>
    </header>
  );
}
