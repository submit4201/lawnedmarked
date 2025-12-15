"""
Game Master - World State and Narrative Orchestration.
Handles market changes, NPC behavior, customer events, vendor dynamics.
Operates completely outside the GameEngine and interacts only via events.

This is NOT an event handler. The GM reads the event log and generates
new narrative/market events based on detected patterns or scheduled triggers.
this will ve an llm based system in the future.
"""

from typing import List
from datetime import datetime
import uuid
import random

from core.events import (
    GameEvent,
    CompetitorPriceChanged,
    VendorPriceFluctuated,
    CustomerReviewSubmitted,
    DeliveryDisruption,
    DilemmaTriggered,
    CompetitorExitedMarket,
)
from core.models import AgentState
from infrastructure.event_repository import EventRepository


class GameMaster:
    """
    Manages world state, NPC behavior, and narrative events.
    
    Responsibilities:
    - Market trend generation (vendor prices, competitor actions)
    - Customer behavior and reviews
    - NPC agent actions
    - Dilemma triggers
    - Delivery disruptions
    - Narrative event generation
    
    Design: Operates asynchronously by reading the event log
    and deciding when to inject new events.
    """
    
    def __init__(self, event_repository: EventRepository):
        """
        Initialize the Game Master.
        
        Args:
            event_repository: Access to the complete event history
        """
        self.event_repository = event_repository
    
    def check_and_trigger_events(self, state: AgentState) -> List[GameEvent]:
        """
        Evaluate the current game state and trigger narrative events.
        
        Called periodically (e.g., after a TimeAdvanced event).
        
        This method:
        1. Analyzes the current state
        2. Decides which narrative events should occur
        3. Returns new events (which the caller saves to the repository)
        
        Args:
            state: Current agent state (read-only)
            
        Returns:
            List of narrative/world events to emit
        """
        events = []
        
        # Example: Trigger customer review randomly
        if random.random() < 0.3:  # 30% chance per tick
            for location_id in state.locations:
                review_event = self._generate_customer_review(state, location_id)
                if review_event:
                    events.append(review_event)
        
        # Example: Vendor price fluctuation
        if random.random() < 0.2:  # 20% chance
            for location_id in state.locations:
                price_event = self._generate_vendor_price_fluctuation(state, location_id)
                if price_event:
                    events.append(price_event)
        
        # Example: Occasional delivery disruption
        if random.random() < 0.1:  # 10% chance
            for location_id in state.locations:
                disruption_event = self._generate_delivery_disruption(state, location_id)
                if disruption_event:
                    events.append(disruption_event)
        
        # Example: Dilemma trigger based on state
        if random.random() < 0.15:  # 15% chance
            dilemma_event = self._generate_dilemma(state)
            if dilemma_event:
                events.append(dilemma_event)
        
        return events
    
    def _generate_customer_review(self, state: AgentState, location_id: str) -> GameEvent:
        """
        Generate a customer review based on location cleanliness and pricing.
        """
        if location_id not in state.locations:
            return None
        
        location = state.locations[location_id]
        
        # Review quality depends on cleanliness
        cleanliness_factor = location.current_cleanliness / 100.0
        rating = int(1 + (cleanliness_factor * 4))  # 1-5 stars
        rating = max(1, min(5, rating))  # Clamp
        
        review_texts = {
            1: "Terrible experience, machines were broken.",
            2: "Not great, place was dirty.",
            3: "Okay, but could be cleaner.",
            4: "Good service and clean facilities.",
            5: "Excellent! Very clean and well-maintained.",
        }
        
        review_event = CustomerReviewSubmitted(
            event_id=str(uuid.uuid4()),
            event_type="CustomerReviewSubmitted",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            location_id=location_id,
            rating=rating,
            review_text=review_texts.get(rating, "Average experience."),
        )
        
        return review_event
    
    def _generate_vendor_price_fluctuation(self, state: AgentState, location_id: str) -> GameEvent:
        """
        Simulate a vendor price change due to market conditions.
        """
        if location_id not in state.locations:
            return None
        
        location = state.locations[location_id]
        
        # Pick a random vendor relationship
        if not location.vendor_relationships:
            return None
        
        vendor_id = random.choice(list(location.vendor_relationships.keys()))
        
        # Random price change (-10% to +10%)
        change_factor = random.uniform(0.9, 1.1)
        old_price = 0.50  # Example
        new_price = old_price * change_factor
        
        price_event = VendorPriceFluctuated(
            event_id=str(uuid.uuid4()),
            event_type="VendorPriceFluctuated",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            vendor_id=vendor_id,
            old_price_per_unit=old_price,
            new_price_per_unit=new_price,
        )
        
        return price_event
    
    def _generate_delivery_disruption(self, state: AgentState, location_id: str) -> GameEvent:
        """
        Simulate an occasional delivery issue from a vendor.
        """
        if location_id not in state.locations:
            return None
        
        location = state.locations[location_id]
        
        if not location.vendor_relationships:
            return None
        
        vendor_id = random.choice(list(location.vendor_relationships.keys()))
        
        disruption_types = ["DELAY", "PARTIAL_SHIPMENT", "QUALITY_ISSUE"]
        disruption_type = random.choice(disruption_types)
        
        disruption_descriptions = {
            "DELAY": "Your order is delayed by 3-5 days due to supplier issues.",
            "PARTIAL_SHIPMENT": "Only 75% of your order arrived; rest coming next week.",
            "QUALITY_ISSUE": "Some detergent arrived with contamination; requesting replacement.",
        }
        
        disruption_event = DeliveryDisruption(
            event_id=str(uuid.uuid4()),
            event_type="DeliveryDisruption",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            vendor_id=vendor_id,
            disruption_type=disruption_type,
            impact_description=disruption_descriptions[disruption_type],
        )
        
        return disruption_event
    
    def _generate_dilemma(self, state: AgentState) -> GameEvent:
        """
        Generate an ethical dilemma for the player to resolve.
        """
        dilemmas = [
            {
                "description": "A competitor offers to form a price-fixing alliance. Accept?",
                "options": {
                    "accept": {
                        "description": "Accept and increase prices with ally",
                        "immediate_cost": 0,
                        "social_score_impact": -10,
                        "regulatory_risk": "HIGH",
                    },
                    "reject": {
                        "description": "Refuse and maintain ethical standards",
                        "immediate_cost": 0,
                        "social_score_impact": 5,
                        "regulatory_risk": "LOW",
                    },
                },
            },
            {
                "description": "You could save $500/week by ignoring safety violations. Do it?",
                "options": {
                    "cut_corners": {
                        "description": "Cut corners on maintenance",
                        "immediate_cost": 0,
                        "social_score_impact": -15,
                        "regulatory_risk": "HIGH",
                    },
                    "maintain_standards": {
                        "description": "Maintain safety and quality standards",
                        "immediate_cost": 500,
                        "social_score_impact": 5,
                        "regulatory_risk": "LOW",
                    },
                },
            },
        ]
        
        dilemma = random.choice(dilemmas)
        
        dilemma_event = DilemmaTriggered(
            event_id=str(uuid.uuid4()),
            event_type="DilemmaTriggered",
            agent_id=state.agent_id,
            timestamp=datetime.now(),
            week=state.current_week,
            dilemma_id=str(uuid.uuid4()),
            description=dilemma["description"],
            options=dilemma["options"],
        )
        
        return dilemma_event


__all__ = ["GameMaster"]
