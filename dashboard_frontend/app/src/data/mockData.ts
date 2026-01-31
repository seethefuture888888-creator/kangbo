import type { 
  Asset, 
  AssetSignal, 
  DailySignal, 
  MacroSwitch, 
  PriceData, 
  WeeklyKondratieff,
  AssetTechnicalData,
  PortfolioPosition
} from '@/types';

export const assets: Asset[] = [
  {
    id: 'BTC',
    name: 'Bitcoin',
    ticker: 'BTC-USD',
    assetType: 'crypto',
    currency: 'USD',
    benchmarkId: 'QQQ',
    baseMaxWeight: 0.25,
    currentWeight: 0.15,
    suggestedMaxWeight: 0.18,
    price: 98750,
    priceChange24h: 2.3,
    priceChange7d: 5.1,
    priceChange30d: 12.5
  },
  {
    id: 'AI_BASKET',
    name: 'AI Basket',
    ticker: 'AI_BASKET',
    assetType: 'equity',
    currency: 'USD',
    benchmarkId: 'SPY',
    baseMaxWeight: 0.40,
    currentWeight: 0.25,
    suggestedMaxWeight: 0.28,
    price: 145.2,
    priceChange24h: 1.8,
    priceChange7d: 3.2,
    priceChange30d: 8.7
  },
  {
    id: 'TSLA',
    name: 'Tesla',
    ticker: 'TSLA',
    assetType: 'equity',
    currency: 'USD',
    benchmarkId: 'SPY',
    baseMaxWeight: 0.15,
    currentWeight: 0.08,
    suggestedMaxWeight: 0.12,
    price: 412.5,
    priceChange24h: -0.5,
    priceChange7d: 2.1,
    priceChange30d: 15.3
  },
  {
    id: 'BABA',
    name: 'Alibaba',
    ticker: '9988.HK',
    assetType: 'hk_equity',
    currency: 'HKD',
    benchmarkId: 'HSTECH',
    baseMaxWeight: 0.15,
    currentWeight: 0.05,
    suggestedMaxWeight: 0.10,
    price: 82.4,
    priceChange24h: 1.2,
    priceChange7d: -1.5,
    priceChange30d: 5.2
  },
  {
    id: 'TENCENT',
    name: 'Tencent',
    ticker: '0700.HK',
    assetType: 'hk_equity',
    currency: 'HKD',
    benchmarkId: 'HSTECH',
    baseMaxWeight: 0.15,
    currentWeight: 0.06,
    suggestedMaxWeight: 0.12,
    price: 385.2,
    priceChange24h: 0.8,
    priceChange7d: 2.3,
    priceChange30d: 7.1
  },
  {
    id: 'XAU',
    name: 'Gold',
    ticker: 'XAUUSD',
    assetType: 'metal',
    currency: 'USD',
    baseMaxWeight: 0.20,
    currentWeight: 0.10,
    suggestedMaxWeight: 0.15,
    price: 2785.5,
    priceChange24h: 0.3,
    priceChange7d: 1.2,
    priceChange30d: 3.5
  },
  {
    id: 'XAG',
    name: 'Silver',
    ticker: 'XAGUSD',
    assetType: 'metal',
    currency: 'USD',
    baseMaxWeight: 0.08,
    currentWeight: 0.03,
    suggestedMaxWeight: 0.06,
    price: 31.25,
    priceChange24h: 0.5,
    priceChange7d: 2.1,
    priceChange30d: 4.8
  },
  {
    id: 'HG',
    name: 'Copper',
    ticker: 'HG=F',
    assetType: 'future',
    currency: 'USD',
    baseMaxWeight: 0.15,
    currentWeight: 0.07,
    suggestedMaxWeight: 0.12,
    price: 4.32,
    priceChange24h: -0.2,
    priceChange7d: 1.5,
    priceChange30d: 6.2
  }
];

export const macroSwitches: MacroSwitch[] = [
  {
    id: 'HY_SPREAD',
    name: '信用开关 (HY利差)',
    currentValue: 3.85,
    change7d: -0.15,
    change1m: -0.42,
    percentile: 35,
    light: 'green',
    freshness: 1,
    frequency: 'D'
  },
  {
    id: 'REAL10Y',
    name: '流动性开关 (10Y实际利率)',
    currentValue: 1.92,
    change7d: -0.08,
    change1m: -0.25,
    percentile: 45,
    light: 'green',
    freshness: 1,
    frequency: 'D'
  },
  {
    id: 'DXY',
    name: '美元强度 (DXY)',
    currentValue: 103.25,
    change7d: -0.45,
    change1m: -1.2,
    percentile: 40,
    light: 'green',
    freshness: 1,
    frequency: 'D'
  },
  {
    id: 'PMI',
    name: '增长开关 (PMI)',
    currentValue: 51.2,
    change7d: 0.3,
    change1m: 0.8,
    percentile: 55,
    light: 'yellow',
    freshness: 5,
    frequency: 'M'
  },
  {
    id: 'CORE_INFL',
    name: '通胀开关 (核心通胀)',
    currentValue: 2.8,
    change7d: 0.0,
    change1m: -0.1,
    percentile: 48,
    light: 'yellow',
    freshness: 12,
    frequency: 'M'
  }
];

