import { useState } from 'react';
import { Users, UserPlus, Briefcase, DollarSign, Heart } from 'lucide-react';
import { useGameStore } from '../store/gameStore';
import { GameService } from '../services/gameService';
import { motion } from 'framer-motion';

interface HRViewProps {
    selectedAgent: string;
}

export const HRView = ({ selectedAgent }: HRViewProps) => {
    const game = useGameStore();
    const [hireRole, setHireRole] = useState<'ATTENDANT' | 'TECHNICIAN' | 'MANAGER'>('ATTENDANT');
    const [wageAdjust, setWageAdjust] = useState<Record<string, number>>({});

    // Get staff from all locations
    const allStaff = Object.values(game.locations).flatMap(loc =>
        Object.values(loc.staff || {}).map(s => ({ ...s, locationId: loc.location_id }))
    );

    // Handlers
    const handleHire = async () => {
        const locationId = Object.keys(game.locations)[0] || 'LOC_001';
        const wage = hireRole === 'MANAGER' ? 25 : hireRole === 'TECHNICIAN' ? 20 : 15;
        await GameService.submitCommand(selectedAgent, 'HIRE_STAFF', {
            location_id: locationId,
            role: hireRole,
            name: `New ${hireRole}`,
            salary_per_hour: wage
        });
        GameService.fetchState(selectedAgent);
    };

    const handleFire = async (staffId: string, locationId: string) => {
        if (!confirm('Are you sure you want to terminate this employee?')) return;
        await GameService.submitCommand(selectedAgent, 'FIRE_STAFF', {
            location_id: locationId,
            staff_id: staffId,
            severance_pay: 0
        });
        GameService.fetchState(selectedAgent);
    };

    const handleWageChange = async (staffId: string, locationId: string, newWage: number) => {
        await GameService.submitCommand(selectedAgent, 'ADJUST_STAFF_WAGE', {
            location_id: locationId,
            staff_id: staffId,
            new_hourly_rate: newWage
        });
        GameService.fetchState(selectedAgent);
    };

    const handleBenefits = async (benefitType: string) => {
        // Get first staff member and location for this demo
        const firstLoc = Object.keys(game.locations)[0] || 'LOC_001';
        const firstStaff = allStaff[0]?.staff_id || 'STAFF_001';
        const benefitMap: Record<string, string> = {
            'HEALTH': 'HEALTH_PLAN',
            'DENTAL': 'HEALTH_PLAN',
            'RETIREMENT': 'PROFIT_SHARING',
            'PTO': 'FLEXIBLE_SCHEDULE'
        };
        await GameService.submitCommand(selectedAgent, 'PROVIDE_BENEFITS', {
            location_id: firstLoc,
            staff_id: firstStaff,
            benefit_type: benefitMap[benefitType] || 'HEALTH_PLAN',
            monthly_cost: 500
        });
        GameService.fetchState(selectedAgent);
    };

    const roles = [
        { type: 'ATTENDANT', name: 'Attendant', wage: '$15/hr', desc: 'Customer service' },
        { type: 'TECHNICIAN', name: 'Technician', wage: '$20/hr', desc: 'Machine maintenance' },
        { type: 'MANAGER', name: 'Manager', wage: '$25/hr', desc: 'Operations oversight' },
    ];

    const benefits = [
        { type: 'HEALTH', name: 'Health Insurance', cost: '$500/mo', icon: '🏥' },
        { type: 'DENTAL', name: 'Dental Plan', cost: '$100/mo', icon: '🦷' },
        { type: 'RETIREMENT', name: '401k Match', cost: '3% match', icon: '📈' },
        { type: 'PTO', name: 'Extra PTO', cost: '5 days', icon: '🏖️' },
    ];

    return (
        <div className="h-full p-6 overflow-y-auto grid grid-cols-12 gap-6">

            {/* HIRE STAFF */}
            <div className="col-span-12 md:col-span-4 glass-card bg-black/40 p-6">
                <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
                    <UserPlus className="text-neon-green" /> Hire Staff
                </h2>
                <div className="space-y-3 mb-4">
                    {roles.map(r => (
                        <button
                            key={r.type}
                            onClick={() => setHireRole(r.type as any)}
                            className={`w-full p-3 rounded border text-left transition-colors ${hireRole === r.type
                                ? 'bg-neon-green/20 border-neon-green text-neon-green'
                                : 'bg-white/5 border-white/10 text-slate-300 hover:border-white/20'
                                }`}
                        >
                            <div className="flex justify-between items-center">
                                <div className="font-bold text-sm">{r.name}</div>
                                <div className="text-xs font-mono">{r.wage}</div>
                            </div>
                            <div className="text-[10px] text-slate-500">{r.desc}</div>
                        </button>
                    ))}
                </div>
                <motion.button
                    whileTap={{ scale: 0.98 }}
                    onClick={handleHire}
                    className="w-full py-3 bg-neon-green/20 border border-neon-green/50 text-neon-green font-bold rounded hover:bg-neon-green/30 transition-colors"
                >
                    POST POSITION
                </motion.button>
            </div>

            {/* STAFF ROSTER */}
            <div className="col-span-12 md:col-span-8 glass-card bg-black/40 p-6">
                <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
                    <Users className="text-neon-cyan" /> Staff Roster
                </h2>
                {allStaff.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {allStaff.map((staff: any) => (
                            <div key={staff.staff_id} className="p-4 bg-white/5 rounded border border-white/10">
                                <div className="flex justify-between items-start mb-2">
                                    <div>
                                        <div className="font-bold text-white">{staff.name || staff.staff_id}</div>
                                        <div className="text-xs text-slate-400">{staff.role}</div>
                                    </div>
                                    <div className={`px-2 py-0.5 rounded text-[10px] font-mono ${(staff.morale || 80) > 70 ? 'bg-neon-green/20 text-neon-green' :
                                        (staff.morale || 80) > 40 ? 'bg-yellow-500/20 text-yellow-400' :
                                            'bg-red-500/20 text-red-400'
                                        }`}>
                                        {staff.morale || 80}% MORALE
                                    </div>
                                </div>
                                <div className="flex items-center gap-2 mb-3">
                                    <DollarSign size={14} className="text-slate-500" />
                                    <input
                                        type="number"
                                        className="w-20 px-2 py-1 bg-black/50 border border-white/20 rounded text-white text-sm"
                                        value={wageAdjust[staff.staff_id] ?? staff.hourly_wage ?? 15}
                                        onChange={(e) => setWageAdjust({ ...wageAdjust, [staff.staff_id]: parseFloat(e.target.value) })}
                                    />
                                    <button
                                        onClick={() => handleWageChange(staff.staff_id, staff.locationId, wageAdjust[staff.staff_id] ?? staff.hourly_wage)}
                                        className="px-2 py-1 bg-neon-cyan/10 border border-neon-cyan/30 text-neon-cyan text-xs rounded"
                                    >
                                        Update
                                    </button>
                                </div>
                                <button
                                    onClick={() => handleFire(staff.staff_id, staff.locationId)}
                                    className="text-red-400 text-xs hover:text-red-300 transition-colors"
                                >
                                    Terminate
                                </button>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-10 text-slate-500">
                        <Users size={48} className="mx-auto mb-3 opacity-30" />
                        <div className="text-sm">No staff employed</div>
                        <div className="text-xs text-slate-600">Hire staff to manage your locations</div>
                    </div>
                )}
            </div>

            {/* BENEFITS */}
            <div className="col-span-12 glass-card bg-black/40 p-6">
                <h2 className="text-xl font-display text-white mb-6 flex items-center gap-2">
                    <Heart className="text-neon-pink" /> Benefits Package
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {benefits.map(b => (
                        <motion.button
                            key={b.type}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => handleBenefits(b.type)}
                            className="p-4 bg-white/5 rounded border border-white/10 hover:border-neon-pink/50 hover:bg-neon-pink/5 transition-all text-left"
                        >
                            <div className="text-2xl mb-2">{b.icon}</div>
                            <div className="text-sm text-white font-bold mb-1">{b.name}</div>
                            <div className="text-[10px] text-neon-pink font-mono">{b.cost}</div>
                        </motion.button>
                    ))}
                </div>
                <div className="text-xs text-slate-500 text-center mt-4">
                    Better benefits improve staff morale and reduce turnover
                </div>
            </div>

        </div>
    );
};
