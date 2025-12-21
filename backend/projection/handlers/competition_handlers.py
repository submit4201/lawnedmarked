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
    """Transfer assets from acquired agent to the player."""
    new_state = deepcopy(state)
    # assets_transferred is expected to contain a 'locations' dict
    locations_data = event.assets_transferred.get("locations", {})
    for loc_id, loc_state in locations_data.items():
        if loc_id not in new_state.locations:
            new_state.locations[loc_id] = loc_state
    return new_state


def handle_competitor_price_changed(state: AgentState, event: CompetitorPriceChanged) -> AgentState:
    """Update known competitor prices at a location."""
    new_state = deepcopy(state)
    if event.location_id in new_state.locations:
        location = new_state.locations[event.location_id]
        if event.competitor_id not in location.competitor_prices:
            location.competitor_prices[event.competitor_id] = {}
        location.competitor_prices[event.competitor_id][event.service_name] = event.new_price
    return new_state


def handle_competitor_exited_market(state: AgentState, event: CompetitorExitedMarket) -> AgentState:
    """Remove competitor from all known price lists."""
    new_state = deepcopy(state)
    for location in new_state.locations.values():
        if event.competitor_id in location.competitor_prices:
            del location.competitor_prices[event.competitor_id]
    return new_state


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
