import axios from 'axios';
import { useGameStore } from '../store/gameStore.ts';
import { useEventStore } from '../store/eventStore.ts';
import type { GameEvent } from '../store/eventStore.ts';
import { showSuccess, showError, showLoading, dismissToast } from '../components/ui/toast.tsx';

const BASE_URL = ''; // Relative path, handled by Vite proxy

export const GameService = {
    fetchState: async (agentId: string) => {
        try {
            // Server endpoint: /state/{agent_id} (proxied)
            const response = await axios.get(`${BASE_URL}/state/${agentId}`);
            useGameStore.getState().setState(response.data);
        } catch (error) {
            console.error('Failed to fetch state:', error);
            // ! Silent fail for polling - don't spam toasts
        }
    },

    fetchEvents: async (agentId: string) => {
        try {
            // Server endpoint: /history/{agent_id} (proxied)
            const response = await axios.get(`${BASE_URL}/history/${agentId}`);
            // The server returns { agent_id, events: [...] }
            const events: GameEvent[] = response.data.events || [];

            // Update event store
            const currentEvents = useEventStore.getState().events;
            if (events.length > currentEvents.length) {
                useEventStore.getState().setEvents(events);
            }
        } catch (error) {
            console.error('Failed to fetch interactions:', error);
            // ! Silent fail for polling - don't spam toasts
        }
    },

    submitCommand: async (agentId: string, commandName: string, payload: any = {}) => {
        const loadingId = showLoading(`Executing ${commandName}...`);
        try {
            // Server endpoint: /api/submit_command (proxied)
            // Payload goes in POST body, agent_id and command_name as query params
            const response = await axios.post(
                `${BASE_URL}/api/submit_command`,
                payload,
                {
                    params: {
                        agent_id: agentId,
                        command_name: commandName,
                    }
                }
            );
            dismissToast(loadingId);

            if (response.data?.success) {
                showSuccess(`${commandName} executed successfully`);
            } else {
                showError(response.data?.message || 'Command failed');
            }
            return response.data;
        } catch (error: any) {
            dismissToast(loadingId);
            const message = error?.response?.data?.detail || error?.message || 'API Error';
            showError(`Failed: ${message}`);
            console.error('Failed to submit command:', error);
            return { success: false, message: 'API Error' };
        }
    },

    advanceTurn: async (agentIds: string[], days: number = 1) => {
        const loadingId = showLoading('Advancing simulation...');
        try {
            const response = await axios.post(`${BASE_URL}/api/advance_day`, {
                agent_ids: agentIds,
                days: days
            });
            dismissToast(loadingId);
            showSuccess(`Advanced ${days} day(s)`);
            return response.data;
        } catch (error: any) {
            dismissToast(loadingId);
            const message = error?.response?.data?.detail || error?.message || 'Server error';
            showError(`Turn failed: ${message}`);
            console.error('Failed to advance turn:', error);
        }
    },

    runTurn: async (agentId: string) => {
        const loadingId = showLoading('Running AI turn...');
        try {
            const response = await axios.post(`${BASE_URL}/api/run_turn`, null, {
                params: { agent_id: agentId }
            });
            dismissToast(loadingId);
            showSuccess('AI turn completed');
            return response.data;
        } catch (error: any) {
            dismissToast(loadingId);
            const message = error?.response?.data?.detail || error?.message || 'AI turn error';
            showError(`AI turn failed: ${message}`);
            console.error('Failed to run turn:', error);
            return { ok: false, error: String(error) };
        }
    },

    maintainMachine: async (agentId: string, locationId: string, machineId: string) => {
        return GameService.submitCommand(agentId, 'PERFORM_MAINTENANCE', {
            location_id: locationId,
            machine_id: machineId
        });
    }
};

