import { motion } from 'framer-motion';
import { Settings, AlertTriangle, CheckCircle, Wrench, Zap } from 'lucide-react';
import type { Machine } from '../store/gameStore.ts';

interface EquipmentCardProps {
    machine: Machine;
    onMaintain?: (id: string) => void;
}

export const EquipmentCard = ({ machine, onMaintain }: EquipmentCardProps) => {
    const isBroken = machine.status === 'BROKEN';
    const isRepairing = machine.status === 'IN_REPAIR';
    const condition = machine.condition;

    const getStatusConfig = () => {
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
    };

    const status = getStatusConfig();
    const StatusIcon = status.icon;

    // SVG ring calculations
    const radius = 32;
    const circumference = 2 * Math.PI * radius;
    const strokeOffset = circumference - (condition / 100) * circumference;

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
            {/* Glow effect on hover */}
            <motion.div
                className={`absolute inset-0 rounded-xl bg-gradient-to-br ${status.gradient} opacity-0`}
                whileHover={{ opacity: 0.05 }}
            />

            {/* Content */}
            <div className="relative z-10 flex gap-4">
                {/* Condition Ring */}
                <div className="relative w-20 h-20 flex-shrink-0">
                    <svg className="w-full h-full -rotate-90" viewBox="0 0 80 80">
                        {/* Background ring */}
                        <circle
                            cx="40" cy="40" r={radius}
                            stroke="currentColor"
                            strokeWidth="6"
                            fill="none"
                            className="text-steel/30"
                        />
                        {/* Progress ring */}
                        <motion.circle
                            cx="40" cy="40" r={radius}
                            stroke={`url(#gradient-${machine.machine_id})`}
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
                        {/* Gradient definition */}
                        <defs>
                            <linearGradient id={`gradient-${machine.machine_id}`} x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" className={`text-${status.color}`} stopColor="currentColor" />
                                <stop offset="100%" className="text-neon-cyan" stopColor="currentColor" />
                            </linearGradient>
                        </defs>
                    </svg>

                    {/* Center content */}
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className={`font-display text-2xl font-bold text-${status.color}`}>
                            {Math.round(condition)}
                        </span>
                        <span className="text-[10px] font-mono text-slate uppercase">%</span>
                    </div>
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                    {/* Machine ID */}
                    <div className="flex items-center gap-2 mb-1">
                        <Settings size={16} className="text-slate" />
                        <h4 className="font-display text-base text-white truncate">
                            {machine.machine_id}
                        </h4>
                    </div>

                    {/* Type */}
                    <div className="text-xs font-mono text-slate uppercase tracking-wider mb-3">
                        {machine.machine_type}
                    </div>

                    {/* Status */}
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

                    {/* Stats */}
                    <div className="flex gap-4 mt-3">
                        <div>
                            <div className="text-xs font-mono text-slate uppercase">Loads</div>
                            <div className="text-sm font-mono text-ice">{machine.loads_processed_since_service}</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Maintenance Button */}
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

            {/* Critical Alert Badge */}
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
