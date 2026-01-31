import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { LightIndicator } from '@/components/ui/custom/LightIndicator';
import { RegimeBadge } from '@/components/ui/custom/RegimeBadge';
import { RiskScore } from '@/components/ui/custom/RiskScore';
import { ActionBadge } from '@/components/ui/custom/ActionBadge';
import { cn } from '@/lib/utils';
import type { Asset, AssetSignal, DailySignal, MacroSwitch } from '@/types';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  DollarSign, 
  Factory, 
  Flame,
  ChevronRight,
  PieChart
} from 'lucide-react';

interface DailyOverviewProps {
  dailySignal: DailySignal;
  macroSwitches: MacroSwitch[];
  assets: Asset[];
  assetSignals: AssetSignal[];
  portfolioSummary: {
    totalCurrentWeight: number;
    totalSuggestedWeight: number;
    availableAddSpace: number;
  };
  onAssetClick: (assetId: string) => void;
}

const switchIcons: Record<string, React.ElementType> = {
  'HY_SPREAD': Activity,
  'REAL10Y': DollarSign,
  'DXY': DollarSign,
  'PMI': Factory,
  'CORE_INFL': Flame
};

export function DailyOverview({ 
  dailySignal, 
  macroSwitches, 
  assets, 
  assetSignals,
  portfolioSummary,
  onAssetClick
}: DailyOverviewProps) {
  return (
    <div className="space-y-6">
      {/* Header Card - Today's Conclusion */}
      <Card className="bg-slate-900/80 border-slate-800">
        <CardContent className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Regime & Risk Score */}
            <div className="lg:col-span-1 flex flex-col items-center justify-center border-r border-slate-800">
              <RegimeBadge regime={dailySignal.regime} size="lg" className="mb-4" />
              <RiskScore score={dailySignal.riskScore} size="md" />
            </div>

            {/* Main Info */}
            <div className="lg:col-span-2 space-y-4">
              <div>
                <p className="text-sm text-slate-400 mb-2">今日总指令</p>
                <div className="flex items-center gap-3">
                  <ActionBadge action={dailySignal.portfolioAction} size="lg" />
                  <span className="text-slate-300">· {dailySignal.riskMode}</span>
                </div>
              </div>

              <div>
                <p className="text-sm text-slate-400 mb-2">主要驱动因子</p>
                <div className="flex flex-wrap gap-2">
                  {dailySignal.drivers.map((driver, idx) => (
                    <span 
                      key={idx}
                      className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-slate-800 text-slate-300 text-sm"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                      {driver}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700">
                <p className="text-sm text-slate-300 leading-relaxed">
                  {dailySignal.commentSummary}
                </p>
              </div>
            </div>

            {/* Portfolio Bar */}
            <div className="lg:col-span-1 border-l border-slate-800 pl-6">
              <div className="flex items-center gap-2 mb-4">
                <PieChart className="w-4 h-4 text-slate-400" />
                <span className="text-sm font-medium text-slate-300">仓位建议</span>
              </div>
              
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">当前仓位</span>
                    <span className="text-slate-300">
                      {(portfolioSummary.totalCurrentWeight * 100).toFixed(0)}%
                    </span>
                  </div>
                  <Progress 
                    value={portfolioSummary.totalCurrentWeight * 100} 
                    className="h-2 bg-slate-800"
                  />
                </div>
                
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">建议上限</span>
                    <span className="text-emerald-400">
                      {(portfolioSummary.totalSuggestedWeight * 100).toFixed(0)}%
                    </span>
                  </div>
                  <Progress 
                    value={portfolioSummary.totalSuggestedWeight * 100} 
                    className="h-2 bg-slate-800"
                  />
                </div>

                <div className="pt-2 border-t border-slate-800">
                  {portfolioSummary.availableAddSpace > 0 ? (
                    <div className="flex items-center gap-2 text-emerald-400">
                      <TrendingUp className="w-4 h-4" />
                      <span className="text-sm">
                        可加仓空间: +{(portfolioSummary.availableAddSpace * 100).toFixed(0)}%
                      </span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-rose-400">
                      <TrendingDown className="w-4 h-4" />
                      <span className="text-sm">
                        需减仓: {(Math.abs(portfolioSummary.availableAddSpace) * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Macro Switches */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {macroSwitches.map((switch_) => {
          const Icon = switchIcons[switch_.id] || Activity;
          return (
            <Card 
              key={switch_.id}
              className="bg-slate-900/80 border-slate-800 hover:border-slate-700 transition-colors"
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4 text-slate-400" />
                    <span className="text-xs text-slate-400">{switch_.name}</span>
                  </div>
                  <LightIndicator status={switch_.light} size="sm" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-bold text-slate-100">
                      {switch_.currentValue.toFixed(2)}
                    </span>
                    <span className={cn(
                      "text-xs",
                      switch_.change7d > 0 ? "text-emerald-400" : "text-rose-400"
                    )}>
                      {switch_.change7d > 0 ? '+' : ''}{switch_.change7d.toFixed(2)} (7d)
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">分位: {switch_.percentile}%</span>
                    <span className="text-slate-500">
                      新鲜度: {switch_.freshness}天
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Asset Heatmap Table */}
      <Card className="bg-slate-900/80 border-slate-800">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" />
            资产热力表
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/50">
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400">资产</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-slate-400">Trend</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-slate-400">Risk</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-slate-400">Catalyst</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-400">建议上限</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-slate-400">动作</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400">备注</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-slate-400">详情</th>
                </tr>
              </thead>
              <tbody>
                {assets.map((asset) => {
                  const signal = assetSignals.find(s => s.assetId === asset.id);
                  if (!signal) return null;

                  return (
                    <tr 
                      key={asset.id}
                      className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors cursor-pointer"
                      onClick={() => onAssetClick(asset.id)}
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center">
                            <span className="text-xs font-bold text-slate-300">
                              {asset.id.slice(0, 3)}
                            </span>
                          </div>
                          <div>
                            <p className="text-sm font-medium text-slate-200">{asset.name}</p>
                            <p className="text-xs text-slate-500">{asset.ticker}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <LightIndicator status={signal.trendLight} size="sm" />
                      </td>
                      <td className="px-4 py-3 text-center">
                        <LightIndicator status={signal.riskLight} size="sm" />
                      </td>
                      <td className="px-4 py-3 text-center">
                        <LightIndicator status={signal.catalystLight} size="sm" />
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className="text-sm font-medium text-slate-300">
                          {(signal.suggestedMaxWeight * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <ActionBadge action={signal.action} size="sm" />
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-xs text-slate-400 truncate max-w-[200px]">
                          {signal.notes}
                        </p>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <ChevronRight className="w-4 h-4 text-slate-500" />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