export const todaySignal: DailySignal = {
  date: '2026-01-30',
  regime: 'B',
  riskScore: 76,
  drivers: [
    '利差回落 (HY Spread ↓)',
    '实际利率下行 (Real10Y ↓)',
    'PMI企稳回升 (PMI ↑)'
  ],
  portfolioAction: 'ADD',
  riskMode: '进攻型',
  aiDiffusionIndex: 72,
  constraintIndex: 58,
  commentSummary: '象限B，RiskScore 76：利差回落、实际利率下行、PMI企稳；总指令加风险。BTC与AI趋势绿且催化绿→允许加；黄金催化转黄→维持；铜趋势黄→观望。',
  dataAsOf: '2026-01-30 16:00 EST'
};

export const assetSignals: AssetSignal[] = [
  {
    assetId: 'BTC',
    date: '2026-01-30',
    trendLight: 'green',
    riskLight: 'yellow',
    catalystLight: 'green',
    suggestedMaxWeight: 0.18,
    action: 'ADD',
    reasonCodes: ['MA200_BREAK', 'REALY_DOWN', 'DXY_DOWN'],
    notes: '突破200日均线，流动性改善'
  },
  {
    assetId: 'AI_BASKET',
    date: '2026-01-30',
    trendLight: 'green',
    riskLight: 'green',
    catalystLight: 'green',
    suggestedMaxWeight: 0.28,
    action: 'ADD',
    reasonCodes: ['ADI_STRONG', 'SMH_SPY_UP'],
    notes: 'AI扩散指数强劲'
  },
  {
    assetId: 'TSLA',
    date: '2026-01-30',
    trendLight: 'yellow',
    riskLight: 'yellow',
    catalystLight: 'green',
    suggestedMaxWeight: 0.12,
    action: 'HOLD',
    reasonCodes: ['EARNINGS_NEAR', 'VOL_PCTILE_MED'],
    notes: '财报周临近，波动中等'
  },
  {
    assetId: 'BABA',
    date: '2026-01-30',
    trendLight: 'yellow',
    riskLight: 'green',
    catalystLight: 'yellow',
    suggestedMaxWeight: 0.10,
    action: 'ADD',
    reasonCodes: ['HK_RISK_ON', 'POLICY_SUPPORT'],
    notes: '港股风险偏好改善'
  },
  {
    assetId: 'TENCENT',
    date: '2026-01-30',
    trendLight: 'green',
    riskLight: 'green',
    catalystLight: 'yellow',
    suggestedMaxWeight: 0.12,
    action: 'ADD',
    reasonCodes: ['GAME_LICENSE', 'BUYBACK'],
    notes: '版号发放，回购支持'
  },
  {
    assetId: 'XAU',
    date: '2026-01-30',
    trendLight: 'green',
    riskLight: 'green',
    catalystLight: 'yellow',
    suggestedMaxWeight: 0.15,
    action: 'HOLD',
    reasonCodes: ['HEDGE_DEMAND', 'REALY_DOWN'],
    notes: '对冲需求存在，实际利率下行'
  },
  {
    assetId: 'XAG',
    date: '2026-01-30',
    trendLight: 'yellow',
    riskLight: 'yellow',
    catalystLight: 'yellow',
    suggestedMaxWeight: 0.06,
    action: 'HOLD',
    reasonCodes: ['VOL_PCTILE_MED'],
    notes: '波动分位中等'
  },
  {
    assetId: 'HG',
    date: '2026-01-30',
    trendLight: 'yellow',
    riskLight: 'green',
    catalystLight: 'yellow',
    suggestedMaxWeight: 0.12,
    action: 'HOLD',
    reasonCodes: ['PMI_STABLE', 'ELECTRIFICATION'],
    notes: 'PMI企稳，电气化需求'
  }
];

