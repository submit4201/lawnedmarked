"""
__init__ file for command handlers module.
Exports all command handlers organized by domain.
"""

from command_handlers.financial_handlers import FINANCIAL_HANDLERS
from command_handlers.operational_handlers import OPERATIONAL_HANDLERS
from command_handlers.staffing_handlers import STAFFING_HANDLERS
from command_handlers.social_handlers import SOCIAL_HANDLERS
from command_handlers.vendor_handlers import VENDOR_HANDLERS
from command_handlers.competition_handlers import COMPETITION_HANDLERS
from command_handlers.adjudication_handlers import ADJUDICATION_HANDLERS

# Consolidated handler registry
ALL_HANDLERS = {
    **FINANCIAL_HANDLERS,
    **OPERATIONAL_HANDLERS,
    **STAFFING_HANDLERS,
    **SOCIAL_HANDLERS,
    **VENDOR_HANDLERS,
    **COMPETITION_HANDLERS,
    **ADJUDICATION_HANDLERS,
}

__all__ = ["ALL_HANDLERS"]
