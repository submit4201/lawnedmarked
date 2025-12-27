import { useState } from 'react';
import { useGameStore } from '../store/gameStore';
import { DollarSign, TrendingUp, CreditCard } from 'lucide-react';
import { GameService } from '../services/gameService';
import { motion } from 'framer-motion';

export const FinanceView = ({ selectedAgent }: { selectedAgent: string }) => {
    const game = useGameStore();
    const [repayAmount, setRepayAmount] = useState(1000);

    const handleRepay = async () => {
        // ! Fix: Using correct command name MAKE_DEBT_PAYMENT instead of REPAY_LOAN
        await GameService.submitCommand(selectedAgent, 'MAKE_DEBT_PAYMENT', {
            debt_id: 'primary_loc',  // Default LOC debt ID
            amount: repayAmount
        });
        GameService.fetchState(selectedAgent);
    };

    // Calculate totals for MVP
    const totalWeeklyRevenue = Object.values(game.locations).reduce((acc, loc) => acc + (loc.accumulated_revenue_week || 0), 0);
    // Mock COGS as 40% of revenue for now if not tracked
    const totalWeeklyCosts = totalWeeklyRevenue * 0.4;
    const netProfit = totalWeeklyRevenue - totalWeeklyCosts;

    return (
        <div className="h-full p-6 overflow-y-auto grid grid-cols-12 gap-6">

            {/* P&L CARD */}
            <div className="col-span-12 md:col-span-8 glass-card bg-black/40 p-6">
                <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
                    <TrendingUp className="text-neon-green" /> Profit & Loss (Weekly)
                </h2>
                <div className="space-y-4">
                    <div className="flex justify-between items-center p-3 bg-white/5 rounded">
                        <span className="text-slate-400 font-mono">REVENUE</span>
                        <span className="text-neon-green font-bold font-mono text-xl">
                            +${totalWeeklyRevenue.toFixed(2)}
                        </span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-white/5 rounded">
                        <span className="text-slate-400 font-mono">EXPENSES (COGS + Opex)</span>
                        <span className="text-red-400 font-bold font-mono text-xl">
                            -${totalWeeklyCosts.toFixed(2)}
                        </span>
                    </div>
                    <div className="h-px bg-white/10 my-2" />
                    <div className="flex justify-between items-center p-4 bg-neon-green/10 border border-neon-green/30 rounded">
                        <span className="text-white font-display tracking-widest">NET PROFIT</span>
                        <span className={`font-bold font-display text-2xl ${netProfit >= 0 ? 'text-neon-green' : 'text-red-500'}`}>
                            ${netProfit.toFixed(2)}
                        </span>
                    </div>
                </div>
            </div>

            {/* DEBT MANAGER */}
            <div className="col-span-12 md:col-span-4 glass-card bg-black/40 p-6 flex flex-col">
                <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
                    <CreditCard className="text-neon-purple" /> Debt Facility
                </h2>

                <div className="flex-1 flex flex-col gap-6">
                    <div>
                        <div className="text-xs uppercase text-slate-500 font-mono mb-1">Total Outstanding</div>
                        <div className="text-3xl font-display text-white">
                            ${(game.cash_balance < 0 ? Math.abs(game.cash_balance) : 0).toFixed(2)}
                            {/* NOTE: Using cash_balance < 0 as proxy for debt for now if no dedicated field */}
                        </div>
                    </div>

                    <div className="bg-white/5 p-4 rounded border border-white/10">
                        <div className="text-sm text-slate-300 mb-2">Quick Repay</div>
                        <div className="flex gap-2 mb-2">
                            {[100, 1000, 5000].map(amt => (
                                <button
                                    key={amt}
                                    onClick={() => setRepayAmount(amt)}
                                    className={`px-3 py-1 text-xs font-mono border rounded transition-colors
                                        ${repayAmount === amt
                                            ? 'bg-neon-purple text-white border-neon-purple'
                                            : 'border-white/20 text-slate-400 hover:border-white/40'}
                                    `}
                                >
                                    ${amt}
                                </button>
                            ))}
                        </div>
                        <motion.button
                            whileTap={{ scale: 0.98 }}
                            onClick={handleRepay}
                            className="w-full py-2 bg-neon-purple/20 border border-neon-purple/50 text-neon-purple font-bold tracking-widest hover:bg-neon-purple/30 transition-colors uppercase text-sm rounded"
                        >
                            Authorize Payment
                        </motion.button>
                    </div>
                </div>
            </div>

            {/* PRICING CONSOLE */}
            <div className="col-span-12 glass-card bg-black/40 p-6">
                <h2 className="text-xl font-display text-white mb-4 flex items-center gap-2">
                    <DollarSign className="text-neon-cyan" /> Pricing Strategy
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {['wash', 'dry', 'detergent', 'softener'].map(serviceType => (
                        <PricingSlider
                            key={serviceType}
                            serviceType={serviceType}
                            selectedAgent={selectedAgent}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
};

const PricingSlider = ({ serviceType, selectedAgent }: { serviceType: string, selectedAgent: string }) => {
    const [price, setPrice] = useState(2.50);
    const [loading, setLoading] = useState(false);

    const handleUpdate = async () => {
        setLoading(true);
        await GameService.submitCommand(selectedAgent, 'SET_PRICE', {
            service_type: serviceType.toUpperCase(),
            price: price
        });
        setLoading(false);
    };

    return (
        <div className="p-4 bg-white/5 rounded border border-white/10">
            <div className="flex justify-between items-center mb-2">
                <div className="text-xs text-slate-400 font-mono mb-2 uppercase">{serviceType}</div>
                <div className="text-xl text-white font-bold">${price.toFixed(2)}</div>
            </div>
            <input
                type="range"
                min="0.50"
                max="10.00"
                step="0.25"
                value={price}
                onChange={(e) => setPrice(parseFloat(e.target.value))}
                className="w-full accent-neon-cyan h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer mb-3"
            />
            <button
                onClick={handleUpdate}
                disabled={loading}
                className="w-full py-1.5 bg-neon-cyan/10 border border-neon-cyan/20 text-neon-cyan text-xs font-mono rounded hover:bg-neon-cyan/20 disabled:opacity-50"
            >
                {loading ? 'UPDATING...' : 'UPDATE PRICE'}
            </button>
        </div>
    );
};

// Loan Request Panel
const LoanPanel = ({ selectedAgent }: { selectedAgent: string }) => {
    const [loanType, setLoanType] = useState<'LOC' | 'EQUIPMENT' | 'EXPANSION' | 'EMERGENCY'>('LOC');
    const [amount, setAmount] = useState(5000);
    const [loading, setLoading] = useState(false);

    const loanInfo = {
        LOC: { rate: '8%', term: 'Revolving', desc: 'Line of Credit' },
        EQUIPMENT: { rate: '6%', term: '24 weeks', desc: 'Equipment Financing' },
        EXPANSION: { rate: '7%', term: '52 weeks', desc: 'Business Expansion' },
        EMERGENCY: { rate: '12%', term: '8 weeks', desc: 'Emergency Capital' },
    };

    const handleTakeLoan = async () => {
        setLoading(true);
        await GameService.submitCommand(selectedAgent, 'TAKE_LOAN', {
            loan_type: loanType,
            amount: amount
        });
        setLoading(false);
    };

    return (
        <div className="bg-white/5 p-4 rounded border border-white/10">
            <div className="text-sm text-slate-300 mb-3 font-mono uppercase">Request Capital</div>
            <div className="grid grid-cols-2 gap-2 mb-4">
                {(Object.keys(loanInfo) as Array<keyof typeof loanInfo>).map(type => (
                    <button
                        key={type}
                        onClick={() => setLoanType(type)}
                        className={`p-2 text-xs rounded border transition-colors ${loanType === type
                                ? 'bg-neon-green/20 border-neon-green text-neon-green'
                                : 'border-white/20 text-slate-400 hover:border-white/40'
                            }`}
                    >
                        <div className="font-bold">{loanInfo[type].desc}</div>
                        <div className="text-[10px] opacity-70">{loanInfo[type].rate} / {loanInfo[type].term}</div>
                    </button>
                ))}
            </div>
            <div className="mb-3">
                <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-500">Amount</span>
                    <span className="text-white font-bold">${amount.toLocaleString()}</span>
                </div>
                <input
                    type="range"
                    min="1000"
                    max="50000"
                    step="1000"
                    value={amount}
                    onChange={(e) => setAmount(parseInt(e.target.value))}
                    className="w-full accent-neon-green h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
                />
            </div>
            <motion.button
                whileTap={{ scale: 0.98 }}
                onClick={handleTakeLoan}
                disabled={loading}
                className="w-full py-2 bg-neon-green/20 border border-neon-green/50 text-neon-green font-bold tracking-widest hover:bg-neon-green/30 transition-colors uppercase text-sm rounded disabled:opacity-50"
            >
                {loading ? 'PROCESSING...' : 'REQUEST FUNDS'}
            </motion.button>
        </div>
    );
};

// Marketing Campaign Cards
const MarketingPanel = ({ selectedAgent }: { selectedAgent: string }) => {
    const campaigns = [
        { type: 'FLYERS', name: 'Local Flyers', cost: 100, reach: '500 homes', icon: '📄' },
        { type: 'SOCIAL_MEDIA', name: 'Social Media', cost: 250, reach: '2K impressions', icon: '📱' },
        { type: 'NEWSPAPER_AD', name: 'Newspaper Ad', cost: 500, reach: '5K readers', icon: '📰' },
        { type: 'SPONSORSHIP', name: 'Event Sponsor', cost: 1000, reach: 'Community event', icon: '🏆' },
    ];

    const handleInvest = async (campaignType: string, cost: number) => {
        await GameService.submitCommand(selectedAgent, 'INVEST_IN_MARKETING', {
            location_id: 'LOC_001',  // Default location
            campaign_type: campaignType,
            cost: cost
        });
    };

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {campaigns.map(c => (
                <motion.button
                    key={c.type}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleInvest(c.type, c.cost)}
                    className="p-4 bg-white/5 rounded border border-white/10 hover:border-neon-pink/50 hover:bg-neon-pink/5 transition-all text-left group"
                >
                    <div className="text-2xl mb-2">{c.icon}</div>
                    <div className="text-sm text-white font-bold mb-1">{c.name}</div>
                    <div className="text-[10px] text-slate-500 mb-2">{c.reach}</div>
                    <div className="text-xs text-neon-pink font-mono group-hover:font-bold transition-all">
                        ${c.cost}
                    </div>
                </motion.button>
            ))}
        </div>
    );
};
