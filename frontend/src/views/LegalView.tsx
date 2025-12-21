
import { useGameStore } from '../store/gameStore';
import { ShieldCheck, AlertTriangle, FileText } from 'lucide-react';
import { GameService } from '../services/gameService';

// ! Fix: Added selectedAgent prop to avoid hardcoded agent ID
interface LegalViewProps {
    selectedAgent: string;
}

export const LegalView = ({ selectedAgent }: LegalViewProps) => {
    const game = useGameStore();

    // Check for active scandals in state
    const activeScandals = game.active_scandals || [];
    const hasScandal = activeScandals.length > 0;

    return (
        <div className="h-full p-6 overflow-y-auto grid grid-cols-12 gap-6">

            {/* SCANDAL TRACKER */}
            <div className="col-span-12 md:col-span-6 glass-card bg-black/40 p-6 relative overflow-hidden">
                {hasScandal && (
                    <div className="absolute inset-0 bg-red-500/5 animate-pulse pointer-events-none" />
                )}
                <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
                    <AlertTriangle className={hasScandal ? "text-red-500" : "text-slate-500"} />
                    Public Relations Status
                </h2>

                {hasScandal ? (
                    <div className="space-y-4">
                        {activeScandals.map((scandal: any, idx: number) => (
                            <div key={idx} className="p-4 bg-red-500/10 border border-red-500/30 rounded">
                                <div className="text-red-400 font-bold mb-1 uppercase tracking-wider">Active Scandal</div>
                                <div className="text-white text-lg mb-2">{scandal.description || "Unknown Incident"}</div>
                                <div className="flex justify-between items-center text-xs font-mono text-red-300">
                                    <span>SEVERITY: {(scandal.severity * 100).toFixed(0)}%</span>
                                    <span>ETA: {scandal.duration_weeks} WEEKS</span>
                                </div>
                                <div className="mt-4 flex gap-2">
                                    <button
                                        onClick={() => GameService.submitCommand(selectedAgent, "RESOLVE_SCANDAL", { scandal_id: scandal.event_id })}
                                        className="px-4 py-2 bg-red-500/20 text-red-400 font-bold text-xs rounded border border-red-500/40 hover:bg-red-500/30 transition-colors"
                                        aria-label="Mitigate scandal with PR campaign"
                                    >
                                        MITIGATE (PR CAMPAIGN)
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-40 text-slate-500">
                        <ShieldCheck size={48} className="mb-2 text-neon-green/50" />
                        <div className="text-neon-green/80 font-mono text-sm">STATUS NORMAL</div>
                        <div className="text-xs">No active investigations.</div>
                    </div>
                )}
            </div>

            {/* COMPLIANCE INBOX */}
            <div className="col-span-12 md:col-span-6 glass-card bg-black/40 p-6">
                <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
                    <FileText className="text-neon-cyan" /> Compliance Inbox
                </h2>
                <div className="text-center py-10 text-slate-500 text-sm font-mono border border-dashed border-white/10 rounded">
                    NO PENDING FILINGS
                </div>
            </div>

        </div>
    );
};
