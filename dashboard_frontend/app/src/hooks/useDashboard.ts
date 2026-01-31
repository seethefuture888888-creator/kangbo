import { useState, useCallback, useMemo, useEffect } from 'react';
import type { DashboardState, DashboardPayload, AssetTechnicalData } from '@/types';
import {
  assets as mockAssets,
  todaySignal as mockTodaySignal,
  assetSignals as mockAssetSignals,
  macroSwitches as mockMacroSwitches,
  weeklyKondratieff as mockWeeklyKondratieff,
  technicalData as mockTechnicalData,
  generatePriceHistory,
} from '@/data/mockData';

export function useDashboard() {
  const defaultTech = (assetId: string): AssetTechnicalData => ({
    assetId,
    ma20: 0,
    ma60: 0,
    ma200: 0,
    mom12w: 0,
    rsToBenchmark: 1,
    vol20Ann: 0,
    mdd60: 0,
    mdd120: 0,
    volPercentile1y: 50,
    ddPercentile1y: 50,
    correlationDXY: 0,
    correlationRealRate: 0,
    correlationSPX: 0,
  });
  const [data, setData] = useState<DashboardPayload>({
    dailySignal: mockTodaySignal,
    macroSwitches: mockMacroSwitches,
    assets: mockAssets,
    assetSignals: mockAssetSignals,
    weeklyKondratieff: mockWeeklyKondratieff,
    technicalData: mockTechnicalData,
    priceHistory: {},
  });

  const [dataStatus, setDataStatus] = useState<{ loading: boolean; source: 'live' | 'mock'; error?: string; lastUpdatedAt?: string }>(
    { loading: true, source: 'mock' }
  );

  const [state, setState] = useState<DashboardState>({
    selectedDate: mockTodaySignal.date,
    selectedAssetId: null,
    currentView: 'daily'
  });

  // 打开/刷新时拉取数据。若开启「打开时立即更新」则请求后端 /api/dashboard/live 先重新生成再返回
  const loadData = useCallback(async () => {
    const env = (import.meta as any)?.env ?? {};
    const baseUrl = env.VITE_DASHBOARD_URL || '/data/dashboard.json';
    const useLiveRefresh = env.VITE_USE_LIVE_REFRESH === 'true' || env.VITE_USE_LIVE_REFRESH === '1';
    const url = useLiveRefresh
      ? (baseUrl.startsWith('http') ? new URL(baseUrl).origin : (typeof window !== 'undefined' ? window.location.origin : '')) + '/api/dashboard/live'
      : `${baseUrl}${baseUrl.includes('?') ? '&' : '?'}t=${Date.now()}`;
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const payload = (await res.json()) as DashboardPayload;
    if (!payload?.dailySignal || !payload?.assets || !payload?.assetSignals || !payload?.macroSwitches) {
      throw new Error('Invalid dashboard.json schema');
    }
    return payload;
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      try {
        const payload = await loadData();
        if (cancelled) return;
        setData({
          ...payload,
          weeklyKondratieff: payload.weeklyKondratieff ?? mockWeeklyKondratieff,
          technicalData: payload.technicalData ?? mockTechnicalData,
          priceHistory: payload.priceHistory ?? {},
        });
        setState(prev => ({ ...prev, selectedDate: payload.dailySignal.date }));
        setDataStatus({ loading: false, source: 'live', lastUpdatedAt: new Date().toLocaleString('zh-CN') });
      } catch (e: any) {
        if (cancelled) return;
        setDataStatus({ loading: false, source: 'mock', error: e?.message || String(e) });
      }
    }
    run();
    return () => {
      cancelled = true;
    };
  }, [loadData]);

  const refresh = useCallback(async () => {
    setDataStatus(prev => ({ ...prev, loading: true }));
    try {
      const payload = await loadData();
      setData({
        ...payload,
        weeklyKondratieff: payload.weeklyKondratieff ?? mockWeeklyKondratieff,
        technicalData: payload.technicalData ?? mockTechnicalData,
        priceHistory: payload.priceHistory ?? {},
      });
      setState(prev => ({ ...prev, selectedDate: payload.dailySignal.date }));
      setDataStatus({ loading: false, source: 'live', lastUpdatedAt: new Date().toLocaleString('zh-CN') });
    } catch (e: any) {
      setDataStatus(prev => ({ ...prev, loading: false, error: e?.message || String(e) }));
    }
  }, [loadData]);

  const setSelectedAsset = useCallback((assetId: string | null) => {
    setState(prev => ({
      ...prev,
      selectedAssetId: assetId,
      currentView: assetId ? 'asset' : 'daily'
    }));
  }, []);

  const setView = useCallback((view: DashboardState['currentView']) => {
    setState(prev => ({
      ...prev,
      currentView: view,
      selectedAssetId: view === 'daily' ? null : prev.selectedAssetId
    }));
  }, []);

  const selectedAsset = useMemo(() => {
    return data.assets.find(a => a.id === state.selectedAssetId) || null;
  }, [state.selectedAssetId, data.assets]);

  const selectedAssetSignal = useMemo(() => {
    return data.assetSignals.find(s => s.assetId === state.selectedAssetId) || null;
  }, [state.selectedAssetId, data.assetSignals]);

  const selectedAssetPriceHistory = useMemo(() => {
    if (!state.selectedAssetId) return [];
    const fromAgent = data.priceHistory?.[state.selectedAssetId];
    if (fromAgent && fromAgent.length > 0) return fromAgent;
    return generatePriceHistory(state.selectedAssetId, 180);
  }, [state.selectedAssetId, data.priceHistory]);

  const selectedAssetTechnicalData = useMemo(() => {
    if (!state.selectedAssetId) return null;
    return (
      data.technicalData?.[state.selectedAssetId] ||
      mockTechnicalData[state.selectedAssetId] ||
      defaultTech(state.selectedAssetId)
    );
  }, [state.selectedAssetId, data.technicalData]);

  const totalCurrentWeight = useMemo(() => {
    return data.assets.reduce((sum, a) => sum + a.currentWeight, 0);
  }, [data.assets]);

  const totalSuggestedWeight = useMemo(() => {
    return data.assetSignals.reduce((sum, s) => sum + s.suggestedMaxWeight, 0);
  }, [data.assetSignals]);

  const availableAddSpace = useMemo(() => {
    return totalSuggestedWeight - totalCurrentWeight;
  }, [totalSuggestedWeight, totalCurrentWeight]);

  return {
    state,
    setSelectedAsset,
    setView,
    refresh,
    assets: data.assets,
    dailySignal: data.dailySignal,
    assetSignals: data.assetSignals,
    macroSwitches: data.macroSwitches,
    weeklyKondratieff: data.weeklyKondratieff,
    dataStatus,
    selectedAsset,
    selectedAssetSignal,
    selectedAssetPriceHistory,
    selectedAssetTechnicalData,
    portfolioSummary: {
      totalCurrentWeight,
      totalSuggestedWeight,
      availableAddSpace
    }
  };
}
