

import { Briefcase, Handshake, ShieldAlert } from 'lucide-react';
import { useGameStore } from '../store/gameStore';

export const StrategyView = () => {
    const game = useGameStore();


    // Mock vendors if not fully implemented in state
    // In a real implementation this would map over game.locations -> vendor_relationships
    // But for now we might mock it or just check if the field exists.

    return (
        <div className="h-full p-6 overflow-y-auto grid grid-cols-12 gap-6">

            {/* VENDORS */}
            <div className="col-span-12 md:col-span-4 glass-card bg-black/40 p-6">
                <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
                    <Handshake className="text-neon-cyan" /> Vendor Relations
                </h2>
                <div className="space-y-4">
                    {Object.values(game.locations).flatMap(loc =>
                        Object.values(loc.vendor_relationships || {})
                    ).map((vendor, idx) => (
                        <div key={`${vendor.vendor_id}-${idx}`} className="p-4 bg-white/5 rounded border border-white/10 hover:bg-white/10 transition-colors cursor-pointer group">
                            <div className="flex justify-between items-start mb-2">
                                <div className="font-bold text-white uppercase">{vendor.vendor_id}</div>
                                <div className="text-[10px] bg-neon-cyan/20 text-neon-cyan px-2 py-0.5 rounded font-mono">TIER {vendor.tier}</div>
                            </div>
                            <div className="text-xs text-slate-400 mb-3">Unit Price: ${vendor.current_price_per_unit.toFixed(2)}</div>
                            <div className="flex gap-2">
                                <button className="px-3 py-1 bg-neon-cyan/10 border border-neon-cyan/30 text-neon-cyan text-xs rounded hover:bg-neon-cyan/20">
                                    Negotiate
                                </button>
                                {vendor.is_exclusive_contract && (
                                    <span className="text-[10px] text-neon-purple border border-neon-purple/50 px-2 flex items-center rounded">EXCLUSIVE</span>
                                )}
                            </div>
                        </div>
                    ))}
                    {Object.values(game.locations).every(l => !l.vendor_relationships || Object.keys(l.vendor_relationships).length === 0) && (
                        <div className="text-slate-500 text-sm italic p-4 text-center">No active vendor contracts found.</div>
                    )}
                </div>
            </div>

            {/* COMPETITORS */}
            <div className="col-span-12 md:col-span-8 glass-card bg-black/40 p-6">
                <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
                    <Briefcase className="text-neon-purple" /> Competitor Dossiers
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Mock Competitor */}
                    <div className="p-4 bg-white/5 rounded border border-white/10 opacity-70">
                        <div className="flex justify-between items-start mb-2">
                            <div className="font-bold text-red-400">CleanWash Corp</div>
                            <ShieldAlert size={16} className="text-red-500" />
                        </div>
                        <div className="text-sm text-slate-300 mb-2">Social Score: <span className="text-red-400 font-mono">35/100</span></div>
                        <div className="text-xs text-slate-500 font-mono">
                            KNOWN MARKETS: ZONE A, ZONE B
                        </div>
                    </div>
                </div>
            </div>

        </div>
    );
};
