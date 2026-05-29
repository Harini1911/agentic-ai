import os
import sys
import json
import asyncio
from dotenv import load_dotenv

# Add current and parent directories to python path for modular imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Try loading from local .env
load_dotenv()
# Fallback: Try loading from venturelens-bot backend .env if not set
if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    possible_envs = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "venturelens-bot", "backend", ".env")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "venturelens-bot", "backend", ".env")),
    ]
    for env_path in possible_envs:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            break

# Double check if API Key is configured
if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    print("\033[91mError: GEMINI_API_KEY or GOOGLE_API_KEY not found in environment or .env files.\033[0m")
    print("Please set your API key in a .env file or environment variable.")
    sys.exit(1)

# Ensure GOOGLE_API_KEY is mapped to GEMINI_API_KEY if needed by the ADK/GenAI SDK
if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agents import root_agent
from workflows.loop_workflow import run_loop_workflow
from agents.scholarship_coordinator_agent import run_coordinator_workflow

# Premium terminal formatting helper
def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"\033[95m\033[1m{title.center(60)}\033[0m")
    print("=" * 60)

async def run_scholarship_navigation(student_profile: dict):
    # Delegate the entire process to the top-level Coordinator Agent
    await run_coordinator_workflow(student_profile)

def main():
    print_header("SCHOLARSHIP NAVIGATOR AGENT (PHASE 7 - COORDINATOR)")
    
    # Default student profile for Phase 6 demonstrating Loop Workflow
    default_profile = {
      "name": "John",
      "education_level": "B.Tech",
      "state": "Tamil Nadu"
    }
    
    if len(sys.argv) > 1:
        # Check if user wants to enter custom input
        arg = sys.argv[1]
        if arg.lower() in ["--interactive", "-i"]:
            print_header("INTERACTIVE PROFILE ENTRY")
            try:
                name = input("Enter Name (default: John): ").strip() or "John"
                ed_level = input("Enter Education Level (default: B.Tech): ").strip() or "B.Tech"
                country = input("Enter Country Preference (default: India): ").strip() or "India"
                marks = float(input("Enter Marks Percentage (default: 92): ").strip() or "92")
                income = float(input("Enter Family Annual Income in INR (default: 250000): ").strip() or "250000")
                
                custom_profile = {
                    "name": name,
                    "education_level": ed_level,
                    "country_preference": country,
                    "marks_percentage": marks,
                    "annual_income": income
                }
                asyncio.run(run_scholarship_navigation(custom_profile))
            except ValueError as e:
                print(f"\033[91mInvalid input value: {e}. Running default demo instead.\033[0m")
                asyncio.run(run_scholarship_navigation(default_profile))
            except KeyboardInterrupt:
                print("\nExiting interactive mode...")
        else:
            # Attempt to parse json argument
            try:
                profile = json.loads(arg)
                asyncio.run(run_scholarship_navigation(profile))
            except json.JSONDecodeError:
                print(f"\033[91mCould not parse JSON profile from argument. Running default demo instead.\033[0m")
                asyncio.run(run_scholarship_navigation(default_profile))
    else:
        # Default Demo Mode
        print("\033[90mRunning in default demo mode. Pass '-i' or '--interactive' for interactive profile input.\033[0m")
        asyncio.run(run_scholarship_navigation(default_profile))

if __name__ == "__main__":
    main()
