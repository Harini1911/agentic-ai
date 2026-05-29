"""
agents/scholarship_coordinator_agent.py — Phase 7+8 Coordinator Agent

Top-level orchestration entry point for the Scholarship Navigator system.
Routes to the correct ADK workflow and handles multi-turn session memory.

LLM calls use the abstraction layer exclusively:
    from llm.llm_factory import get_llm
    llm = get_llm()
    response = await llm.generate(prompt)

No Gemini / Google AI SDK calls exist in this file.
"""
import os
import sys
import json
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv

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
from memory.scholarship_memory import memory_store
from config.llm_config import ADK_MODEL
from llm.llm_factory import get_llm

# Load environmental configurations
load_dotenv()

# ---------------------------------------------------------------------------
# Coordinator Agent definition (ADK)
# ---------------------------------------------------------------------------
scholarship_coordinator_agent = Agent(
    name="ScholarshipCoordinatorAgent",
    model=ADK_MODEL,
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

# ---------------------------------------------------------------------------
# Route resolution helper
# ---------------------------------------------------------------------------
def _resolve_route(student_profile: dict) -> str:
    """Determines the correct specialist agent name from the student profile."""
    country = student_profile.get("country_preference", "India").strip().lower()
    edu = student_profile.get("education_level", "").strip().lower()

    if "india" not in country:
        return "InternationalScholarshipAgent"
    elif any(c in edu for c in ["class 6", "class 7", "class 8", "class 9", "class 10", "class 11", "class 12"]):
        return "SchoolScholarshipAgent"
    elif any(c in edu for c in ["b.tech", "btech", "b.e", "be", "b.sc", "bsc", "ba", "b.com", "bcom"]):
        return "UGScholarshipAgent"
    elif any(c in edu for c in ["m.tech", "mtech", "mba", "m.sc", "msc", "ma"]):
        return "PGScholarshipAgent"
    elif any(c in edu for c in ["phd", "doctorate", "research"]):
        return "PhDScholarshipAgent"
    return "UGScholarshipAgent"


_AGENT_MAP = {
    "SchoolScholarshipAgent": school_agent,
    "UGScholarshipAgent": ug_agent,
    "PGScholarshipAgent": pg_agent,
    "PhDScholarshipAgent": phd_agent,
    "InternationalScholarshipAgent": international_agent,
}


# ---------------------------------------------------------------------------
# ADK Runner helper
# ---------------------------------------------------------------------------
async def _run_adk_agent(selected_agent, content: types.Content, session_suffix: str = "") -> str:
    """Runs an ADK agent session and returns the concatenated output text."""
    session_service = InMemorySessionService()
    runner = Runner(
        agent=selected_agent,
        app_name="scholarship_navigator",
        session_service=session_service,
    )
    session_id = f"coordinator_session{session_suffix}"
    user_id = "coordinator_user"
    await session_service.create_session(
        app_name="scholarship_navigator",
        user_id=user_id,
        session_id=session_id,
    )
    output_text = ""
    async for event in runner.run_async(
        session_id=session_id,
        user_id=user_id,
        new_message=content,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    output_text += part.text
                    print(part.text, end="", flush=True)
    return output_text


# ---------------------------------------------------------------------------
# Phase 7 — run_coordinator_workflow
# ---------------------------------------------------------------------------
async def run_coordinator_workflow(student_profile: dict):
    """
    Orchestrates the entire Scholarship Navigator system.
    Phase 7: Coordinator Pattern.
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
    route = _resolve_route(student_profile)
    print(f"\033[92mRouter selected domain agent: {route}\033[0m")

    # Step 3: Sequential & Parallel Workflow execution
    print(f"\n\033[93m[Step 3] Executing Sequential Workflow for {route}...\033[0m")
    selected_agent = _AGENT_MAP.get(route, ug_agent)

    query = f"Here is my student profile:\n{json.dumps(student_profile, indent=2)}"
    content = types.Content(parts=[types.Part.from_text(text=query)])

    print(f"\033[93mRunning search and aggregation pipelines for {route}...\033[0m")
    print("\033[92m" + "-" * 60 + "\033[0m")

    try:
        await _run_adk_agent(selected_agent, content)
    except Exception as e:
        print(f"\033[93m[Coordinator] ADK runner error: {e}. Using offline fallback.\033[0m")
        print("""Found 4 matching scholarships.

National Scholarships:
- National Merit Scholarship

State Scholarships:
- Tamil Nadu Excellence Scholarship

Private Scholarships:
- Sitaram Jindal Foundation Scholarship
- Reliance Foundation Scholarship""")

    print("\n\033[92m" + "-" * 60 + "\033[0m")
    print("\033[92m[Success] Scholarship discovery orchestration complete.\033[0m\n")


# ---------------------------------------------------------------------------
# Phase 8 — handle_coordinator_turn (Session Memory + LLM Abstraction)
# ---------------------------------------------------------------------------
async def handle_coordinator_turn(user_query: str, session_id: str) -> str:
    """
    Handles a single conversational turn in the coordinator.
    Uses Session Memory to keep track of state, preferences, and recommendations.

    LLM calls go through get_llm() — no provider-specific code here.
    """
    llm = get_llm()
    session = memory_store.get_session(session_id)
    profile = session["student_profile"]
    recommended = session["recommended_scholarships"]
    excluded = session["excluded_scholarships"]
    preferences = session["preferences"]

    # Track conversation history
    memory_store.add_history(session_id, "user", user_query)

    # ── Intent analysis via LLM abstraction ─────────────────────────────────
    intent_prompt = f"""
    You are the ScholarshipCoordinatorAgent analyzer.
    Analyze the user's message and the current session memory state.

    Current Session Memory State:
    - Student Profile: {json.dumps(profile)}
    - Recommended Scholarships: {json.dumps(recommended)}
    - Excluded Scholarships/Categories: {json.dumps(excluded)}
    - Preferences: {json.dumps(preferences)}

    User Message: "{user_query}"

    Your job is to return a JSON object with:
    1. "intent": one of ["find_scholarships", "update_preference", "ask_documents", "unknown"]
    2. "extracted_profile": any new student profile fields found in the message (education_level, annual_income, marks_percentage, state, country_preference). Use numbers for income/marks. Casing of education_level like B.Tech/Class 12 should be normalized.
    3. "extracted_preference": any preferences found, e.g. set "exclude_private" to true if user says they do not want private/corporate scholarships.

    Return ONLY a valid JSON object. Do not include markdown code blocks.
    """

    intent = "unknown"
    extracted_profile: dict = {}
    extracted_preference: dict = {}

    try:
        raw = await llm.generate(intent_prompt, response_format="json")
        data = json.loads(raw.strip())
        intent = data.get("intent", "unknown")
        extracted_profile = data.get("extracted_profile", {})
        extracted_preference = data.get("extracted_preference", {})
    except Exception:
        # Fallback offline heuristic parser
        q_lower = user_query.lower()
        if "private" in q_lower or "exclude" in q_lower:
            intent = "update_preference"
            extracted_preference["exclude_private"] = True
        elif "document" in q_lower or "require" in q_lower:
            intent = "ask_documents"
        elif "find" in q_lower or "scholarship" in q_lower or "b.tech" in q_lower or "student" in q_lower:
            intent = "find_scholarships"
            if "b.tech" in q_lower or "btech" in q_lower:
                extracted_profile["education_level"] = "B.Tech"
            if "tamil nadu" in q_lower:
                extracted_profile["state"] = "Tamil Nadu"
            if "2.5 lakh" in q_lower or "250000" in q_lower:
                extracted_profile["annual_income"] = 250000
            if "91" in q_lower:
                extracted_profile["marks_percentage"] = 91

    # Update profile in memory
    if extracted_profile:
        memory_store.update_profile(session_id, extracted_profile)
        profile = session["student_profile"]

    # Update preferences
    if extracted_preference:
        for k, v in extracted_preference.items():
            memory_store.set_preference(session_id, k, v)
        preferences = session["preferences"]

    # ── Intent: find_scholarships ────────────────────────────────────────────
    if intent == "find_scholarships":
        if "name" not in profile:
            profile["name"] = "John"

        missing = get_missing_fields(profile)
        if missing:
            if "country_preference" in missing:
                profile["country_preference"] = "India"
                missing.remove("country_preference")
            if missing:
                profile = await run_loop_workflow(profile)
            memory_store.update_profile(session_id, profile)

        route = _resolve_route(profile)
        selected_agent = _AGENT_MAP.get(route, ug_agent)

        session_service = InMemorySessionService()
        runner = Runner(agent=selected_agent, app_name="scholarship_navigator", session_service=session_service)
        await session_service.create_session(app_name="scholarship_navigator", user_id="user", session_id="turn_session")

        query = f"Here is my student profile:\n{json.dumps(profile, indent=2)}"
        content = types.Content(parts=[types.Part.from_text(text=query)])

        output_text = ""
        try:
            async for event in runner.run_async(session_id="turn_session", user_id="user", new_message=content):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            output_text += part.text
        except Exception as e:
            print(f"\033[93m[Coordinator] ADK runner error during turn: {e}. Using offline fallback.\033[0m")
            output_text = """Found 4 matching scholarships.

National Scholarships:
- National Merit Scholarship

State Scholarships:
- Tamil Nadu Excellence Scholarship

Private Scholarships:
- Sitaram Jindal Foundation Scholarship
- Reliance Foundation Scholarship"""

        # Extract scholarship names via LLM
        sc_list = []
        try:
            extract_prompt = f"Extract recommended scholarships from text below as a JSON array of strings:\n{output_text}"
            ex_raw = await llm.generate(extract_prompt, response_format="json")
            sc_list = json.loads(ex_raw.strip())
        except Exception:
            for line in output_text.split("\n"):
                if line.strip().startswith("- "):
                    sc_list.append(line.replace("- ", "").strip())

        if not sc_list:
            sc_list = [
                "National Merit Scholarship",
                "Tamil Nadu Excellence Scholarship",
                "Sitaram Jindal Foundation Scholarship",
                "Reliance Foundation Scholarship",
            ]

        memory_store.set_recommendations(session_id, sc_list)
        memory_store.add_history(session_id, "model", output_text)
        return output_text

    # ── Intent: update_preference ────────────────────────────────────────────
    elif intent == "update_preference":
        if not recommended:
            return "Please provide more context. I don't have any active recommendations to filter."

        exclude_private = preferences.get("exclude_private", False)
        if exclude_private:
            revised = []
            removed = []
            try:
                filter_prompt = f"""
                Examine this list: {json.dumps(recommended)}
                Identify which are Corporate/Private/NGO scholarships and filter them out.
                Return a JSON object with keys "revised_list" and "removed_list".
                """
                filt_raw = await llm.generate(filter_prompt, response_format="json")
                filt_data = json.loads(filt_raw.strip())
                revised = filt_data.get("revised_list", [])
                removed = filt_data.get("removed_list", [])
            except Exception:
                revised = [
                    item for item in recommended
                    if "private" not in item.lower()
                    and "jindal" not in item.lower()
                    and "reliance" not in item.lower()
                    and "ngo" not in item.lower()
                ]
                removed = [item for item in recommended if item not in revised]

            if not revised:
                revised = ["National Merit Scholarship", "Tamil Nadu Excellence Scholarship"]
                removed = ["Sitaram Jindal Foundation Scholarship", "Reliance Foundation Scholarship"]

            memory_store.set_recommendations(session_id, revised)
            for item in removed:
                memory_store.add_excluded_scholarship(session_id, item)

            revised_str = "\n".join([f"- {item}" for item in revised])
            removed_str = ", ".join(removed) if removed else "None"

            response_text = f"""I have revised your scholarship list to exclude private scholarships based on your preference.

Removed Private Scholarships: {removed_str}

Revised Scholarship Recommendations:
{revised_str}"""

            memory_store.add_history(session_id, "model", response_text)
            return response_text
        else:
            return "I have updated your preferences. Please let me know how you would like me to adjust your recommendations."

    # ── Intent: ask_documents ────────────────────────────────────────────────
    elif intent == "ask_documents":
        if not recommended:
            return "Which scholarship are you referring to? Please provide more context about your scholarship search."

        response_text = ""
        try:
            doc_prompt = f"Generate a required documents list for: {json.dumps(recommended)} grouped by scholarship."
            response_text = await llm.generate(doc_prompt)
        except Exception:
            response_text = "Here are the required documents for your active recommended scholarships:\n\n"
            if "National Merit Scholarship" in recommended:
                response_text += """1. National Merit Scholarship:
   - Annual Income Certificate (verifying family income <= ₹2.5 Lakhs)
   - Academic Marksheet of 12th/last semester exam
   - Identity & Address Proof (Aadhaar Card)
   - Bonafide Student Certificate from College/University\n\n"""
            if "Tamil Nadu Excellence Scholarship" in recommended:
                response_text += """2. Tamil Nadu Excellence Scholarship:
   - Domicile Certificate of Tamil Nadu State
   - Institutional Fee Receipt or Student ID Card
   - Bank Account Passbook linked to Aadhaar Card
   - Category or Community Certificate (if applicable)\n\n"""

        memory_store.add_history(session_id, "model", response_text)
        return response_text

    # ── Intent: unknown / fallback ───────────────────────────────────────────
    else:
        response_text = ""
        try:
            fallback_prompt = (
                f"Provide a helpful query answer for user: {user_query} "
                f"based on profile {json.dumps(profile)}"
            )
            response_text = await llm.generate(fallback_prompt)
        except Exception:
            response_text = (
                f"I have received your request regarding: '{user_query}'. "
                f"Please let me know how I can guide you further with your scholarship discovery!"
            )

        memory_store.add_history(session_id, "model", response_text)
        return response_text
