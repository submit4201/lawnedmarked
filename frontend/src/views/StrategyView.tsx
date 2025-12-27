
import { useState } from 'react';
import { Briefcase, Handshake, ShieldAlert, MessageSquare, Send } from 'lucide-react';
import { useGameStore } from '../store/gameStore';
import { GameService } from '../services/gameService';
import { motion } from 'framer-motion';

interface StrategyViewProps {
    selectedAgent: string;
}

export const StrategyView = ({ selectedAgent }: StrategyViewProps) => {
    const game = useGameStore();
    const [messageText, setMessageText] = useState('');
    const [selectedTarget, setSelectedTarget] = useState('GM');

    // Vendor actions
    const handleNegotiate = async (vendorId: string, locationId: string) => {
        await GameService.submitCommand(selectedAgent, 'NEGOTIATE_VENDOR_DEAL', {
            location_id: locationId,
            vendor_id: vendorId,
            target_supply_type: 'DETERGENT',
            requested_discount: 0.05,
            proposal_text: 'Looking for better bulk pricing on consistent orders'
        });
        GameService.fetchState(selectedAgent);
    };

    const handleExclusive = async (vendorId: string, locationId: string) => {
        await GameService.submitCommand(selectedAgent, 'SIGN_EXCLUSIVE_CONTRACT', {
            location_id: locationId,
            vendor_id: vendorId,
            duration_weeks: 12
        });
        GameService.fetchState(selectedAgent);
    };

    const handleCancelContract = async (vendorId: string, locationId: string) => {
        await GameService.submitCommand(selectedAgent, 'CANCEL_VENDOR_CONTRACT', {
            location_id: locationId,
            vendor_id: vendorId
        });
        GameService.fetchState(selectedAgent);
    };

    // Competition actions
    const handleAlliance = async (targetAgentId: string) => {
        await GameService.submitCommand(selectedAgent, 'ENTER_ALLIANCE', {
            partner_agent_id: targetAgentId,
            alliance_type: 'INFORMAL'
        });
        GameService.fetchState(selectedAgent);
    };

    const handleBuyout = async (targetAgentId: string) => {
        await GameService.submitCommand(selectedAgent, 'PROPOSE_BUYOUT', {
            target_agent_id: targetAgentId,
            offer_amount: 50000,
            is_hostile_attempt: false
        });
        GameService.fetchState(selectedAgent);
    };

    // Messaging
    const handleSendMessage = async () => {
        if (!messageText.trim()) return;
        await GameService.submitCommand(selectedAgent, 'COMMUNICATE_TO_AGENT', {
            recipient_agent_id: selectedTarget,
            channel: 'PROPOSAL',
            message_content: messageText
        });
        setMessageText('');
        GameService.fetchState(selectedAgent);
    };

    // Mock competitors (replace with actual data when available)
    const competitors = ['AI_PLAYER_001', 'AI_PLAYER_002'];

    return (
        <div className="h-full p-6 overflow-y-auto grid grid-cols-12 gap-6">

            {/* VENDORS */}
            <div className="col-span-12 md:col-span-4 glass-card bg-black/40 p-6">
                <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
                    <Handshake className="text-neon-cyan" /> Vendor Relations
                </h2>
                <div className="space-y-4">
                    {Object.entries(game.locations).flatMap(([locId, loc]) =>
                        Object.values(loc.vendor_relationships || {}).map(vendor => ({ ...vendor, locationId: locId }))
                    ).map((vendor, idx) => (
                        <div key={`${vendor.vendor_id}-${idx}`} className="p-4 bg-white/5 rounded border border-white/10 hover:bg-white/10 transition-colors">
                            <div className="flex justify-between items-start mb-2">
                                <div className="font-bold text-white uppercase">{vendor.vendor_id}</div>
                                <div className="text-[10px] bg-neon-cyan/20 text-neon-cyan px-2 py-0.5 rounded font-mono">TIER {vendor.tier}</div>
                            </div>
                            <div className="text-xs text-slate-400 mb-3">Unit Price: ${vendor.current_price_per_unit.toFixed(2)}</div>
                            <div className="flex flex-wrap gap-2">
                                <button
                                    onClick={() => handleNegotiate(vendor.vendor_id, vendor.locationId)}
                                    className="px-3 py-1 bg-neon-cyan/10 border border-neon-cyan/30 text-neon-cyan text-xs rounded hover:bg-neon-cyan/20 transition-colors"
                                >
                                    Negotiate
                                </button>
                                {!vendor.is_exclusive_contract ? (
                                    <button
                                        onClick={() => handleExclusive(vendor.vendor_id, vendor.locationId)}
                                        className="px-3 py-1 bg-neon-purple/10 border border-neon-purple/30 text-neon-purple text-xs rounded hover:bg-neon-purple/20 transition-colors"
                                    >
                                        Go Exclusive
                                    </button>
                                ) : (
                                    <button
                                        onClick={() => handleCancelContract(vendor.vendor_id, vendor.locationId)}
                                        className="px-3 py-1 bg-red-500/10 border border-red-500/30 text-red-400 text-xs rounded hover:bg-red-500/20 transition-colors"
                                    >
                                        Cancel
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                    {Object.values(game.locations).every(l => !l.vendor_relationships || Object.keys(l.vendor_relationships).length === 0) && (
                        <div className="text-slate-500 text-sm italic p-4 text-center">No active vendor contracts.</div>
                    )}
                </div>
            </div>

            {/* COMPETITORS */}
            <div className="col-span-12 md:col-span-4 glass-card bg-black/40 p-6">
                <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
                    <Briefcase className="text-neon-purple" /> Competition
                </h2>
                <div className="space-y-4">
                    {competitors.map((agentId) => (
                        <div key={agentId} className="p-4 bg-white/5 rounded border border-white/10">
                            <div className="flex justify-between items-start mb-3">
                                <div className="font-bold text-white">{agentId}</div>
                                <ShieldAlert size={16} className="text-orange-400" />
                            </div>
                            <div className="flex flex-wrap gap-2">
                                <motion.button
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => handleAlliance(agentId)}
                                    className="px-3 py-1.5 bg-neon-green/10 border border-neon-green/30 text-neon-green text-xs rounded hover:bg-neon-green/20"
                                >
                                    🤝 Propose Alliance
                                </motion.button>
                                <motion.button
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => handleBuyout(agentId)}
                                    className="px-3 py-1.5 bg-neon-pink/10 border border-neon-pink/30 text-neon-pink text-xs rounded hover:bg-neon-pink/20"
                                >
                                    💰 Buyout Offer
                                </motion.button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* MESSAGING SYSTEM */}
            <div className="col-span-12 md:col-span-4 glass-card bg-black/40 p-6">
                <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
                    <MessageSquare className="text-neon-orange" /> Comms Channel
                </h2>
                <div className="space-y-4">
                    <div>
                        <label className="text-xs text-slate-500 font-mono mb-2 block">RECIPIENT</label>
                        <select
                            value={selectedTarget}
                            onChange={(e) => setSelectedTarget(e.target.value)}
                            className="w-full px-3 py-2 bg-black/50 border border-white/20 rounded text-white text-sm focus:border-neon-cyan outline-none"
                        >
                            <option value="GM">Game Master</option>
                            {competitors.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="text-xs text-slate-500 font-mono mb-2 block">MESSAGE</label>
                        <textarea
                            value={messageText}
                            onChange={(e) => setMessageText(e.target.value)}
                            placeholder="Type your message or proposal..."
                            className="w-full h-24 px-3 py-2 bg-black/50 border border-white/20 rounded text-white text-sm focus:border-neon-cyan outline-none resize-none"
                        />
                    </div>
                    <motion.button
                        whileTap={{ scale: 0.98 }}
                        onClick={handleSendMessage}
                        disabled={!messageText.trim()}
                        className="w-full py-2 bg-neon-orange/20 border border-neon-orange/50 text-neon-orange font-bold rounded flex items-center justify-center gap-2 hover:bg-neon-orange/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Send size={16} /> TRANSMIT
                    </motion.button>
                </div>
            </div>

        </div>
    );
};
