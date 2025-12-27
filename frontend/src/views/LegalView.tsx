
import { useState } from 'react';
import { useGameStore } from '../store/gameStore';
import { ShieldCheck, AlertTriangle, FileText, Heart, Gavel } from 'lucide-react';
import { GameService } from '../services/gameService';
import { motion } from 'framer-motion';

interface LegalViewProps {
    selectedAgent: string;
}

// Sub-components
const ScandalTracker = ({ scandals, onResolve }: { scandals: any[]; onResolve: (id: string) => void }) => {
    const hasScandal = scandals.length > 0;

    return (
        <div className="col-span-12 md:col-span-6 glass-card bg-black/40 p-6 relative overflow-hidden">
            {hasScandal && (
                <div className="absolute inset-0 bg-red-500/5 animate-pulse pointer-events-none" />
            )}
            <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
                <AlertTriangle className={hasScandal ? "text-red-500" : "text-slate-500"} />
                Public Relations
            </h2>

            {hasScandal ? (
                <div className="space-y-4">
                    {scandals.map((scandal: any, idx: number) => (
                        <div key={idx} className="p-4 bg-red-500/10 border border-red-500/30 rounded">
                            <div className="text-red-400 font-bold mb-1 uppercase tracking-wider">Active Scandal</div>
                            <div className="text-white text-lg mb-2">{scandal.description || "Unknown Incident"}</div>
                            <div className="flex justify-between items-center text-xs font-mono text-red-300 mb-4">
                                <span>SEVERITY: {(scandal.severity * 100).toFixed(0)}%</span>
                                <span>ETA: {scandal.duration_weeks} WEEKS</span>
                            </div>
                            <motion.button
                                whileTap={{ scale: 0.95 }}
                                onClick={() => onResolve(scandal.event_id)}
                                className="px-4 py-2 bg-red-500/20 text-red-400 font-bold text-xs rounded border border-red-500/40 hover:bg-red-500/30"
                            >
                                🎙️ PR CAMPAIGN
                            </motion.button>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="flex flex-col items-center justify-center h-32 text-slate-500">
                    <ShieldCheck size={48} className="mb-2 text-neon-green/50" />
                    <div className="text-neon-green/80 font-mono text-sm">STATUS NORMAL</div>
                </div>
            )}
        </div>
    );
};

const CharityPanel = ({ amount, setAmount, onDonate }: { amount: number; setAmount: (n: number) => void; onDonate: (type: string) => void }) => {
    const charities = [
        { type: 'FOOD_BANK', name: 'Local Food Bank', icon: '🍞' },
        { type: 'SHELTER', name: 'Homeless Shelter', icon: '🏠' },
        { type: 'YOUTH', name: 'Youth Programs', icon: '👧' },
        { type: 'ENVIRONMENT', name: 'Green Initiative', icon: '🌱' },
    ];

    return (
        <div className="col-span-12 md:col-span-6 glass-card bg-black/40 p-6">
            <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
                <Heart className="text-neon-pink" /> Community Outreach
            </h2>
            <div className="mb-4">
                <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-500">Donation</span>
                    <span className="text-white font-bold">${amount.toLocaleString()}</span>
                </div>
                <input
                    type="range" min="100" max="5000" step="100"
                    value={amount}
                    onChange={(e) => setAmount(parseInt(e.target.value))}
                    className="w-full accent-neon-pink h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
                />
            </div>
            <div className="grid grid-cols-2 gap-3">
                {charities.map(c => (
                    <motion.button
                        key={c.type}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => onDonate(c.type)}
                        className="p-3 bg-white/5 rounded border border-white/10 hover:border-neon-pink/50 hover:bg-neon-pink/5 transition-all text-left"
                    >
                        <div className="text-xl mb-1">{c.icon}</div>
                        <div className="text-xs text-white font-bold">{c.name}</div>
                    </motion.button>
                ))}
            </div>
        </div>
    );
};

const CompliancePanel = ({ onFileReport }: { onFileReport: () => void }) => (
    <div className="col-span-12 md:col-span-6 glass-card bg-black/40 p-6">
        <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
            <FileText className="text-neon-cyan" /> Compliance
        </h2>
        <div className="space-y-4">
            <motion.button
                whileTap={{ scale: 0.98 }}
                onClick={onFileReport}
                className="w-full p-4 bg-neon-cyan/10 border border-neon-cyan/30 rounded text-left hover:bg-neon-cyan/20 transition-colors group"
            >
                <div className="flex justify-between items-center">
                    <div>
                        <div className="text-neon-cyan font-bold text-sm">Quarterly Report</div>
                        <div className="text-xs text-slate-400">File standard regulatory disclosure</div>
                    </div>
                    <div className="text-neon-cyan opacity-50 group-hover:opacity-100">📋</div>
                </div>
            </motion.button>
            <div className="text-xs text-slate-500 text-center">
                Filing proactively improves regulatory standing
            </div>
        </div>
    </div>
);

const FinesPanel = ({ onAppeal }: { onAppeal: (id: string) => void }) => (
    <div className="col-span-12 md:col-span-6 glass-card bg-black/40 p-6">
        <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
            <Gavel className="text-neon-orange" /> Fines & Appeals
        </h2>
        <div className="p-4 bg-orange-500/10 border border-orange-500/30 rounded">
            <div className="flex justify-between items-start mb-2">
                <div className="text-orange-400 font-bold text-sm">SAFETY VIOLATION</div>
                <div className="text-orange-300 font-mono text-xs">$2,500</div>
            </div>
            <div className="text-xs text-slate-400 mb-3">Inadequate ventilation in Zone A facility</div>
            <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={() => onAppeal('fine_001')}
                className="px-4 py-2 bg-orange-500/20 text-orange-400 font-bold text-xs rounded border border-orange-500/40 hover:bg-orange-500/30"
            >
                ⚖️ CONTEST FINDING
            </motion.button>
        </div>
    </div>
);

export const LegalView = ({ selectedAgent }: LegalViewProps) => {
    const game = useGameStore();
    const [charityAmount, setCharityAmount] = useState(500);
    const activeScandals = game.active_scandals || [];

    // Handlers
    const handleResolveScandal = async (scandalId: string) => {
        await GameService.submitCommand(selectedAgent, 'RESOLVE_SCANDAL', {
            scandal_id: scandalId, resolution_strategy: 'PR_FIRM_ENGAGEMENT', cost: 1000
        });
        GameService.fetchState(selectedAgent);
    };

    const handleCharity = async (charityType: string) => {
        await GameService.submitCommand(selectedAgent, 'INITIATE_CHARITY', {
            charity_name: charityType, donation_amount: charityAmount
        });
        GameService.fetchState(selectedAgent);
    };

    const handleFileReport = async () => {
        await GameService.submitCommand(selectedAgent, 'FILE_REGULATORY_REPORT', {
            report_type: 'TAX_QUARTERLY', filing_cost: 50
        });
        GameService.fetchState(selectedAgent);
    };

    const handleAppeal = async (fineId: string) => {
        await GameService.submitCommand(selectedAgent, 'FILE_APPEAL', {
            fine_id: fineId, appeal_cost: 500, appeal_argument: 'Procedural error in assessment'
        });
        GameService.fetchState(selectedAgent);
    };

    return (
        <div className="h-full p-6 overflow-y-auto grid grid-cols-12 gap-6">
            <ScandalTracker scandals={activeScandals} onResolve={handleResolveScandal} />
            <CharityPanel amount={charityAmount} setAmount={setCharityAmount} onDonate={handleCharity} />
            <CompliancePanel onFileReport={handleFileReport} />
            <FinesPanel onAppeal={handleAppeal} />
        </div>
    );
};
