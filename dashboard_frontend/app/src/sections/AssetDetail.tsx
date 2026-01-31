import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LightBadge } from '@/components/ui/custom/LightIndicator';
import { ActionBadge } from '@/components/ui/custom/ActionBadge';
import { cn } from '@/lib/utils';
import type { Asset, AssetSignal, PriceData, AssetTechnicalData } from '@/types';
import { 
  ArrowLeft, 
  TrendingUp, 
  Activity, 
  BarChart3,
  Zap
} from 'lucide-react';
import { 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine,
  ComposedChart,
  Line
} from 'recharts';

interface AssetDetailProps {
  asset: Asset;
  signal: AssetSignal;
  priceHistory: PriceData[];
  technicalData: AssetTechnicalData;
  onBack: () => void;
}

function formatNumber(num: number, decimals: number = 2): string {
  return num.toLocaleString('en-US', { 
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals 
  });
}

function formatPercent(num: number): string {
  return `${num >= 0 ? '+' : ''}${(num * 100).toFixed(2)}%`;
}

export function AssetDetail({ 
  asset, 
  signal, 
  priceHistory,
  technicalData,
  onBack 
}: AssetDetailProps) {
  const chartData = priceHistory.map(d => ({
    date: d.date,
    price: d.close,
    ma20: d.close * (1 + (Math.random() - 0.5) * 0.02),
    ma60: d.close * (1 + (Math.random() - 0.5) * 0.04),
    ma200: d.close * (1 + (Math.random() - 0.5) * 0.06),
  }));

  const latestPrice = priceHistory[priceHistory.length - 1]?.close || asset.price;
  const priceChange = asset.priceChange24h;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={onBack}
            className="border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回
          </Button>
          
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
              <span className="text-lg font-bold text-white">{asset.id.slice(0, 2)}</span>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-800">{asset.name}</h2>
              <p className="text-sm text-slate-500">{asset.ticker}</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-3xl font-bold text-slate-800">
              ${formatNumber(latestPrice)}
            </p>
            <p className={cn(
              "text-sm font-medium",
              priceChange >= 0 ? "text-emerald-600" : "text-rose-600"
            )}>
              {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}% (24h)
            </p>
          </div>
        </div>
      </div>

      {/* Three Lights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-slate-500" />
                <span className="text-sm text-slate-700">Trend 趋势</span>
              </div>
              <LightBadge status={signal.trendLight} />
            </div>
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">MA20</span>
                <span className="text-slate-700">${formatNumber(technicalData.ma20)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">MA60</span>
                <span className="text-slate-700">${formatNumber(technicalData.ma60)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">MA200</span>
                <span className="text-slate-700">${formatNumber(technicalData.ma200)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">12周动量</span>
                <span className={technicalData.mom12w >= 0 ? "text-emerald-600" : "text-rose-600"}>
                  {formatPercent(technicalData.mom12w)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-slate-500" />
                <span className="text-sm text-slate-700">Risk 风险</span>
              </div>
              <LightBadge status={signal.riskLight} />
            </div>
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">20日波动率</span>
                <span className="text-slate-700">{(technicalData.vol20Ann * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">60日最大回撤</span>
                <span className="text-rose-600">{(technicalData.mdd60 * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">波动分位(1年)</span>
                <span className="text-slate-700">{technicalData.volPercentile1y}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">回撤分位(1年)</span>
                <span className="text-slate-700">{technicalData.ddPercentile1y}%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-slate-500" />
                <span className="text-sm text-slate-700">Catalyst 催化</span>
              </div>
              <LightBadge status={signal.catalystLight} />
            </div>
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">相对强弱(RS)</span>
                <span className="text-slate-700">{technicalData.rsToBenchmark.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">vs DXY相关</span>
                <span className="text-slate-700">{technicalData.correlationDXY.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">vs 实际利率</span>
                <span className="text-slate-700">{technicalData.correlationRealRate.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">vs SPX相关</span>
                <span className="text-slate-700">{technicalData.correlationSPX.toFixed(2)}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Price Chart */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            价格走势 (6个月)
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <div className="h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData}>
                <defs>
                  <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis 
                  dataKey="date" 
                  stroke="#64748b"
                  tick={{ fill: '#475569', fontSize: 12 }}
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis 
                  stroke="#64748b"
                  tick={{ fill: '#475569', fontSize: 12 }}
                  domain={['auto', 'auto']}
                  tickFormatter={(value) => `$${value.toFixed(0)}`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#ffffff', 
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px'
                  }}
                  labelStyle={{ color: '#475569' }}
                  itemStyle={{ color: '#0f172a' }}
                  formatter={(value: number) => [`$${value.toFixed(2)}`, '']}
                />
                <Area 
                  type="monotone" 
                  dataKey="price" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  fill="url(#priceGradient)"
                />
                <Line 
                  type="monotone" 
                  dataKey="ma20" 
                  stroke="#10b981" 
                  strokeWidth={1}
                  dot={false}
                  strokeDasharray="5 5"
                />
                <Line 
                  type="monotone" 
                  dataKey="ma60" 
                  stroke="#f59e0b" 
                  strokeWidth={1}
                  dot={false}
                  strokeDasharray="5 5"
                />
                <ReferenceLine 
                  y={technicalData.ma200} 
                  stroke="#ef4444" 
                  strokeDasharray="3 3"
                  label={{ value: 'MA200', fill: '#ef4444', fontSize: 12 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-6 mt-4 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-blue-500" />
              <span className="text-slate-500">价格</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-emerald-500" style={{ borderTop: '1px dashed' }} />
              <span className="text-slate-500">MA20</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-amber-500" style={{ borderTop: '1px dashed' }} />
              <span className="text-slate-500">MA60</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-rose-500" style={{ borderTop: '1px dashed' }} />
              <span className="text-slate-500">MA200</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Action & Recommendation */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-slate-500 mb-3">建议动作</p>
              <div className="flex items-center gap-3">
                <ActionBadge action={signal.action} size="lg" />
                <span className="text-slate-700">
                  建议仓位上限: {(signal.suggestedMaxWeight * 100).toFixed(0)}%
                </span>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {signal.reasonCodes.map((code, idx) => (
                  <span 
                    key={idx}
                    className="px-2 py-1 rounded bg-slate-100 text-xs text-slate-500"
                  >
                    {code}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm text-slate-500 mb-3">分析备注</p>
              <p className="text-slate-700">{signal.notes}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
