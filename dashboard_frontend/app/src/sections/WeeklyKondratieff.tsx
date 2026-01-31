import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import type { WeeklyKondratieff } from '@/types';
import { 
  Cpu, 
  Zap, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Factory,
  Lightbulb,
  Battery,
  Flame,
  ArrowRight
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Cell,
  ReferenceLine
} from 'recharts';

interface WeeklyKondratieffProps {
  data: WeeklyKondratieff;
}

const phaseConfig = {
  spring: {
    label: '春季 (扩散>约束)',
    description: 'AI扩散强劲，资源约束尚未显现',
    strategy: '偏AI卖铲子 + 适度资源',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500',
    border: 'border-emerald-500/30',
    icon: TrendingUp
  },
  winter: {
    label: '冬季 (约束掐住扩散)',
    description: '资源瓶颈制约AI扩张',
    strategy: '偏资源 + 防守',
    color: 'text-rose-400',
    bg: 'bg-rose-500',
    border: 'border-rose-500/30',
    icon: TrendingDown
  },
  transition: {
    label: '过渡期 (均衡震荡)',
    description: '扩散与约束力量均衡',
    strategy: '均衡配置 + 灵活调整',
    color: 'text-amber-400',
    bg: 'bg-amber-500',
    border: 'border-amber-500/30',
    icon: Minus
  }
};

