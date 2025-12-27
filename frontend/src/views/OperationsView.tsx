import { useState } from 'react';

import { useGameStore } from '../store/gameStore';
import { EquipmentCard } from '../components/EquipmentCard';
import { LayoutGrid, Plus, Package } from 'lucide-react';
import { GameService } from '../services/gameService';
import { motion } from 'framer-motion';

export const OperationsView = ({ selectedAgent }: { selectedAgent: string }) => {
    const game = useGameStore();

    const handleMaintain = async (machineId: string) => {
        const loc = Object.values(game.locations).find(l => l.equipment[machineId]);
        if (loc) {
            await GameService.maintainMachine(selectedAgent, loc.location_id, machineId);
            GameService.fetchState(selectedAgent);
        }
    };

    const handleFix = async (machineId: string) => {
        const loc = Object.values(game.locations).find(l => l.equipment[machineId]);
        if (loc) {
            await GameService.submitCommand(selectedAgent, 'FIX_MACHINE', {
                location_id: loc.location_id,
                machine_id: machineId
            });
            GameService.fetchState(selectedAgent);
        }
    };

    const handleSell = async (machineId: string) => {
        const loc = Object.values(game.locations).find(l => l.equipment[machineId]);
        if (loc) {
            await GameService.submitCommand(selectedAgent, 'SELL_EQUIPMENT', {
                location_id: loc.location_id,
                machine_id: machineId
            });
            GameService.fetchState(selectedAgent);
        }
    };

    const handleBuy = async (locationId: string, equipmentType: string) => {
        await GameService.submitCommand(selectedAgent, 'BUY_EQUIPMENT', {
            location_id: locationId,
            equipment_type: equipmentType,
            vendor_id: 'COMMERCIAL_SUPPLIER'
        });
        GameService.fetchState(selectedAgent);
    };

    return (
        <div className="h-full p-6 overflow-y-auto">
            {/* INVENTORY SILOS */}
            <div className="mb-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                {Object.values(game.locations).map(loc => (
                    <div key={loc.location_id} className="glass-card bg-black/40 p-6 relative overflow-hidden">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-display text-white flex items-center gap-2">
                                <span className="w-2 h-8 bg-neon-cyan rounded-full" />
                                {loc.zone} Inventory
                            </h2>
                            <div className="text-xs font-mono text-slate-400">LOC: {loc.location_id}</div>
                        </div>

                        <div className="grid grid-cols-2 gap-6">
                            <InventorySilo
                                type="Detergent"
                                level={loc.inventory_detergent}
                                locationId={loc.location_id}
                                vendors={loc.vendor_relationships}
                                selectedAgent={selectedAgent}
                            />
                            <InventorySilo
                                type="Softener"
                                level={loc.inventory_softener}
                                locationId={loc.location_id}
                                vendors={loc.vendor_relationships}
                                selectedAgent={selectedAgent}
                            />
                        </div>
                    </div>
                ))}
            </div>

            <h3 className="text-lg font-display text-white mb-4 pl-1 border-l-4 border-neon-purple">Machine Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-4">
                {Object.values(game.locations).length > 0 ? (
                    Object.values(game.locations).flatMap(loc =>
                        Object.values(loc.equipment).map(machine => (
                            <EquipmentCard
                                key={machine.machine_id}
                                machine={machine}
                                onMaintain={handleMaintain}
                                onFix={handleFix}
                                onSell={handleSell}
                            />
                        ))
                    )
                ) : (
                    <div className="col-span-full py-20 text-center text-slate-400 flex flex-col items-center gap-4">
                        <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center">
                            <LayoutGrid size={40} className="text-slate-600" />
                        </div>
                        <p className="text-2xl font-display">No units deployed.</p>
                        <p className="text-base text-slate-500">Open a location to see your machines.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

const InventorySilo = ({ type, level, locationId, vendors, selectedAgent }: {
    type: string,
    level: number,
    locationId: string,
    vendors: Record<string, any>,
    selectedAgent: string
}) => {
    const [buying, setBuying] = useState(false);

    // Helper to find best vendor or fallback
    const getVendorId = () => {
        const v = Object.values(vendors || {});
        return v.length > 0 ? v[0].vendor_id : "SPOT_MARKET";
    };

    const handleBuy = async (amount: number) => {
        setBuying(true);
        await GameService.submitCommand(selectedAgent, 'BUY_SUPPLIES', {
            location_id: locationId,
            supply_type: type.toUpperCase(), // "DETERGENT" or "SOFTENER"
            vendor_id: getVendorId(),
            quantity_loads: amount
        });
        setBuying(false);
    };

    const maxLevel = 2000; // Visual max
    const percentage = Math.min((level / maxLevel) * 100, 100);
    const isLow = percentage < 25;

    return (
        <div className="bg-white/5 rounded border border-white/10 p-4">
            <div className="flex justify-between items-end mb-2">
                <div className="text-sm text-slate-400 font-mono uppercase">{type}</div>
                <div className={`text-xl font-bold font-mono ${isLow ? 'text-red-400 animate-pulse' : 'text-white'}`}>
                    {level} <span className="text-xs font-normal text-slate-500">LDS</span>
                </div>
            </div>

            {/* Visual Bar */}
            <div className="h-32 bg-black/50 rounded-lg relative overflow-hidden border border-white/5 mb-3 group">
                {/* Fluid Level */}
                <div
                    className={`absolute bottom-0 left-0 right-0 transition-all duration-1000 ease-in-out ${type === 'Detergent' ? 'bg-neon-cyan/60' : 'bg-neon-purple/60'
                        }`}
                    style={{ height: `${percentage}%` }}
                >
                    {/* Liquid Top highlight */}
                    <div className="absolute top-0 left-0 right-0 h-1 bg-white/50" />
                </div>

                {/* Grid overlay */}
                <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20 mix-blend-overlay" />

                {/* Hover overlay for restock */}
                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2 backdrop-blur-sm">
                    <button
                        onClick={() => handleBuy(100)}
                        disabled={buying}
                        className="px-3 py-1 bg-white/10 hover:bg-white/20 border border-white/30 rounded text-xs font-mono text-white"
                    >
                        +100
                    </button>
                    <button
                        onClick={() => handleBuy(500)}
                        disabled={buying}
                        className={`px-3 py-1 rounded text-xs font-mono text-white border transition-colors ${type === 'Detergent'
                            ? 'bg-neon-cyan/20 border-neon-cyan text-neon-cyan hover:bg-neon-cyan/30'
                            : 'bg-neon-purple/20 border-neon-purple text-neon-purple hover:bg-neon-purple/30'
                            }`}
                    >
                        +500
                    </button>
                </div>
            </div>

            <div className="flex justify-between text-[10px] font-mono text-slate-500">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
            </div>
        </div>
    );
};
