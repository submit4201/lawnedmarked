
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

os.environ["LLM_DISCOVER_ONLY"] = "phi,azure,human"
os.environ["PLAYER_001_PROVIDER"] = "human"

from backend.application_factory import ApplicationFactory

print("--- Verifying Discovery ---")
game_engine, gm, judge, llm_dispatcher = ApplicationFactory.create_game_engine()

providers = list(llm_dispatcher.provider_map.keys())
print(f"Discovered Providers: {providers}")

# We expect phi, azure, human, mock (always there), default, azure_openai (legacy alias)
expected = ["phi", "azure", "human", "mock", "default", "azure_openai"]
missing = [e for e in expected if e not in providers]
if not missing:
    print("SUCCESS: All expected providers found.")
else:
    print(f"FAILURE: Missing providers: {missing}")

print("\n--- Verifying Player Config ---")
cfg = llm_dispatcher.provider_config_map
print(f"PLAYER_001 provider: {cfg.get('PLAYER_001')}")
print(f"PLAYER_HUMAN provider: {cfg.get('PLAYER_HUMAN')}")

if cfg.get("PLAYER_HUMAN", {}).get("provider_key") == "human":
    print("SUCCESS: PLAYER_HUMAN correctly mapped to human.")
else:
    print("FAILURE: PLAYER_HUMAN mapping incorrect.")

if cfg.get("PLAYER_001", {}).get("provider_key") == "human":
    print("SUCCESS: PLAYER_001 correctly overridden to human.")
else:
    print("FAILURE: PLAYER_001 override failed.")

print("\n--- Verifying Human Turn Pause ---")
import asyncio
from backend.turn_orchestrator import TurnOrchestrator

orchestrator = TurnOrchestrator(game_engine, llm_dispatcher, gm, judge)

async def test_turn():
    # Advance 5 days. Should stop at day 1 because PLAYER_001 is human.
    result = await orchestrator.run_full_tick_cycle(agent_ids=["PLAYER_001"], days=5)
    ticks = result.get("ticks", [])
    print(f"Number of ticks run: {len(ticks)}")
    if len(ticks) == 1:
        player_res = ticks[0]["agents"]["PLAYER_001"]["player"]
        if player_res.get("status") == "awaiting_human_input":
            print("SUCCESS: Loop paused for human player.")
        else:
            print(f"FAILURE: Incorrect player status: {player_res.get('status')}")
    else:
        print(f"FAILURE: Expected 1 tick, got {len(ticks)}")

asyncio.run(test_turn())
