import { create } from 'zustand';

export interface GameEvent {
    event_id: string;
    event_type: string;
    agent_id: string;
    timestamp: string;
    [key: string]: any;
}

interface EventState {
    events: GameEvent[];
    thoughts: GameEvent[];
    addEvent: (event: GameEvent) => void;
    setEvents: (events: GameEvent[]) => void;
}

export const useEventStore = create<EventState>((set) => ({
    events: [],
    thoughts: [],
    addEvent: (event) => set((state) => {
        const isThought = event.event_type === 'ThoughtBroadcasted';
        return {
            events: [...state.events, event],
            thoughts: isThought ? [...state.thoughts, event] : state.thoughts,
        };
    }),
    setEvents: (events) => set({
        events,
        thoughts: events.filter(e => e.event_type === 'ThoughtBroadcasted'),
    }),
}));
