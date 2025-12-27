import { useEffect } from 'react';
import { GameService } from '../services/gameService.ts';

export const usePolling = (agentId: string, intervalMs: number = 2000) => {
    useEffect(() => {
        if (!agentId) return;

        // Initial fetch
        GameService.fetchState(agentId);
        GameService.fetchEvents(agentId);

        const interval = setInterval(() => {
            GameService.fetchState(agentId);
            GameService.fetchEvents(agentId);
        }, intervalMs);

        return () => clearInterval(interval);
    }, [agentId, intervalMs]);
};
