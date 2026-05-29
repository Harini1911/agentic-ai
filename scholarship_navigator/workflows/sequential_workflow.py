from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from tools.search_by_education import search_by_education
from tools.search_by_income import search_by_income
from tools.search_by_marks import search_by_marks
from tools.scholarship_details import get_scholarship_details
from agents.profile_agent import ProfileInput, ProfileOutput
from agents.eligibility_agent import EligibilityOutput
from agents.nsp_agent import SourceScholarshipOutput
from tools.scholarship_repository import set_active_source

# Dynamic callbacks to ensure safe context variables per async source search execution
def nsp_before(ctx):
    set_active_source("nsp")

def state_before(ctx):
    set_active_source("state")

def university_before(ctx):
    set_active_source("university")

def private_before(ctx):
    set_active_source("private")

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

def create_parallel_search_agent() -> Agent:
    """
    Creates a fresh instance of the ParallelScholarshipSearchAgent,
    establishing fresh nested sub-agent instances (NSP, State, etc.)
    to strictly satisfy the Single Parent Rule in ADK.
    """
    # 1. Instantiate fresh source agents
    nsp = Agent(
        name="NSPScholarshipAgent",
        model="gemini-2.5-flash",
        description="Searches national-level scholarships on the National Scholarship Portal.",
        instruction="""
You are the NSPScholarshipAgent. Your job is to search the National Scholarship Portal (NSP) database using your tools.
Read 'profile_data' from context: `education_level`, `annual_income`, and `marks_percentage`.
Invoke search tools, intersect, retrieve details, and return results matching the SourceScholarshipOutput schema.
""",
        tools=[search_by_education, search_by_income, search_by_marks, get_scholarship_details],
        output_schema=SourceScholarshipOutput,
        output_key="nsp_results",
        before_agent_callback=nsp_before
    )

    state = Agent(
        name="StateScholarshipAgent",
        model="gemini-2.5-flash",
        description="Searches state-level and state-specific scholarships.",
        instruction="""
You are the StateScholarshipAgent. Your job is to search the State Scholarship database using your tools.
Read 'profile_data' from context: `education_level`, `annual_income`, and `marks_percentage`.
Invoke search tools, intersect, retrieve details, and return results matching the SourceScholarshipOutput schema.
""",
        tools=[search_by_education, search_by_income, search_by_marks, get_scholarship_details],
        output_schema=SourceScholarshipOutput,
        output_key="state_results",
        before_agent_callback=state_before
    )

    uni = Agent(
        name="UniversityScholarshipAgent",
        model="gemini-2.5-flash",
        description="Searches university-specific and institution-level scholarships.",
        instruction="""
You are the UniversityScholarshipAgent. Your job is to search the University Scholarship database using your tools.
Read 'profile_data' from context: `education_level`, `annual_income`, and `marks_percentage`.
Invoke search tools, intersect, retrieve details, and return results matching the SourceScholarshipOutput schema.
""",
        tools=[search_by_education, search_by_income, search_by_marks, get_scholarship_details],
        output_schema=SourceScholarshipOutput,
        output_key="university_results",
        before_agent_callback=university_before
    )

    priv = Agent(
        name="PrivateScholarshipAgent",
        model="gemini-2.5-flash",
        description="Searches corporate, NGO, and private scholarships.",
        instruction="""
You are the PrivateScholarshipAgent. Your job is to search the Private Scholarship database using your tools.
Read 'profile_data' from context: `education_level`, `annual_income`, and `marks_percentage`.
Invoke search tools, intersect, retrieve details, and return results matching the SourceScholarshipOutput schema.
""",
        tools=[search_by_education, search_by_income, search_by_marks, get_scholarship_details],
        output_schema=SourceScholarshipOutput,
        output_key="private_results",
        before_agent_callback=private_before
    )

    # 2. Instantiate parallel orchestrator sub-workflow
    workflow = ParallelAgent(
        name="ParallelScholarshipSearchWorkflow",
        sub_agents=[nsp, state, uni, priv]
    )

    # 3. Return the fresh main search agent wrapping this workflow
    return Agent(
        name="ParallelScholarshipSearchAgent",
        model="gemini-2.5-flash",
        description="Orchestrates concurrent searches across multiple providers and merges, deduplicates, and formats their results.",
        instruction="""
You are the ParallelScholarshipSearchAgent. Your responsibility is to coordinate the parallel search of scholarships across different sources and produce a deduplicated, unified summary.

Follow these exact steps:
1. First, check if the student is eligible by reading the context key 'eligibility_data'.
   - If the student is NOT eligible (i.e. 'eligible' is false), you MUST immediately terminate the workflow and output exactly this text:

Unfortunately you do not meet the minimum scholarship eligibility requirements.

Reason:
[Reason from eligibility_data]

2. If 'eligible' is true, proceed with the parallel search:
   - Trigger the `ParallelScholarshipSearchWorkflow` sub-agent. This will run all four source agents (NSP, State, University, Private) concurrently.
3. Once all source agents complete, read their output keys from the context:
   - `nsp_results` (National Scholarships)
   - `state_results` (State Scholarships)
   - `university_results` (University Scholarships)
   - `private_results` (Private Scholarships)
4. Combine the scholarship items from all four results into a single consolidated list.
5. DEDUPLICATE the combined list:
   - If a scholarship (matched by name or ID) appears in multiple sources (e.g. 'National Merit Scholarship' in both NSP and University), you MUST include it only ONCE in the final response.
6. Format the final output exactly in this style (replacing [Total Count] with the number of unique matches, and listing matching names):

Found [Total Count] matching scholarships.

National Scholarships:
- [Scholarship Name]

State Scholarships:
- [Scholarship Name]

University Scholarships:
- [Scholarship Name]

Private Scholarships:
- [Scholarship Name]

Only list a category header if there is at least one eligible scholarship returned under that category. If a category has no matches, do not show its header at all.
""",
        sub_agents=[workflow]
    )

def create_sequential_workflow(name: str) -> SequentialAgent:
    """
    Creates a new SequentialAgent pipeline acting as a category-specific orchestrator.
    This resolves the Single Parent Rule by instantiating fresh sub-agents, including the ParallelSearch agent.
    """
    return SequentialAgent(
        name=name,
        sub_agents=[create_profile_agent(), create_eligibility_agent(), create_parallel_search_agent()]
    )
