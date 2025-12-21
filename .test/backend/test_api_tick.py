import asyncio
import httpx
import sys

async def run_test():
    print("[TEST] Starting test...")
    async with httpx.AsyncClient(base_url="http://localhost:9000", timeout=300.0) as client:
        # We don't call start_game anymore, advance_day should handle it
        print("[TEST] Advancing day (should auto-start)...")
        resp = await client.post("/api/advance_day", json={"days": 1, "agent_ids": ["PLAYER_TEST_001"]})
        print(f"[TEST] Response: {resp.status_code}")
        if resp.status_code == 200:
            print("[TEST] Success!")
            data = resp.json()
            # Check if PLAYER_TEST_001 is in the results
            ticks = data.get("ticks", [])
            if ticks and "PLAYER_TEST_001" in ticks[0].get("agents", {}):
                print("[TEST] PLAYER_TEST_001 found in tick results.")
            else:
                print("[TEST] PLAYER_TEST_001 NOT found in tick results.")
        else:
            print(f"[TEST] Failed: {resp.text}")

if __name__ == "__main__":
    asyncio.run(run_test())
