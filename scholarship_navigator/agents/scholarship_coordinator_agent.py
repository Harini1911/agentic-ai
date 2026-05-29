import os
import sys
import json
import asyncio
from typing import Dict, Any

from google.adk.agents import Agent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from workflows.loop_workflow import run_loop_workflow, get_missing_fields
from agents.scholarship_router_agent import root_agent as router_agent
from agents.school_agent import school_agent
from agents.ug_agent import ug_agent
from agents.pg_agent import pg_agent
from agents.phd_agent import phd_agent
from agents.international_agent import international_agent

# Define the central ScholarshipCoordinatorAgent that coordinates other workflows
scholarship_coordinator_agent = Agent(
    name="ScholarshipCoordinatorAgent",
    model="gemini-2.5-flash",
    description="Top-level coordinator agent that manages and orchestrates the scholarship workflows.",
    instruction="""
You are the ScholarshipCoordinatorAgent. Your sole responsibility is to oversee and orchestrate the scholarship discovery workflows.

You manage the following phases:
1. **Loop Workflow**: Intercepts the request and completes missing profile fields interactively.
2. **Router Workflow**: Evaluates the completed profile and routes to the correct specialist domain.
3. **Sequential & Parallel Workflow**: Triggers the selected category-specific search pipeline to validate, execute concurrent searches, and aggregate the recommendations.

You represent the single unified entry point for all scholarship requests.
"""
)

async def run_coordinator_workflow(student_profile: dict):
    """
    Orchestrates the entire Scholarship Navigator system.
    Step 1: Check completeness / Run Loop Workflow if needed.
    Step 2: Run Router Workflow logic to select domain.
    Step 3: Execute Sequential Workflow & Parallel search for selected domain.
    """
    print("\n" + "=" * 60)
    print("\033[95m\033[1m[ScholarshipCoordinatorAgent] Initiating Orchestration...\033[0m")
    print("=" * 60)

    # Step 1: Check completeness / Loop Workflow
    print("\033[93m[Step 1] Checking profile completeness...\033[0m")
    missing = get_missing_fields(student_profile)
    if missing:
        print(f"\033[93mProfile is incomplete. Missing fields: {missing}. Invoking Loop Workflow...\033[0m")
        student_profile = await run_loop_workflow(student_profile)
    else:
        print("\033[92mProfile is already complete. Skipping Loop Workflow.\033[0m")

    # Step 2: Router Workflow
    print("\n\033[93m[Step 2] Invoking Router Workflow to select domain...\033[0m")
    country = student_profile.get("country_preference", "India").strip().lower()
    edu = student_profile.get("education_level", "").strip().lower()
    
    if "india" not in country:
        route = "InternationalScholarshipAgent"
    elif any(c in edu for c in ["class 6", "class 7", "class 8", "class 9", "class 10", "class 11", "class 12"]):
        route = "SchoolScholarshipAgent"
    elif any(c in edu for c in ["b.tech", "btech", "b.e", "be", "b.sc", "bsc", "ba", "b.com", "bcom"]):
        route = "UGScholarshipAgent"
    elif any(c in edu for c in ["m.tech", "mtech", "mba", "m.sc", "msc", "ma"]):
        route = "PGScholarshipAgent"
    elif any(c in edu for c in ["phd", "doctorate", "research"]):
        route = "PhDScholarshipAgent"
    else:
        route = "UGScholarshipAgent" # Default fallback
        
    print(f"\033[92mRouter selected domain agent: {route}\033[0m")

    # Step 3: Sequential & Parallel Workflow execution
    print(f"\n\033[93m[Step 3] Executing Sequential Workflow for {route}...\033[0m")
    
    agent_map = {
        "SchoolScholarshipAgent": school_agent,
        "UGScholarshipAgent": ug_agent,
        "PGScholarshipAgent": pg_agent,
        "PhDScholarshipAgent": phd_agent,
        "InternationalScholarshipAgent": international_agent
    }
    selected_agent = agent_map.get(route, ug_agent)

    # Initialize ADK Runner for the selected Sequential Agent
    session_service = InMemorySessionService()
    runner = Runner(
        agent=selected_agent,
        app_name="scholarship_navigator",
        session_service=session_service
    )
    
    session_id = "coordinator_session"
    user_id = "coordinator_user"
    
    await session_service.create_session(
        app_name="scholarship_navigator",
        user_id=user_id,
        session_id=session_id
    )
    
    query = f"Here is my student profile:\n{json.dumps(student_profile, indent=2)}"
    content = types.Content(parts=[types.Part.from_text(text=query)])
    
    print(f"\033[93mRunning search and aggregation pipelines for {route}...\033[0m")
    print("\033[92m" + "-" * 60 + "\033[0m")
    
    async for event in runner.run_async(
        session_id=session_id,
        user_id=user_id,
        new_message=content
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
                    
    print("\n\033[92m" + "-" * 60 + "\033[0m")
    print("\033[92m[Success] Scholarship discovery orchestration complete.\033[0m\n")
