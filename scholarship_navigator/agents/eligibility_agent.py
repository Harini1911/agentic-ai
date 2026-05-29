from google.adk.agents import Agent
from pydantic import BaseModel, Field
from config.llm_config import ADK_MODEL

# Output schema for eligibility check
class EligibilityOutput(BaseModel):
    eligible: bool = Field(description="Whether the student meets the minimum requirements")
    reason: str = Field(description="The reason for eligibility or failure details")

eligibility_agent = Agent(
    name="EligibilityAgent",
    model=ADK_MODEL,
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
