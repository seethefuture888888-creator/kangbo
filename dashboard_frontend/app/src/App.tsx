import { useDashboard } from '@/hooks/useDashboard';
import { Navigation, Header } from '@/components/Navigation';
import { DailyOverview } from '@/sections/DailyOverview';
import { AssetDetail } from '@/sections/AssetDetail';
import { WeeklyKondratieffView } from '@/sections/WeeklyKondratieff';
import './App.css';

function App() {
  const {
    state,
    setSelectedAsset,
    setView,
    refresh,
    assets,
    dailySignal,
    assetSignals,
    macroSwitches,
    weeklyKondratieff,
    dataStatus,
    selectedAsset,
    selectedAssetSignal,
    selectedAssetPriceHistory,
    selectedAssetTechnicalData,
    portfolioSummary
  } = useDashboard();

  const renderContent = () => {
    switch (state.currentView) {
      case 'daily':
        return (
          <DailyOverview
            dailySignal={dailySignal}
            macroSwitches={macroSwitches}
            assets={assets}
            assetSignals={assetSignals}
            portfolioSummary={portfolioSummary}
            onAssetClick={setSelectedAsset}
          />
        );
      
      case 'asset':
        if (selectedAsset && selectedAssetSignal) {
          return (
            <AssetDetail
              asset={selectedAsset}
              signal={selectedAssetSignal}
              priceHistory={selectedAssetPriceHistory}
              technicalData={selectedAssetTechnicalData!}
              onBack={() => setView('daily')}
            />
          );
        }
        return null;
      
      case 'weekly':
        return (
          <WeeklyKondratieffView data={weeklyKondratieff!} />
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Background gradient */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl" />
      </div>

      {/* Main content */}
      <div className="relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Header 
            date={dailySignal.date}
            dataAsOf={dailySignal.dataAsOf}
            onRefresh={refresh}
            lastUpdatedAt={dataStatus.lastUpdatedAt}
            loading={dataStatus.loading}
          />
          
          <Navigation 
            currentView={state.currentView}
            onViewChange={setView}
            className="mb-6"
          />

          <main className="pb-12">
            {renderContent()}
          </main>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950/50 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-slate-500">
              Investment Decision Dashboard · 基于康波周期框架
            </p>
            <div className="flex items-center gap-4 text-xs text-slate-600">
              <span>Regime: {dailySignal.regime}</span>
              <span>RiskScore: {dailySignal.riskScore}</span>
              <span>ADI: {dailySignal.aiDiffusionIndex}</span>
              <span>CI: {dailySignal.constraintIndex}</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