export function WeeklyKondratieffView({ data }: WeeklyKondratieffProps) {
  const phase = phaseConfig[data.phase];
  const PhaseIcon = phase.icon;

  const comparisonData = [
    { name: 'AI扩散指数', value: data.aiDiffusionIndex, type: 'diffusion' },
    { name: '资源约束指数', value: data.constraintIndex, type: 'constraint' }
  ];

  return (
    <div className="space-y-6">
      {/* Phase Card */}
      <Card className={cn("bg-slate-900/80 border-slate-800", phase.border)}>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Phase Indicator */}
            <div className="lg:col-span-1 flex flex-col items-center justify-center border-r border-slate-800">
              <div className={cn(
                "w-20 h-20 rounded-2xl flex items-center justify-center mb-4",
                phase.bg.replace('bg-', 'bg-').replace('500', '500/20')
              )}>
                <PhaseIcon className={cn("w-10 h-10", phase.color)} />
              </div>
              <h3 className={cn("text-xl font-bold", phase.color)}>
                {phase.label}
              </h3>
              <p className="text-sm text-slate-400 mt-1 text-center">
                {phase.description}
              </p>
            </div>

            {/* Index Comparison */}
            <div className="lg:col-span-1 border-r border-slate-800 px-6">
              <p className="text-sm text-slate-400 mb-4">指数对比</p>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-300 flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-blue-400" />
                      AI扩散指数
                    </span>
                    <span className="text-blue-400 font-medium">{data.aiDiffusionIndex}</span>
                  </div>
                  <Progress 
                    value={data.aiDiffusionIndex} 
                    className="h-2 bg-slate-800"
                  />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-300 flex items-center gap-2">
                      <Factory className="w-4 h-4 text-amber-400" />
                      资源约束指数
                    </span>
                    <span className="text-amber-400 font-medium">{data.constraintIndex}</span>
                  </div>
                  <Progress 
                    value={data.constraintIndex} 
                    className="h-2 bg-slate-800"
                  />
                </div>
                <div className="pt-2 border-t border-slate-800">
                  <div className="flex items-center justify-center gap-2">
                    <span className="text-sm text-slate-400">差距:</span>
                    <span className={cn(
                      "text-lg font-bold",
                      data.aiDiffusionIndex > data.constraintIndex ? "text-emerald-400" : "text-rose-400"
                    )}>
                      {data.aiDiffusionIndex > data.constraintIndex ? '+' : ''}
                      {(data.aiDiffusionIndex - data.constraintIndex).toFixed(0)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Strategy */}
            <div className="lg:col-span-1 px-6">
              <p className="text-sm text-slate-400 mb-4">策略偏好</p>
              <div className={cn(
                "p-4 rounded-xl border",
                "bg-slate-800/50",
                phase.border
              )}>
                <div className="flex items-center gap-2 mb-2">
                  <Lightbulb className={cn("w-5 h-5", phase.color)} />
                  <span className={cn("font-medium", phase.color)}>
                    下周策略
                  </span>
                </div>
                <p className="text-slate-300">{data.strategy}</p>
              </div>
              <div className="mt-4 space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <ArrowRight className="w-4 h-4 text-slate-500" />
                  <span className="text-slate-400">AI卖铲子: </span>
                  <span className={cn(
                    data.aiDiffusionIndex > 60 ? "text-emerald-400" : "text-slate-500"
                  )}>
                    {data.aiDiffusionIndex > 60 ? '偏好' : '中性'}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <ArrowRight className="w-4 h-4 text-slate-500" />
                  <span className="text-slate-400">资源/瓶颈: </span>
                  <span className={cn(
                    data.constraintIndex > 60 ? "text-emerald-400" : "text-slate-500"
                  )}>
                    {data.constraintIndex > 60 ? '偏好' : '中性'}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <ArrowRight className="w-4 h-4 text-slate-500" />
                  <span className="text-slate-400">防守配置: </span>
                  <span className={cn(
                    data.aiDiffusionIndex < 50 && data.constraintIndex > 50 ? "text-emerald-400" : "text-slate-500"
                  )}>
                    {data.aiDiffusionIndex < 50 && data.constraintIndex > 50 ? '偏好' : '中性'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Component Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Diffusion Components */}
        <Card className="bg-slate-900/80 border-slate-800">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-semibold text-slate-100 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-blue-400" />
              AI扩散指数构成
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                    <Cpu className="w-5 h-5 text-blue-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">半导体相对强弱</p>
                    <p className="text-xs text-slate-500">SOX/SPX</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={cn(
                    "text-lg font-bold",
                    data.components.soxRatio > 1 ? "text-emerald-400" : "text-rose-400"
                  )}>
                    {data.components.soxRatio > 1 ? '+' : ''}
                    {((data.components.soxRatio - 1) * 100).toFixed(1)}%
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                    <Zap className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">AI龙头相对强弱</p>
                    <p className="text-xs text-slate-500">NVDA/QQQ</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={cn(
                    "text-lg font-bold",
                    data.components.nvdaRatio > 1 ? "text-emerald-400" : "text-rose-400"
                  )}>
                    {data.components.nvdaRatio > 1 ? '+' : ''}
                    {((data.components.nvdaRatio - 1) * 100).toFixed(1)}%
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
                    <Battery className="w-5 h-5 text-amber-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">数据中心电力</p>
                    <p className="text-xs text-slate-500">公用事业相对强弱</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={cn(
                    "text-lg font-bold",
                    data.components.utilityRatio > 1 ? "text-emerald-400" : "text-rose-400"
                  )}>
                    {data.components.utilityRatio > 1 ? '+' : ''}
                    {((data.components.utilityRatio - 1) * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Constraint Components */}
        <Card className="bg-slate-900/80 border-slate-800">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-semibold text-slate-100 flex items-center gap-2">
              <Factory className="w-5 h-5 text-amber-400" />
              资源约束指数构成
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center">
                    <Factory className="w-5 h-5 text-orange-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">铜趋势动量</p>
                    <p className="text-xs text-slate-500">电气化/基建温度计</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={cn(
                    "text-lg font-bold",
                    data.components.copperMomentum > 0 ? "text-emerald-400" : "text-rose-400"
                  )}>
                    {data.components.copperMomentum > 0 ? '+' : ''}
                    {(data.components.copperMomentum * 100).toFixed(1)}%
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                    <Flame className="w-5 h-5 text-red-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">能源价格</p>
                    <p className="text-xs text-slate-500">电力成本指标</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-slate-200">
                    ${data.components.energyPrice.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-6 p-4 rounded-lg bg-slate-800/30 border border-slate-700">
              <p className="text-sm text-slate-400 mb-2">康波链条解读</p>
              <p className="text-sm text-slate-300 leading-relaxed">
                当前处于<span className={phase.color}>「{phase.label.split(' ')[0]}」</span>阶段。
                {data.aiDiffusionIndex > data.constraintIndex 
                  ? `AI扩散指数(${data.aiDiffusionIndex})高于资源约束指数(${data.constraintIndex})，表明技术创新驱动力强于资源瓶颈制约，有利于风险资产尤其是AI产业链。`
                  : `资源约束指数(${data.constraintIndex})高于AI扩散指数(${data.aiDiffusionIndex})，表明资源瓶颈开始制约技术扩张，需关注通胀与成本压力。`
                }
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Comparison Chart */}
      <Card className="bg-slate-900/80 border-slate-800">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-400" />
            扩散 vs 约束 对比
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis 
                  type="number" 
                  domain={[0, 100]}
                  stroke="#475569"
                  tick={{ fill: '#64748b', fontSize: 12 }}
                />
                <YAxis 
                  type="category" 
                  dataKey="name"
                  stroke="#475569"
                  tick={{ fill: '#94a3b8', fontSize: 12 }}
                  width={100}
                />
                <Tooltip 
                  cursor={{ fill: '#1e293b' }}
                  contentStyle={{ 
                    backgroundColor: '#0f172a', 
                    border: '1px solid #1e293b',
                    borderRadius: '8px'
                  }}
                  labelStyle={{ color: '#94a3b8' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <ReferenceLine x={50} stroke="#475569" strokeDasharray="3 3" />
                <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={40}>
                  {comparisonData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.type === 'diffusion' ? '#3b82f6' : '#f59e0b'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-6 mt-4 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-blue-500" />
              <span className="text-slate-400">AI扩散指数</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-amber-500" />
              <span className="text-slate-400">资源约束指数</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-slate-500" style={{ borderTop: '1px dashed' }} />
              <span className="text-slate-400">中性线(50)</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
