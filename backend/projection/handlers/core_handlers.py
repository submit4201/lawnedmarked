"""
Projection handler registry aggregator. Handlers are organized by domain modules.
"""

from .time_handlers import (
    TIME_EVENT_HANDLERS,
    handle_time_advanced,
    handle_daily_revenue_processed,
    handle_weekly_fixed_costs_billed,
    handle_weekly_wages_billed,
)
from .financial_handlers import (
    FINANCIAL_EVENT_HANDLERS,
    handle_funds_transferred,
    handle_loan_taken,
    handle_debt_payment_processed,
    handle_marketing_boost_applied,
    handle_tax_liability_calculated,
    handle_monthly_interest_accrued,
    handle_tax_bracket_adjusted,
    handle_default_recorded,
)
from .operational_handlers import (
    OPERATIONAL_EVENT_HANDLERS,
    handle_price_set,
    handle_equipment_purchased,
    handle_equipment_sold,
    handle_equipment_repaired,
    handle_supplies_acquired,
    handle_new_location_opened,
    handle_machine_status_changed,
    handle_machine_broken_down,
    handle_machine_wear_updated,
    handle_stockout_started,
    handle_stockout_ended,
)
from .staffing_handlers import (
    STAFFING_EVENT_HANDLERS,
    handle_staff_hired,
    handle_staff_fired,
    handle_wage_adjusted,
    handle_benefit_implemented,
    handle_staff_quit,
)
from .social_regulatory_handlers import (
    SOCIAL_REGULATORY_EVENT_HANDLERS,
    handle_social_score_adjusted,
    handle_regulatory_status_updated,
    handle_scandal_started,
    handle_scandal_marker_decayed,
    handle_regulatory_finding,
    handle_dilemma_resolved,
    handle_dilemma_triggered,
    handle_loyalty_member_registered,
    handle_customer_review_submitted,
    handle_investigation_started,
    handle_investigation_stage_advanced,
)
from .vendor_handlers import (
    VENDOR_EVENT_HANDLERS,
    handle_vendor_negotiation_result,
    handle_exclusive_contract_signed,
    handle_vendor_terms_updated,
    handle_vendor_tier_promoted,
    handle_vendor_tier_demoted,
    handle_vendor_price_fluctuated,
    handle_delivery_disruption,
)
from .competition_handlers import (
    COMPETITION_EVENT_HANDLERS,
    handle_alliance_formed,
    handle_agent_acquired,
    handle_competitor_price_changed,
    handle_competitor_exited_market,
    handle_communication_intercepted,
)


CORE_EVENT_HANDLERS = {
    **TIME_EVENT_HANDLERS,
    **FINANCIAL_EVENT_HANDLERS,
    **OPERATIONAL_EVENT_HANDLERS,
    **STAFFING_EVENT_HANDLERS,
    **SOCIAL_REGULATORY_EVENT_HANDLERS,
    **VENDOR_EVENT_HANDLERS,
    **COMPETITION_EVENT_HANDLERS,
}


__all__ = [
    "CORE_EVENT_HANDLERS",
    # Time
    "handle_time_advanced",
    "handle_daily_revenue_processed",
    "handle_weekly_fixed_costs_billed",
    "handle_weekly_wages_billed",
    # Financial
    "handle_funds_transferred",
    "handle_loan_taken",
    "handle_debt_payment_processed",
    "handle_marketing_boost_applied",
    "handle_tax_liability_calculated",
    "handle_monthly_interest_accrued",
    "handle_tax_bracket_adjusted",
    "handle_default_recorded",
    # Operational
    "handle_price_set",
    "handle_equipment_purchased",
    "handle_equipment_sold",
    "handle_equipment_repaired",
    "handle_supplies_acquired",
    "handle_new_location_opened",
    "handle_machine_status_changed",
    "handle_machine_broken_down",
    "handle_machine_wear_updated",
    "handle_stockout_started",
    "handle_stockout_ended",
    # Staffing
    "handle_staff_hired",
    "handle_staff_fired",
    "handle_wage_adjusted",
    "handle_benefit_implemented",
    "handle_staff_quit",
    # Social & Regulatory
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
    # Vendor
    "handle_vendor_negotiation_result",
    "handle_exclusive_contract_signed",
    "handle_vendor_terms_updated",
    "handle_vendor_tier_promoted",
    "handle_vendor_tier_demoted",
    "handle_vendor_price_fluctuated",
    "handle_delivery_disruption",
    # Competition
    "handle_alliance_formed",
    "handle_agent_acquired",
    "handle_competitor_price_changed",
    "handle_competitor_exited_market",
    "handle_communication_intercepted",
]

