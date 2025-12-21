import React, { useEffect, useState } from 'react';
import {
    Wifi, Cpu, Clock, Users, DollarSign, Bell,
    LayoutGrid, Map, TrendingUp, ShieldCheck, Briefcase, Eye
} from 'lucide-react';
import { useGameStore } from '../store/gameStore';
import { motion } from 'framer-motion';

// --- Sub-components for HUD ---

export const AnimatedNumber = ({ value, prefix = '' }: { value: number; prefix?: string }) => {
    const [displayValue, setDisplayValue] = useState(0);

    useEffect(() => {
        // Quick animation for numbers
        const duration = 800;
        const start = displayValue;
        const end = value;
        if (start === end) return;

        const startTime = performance.now();

        const animate = (currentTime: number) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out quart
            const ease = 1 - Math.pow(1 - progress, 4);

            const current = start + (end - start) * ease;

            setDisplayValue(current);

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }, [value]);

    return <>{prefix}{Math.floor(displayValue).toLocaleString()}</>;
};

// MetricCard component removed as it was unused

// --- Main HUD Component ---

interface GlobalHUDProps {
    onNavigate: (view: string) => void;
    currentView: string;
    onAdvanceTurn: () => void;
    onRunTurn: () => void;
    selectedAgent: string;
    onAgentChange: (id: string) => void;
}

export const GlobalHUD: React.FC<GlobalHUDProps> = ({
    onNavigate,
    currentView,
    onAdvanceTurn,
    onRunTurn,
    selectedAgent,
    onAgentChange
}) => {
    const game = useGameStore();
    const [currentTime, setCurrentTime] = useState(new Date());

    // Update real-world clock
    useEffect(() => {
        const timer = setInterval(() => setCurrentTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    const menuItems = [
        { id: 'DASHBOARD', label: 'Command', icon: LayoutGrid },
        { id: 'OPERATIONS', label: 'Ops', icon: Map },
        { id: 'FINANCE', label: 'Finance', icon: TrendingUp },
        { id: 'STRATEGY', label: 'Strat', icon: Briefcase },
        { id: 'LEGAL', label: 'Legal', icon: ShieldCheck },
        { id: 'OBSERVER', label: 'Watch', icon: Eye },
    ];

    return (
        <div className="flex flex-col w-full z-50 relative shrink-0">

            {/* 1. TOP SYSTEM BAR */}
            <div className="h-8 bg-abyss border-b border-white/10 flex items-center justify-between px-4 text-[10px] font-mono tracking-widest text-slate-400">
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                        <Wifi size={12} className="text-neon-green animate-pulse" />
                        <span className="text-neon-green/80">SUNNYSIDE NET :: SECURE</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Cpu size={12} className="text-neon-cyan" />
                        <span>CORE v0.9.1</span>
                    </div>
                </div>
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                        <Clock size={12} />
                        <span>{currentTime.toLocaleTimeString('en-US', { hour12: false })}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Users size={12} />
                        <span>AGENTS: {Object.keys(game.agents || {}).length}</span>
                    </div>
                </div>
            </div>

            {/* 2. MAIN HUD HEADER */}
            <header className="px-6 py-4 bg-void/95 backdrop-blur-md border-b border-white/5">
                <div className="flex justify-between items-center">

                    {/* LEFT: Branding & Agent Select */}
                    <div className="flex items-center gap-6">
                        <div className="w-12 h-12 rounded bg-gradient-to-br from-neon-cyan/20 to-blue-600/20 border border-neon-cyan/50 flex items-center justify-center shadow-[0_0_15px_rgba(0,245,255,0.2)]">
                            <span className="font-display font-bold text-neon-cyan text-xl">L</span>
                        </div>
                        <div>
                            <h1 className="font-display text-2xl tracking-widest text-white leading-none">
                                TYCOON<span className="text-neon-cyan">OS</span>
                            </h1>
                            <div className="flex items-center gap-2 mt-1">
                                <span className="text-[10px] uppercase text-slate-500 font-mono">Operator</span>
                                <select
                                    value={selectedAgent}
                                    onChange={(e) => onAgentChange(e.target.value)}
                                    className="bg-transparent border-none text-neon-cyan font-mono text-xs focus:ring-0 cursor-pointer p-0"
                                >
                                    <option value="PLAYER_001">PLAYER_001</option>
                                    <option value="PLAYER_HUMAN">HUMAN_OP</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* CENTER: Navigation Tabs */}
                    <div className="flex bg-black/40 p-1 rounded-lg border border-white/10">
                        {menuItems.map((item) => {
                            const isActive = currentView === item.id;
                            const Icon = item.icon;
                            return (
                                <button
                                    key={item.id}
                                    onClick={() => onNavigate(item.id)}
                                    className={`
                    relative px-4 py-2 rounded-md flex items-center gap-2 text-sm font-bold transition-all
                    ${isActive
                                            ? 'text-black bg-neon-cyan shadow-[0_0_15px_rgba(0,245,255,0.4)]'
                                            : 'text-slate-400 hover:text-white hover:bg-white/5'
                                        }
                  `}
                                >
                                    <Icon size={14} />
                                    {item.label}
                                    {isActive && (
                                        <motion.div
                                            layoutId="activeTab"
                                            className="absolute inset-0 bg-white/20 rounded-md"
                                            initial={false}
                                        />
                                    )}
                                </button>
                            );
                        })}
                    </div>

                    {/* RIGHT: Major Metrics & Actions */}
                    <div className="flex items-center gap-6">

                        {/* Cash Ticker */}
                        <div className="text-right">
                            <div className="flex items-center justify-end gap-1">
                                <DollarSign size={20} className="text-neon-green" />
                                <span className="text-3xl font-display font-bold text-neon-green text-glow-green">
                                    <AnimatedNumber value={game.cash_balance || 0} />
                                </span>
                            </div>
                            <div className="text-[10px] text-neon-green/60 font-mono tracking-wider uppercase">
                                Liquid Assets
                            </div>
                        </div>

                        {/* Time Control */}
                        <div className="border-l border-white/10 pl-6 text-right">
                            <div className="flex items-center justify-end gap-2">
                                <span className="text-xl font-display text-white">WK {game.current_week || 1}</span>
                                <span className="text-sm font-mono text-slate-400">Thinking...</span>
                            </div>
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={onAdvanceTurn}
                                className="mt-1 px-4 py-1 bg-neon-purple/20 border border-neon-purple/50 rounded text-neon-purple text-xs font-bold tracking-widest hover:bg-neon-purple/30 transition-colors uppercase"
                            >
                                Next Week
                            </motion.button>
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={onRunTurn}
                                className="mt-1 ml-2 px-4 py-1 bg-neon-cyan/20 border border-neon-cyan/50 rounded text-neon-cyan text-xs font-bold tracking-widest hover:bg-neon-cyan/30 transition-colors uppercase"
                            >
                                Run Turn
                            </motion.button>
                        </div>

                        {/* Alerts */}
                        <div className="border-l border-white/10 pl-6">
                            <button className="relative w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center border border-white/10 transition-colors">
                                <Bell size={18} className="text-slate-300" />
                                {/* Badge */}
                                <span className="absolute top-0 right-0 w-3 h-3 bg-red-500 rounded-full border border-black transform translate-x-1 -translate-y-1" />
                            </button>
                        </div>

                    </div>
                </div>
            </header>
        </div>
    );
};
