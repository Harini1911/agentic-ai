import os
import sys
from typing import Dict, Any, List, Tuple

# Add parent directory for modular importing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_FIELDS = [
    "education_level",
    "annual_income",
    "marks_percentage",
    "state",
    "country_preference"
]

def get_missing_fields(profile: Dict[str, Any]) -> List[str]:
    """Detects missing fields in the student profile."""
    missing = []
    for field in REQUIRED_FIELDS:
        val = profile.get(field)
        if val is None or str(val).strip() == "" or val == "None":
            missing.append(field)
    return missing

def validate_input(field: str, value: str) -> Tuple[bool, Any, str]:
    """
    Validates and normalizes user input based on Phase 6 specifications.

    Returns:
        (is_valid, normalized_value, error_message)
    """
    val_str = str(value).strip()
    if not val_str:
        return False, None, "Input cannot be empty."

    if field == "annual_income":
        try:
            val = float(val_str.replace(",", ""))
            if val < 0:
                return False, None, "Please enter a positive numeric income."
            return True, val, ""
        except ValueError:
            return False, None, "Please enter a valid numeric income."

    elif field == "marks_percentage":
        try:
            val = float(val_str)
            if 0 <= val <= 100:
                return True, val, ""
            return False, None, "Please enter a valid marks percentage between 0 and 100."
        except ValueError:
            return False, None, "Please enter a valid numeric percentage between 0 and 100."

    elif field == "education_level":
        cleaned = val_str.lower().replace(".", "")
        supported_levels = ["class 12", "b.tech", "b.e.", "b.sc.", "ba", "b.com.", "m.tech", "mba", "m.sc.", "ma", "phd", "doctorate", "research scholar"]
        for i in range(6, 12):
            supported_levels.append(f"class {i}")
            
        for level in supported_levels:
            if level.replace(".", "") in cleaned or cleaned in level.replace(".", ""):
                if "class 12" in cleaned: return True, "Class 12", ""
                if "btech" in cleaned or "be" in cleaned: return True, "B.Tech", ""
                if "mba" in cleaned: return True, "MBA", ""
                if "phd" in cleaned: return True, "PhD", ""
                return True, val_str.title(), ""
        return False, None, "Please enter a supported education level (e.g. Class 12, B.Tech, MBA, PhD)."

    elif field == "country_preference":
        cleaned = val_str.lower()
        if "india" in cleaned:
            return True, "India", ""
        if "international" in cleaned or "abroad" in cleaned or "outside" in cleaned:
            return True, "International", ""
        return False, None, "Please specify either 'India' or 'International'."

    elif field == "state":
        if len(val_str) > 1:
            return True, val_str.title(), ""
        return False, None, "Please enter a valid state name."

    return True, val_str, ""

def get_field_prompt(field: str) -> str:
    """Returns the custom prompt for the missing field."""
    prompts = {
        "education_level": "What is your current education level?\n\nExamples:\nClass 12\nB.Tech\nMBA\nPhD",
        "annual_income": "What is your annual family income in INR?",
        "marks_percentage": "What is your latest percentage or CGPA?",
        "state": "Which state are you currently studying in?",
        "country_preference": "Are you looking for scholarships in India or internationally?"
    }
    return prompts.get(field, f"Please enter your {field}:")

async def ask_completion_agent(profile: Dict[str, Any]) -> str:
    """Uses ProfileCompletionAgent via ADK to get the next question for missing fields."""
    try:
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
        from agents.profile_completion_agent import profile_completion_agent

        session_service = InMemorySessionService()
        runner = Runner(
            agent=profile_completion_agent,
            app_name="profile_completion",
            session_service=session_service
        )
        session_id = "completion_session"
        user_id = "completion_user"
        await session_service.create_session("profile_completion", user_id, session_id)
        
        # Format the query with the current profile
        query = f"Current profile: {json.dumps(profile)}"
        content = types.Content(parts=[types.Part.from_text(text=query)])
        
        response_text = ""
        async for event in runner.run_async(session_id=session_id, user_id=user_id, new_message=content):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
        return response_text.strip()
    except Exception as e:
        # Robust fallback using get_field_prompt in case of any issues with the runner
        missing = get_missing_fields(profile)
        if missing:
            return get_field_prompt(missing[0])
        return ""

async def run_loop_workflow(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the Loop Workflow Pattern.
    Repeatedly checks for missing fields, generates questions using the ProfileCompletionAgent,
    receives user input, validates and normalizes it, and updates the profile until complete.
    """
    import json
    
    missing_fields = get_missing_fields(profile)
    if not missing_fields:
        return profile

    print("\n" + "=" * 60)
    print("\033[93m\033[1m[Profile Incomplete] Launching Profile Completion Loop...\033[0m")
    print("=" * 60)
    
    iteration = 1
    while True:
        missing_fields = get_missing_fields(profile)
        if not missing_fields:
            break
            
        print(f"\n\033[95m--- Iteration {iteration} ---\033[0m")
        print(f"\033[94m[Detected Missing Fields]:\033[0m {', '.join(missing_fields)}")
        
        # Get the first missing field
        target_field = missing_fields[0]
        
        # Generate the follow-up question using the ProfileCompletionAgent
        print("\033[90mProfileCompletionAgent generating question...\033[0m")
        question = await ask_completion_agent(profile)
        
        # If the generated question is empty/invalid, use fallback
        if not question:
            question = get_field_prompt(target_field)
            
        print(f"\n\033[96m\033[1m{question}\033[0m")
        
        # Prompt user for input
        try:
            user_input = input("\033[92mYour Answer: \033[0m").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\033[91mProfile completion cancelled by user.\033[0m")
            sys.exit(0)
            
        # Validate and normalize the input
        is_valid, normalized_value, error_msg = validate_input(target_field, user_input)
        
        if not is_valid:
            print(f"\033[91mError: {error_msg}\033[0m")
            # Loop continues, re-prompting for the same field
            continue
        
        # Update profile with normalized value
        profile[target_field] = normalized_value
        print(f"\033[92m✓ Successfully updated {target_field} -> {normalized_value}\033[0m")
        
        iteration += 1

    print("\n" + "=" * 60)
    print("\033[92m\033[1m[Profile Fully Completed] Loop exited successfully.\033[0m")
    print("=" * 60 + "\n")
    
    return profile

