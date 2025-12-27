import { create } from 'zustand';

export interface Machine {
    machine_id: string;
    machine_type: string;
    status: string;
    condition: number;
    loads_processed_since_service: number;
}

export interface VendorRelationship {
    vendor_id: string;
    tier: number;
    weeks_at_tier: number;
    payment_history: string[];
    is_exclusive_contract: boolean;
    current_price_per_unit: number;
    is_disrupted: boolean;
}

export interface Location {
    location_id: string;
    zone: string;
    equipment: Record<string, Machine>;
    inventory_detergent: number;
    inventory_softener: number;
    accumulated_revenue_week: number;
    vendor_relationships: Record<string, VendorRelationship>;
}

interface GameState {
    agent_id: string;
    cash_balance: number;
    current_week: number;
    current_day: number;
    locations: Record<string, Location>;
    agents: Record<string, any>;
    active_scandals: any[];
    // Reputation metrics
    social_score: number;
    regulatory_status: string;
    credit_rating: number;
    // Financial metrics
    total_debt_owed: number;
    line_of_credit_balance: number;
    line_of_credit_limit: number;
    current_tax_liability: number;
    setState: (state: Partial<GameState>) => void;
}

export const useGameStore = create<GameState>((set) => ({
    agent_id: '',
    cash_balance: 0,
    current_week: 0,
    current_day: 0,
    locations: {},
    agents: {},
    active_scandals: [],
    // Reputation defaults
    social_score: 50,
    regulatory_status: 'COMPLIANT',
    credit_rating: 700,
    // Financial defaults
    total_debt_owed: 0,
    line_of_credit_balance: 0,
    line_of_credit_limit: 5000,
    current_tax_liability: 0,
    setState: (newState) => set((state) => ({ ...state, ...newState })),
}));

