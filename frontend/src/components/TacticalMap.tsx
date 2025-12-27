import { motion } from 'framer-motion';
import { Map, Users, TrendingUp, DollarSign } from 'lucide-react';
import { useGameStore } from '../store/gameStore.ts';
import { useMemo } from 'react';

// Zone mapping configuration
const ZONE_CONFIG = [
    { id: 'Zone A', name: 'Downtown Core', x: 0, y: 0, color: '#00f5ff' },
    { id: 'Zone B', name: 'Industrial Sector', x: 160, y: 0, color: '#00ffa3' },
    { id: 'Zone C', name: 'Residential Hills', x: 0, y: 160, color: '#ffd60a' },
    { id: 'Zone D', name: 'Market District', x: 160, y: 160, color: '#ff3b30' },
];

interface ZoneData {
    id: string;
    name: string;
    x: number;
    y: number;
    color: string;
    active: boolean;
    traffic: number;
    competition: number;
    revenue: number;
    machineCount: number;
}

const useZoneData = (): ZoneData[] => {
    const locations = useGameStore(state => state.locations);

    return useMemo(() => {
        return ZONE_CONFIG.map(config => {
            const loc = Object.values(locations).find(l => l.zone === config.id || l.zone === config.name)
                || Object.values(locations).find(l => l.location_id === config.id);

            if (!loc) return {
                ...config,
                active: false,
                traffic: 0,
                competition: 0,
                revenue: 0,
                machineCount: 0
            };

            const machineCount = Object.keys(loc.equipment || {}).length;
            const revenue = loc.accumulated_revenue_week || 0;
            const traffic = Math.min(100, Math.floor(revenue / 10)); // Proxy traffic from revenue for now
            const competition = 0;

            return {
                ...config,
                active: true,
                traffic,
                competition,
                revenue,
                machineCount
            };
        });
    }, [locations]);
};

const ZoneMarker = ({ zone, index }: { zone: ZoneData; index: number }) => {
    if (!zone.active) {
        return (
            <div
                className="absolute border border-white/5 opacity-20"
                style={{
                    left: zone.x + 100, top: zone.y + 100,
                    width: '140px', height: '140px'
                }}
            />
        );
    }

    const { traffic: height, color } = zone;

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
            className="absolute shadow-lg border border-white/10 backdrop-blur-sm hover:brightness-125 transition-all cursor-pointer"
            style={{
                left: zone.x + 100,
                top: zone.y + 100,
                width: '140px',
                height: '140px',
                backgroundColor: `${color}10`,
                border: `1px solid ${color}40`,
                boxShadow: `0 0 20px ${color}20`,
            }}
        >
            {/* 3D Pillar Effect */}
            <div
                className="absolute bottom-0 left-0 w-full bg-current opacity-20 transition-all duration-500"
                style={{
                    height: `${height}%`,
                    color: color,
                    bottom: 0,
                    transform: 'translateZ(0)',
                }}
            />

            {/* Data Pin */}
            <div className="absolute -top-10 left-1/2 -translate-x-1/2 transform -rotate-z-45 text-center w-32 pointer-events-none">
                <div className="text-[10px] font-display font-bold text-white bg-black/50 px-2 py-0.5 rounded border border-white/10 backdrop-blur-md inline-block whitespace-nowrap">
                    {zone.name}
                </div>
                <div className="flex justify-center gap-2 mt-1">
                    <span className="flex items-center gap-0.5 text-[8px] font-mono text-neon-green">
                        <Users size={8} /> {zone.traffic}
                    </span>
                    <span className="flex items-center gap-0.5 text-[8px] font-mono text-white">
                        <DollarSign size={8} /> {zone.revenue}
                    </span>
                </div>
            </div>

            {/* Base Grid */}
            <div className="absolute inset-0 grid grid-cols-4 grid-rows-4 opacity-10">
                {[...Array(16)].map((_, j) => (
                    <div key={j} className="border border-white/20" />
                ))}
            </div>
        </motion.div>
    );
};

export const TacticalMap = () => {
    const zoneData = useZoneData();

    return (
        <div className="glass-card h-[400px] flex flex-col overflow-hidden relative group">
            <div className="absolute top-4 left-4 z-10 flex flex-col gap-1 pointer-events-none">
                <div className="flex items-center gap-2">
                    <Map size={16} className="text-neon-cyan" />
                    <h3 className="font-display text-sm tracking-widest text-white">TACTICAL VIEW</h3>
                </div>
                <div className="text-[10px] font-mono text-slate">REAL-TIME CITY TELEMETRY</div>
            </div>

            <div className="flex-1 bg-[#05070a] relative overflow-hidden flex items-center justify-center perspective-[1000px]">
                <div className="absolute inset-0 opacity-20"
                    style={{
                        backgroundImage: 'radial-gradient(circle, #00f5ff 1px, transparent 1px)',
                        backgroundSize: '30px 30px',
                        transform: 'rotateX(60deg) scale(2)',
                    }}
                />

                <div
                    className="relative w-[600px] h-[600px] transform-style-3d rotate-x-60 rotate-z-45 transition-transform duration-700 ease-out group-hover:rotate-z-[50deg]"
                    style={{ transform: 'rotateX(55deg) rotateZ(45deg)' }}
                >
                    {zoneData.map((zone, i) => (
                        <ZoneMarker key={zone.id} zone={zone} index={i} />
                    ))}
                </div>
            </div>

            <div className="absolute bottom-4 right-4 flex gap-2">
                <button className="p-2 glass rounded hover:bg-white/10" aria-label="Toggle map view">
                    <Map size={14} />
                </button>
                <button className="p-2 glass rounded hover:bg-white/10" aria-label="Show traffic trends">
                    <TrendingUp size={14} />
                </button>
            </div>
        </div>
    );
};
