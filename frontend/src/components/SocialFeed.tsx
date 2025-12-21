import { useEventStore } from '../store/eventStore.ts';
import { motion, AnimatePresence } from 'framer-motion';
import { Star, AlertCircle, TrendingUp, Bell } from 'lucide-react';

export const SocialFeed = () => {
    const events = useEventStore((state) => state.events);

    const socialEvents = events.filter(e =>
        ['CustomerReviewSubmitted', 'DilemmaTriggered', 'CompetitorPriceChanged'].includes(e.event_type)
    ).reverse().slice(0, 10);

    // Demo data for empty state
    const demoEvents = [
        {
            id: 'demo1',
            type: 'review',
            rating: 5,
            text: '"Amazing service! The new machines are so fast."',
            location: 'Zone A',
            time: '2m ago'
        },
        {
            id: 'demo2',
            type: 'alert',
            title: 'Competitor Activity',
            text: 'CleanWash Inc. reduced prices by 15% in Zone B',
            time: '15m ago'
        },
        {
            id: 'demo3',
            type: 'dilemma',
            title: 'Ethical Decision Required',
            text: 'An employee requests unpaid overtime. How do you respond?',
            time: '1h ago'
        },
    ];

    return (
        <div className="glass-card h-full flex flex-col">
            {/* Header */}
            <div className="section-header">
                <div className="section-header-icon bg-neon-pink/10 border-neon-pink/30">
                    <Bell size={16} className="text-neon-pink" />
                </div>
                <h3 className="section-title">Social Feed</h3>
                <span className="ml-auto px-2 py-0.5 bg-neon-pink/20 text-neon-pink text-[10px] font-mono rounded">
                    LIVE
                </span>
            </div>

            {/* Feed Content */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                <AnimatePresence initial={false}>
                    {socialEvents.length > 0 ? (
                        socialEvents.map((event, idx) => (
                            <motion.div
                                key={event.event_id || idx}
                                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.95 }}
                                transition={{ duration: 0.3 }}
                                className="group"
                            >
                                <FeedCard event={event} />
                            </motion.div>
                        ))
                    ) : (
                        // Demo content
                        demoEvents.map((demo, idx) => (
                            <motion.div
                                key={demo.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 0.6, y: 0 }}
                                transition={{ delay: idx * 0.2, duration: 0.3 }}
                            >
                                {demo.type === 'review' && (
                                    <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5">
                                        <div className="flex items-center gap-1 mb-2">
                                            {[1, 2, 3, 4, 5].map(s => (
                                                <Star
                                                    key={s}
                                                    size={10}
                                                    fill={s <= (demo.rating ?? 0) ? '#ffd60a' : 'none'}
                                                    className={s <= (demo.rating ?? 0) ? 'text-gold' : 'text-steel'}
                                                />
                                            ))}
                                            <span className="ml-auto text-[9px] text-slate">{demo.time}</span>
                                        </div>
                                        <p className="text-xs text-slate/80 italic">{demo.text}</p>
                                        <div className="text-[9px] text-slate/50 mt-2">{demo.location}</div>
                                    </div>
                                )}
                                {demo.type === 'alert' && (
                                    <div className="p-3 rounded-lg bg-ice/5 border border-ice/20">
                                        <div className="flex items-center gap-2 mb-2">
                                            <TrendingUp size={12} className="text-ice" />
                                            <span className="text-[10px] font-bold text-ice uppercase">{demo.title}</span>
                                            <span className="ml-auto text-[9px] text-slate">{demo.time}</span>
                                        </div>
                                        <p className="text-xs text-slate/80">{demo.text}</p>
                                    </div>
                                )}
                                {demo.type === 'dilemma' && (
                                    <div className="p-3 rounded-lg bg-neon-purple/5 border border-neon-purple/20">
                                        <div className="flex items-center gap-2 mb-2">
                                            <AlertCircle size={12} className="text-neon-purple" />
                                            <span className="text-[10px] font-bold text-neon-purple uppercase">{demo.title}</span>
                                        </div>
                                        <p className="text-xs text-slate/80">{demo.text}</p>
                                        <div className="flex gap-2 mt-3">
                                            <button className="flex-1 py-1.5 text-[9px] font-mono uppercase bg-neon-purple/10 text-neon-purple border border-neon-purple/30 rounded hover:bg-neon-purple/20">
                                                Respond
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </motion.div>
                        ))
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

// Individual feed card component
const FeedCard = ({ event }: { event: any }) => {
    if (event.event_type === 'CustomerReviewSubmitted') {
        return (
            <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5 hover:border-gold/30 transition-colors">
                <div className="flex items-center gap-1 mb-2">
                    {[1, 2, 3, 4, 5].map(s => (
                        <Star
                            key={s}
                            size={10}
                            fill={s <= (event.rating || 4) ? '#ffd60a' : 'none'}
                            className={s <= (event.rating || 4) ? 'text-gold' : 'text-steel'}
                        />
                    ))}
                    <span className="text-[9px] text-gold font-mono ml-1">{event.rating || 4}.0</span>
                </div>
                <p className="text-xs text-slate/80 italic">"{event.review_text || 'Great experience!'}"</p>
                <div className="flex justify-between mt-2 text-[9px] text-slate/50">
                    <span>{event.location_id || 'Zone A'}</span>
                    <span>Week {event.week || 1}</span>
                </div>
            </div>
        );
    }

    if (event.event_type === 'DilemmaTriggered') {
        return (
            <div className="p-3 rounded-lg bg-neon-purple/5 border border-neon-purple/20">
                <div className="flex items-center gap-2 mb-2">
                    <AlertCircle size={12} className="text-neon-purple" />
                    <span className="text-[10px] font-bold text-neon-purple uppercase">Ethical Dilemma</span>
                </div>
                <h4 className="text-xs font-bold text-white mb-1">{event.title || 'Decision Required'}</h4>
                <p className="text-[11px] text-slate/70">{event.description}</p>
                <div className="flex gap-2 mt-3">
                    <motion.button
                        className="flex-1 py-1.5 text-[9px] font-mono uppercase bg-neon-purple/10 text-neon-purple border border-neon-purple/30 rounded"
                        whileHover={{ scale: 1.02, backgroundColor: 'rgba(191, 0, 255, 0.2)' }}
                        whileTap={{ scale: 0.98 }}
                    >
                        Resolve
                    </motion.button>
                </div>
            </div>
        );
    }

    if (event.event_type === 'CompetitorPriceChanged') {
        return (
            <div className="p-3 rounded-lg bg-ice/5 border border-ice/20 hover:border-ice/40 transition-colors">
                <div className="flex items-center gap-2 mb-2">
                    <TrendingUp size={12} className="text-ice" />
                    <span className="text-[10px] font-bold text-ice uppercase">Market Intelligence</span>
                </div>
                <p className="text-xs text-slate/80">
                    <span className="text-ice font-bold">{event.competitor_id || 'Competitor'}</span>
                    {' adjusted pricing in '}
                    <span className="text-white">{event.zone || 'Zone A'}</span>
                </p>
            </div>
        );
    }

    return null;
};
