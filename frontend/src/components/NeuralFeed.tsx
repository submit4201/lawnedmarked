import { useEffect, useRef, useState } from 'react';
import { useEventStore } from '../store/eventStore.ts';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, ChevronRight } from 'lucide-react';

// Typewriter effect with variable speed
const TypewriterText = ({ text, speed = 15 }: { text: string; speed?: number }) => {
    const [displayed, setDisplayed] = useState('');
    const [isComplete, setIsComplete] = useState(false);

    useEffect(() => {
        setDisplayed('');
        setIsComplete(false);
        let i = 0;
        const interval = setInterval(() => {
            setDisplayed(text.slice(0, i + 1));
            i++;
            if (i >= text.length) {
                clearInterval(interval);
                setIsComplete(true);
            }
        }, speed);
        return () => clearInterval(interval);
    }, [text, speed]);

    return (
        <span>
            {displayed}
            {!isComplete && <span className="terminal-cursor" />}
        </span>
    );
};



export const NeuralFeed = () => {
    const thoughts = useEventStore((state) => state.thoughts);
    const scrollRef = useRef<HTMLDivElement>(null);
    const [isLocked, setIsLocked] = useState(false);

    useEffect(() => {
        if (scrollRef.current && !isLocked) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [thoughts, isLocked]);

    const displayThoughts = thoughts.length > 0 ? thoughts : [];

    return (
        <div className="glass-card flex flex-col h-[350px]">
            {/* Header */}
            <div className="section-header">
                <div className="section-header-icon">
                    <Terminal size={16} className="text-neon-green" />
                </div>
                <h3 className="section-title">Neural Feed</h3>
                <div className="ml-auto flex items-center gap-2">
                    <span className="status-dot status-dot-online" />
                    <span className="text-[10px] font-mono text-neon-green">LIVE</span>
                </div>
            </div>

            {/* Terminal Content */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto font-mono text-xs space-y-3 pr-2"
                onScroll={(e) => {
                    const el = e.currentTarget;
                    const atBottom = el.scrollHeight - el.scrollTop <= el.clientHeight + 50;
                    setIsLocked(!atBottom);
                }}
            >
                <AnimatePresence initial={false}>
                    {displayThoughts.length > 0 ? (
                        displayThoughts.map((thought, idx) => (
                            <motion.div
                                key={thought.event_id || idx}
                                initial={{ opacity: 0, x: -10, height: 0 }}
                                animate={{ opacity: 1, x: 0, height: 'auto' }}
                                exit={{ opacity: 0, x: 10 }}
                                transition={{ duration: 0.3 }}
                                className="border-l-2 border-neon-green/30 pl-3 py-1"
                            >
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-[10px] text-slate">
                                        [{new Date(thought.timestamp).toLocaleTimeString('en-US', { hour12: false })}]
                                    </span>
                                    <span className="text-[10px] text-neon-cyan font-bold">{thought.agent_id}</span>
                                </div>
                                <div className="text-slate/90 leading-relaxed font-mono text-xs">
                                    <TypewriterText
                                        text={thought.thought_text || thought.content || ''}
                                        speed={idx === displayThoughts.length - 1 ? 10 : 0}
                                    />
                                </div>
                            </motion.div>
                        ))
                    ) : (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.5 }}
                            className="flex items-center gap-2 text-slate/60 mt-4 px-4"
                        >
                            <ChevronRight size={12} className="text-neon-green animate-pulse" />
                            <span className="italic">Awaiting live neural data...</span>
                            <span className="terminal-cursor" />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Input prompt */}
            <div className="mt-3 pt-3 border-t border-white/5">
                <div className="flex items-center gap-2 text-slate/60">
                    <span className="text-neon-green">▸</span>
                    <span className="text-[10px] font-mono">STREAM_BUFFER: {thoughts.length} EVENTS</span>
                </div>
            </div>
        </div>
    );
};
