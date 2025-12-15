"""
Social, loyalty, and regulatory projection handlers.
"""

from copy import deepcopy
from core.models import AgentState, RegulatoryStatus, ScandalMarker, Fine
from core.events import (
    SocialScoreAdjusted,
    RegulatoryStatusUpdated,
    ScandalStarted,
    ScandalMarkerDecayed,
    RegulatoryFinding,
    DilemmaResolved,
    DilemmaTriggered,
    LoyaltyMemberRegistered,
    CustomerReviewSubmitted,
    InvestigationStarted,
    InvestigationStageAdvanced,
)


def handle_social_score_adjusted(state: AgentState, event: SocialScoreAdjusted) -> AgentState:
    """Update the social score and clamp between 0 and 100."""
    new_state = deepcopy(state)
    new_state.social_score += event.adjustment
    new_state.social_score = max(0.0, min(100.0, new_state.social_score))
    return new_state


def handle_regulatory_status_updated(state: AgentState, event: RegulatoryStatusUpdated) -> AgentState:
    """Update the regulatory status."""
    new_state = deepcopy(state)
    try:
        new_state.regulatory_status = RegulatoryStatus(event.new_status)
    except Exception:
        new_state.regulatory_status = event.new_status
    return new_state


def handle_scandal_started(state: AgentState, event: ScandalStarted) -> AgentState:
    """Add a new scandal marker to active_scandals."""
    new_state = deepcopy(state)
    scandal = ScandalMarker(
        scandal_id=event.scandal_id,
        description=event.description,
        severity=event.severity,
        duration_weeks=event.duration_weeks,
        decay_rate=0.1,
        start_week=state.current_week,
    )
    new_state.active_scandals.append(scandal)
    return new_state


def handle_scandal_marker_decayed(state: AgentState, event: ScandalMarkerDecayed) -> AgentState:
    """Reduce a scandal's remaining duration and remove if expired."""
    new_state = deepcopy(state)
    for scandal in list(new_state.active_scandals):
        if scandal.scandal_id == event.scandal_id:
            scandal.duration_weeks = event.remaining_weeks
            if scandal.duration_weeks <= 0:
                new_state.active_scandals.remove(scandal)
            break
    return new_state


def handle_regulatory_finding(state: AgentState, event: RegulatoryFinding) -> AgentState:
    """Add a pending fine to the agent."""
    new_state = deepcopy(state)
    fine = Fine(
        fine_id=event.fine_id,
        description=event.description,
        amount=event.fine_amount,
        issued_week=state.current_week,
        due_date=event.due_date,
    )
    new_state.pending_fines.append(fine)
    return new_state


def handle_dilemma_resolved(state: AgentState, event: DilemmaResolved) -> AgentState:
    """Record the player's ethical dilemma choice (mechanical no-op)."""
    return deepcopy(state)


def handle_dilemma_triggered(state: AgentState, event: DilemmaTriggered) -> AgentState:
    """Placeholder for dilemma presentation (no state change)."""
    return deepcopy(state)


def handle_loyalty_member_registered(state: AgentState, event: LoyaltyMemberRegistered) -> AgentState:
    """Register loyalty program members."""
    new_state = deepcopy(state)
    new_state.customer_loyalty_members += event.member_count
    return new_state


def handle_customer_review_submitted(state: AgentState, event: CustomerReviewSubmitted) -> AgentState:
    """Adjust social score based on customer rating."""
    new_state = deepcopy(state)
    delta = event.rating - 3.0
    new_state.social_score += delta
    new_state.social_score = max(0.0, min(100.0, new_state.social_score))
    return new_state


def handle_investigation_started(state: AgentState, event: InvestigationStarted) -> AgentState:
    """Set regulatory status to investigation when an inquiry starts."""
    new_state = deepcopy(state)
    new_state.regulatory_status = RegulatoryStatus.INVESTIGATION
    return new_state


def handle_investigation_stage_advanced(state: AgentState, event: InvestigationStageAdvanced) -> AgentState:
    """Placeholder handler for investigation stage progression."""
    return deepcopy(state)


SOCIAL_REGULATORY_EVENT_HANDLERS = {
    "SocialScoreAdjusted": handle_social_score_adjusted,
    "RegulatoryStatusUpdated": handle_regulatory_status_updated,
    "ScandalStarted": handle_scandal_started,
    "ScandalMarkerDecayed": handle_scandal_marker_decayed,
    "RegulatoryFinding": handle_regulatory_finding,
    "DilemmaResolved": handle_dilemma_resolved,
    "DilemmaTriggered": handle_dilemma_triggered,
    "LoyaltyMemberRegistered": handle_loyalty_member_registered,
    "CustomerReviewSubmitted": handle_customer_review_submitted,
    "InvestigationStarted": handle_investigation_started,
    "InvestigationStageAdvanced": handle_investigation_stage_advanced,
}

__all__ = [
    "SOCIAL_REGULATORY_EVENT_HANDLERS",
    "handle_social_score_adjusted",
    "handle_regulatory_status_updated",
    "handle_scandal_started",
    "handle_scandal_marker_decayed",
    "handle_regulatory_finding",
    "handle_dilemma_resolved",
    "handle_dilemma_triggered",
    "handle_loyalty_member_registered",
    "handle_customer_review_submitted",
    "handle_investigation_started",
    "handle_investigation_stage_advanced",
]