export const technicalData: Record<string, AssetTechnicalData> = {
  BTC: {
    assetId: 'BTC',
    ma20: 96500,
    ma60: 94200,
    ma200: 91800,
    mom12w: 0.125,
    rsToBenchmark: 1.08,
    vol20Ann: 0.45,
    mdd60: -0.08,
    mdd120: -0.15,
    volPercentile1y: 55,
    ddPercentile1y: 40,
    correlationDXY: -0.65,
    correlationRealRate: -0.72,
    correlationSPX: 0.58
  },
  AI_BASKET: {
    assetId: 'AI_BASKET',
    ma20: 142.5,
    ma60: 138.2,
    ma200: 132.8,
    mom12w: 0.087,
    rsToBenchmark: 1.12,
    vol20Ann: 0.28,
    mdd60: -0.05,
    mdd120: -0.08,
    volPercentile1y: 45,
    ddPercentile1y: 35,
    correlationDXY: -0.35,
    correlationRealRate: -0.42,
    correlationSPX: 0.85
  },
  TSLA: {
    assetId: 'TSLA',
    ma20: 408.5,
    ma60: 395.2,
    ma200: 385.0,
    mom12w: 0.153,
    rsToBenchmark: 1.25,
    vol20Ann: 0.52,
    mdd60: -0.12,
    mdd120: -0.18,
    volPercentile1y: 65,
    ddPercentile1y: 55,
    correlationDXY: -0.25,
    correlationRealRate: -0.32,
    correlationSPX: 0.72
  },
  BABA: {
    assetId: 'BABA',
    ma20: 80.5,
    ma60: 78.2,
    ma200: 75.8,
    mom12w: 0.052,
    rsToBenchmark: 0.95,
    vol20Ann: 0.32,
    mdd60: -0.08,
    mdd120: -0.12,
    volPercentile1y: 48,
    ddPercentile1y: 42,
    correlationDXY: -0.15,
    correlationRealRate: -0.22,
    correlationSPX: 0.45
  },
  TENCENT: {
    assetId: 'TENCENT',
    ma20: 382.5,
    ma60: 375.2,
    ma200: 368.0,
    mom12w: 0.071,
    rsToBenchmark: 1.05,
    vol20Ann: 0.25,
    mdd60: -0.05,
    mdd120: -0.08,
    volPercentile1y: 42,
    ddPercentile1y: 38,
    correlationDXY: -0.12,
    correlationRealRate: -0.18,
    correlationSPX: 0.48
  },
  XAU: {
    assetId: 'XAU',
    ma20: 2765.0,
    ma60: 2742.5,
    ma200: 2718.0,
    mom12w: 0.035,
    rsToBenchmark: 0.88,
    vol20Ann: 0.15,
    mdd60: -0.03,
    mdd120: -0.05,
    volPercentile1y: 35,
    ddPercentile1y: 30,
    correlationDXY: -0.75,
    correlationRealRate: -0.82,
    correlationSPX: 0.15
  },
  XAG: {
    assetId: 'XAG',
    ma20: 30.85,
    ma60: 30.42,
    ma200: 29.95,
    mom12w: 0.048,
    rsToBenchmark: 0.92,
    vol20Ann: 0.22,
    mdd60: -0.05,
    mdd120: -0.08,
    volPercentile1y: 52,
    ddPercentile1y: 45,
    correlationDXY: -0.65,
    correlationRealRate: -0.72,
    correlationSPX: 0.35
  },
  HG: {
    assetId: 'HG',
    ma20: 4.28,
    ma60: 4.22,
    ma200: 4.15,
    mom12w: 0.062,
    rsToBenchmark: 1.02,
    vol20Ann: 0.18,
    mdd60: -0.04,
    mdd120: -0.06,
    volPercentile1y: 40,
    ddPercentile1y: 35,
    correlationDXY: -0.45,
    correlationRealRate: -0.52,
    correlationSPX: 0.55
  }
};

export const weeklyKondratieff: WeeklyKondratieff = {
  date: '2026-01-30',
  aiDiffusionIndex: 72,
  constraintIndex: 58,
  phase: 'spring',
  strategy: '偏AI卖铲子 + 适度资源',
  components: {
    soxRatio: 1.15,
    nvdaRatio: 1.28,
    utilityRatio: 0.95,
    copperMomentum: 0.062,
    energyPrice: 72.5
  }
};

export function generatePriceHistory(assetId: string, days: number = 252): PriceData[] {
  const data: PriceData[] = [];
  const asset = assets.find(a => a.id === assetId);
  if (!asset) return data;
  
  let price = asset.price * 0.85;
  const volatility = 0.02;
  
  for (let i = days; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    
    const change = (Math.random() - 0.48) * volatility;
    price = price * (1 + change);
    
    const dailyVol = price * volatility * 0.5;
    
    data.push({
      date: date.toISOString().split('T')[0],
      open: price - dailyVol * 0.2,
      high: price + dailyVol,
      low: price - dailyVol,
      close: price,
      volume: Math.floor(Math.random() * 1000000) + 500000
    });
  }
  
  return data;
}

export function getPortfolioPositions(): PortfolioPosition[] {
  return assets.map(asset => {
    const signal = assetSignals.find(s => s.assetId === asset.id);
    const targetWeight = signal?.suggestedMaxWeight || asset.baseMaxWeight;
    const allowedAddSpace = Math.max(0, targetWeight - asset.currentWeight);
    const needReduce = Math.max(0, asset.currentWeight - targetWeight);
    
    return {
      assetId: asset.id,
      currentWeight: asset.currentWeight,
      targetWeight,
      allowedAddSpace,
      needReduce
    };
  });
}
