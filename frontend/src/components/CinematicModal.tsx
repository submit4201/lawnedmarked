import { motion, AnimatePresence } from 'framer-motion';
import type { GameEvent } from '../store/eventStore.ts';
import { User, ShieldAlert, X } from 'lucide-react';

interface CinematicModalProps {
    event: GameEvent | null;
    onClose: () => void;
    onResolve: (decision: string) => void;
}

export const CinematicModal = ({ event, onClose, onResolve }: CinematicModalProps) => {
    if (!event) return null;

    // Determine character archetype based on dilemma type (mock logic for now)
    const getCharacter = () => {
        // We could parse event.content for keywords like "Inspector", "Union", "Mob"
        return {
            name: "Chief Inspector Vance",
            role: "Municipal Licensing Bureau",
            image: "bg-void", // Placeholder for actual image asset
            color: "crimson"
        };
    };

    const char = getCharacter();

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center bg-void/90 backdrop-blur-md"
            >
                <div className="absolute inset-0 bg-[url('https://transparenttextures.com/patterns/carbon-fibre.png')] opacity-10" />

                {/* Cinematic Letterbox Bars */}
                <motion.div
                    initial={{ height: 0 }} animate={{ height: '10vh' }}
                    className="absolute top-0 left-0 right-0 bg-black z-10"
                />
                <motion.div
                    initial={{ height: 0 }} animate={{ height: '10vh' }}
                    className="absolute bottom-0 left-0 right-0 bg-black z-10"
                />

                {/* Main Interface */}
                <div className="relative z-20 w-full max-w-5xl h-[70vh] flex gap-8 p-12">

                    {/* Character Column */}
                    <motion.div
                        initial={{ x: -50, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: 0.2 }}
                        className="w-1/3 flex flex-col justify-end"
                    >
                        <div className={`
              h-[500px] w-full bg-gradient-to-t from-${char.color}/20 to-transparent 
              border-b-4 border-${char.color} flex items-end justify-center relative overflow-hidden
            `}>
                            {/* Silhouette Placeholder */}
                            <User size={300} className={`text-${char.color} opacity-80 drop-shadow-[0_0_15px_rgba(255,59,48,0.5)]`} />

                            {/* Scanline Effect on Character */}
                            <div className="absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(0,0,0,0.5)_50%)] bg-[length:10px_10px] opacity-20" />
                        </div>

                        <div className="mt-4">
                            <h2 className={`font-display text-2xl text-${char.color} uppercase tracking-widest`}>{char.name}</h2>
                            <div className="flex items-center gap-2 text-slate font-mono text-xs uppercase">
                                <ShieldAlert size={12} />
                                {char.role}
                            </div>
                        </div>
                    </motion.div>

                    {/* Dialogue Column */}
                    <motion.div
                        initial={{ x: 50, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: 0.4 }}
                        className="flex-1 flex flex-col justify-center"
                    >
                        {/* Event Title Badge */}
                        <div className="mb-6 flex">
                            <span className={`
                px-3 py-1 bg-${char.color}/20 text-${char.color} border border-${char.color}/30 
                rounded text-xs font-mono uppercase tracking-[0.2em] animate-pulse
              `}>
                                High-Stakes Interaction
                            </span>
                        </div>

                        {/* Dialogue Box */}
                        <div className="glass-card p-8 border-l-4 border-l-white/20 relative">
                            <h3 className="font-display text-xl text-white mb-4 uppercase tracking-wider">
                                {event.title || "Urgent Matter"}
                            </h3>
                            <p className="font-mono text-lg text-ice leading-relaxed typing-effect">
                                "{event.description || event.content}"
                            </p>

                            <div className="absolute -right-2 -bottom-2 w-4 h-4 border-r-2 border-b-2 border-white/30" />
                            <div className="absolute -left-2 -top-2 w-4 h-4 border-l-2 border-t-2 border-white/30" />
                        </div>

                        {/* Choices */}
                        <div className="mt-8 space-y-3">
                            <p className="text-[10px] font-mono text-slate uppercase mb-2">Select Response Protocol:</p>

                            {['Comply with Demands', 'Negotiate Terms', 'Refuse & Escalate'].map((choice, i) => (
                                <motion.button
                                    key={i}
                                    whileHover={{ x: 10, backgroundColor: 'rgba(255, 255, 255, 0.05)' }}
                                    onClick={() => onResolve(choice)}
                                    className={`
                    w-full text-left p-4 rounded border border-white/10 bg-black/40
                    flex items-center gap-4 group transition-all
                  `}
                                >
                                    <span className="font-mono text-slate/50 text-xs">0{i + 1}</span>
                                    <span className="font-display text-sm tracking-widest text-white group-hover:text-neon-cyan transition-colors">
                                        {choice}
                                    </span>
                                </motion.button>
                            ))}
                        </div>

                        <button
                            onClick={onClose}
                            className="absolute top-0 right-0 p-2 text-slate hover:text-white"
                        >
                            <X size={24} />
                        </button>
                    </motion.div>
                </div>
            </motion.div>
        </AnimatePresence>
    );
};
