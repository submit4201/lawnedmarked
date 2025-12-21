import { motion } from 'framer-motion';
import { Settings, AlertTriangle, CheckCircle, Wrench, Zap, LucideIcon } from 'lucide-react';
import type { Machine } from '../store/gameStore.ts';
import { useMemo } from 'react';

interface EquipmentCardProps {
    machine: Machine;
    onMaintain?: (id: string) => void;
}

interface StatusConfig {
    color: string;
    gradient: string;
    icon: LucideIcon;
    label: string;
}

const useMachineStatus = (machine: Machine): StatusConfig => {
    return useMemo(() => {
        const { status, condition } = machine;
        const isBroken = status === 'BROKEN';
        const isRepairing = status === 'IN_REPAIR';

        if (isBroken) return {
            color: 'crimson',
            gradient: 'from-crimson to-neon-pink',
            icon: AlertTriangle,
            label: 'CRITICAL'
        };
        if (isRepairing) return {
            color: 'gold',
            gradient: 'from-gold to-neon-orange',
            icon: Wrench,
            label: 'REPAIRING'
        };
        if (condition > 70) return {
            color: 'neon-green',
            gradient: 'from-neon-green to-neon-cyan',
            icon: CheckCircle,
            label: 'OPTIMAL'
        };
        if (condition > 40) return {
            color: 'gold',
            gradient: 'from-gold to-neon-orange',
            icon: Zap,
            label: 'FAIR'
        };
        return {
            color: 'crimson',
            gradient: 'from-crimson to-neon-pink',
            icon: AlertTriangle,
            label: 'DEGRADED'
        };
    }, [machine.status, machine.condition]);
};

const ConditionRing = ({ condition, status, machineId }: { condition: number, status: StatusConfig, machineId: string }) => {
    const radius = 32;
    const circumference = 2 * Math.PI * radius;
    const strokeOffset = circumference - (condition / 100) * circumference;

    return (
        <div className="relative w-20 h-20 flex-shrink-0">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 80 80">
                <circle
                    cx="40" cy="40" r={radius}
                    stroke="currentColor"
                    strokeWidth="6"
                    fill="none"
                    className="text-steel/30"
                />
                <motion.circle
                    cx="40" cy="40" r={radius}
                    stroke={`url(#gradient-${machineId})`}
                    strokeWidth="6"
                    fill="none"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    initial={{ strokeDashoffset: circumference }}
                    animate={{ strokeDashoffset: strokeOffset }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                    style={{
                        filter: `drop-shadow(0 0 8px var(--color-${status.color}))`
                    }}
                />
                <defs>
                    <linearGradient id={`gradient-${machineId}`} x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" className={`text-${status.color}`} stopColor="currentColor" />
                        <stop offset="100%" className="text-neon-cyan" stopColor="currentColor" />
                    </linearGradient>
                </defs>
            </svg>

            <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`font-display text-2xl font-bold text-${status.color}`}>
                    {Math.round(condition)}
                </span>
                <span className="text-[10px] font-mono text-slate uppercase">%</span>
            </div>
        </div>
    );
};

export const EquipmentCard = ({ machine, onMaintain }: EquipmentCardProps) => {
    const status = useMachineStatus(machine);
    const StatusIcon = status.icon;
    const isBroken = machine.status === 'BROKEN';
    const isRepairing = machine.status === 'IN_REPAIR';
    const condition = machine.condition;

    return (
        <motion.div
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
            className={`
        glass-card relative overflow-visible cursor-pointer
        ${isBroken ? 'border-crimson/30' : 'border-white/10'}
        hover:border-${status.color}/50
        transition-colors duration-300
      `}
        >
            <motion.div
                className={`absolute inset-0 rounded-xl bg-gradient-to-br ${status.gradient} opacity-0`}
                whileHover={{ opacity: 0.05 }}
            />

            <div className="relative z-10 flex gap-4">
                <ConditionRing condition={condition} status={status} machineId={machine.machine_id} />

                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                        <Settings size={16} className="text-slate" />
                        <h4 className="font-display text-base text-white truncate">
                            {machine.machine_id}
                        </h4>
                    </div>

                    <div className="text-xs font-mono text-slate uppercase tracking-wider mb-3">
                        {machine.machine_type}
                    </div>

                    <div className="flex items-center gap-2">
                        <div className={`
              flex items-center gap-1.5 px-2 py-1 rounded-md
              bg-${status.color}/10 border border-${status.color}/30
            `}>
                            <StatusIcon size={12} className={`text-${status.color}`} />
                            <span className={`text-xs font-mono font-bold text-${status.color}`}>
                                {status.label}
                            </span>
                        </div>
                    </div>

                    <div className="flex gap-4 mt-3">
                        <div>
                            <div className="text-xs font-mono text-slate uppercase">Loads</div>
                            <div className="text-sm font-mono text-ice">{machine.loads_processed_since_service}</div>
                        </div>
                    </div>
                </div>
            </div>

            <motion.button
                onClick={(e) => {
                    e.stopPropagation();
                    onMaintain?.(machine.machine_id);
                }}
                disabled={isRepairing || condition > 95}
                className={`
          w-full mt-4 py-2 rounded-lg font-mono text-xs font-bold uppercase tracking-wider
          transition-all duration-300
          ${isRepairing || condition > 95
                        ? 'bg-steel/20 text-slate cursor-not-allowed'
                        : `bg-${status.color}/10 text-${status.color} border border-${status.color}/30
               hover:bg-${status.color}/20 hover:border-${status.color}/50`
                    }
        `}
                whileHover={!(isRepairing || condition > 95) ? { scale: 1.02 } : {}}
                whileTap={!(isRepairing || condition > 95) ? { scale: 0.98 } : {}}
            >
                {isRepairing ? 'REPAIR IN PROGRESS' : condition > 95 ? 'OPTIMAL CONDITION' : 'SCHEDULE MAINTENANCE'}
            </motion.button>

            {isBroken && (
                <motion.div
                    className="absolute -top-2 -right-2 px-2 py-1 rounded-full bg-crimson text-white text-[8px] font-bold uppercase"
                    animate={{
                        scale: [1, 1.1, 1],
                        boxShadow: ['0 0 10px #ff3b30', '0 0 20px #ff3b30', '0 0 10px #ff3b30']
                    }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                >
                    CRITICAL
                </motion.div>
            )}
        </motion.div>
    );
};
