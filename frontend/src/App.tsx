import { useState, useEffect, useCallback, useMemo } from 'react';

import { GameService } from './services/gameService.ts';
import { usePolling } from './hooks/usePolling.ts';
import { GlobalHUD } from './components/GlobalHUD.tsx';
import { ToastContainer } from './components/ui/toast.tsx';
import { useGameStore } from './store/gameStore.ts';

// Views
import { NeuralFeed } from './components/NeuralFeed.tsx';
import { MarketShareSpider } from './components/MarketShareSpider.tsx';
import { SocialFeed } from './components/SocialFeed.tsx';
import { TacticalMap } from './components/TacticalMap.tsx';
import { CinematicModal } from './components/CinematicModal.tsx';
import { OperationsView } from './views/OperationsView.tsx';
import { FinanceView } from './views/FinanceView.tsx';
import { StrategyView } from './views/StrategyView.tsx';
import { LegalView } from './views/LegalView.tsx';
import { HRView } from './views/HRView.tsx';
import { TrendingUp, LayoutGrid, Radio, Users } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Placeholder views for empty states
const PlaceholderView = ({ title, icon: Icon }: any) => (
  <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-4">
    <div className="w-24 h-24 rounded-full bg-white/5 flex items-center justify-center">
      {Icon && <Icon size={48} />}
    </div>
    <h2 className="text-2xl font-display text-slate-400">{title}</h2>
    <p className="font-mono text-sm border px-3 py-1 rounded border-white/10">SYSTEM OFFLINE // UNDER CONSTRUCTION</p>
  </div>
);

