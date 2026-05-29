"""
examples/memory_success_demo.py — Phase 8 Memory Success Demonstration

Demonstrates that session memory persists across multiple turns within the
same session. Now powered by the self-hosted Gemma model via the LLM
abstraction layer — no Gemini API keys required.
"""
import sys
import os
import asyncio

# Setup python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load environment configuration (.env in scholarship_navigator/)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from config.llm_config import LLM_PROVIDER, OLLAMA_BASE_URL, LLM_MODEL
from agents.scholarship_coordinator_agent import handle_coordinator_turn
from memory.scholarship_memory import memory_store


async def run_memory_success_demonstration():
    session_id = "success_demo_session"

    print("\n" + "="*80)
    print("\033[92m\033[1mSCENARIO A: AGENT WITH MEMORY (SUCCESS DEMONSTRATION)\033[0m")
    print(f"\033[90mProvider: {LLM_PROVIDER} | Model: {LLM_MODEL} | Endpoint: {OLLAMA_BASE_URL}\033[0m")
    print("="*80)

    # Turn 1: Initial Discovery
    print("\n\033[94m\033[1m[Turn 1] User:\033[0m I am a B.Tech student in Tamil Nadu. Family income ₹2.5 lakh. Marks 91%. Find scholarships for me.")
    print("\033[93mOrchestrator processing turn with session memory persistence...\033[0m")
    t1_response = await handle_coordinator_turn(
        "I am a B.Tech student in Tamil Nadu. Family income ₹2.5 lakh. Marks 91%. Find scholarships for me.",
        session_id=session_id
    )
    print(f"\n\033[95m\033[1m[Turn 1] Agent Response:\033[0m\n{t1_response}")
    print("-" * 80)

    # Turn 2: Filter by Preference
    print("\n\033[94m\033[1m[Turn 2] User:\033[0m I am not interested in private scholarships.")
    print("\033[93mOrchestrator processing turn with session memory persistence...\033[0m")
    t2_response = await handle_coordinator_turn(
        "I am not interested in private scholarships.",
        session_id=session_id
    )
    print(f"\n\033[95m\033[1m[Turn 2] Agent Response:\033[0m\n{t2_response}")
    print("-" * 80)

    # Turn 3: Ask Documents for Kept Recommendations
    print("\n\033[94m\033[1m[Turn 3] User:\033[0m Tell me the required documents.")
    print("\033[93mOrchestrator processing turn with session memory persistence...\033[0m")
    t3_response = await handle_coordinator_turn(
        "Tell me the required documents.",
        session_id=session_id
    )
    print(f"\n\033[95m\033[1m[Turn 3] Agent Response:\033[0m\n{t3_response}")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_memory_success_demonstration())
