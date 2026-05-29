"""
examples/memory_failure_demo.py — Phase 8 Memory Failure Demonstration

Demonstrates that context is lost when a new session is used per turn.
Now powered by the self-hosted Gemma model via the LLM abstraction layer
— no Gemini API keys required.
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


async def run_memory_failure_demonstration():
    print("\n" + "="*80)
    print("\033[91m\033[1mSCENARIO B: AGENT WITHOUT MEMORY (FAILURE DEMONSTRATION)\033[0m")
    print(f"\033[90mProvider: {LLM_PROVIDER} | Model: {LLM_MODEL} | Endpoint: {OLLAMA_BASE_URL}\033[0m")
    print("="*80)

    # Turn 1: Initial Discovery (Session 1)
    session_id_1 = "failure_session_turn_1"
    print(f"\n\033[94m\033[1m[Turn 1] User:\033[0m I am a B.Tech student in Tamil Nadu. Family income ₹2.5 lakh. Marks 91%. Find scholarships for me. (Session: {session_id_1})")
    print("\033[90mOrchestrator processing turn with a fresh session...\033[0m")
    t1_response = await handle_coordinator_turn(
        "I am a B.Tech student in Tamil Nadu. Family income ₹2.5 lakh. Marks 91%. Find scholarships for me.",
        session_id=session_id_1
    )
    print(f"\n\033[95m\033[1m[Turn 1] Agent Response:\033[0m\n{t1_response}")
    print("-" * 80)

    # Turn 2: Filter by Preference (NEW Session — context lost)
    session_id_2 = "failure_session_turn_2"
    print(f"\n\033[94m\033[1m[Turn 2] User:\033[0m I am not interested in private scholarships. (Session: {session_id_2})")
    print("\033[90mOrchestrator processing turn with a NEW session...\033[0m")
    t2_response = await handle_coordinator_turn(
        "I am not interested in private scholarships.",
        session_id=session_id_2
    )
    print(f"\n\033[95m\033[1m[Turn 2] Agent Response:\033[0m\n{t2_response}")
    print("-" * 80)

    # Turn 3: Ask Documents (NEW Session — context lost again)
    session_id_3 = "failure_session_turn_3"
    print(f"\n\033[94m\033[1m[Turn 3] User:\033[0m Tell me the required documents. (Session: {session_id_3})")
    print("\033[90mOrchestrator processing turn with a NEW session...\033[0m")
    t3_response = await handle_coordinator_turn(
        "Tell me the required documents.",
        session_id=session_id_3
    )
    print(f"\n\033[95m\033[1m[Turn 3] Agent Response:\033[0m\n{t3_response}")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_memory_failure_demonstration())