function App() {
  const [selectedAgent, setSelectedAgent] = useState('PLAYER_001');
  const [currentView, setCurrentView] = useState('DASHBOARD');
  const [activeDilemma, setActiveDilemma] = useState<any>(null);



  usePolling(selectedAgent);

  // Keyboard shortcut lookup table
  const KEYBOARD_NAV: Record<string, string> = {
    'd': 'DASHBOARD',
    'o': 'OPERATIONS',
    'f': 'FINANCE',
    's': 'STRATEGY',
    'l': 'LEGAL',
    'h': 'HR',
  };

  // ! Keyboard shortcuts for power users
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Ignore if typing in an input
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

    const key = e.key.toLowerCase();

    // Handle navigation keys
    if (key in KEYBOARD_NAV) {
      setCurrentView(KEYBOARD_NAV[key]);
      return;
    }

    // Handle spacebar for end turn
    if (key === ' ') {
      e.preventDefault();
      handleEndTurn();
    }
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const handleEndTurn = async () => {
    // Optimistic UI update or loading state could be added here
    await GameService.advanceTurn([selectedAgent]);
  };

  const handleRunTurn = async () => {
    await GameService.runTurn(selectedAgent);
  };



  // --- View Renders ---

  // Derive performance metrics from real game state
  const game = useGameStore();
  const performanceData = useMemo(() => {
    const locations = Object.values(game.locations || {});
    const totalMachines = locations.reduce((acc, loc) => acc + Object.keys(loc.equipment || {}).length, 0);
    const avgCondition = locations.length > 0
      ? locations.reduce((acc, loc) => {
        const machines = Object.values(loc.equipment || {});
        return acc + machines.reduce((m, machine) => m + (machine.condition || 0), 0) / Math.max(machines.length, 1);
      }, 0) / locations.length
      : 50;

    return [
      { axis: 'FINANCE', value: Math.min(100, Math.floor((game.cash_balance || 0) / 500)) },
      { axis: 'OPS', value: Math.min(100, Math.floor(avgCondition)) },
      { axis: 'SOCIAL', value: Math.min(100, Math.floor(game.social_score || 50)) },
      { axis: 'CREDIT', value: Math.min(100, Math.floor((game.credit_rating || 700) / 10)) },
      { axis: 'ASSETS', value: Math.min(100, totalMachines * 10 + locations.length * 20) },
    ];
  }, [game.locations, game.cash_balance, game.social_score, game.credit_rating]);

  const renderDashboard = () => (
    <div className="grid grid-cols-12 gap-6 h-full p-6 overflow-hidden">
      {/* LEFT COLUMN: Intel */}
      <section className="col-span-3 flex flex-col gap-6 overflow-hidden h-full">
        <NeuralFeed />
        <div className="glass-card flex-1 bg-black/20 min-h-0 flex flex-col">
          <div className="section-header mb-4 shrink-0">
            <div className="section-header-icon">
              <TrendingUp size={18} className="text-neon-cyan" />
            </div>
            <h3 className="section-title text-sm text-white">Performance Matrix</h3>
          </div>
          <div className="flex-1 min-h-0">
            <MarketShareSpider
              data={performanceData}
              label=""
            />
          </div>
        </div>
      </section>

      {/* CENTER COLUMN: Map */}
      <section className="col-span-6 flex flex-col gap-6 h-full overflow-hidden">
        <div className="glass-card flex-1 p-0 overflow-hidden relative border-white/10 bg-black/40">
          <TacticalMap />
        </div>
      </section>

      {/* RIGHT COLUMN: Social & News */}
      <section className="col-span-3 flex flex-col gap-4 h-full overflow-hidden">
        <div className="glass-card overflow-hidden shrink-0">
          <div className="section-header">
            <div className="section-header-icon bg-neon-pink/10 border-neon-pink/30">
              <Radio size={16} className="text-neon-pink" />
            </div>
            <h3 className="section-title">The Pulse</h3>
          </div>
          <div className="bg-black/30 p-2 mb-2 rounded border border-white/5 overflow-hidden whitespace-nowrap">
            <motion.div
              animate={{ x: ["100%", "-100%"] }}
              transition={{ repeat: Infinity, duration: 20, ease: "linear" }}
              className="inline-block text-[10px] font-mono text-neon-green"
            >
              BREAKING: COMPETITOR "CLEANWASH" ANNOUNCES 20% PRICE CUT •• REGULATORY AUDIT SCHEDULED FOR ZONE B •• NEW SOAP SUPPLIER CONTRACTS AVAILABLE ••
            </motion.div>
          </div>
        </div>
        <div className="flex-1 overflow-hidden min-h-0">
          <SocialFeed />
        </div>
      </section>
    </div>
  );

  // Render functions


  return (
    <>
      <div className="h-screen bg-void text-slate-200 overflow-hidden flex flex-col font-sans selection:bg-neon-cyan/30">

        <CinematicModal
          event={activeDilemma}
          onClose={() => setActiveDilemma(null)}
          onResolve={(_decision) => setActiveDilemma(null)}
        />

        {/* GLOBAL HUD */}
        <GlobalHUD
          currentView={currentView}
          onNavigate={setCurrentView}
          onAdvanceTurn={handleEndTurn}
          onRunTurn={handleRunTurn}
          selectedAgent={selectedAgent}
          onAgentChange={setSelectedAgent}
        />

        {/* MAIN CONTENT AREA */}
        <main className="flex-1 overflow-hidden bg-gradient-to-b from-void to-abyss">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentView}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.25 }}
              className="h-full"
            >
              {currentView === 'DASHBOARD' && renderDashboard()}
              {currentView === 'OPERATIONS' && <OperationsView selectedAgent={selectedAgent} />}
              {currentView === 'FINANCE' && <FinanceView selectedAgent={selectedAgent} />}
              {currentView === 'STRATEGY' && <StrategyView selectedAgent={selectedAgent} />}
              {currentView === 'LEGAL' && <LegalView selectedAgent={selectedAgent} />}
              {currentView === 'HR' && <HRView selectedAgent={selectedAgent} />}
              {currentView === 'OBSERVER' && <PlaceholderView title="Observer Console" icon={LayoutGrid} />}
            </motion.div>
          </AnimatePresence>
        </main>

      </div>

      {/* Toast notifications */}
      <ToastContainer />
    </>
  );
}

export default App;
