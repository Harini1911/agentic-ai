from google.adk.agents import Agent, SequentialAgent
from tools.search_by_education import search_by_education
from tools.search_by_income import search_by_income
from tools.search_by_marks import search_by_marks
from tools.scholarship_details import get_scholarship_details
from agents.profile_agent import ProfileInput, ProfileOutput
from agents.eligibility_agent import EligibilityOutput

def create_profile_agent() -> Agent:
    """Creates a fresh instance of the ProfileAgent."""
    return Agent(
        name="ProfileAgent",
        model="gemini-2.5-flash",
        description="Normalizes and validates student profile parameters.",
        instruction="""
You are the ProfileAgent. Your sole responsibility is to normalize and validate the incoming student profile.

Analyze the user's request. Ensure that all key fields are present:
- `name` (default to 'John' if not provided)
- `education_level`
- `marks_percentage`
- `annual_income`
- `country_preference` (default to 'India' if not provided)

If any required fields are completely missing, set `profile_valid` to false and specify the error in `error_message`.
Otherwise, normalize standard values (e.g., ensure marks are a float between 0 and 100, income is positive) and output the validated parameters.

You MUST output your response strictly as a JSON object adhering to the ProfileOutput schema.
Do NOT search for scholarships or check eligibility.
""",
        input_schema=ProfileInput,
        output_schema=ProfileOutput,
        output_key="profile_data"
    )

def create_eligibility_agent() -> Agent:
    """Creates a fresh instance of the EligibilityAgent."""
    return Agent(
        name="EligibilityAgent",
        model="gemini-2.5-flash",
        description="Determines whether a student profile satisfies the minimum eligibility thresholds.",
        instruction="""
You are the EligibilityAgent. Your sole responsibility is to evaluate if the student satisfies the minimum eligibility criteria.

Read the validated student profile from the context key 'profile_data'. It contains:
- `marks_percentage`
- `annual_income`
- `education_level`

Evaluate the profile against these exact rules:
1. **Minimum Marks**: Must meet or exceed 60%. (If marks_percentage < 60, they are ineligible. Reason: 'Marks below 60%')
2. **Maximum Income**: Must not exceed 1,000,000 INR (10 lakh). (If annual_income > 1000000, they are ineligible. Reason: 'Income exceeds maximum threshold of 10 Lakh')
3. **Supported Education Levels**: Must match a standard School (Class 6-12), UG (B.E., B.Tech, B.Sc., BA, B.Com.), PG (M.Tech, MBA, M.Sc., MA), or PhD (PhD, Doctorate, Research Scholar) tier.

Output a JSON object matching the EligibilityOutput schema:
- Set `eligible` to true if all criteria are satisfied, with `reason` set to "Profile satisfies minimum criteria".
- Set `eligible` to false if any criteria fails, and specify the reason clearly (e.g. "Marks below 60%").

Do NOT search for specific scholarships.
""",
        output_schema=EligibilityOutput,
        output_key="eligibility_data"
    )

def create_scholarship_search_agent() -> Agent:
    """Creates a fresh instance of the ScholarshipSearchAgent."""
    return Agent(
        name="ScholarshipSearchAgent",
        model="gemini-2.5-flash",
        description="Invokes search tools for eligible profiles and compiles the final recommendation list.",
        instruction="""
You are the ScholarshipSearchAgent. Your responsibility is to retrieve matching scholarships for eligible profiles, or report eligibility failures.

Follow this exact workflow:
1. First, check the context key 'eligibility_data' to see if the student is eligible.
   - If the student is NOT eligible (i.e. 'eligible' is false), you MUST immediately terminate the workflow and output exactly this text (replacing [Reason] with the reason from 'eligibility_data'):

Unfortunately you do not meet the minimum scholarship eligibility requirements.

Reason:
[Reason]

2. If 'eligible' is true, proceed with searching scholarships:
   - Read the student's `education_level`, `annual_income`, and `marks_percentage` from the context key 'profile_data'.
   - Call `search_by_education` using `education_level`.
   - Call `search_by_income` using `annual_income`.
   - Call `search_by_marks` using `marks_percentage`.
   - Compute the mathematical intersection of the three lists of scholarship IDs.
   - For each intersected scholarship ID, call `get_scholarship_details` to retrieve the scholarship's full details (specifically the name).
3. Output the final recommendations exactly in this format:

Routing Category:
[Determine Category Name: 'School Scholarships', 'Undergraduate Scholarships', 'Postgraduate Scholarships', 'PhD Scholarships', or 'International Scholarships']

Recommended Scholarships:

1. [Scholarship Name]
2. [Scholarship Name]

If no scholarships qualify, state that politely under the Recommended Scholarships header. Do not output anything else.
""",
        tools=[search_by_education, search_by_income, search_by_marks, get_scholarship_details]
    )

def create_sequential_workflow(name: str) -> SequentialAgent:
    """
    Creates a new SequentialAgent pipeline acting as a category-specific orchestrator.
    This resolves the Single Parent Rule by instantiating fresh sub-agents.
    """
    return SequentialAgent(
        name=name,
        sub_agents=[create_profile_agent(), create_eligibility_agent(), create_scholarship_search_agent()]
    )
