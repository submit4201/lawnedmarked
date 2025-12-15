"""
Competition and alliance projection handlers.
"""

from copy import deepcopy
from core.models import AgentState, Alliance
from core.events import (
    AllianceFormed,
    AgentAcquired,
    CompetitorPriceChanged,
    CompetitorExitedMarket,
    CommunicationIntercepted,
)


def handle_alliance_formed(state: AgentState, event: AllianceFormed) -> AgentState:
    """Record a new alliance."""
    new_state = deepcopy(state)
    alliance = Alliance(
        alliance_id=event.alliance_id,
        partner_agent_id=event.partner_agent_id,
        alliance_type=event.alliance_type,
        duration_weeks=event.duration_weeks,
        start_week=state.current_week,
    )
    new_state.active_alliances.append(alliance)
    return new_state


def handle_agent_acquired(state: AgentState, event: AgentAcquired) -> AgentState:
    """Placeholder handler for acquisitions (no direct state change)."""
    return deepcopy(state)


def handle_competitor_price_changed(state: AgentState, event: CompetitorPriceChanged) -> AgentState:
    """Placeholder handler for competitor price changes."""
    return deepcopy(state)


def handle_competitor_exited_market(state: AgentState, event: CompetitorExitedMarket) -> AgentState:
    """Placeholder handler for competitor exit events."""
    return deepcopy(state)


def handle_communication_intercepted(state: AgentState, event: CommunicationIntercepted) -> AgentState:
    """Placeholder handler for intercepted communications."""
    return deepcopy(state)


COMPETITION_EVENT_HANDLERS = {
    "AllianceFormed": handle_alliance_formed,
    "AgentAcquired": handle_agent_acquired,
    "CompetitorPriceChanged": handle_competitor_price_changed,
    "CompetitorExitedMarket": handle_competitor_exited_market,
    "CommunicationIntercepted": handle_communication_intercepted,
}

__all__ = [
    "COMPETITION_EVENT_HANDLERS",
    "handle_alliance_formed",
    "handle_agent_acquired",
    "handle_competitor_price_changed",
    "handle_competitor_exited_market",
    "handle_communication_intercepted",
]
