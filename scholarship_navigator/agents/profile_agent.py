from google.adk.agents import Agent
from pydantic import BaseModel, Field

# Input schema for profile validation
class ProfileInput(BaseModel):
    name: str = Field(default="John", description="The student's name")
    education_level: str = Field(description="The student's education level (e.g. 'Class 12', 'B.Tech')")
    marks_percentage: float = Field(description="The student's academic marks percentage out of 100")
    annual_income: float = Field(description="The student's family annual income in INR")
    country_preference: str = Field(default="India", description="The student's country preference")

# Output schema for validated profile
class ProfileOutput(BaseModel):
    profile_valid: bool = Field(description="Whether the profile contains valid parameters")
    name: str = Field(description="The student's name")
    education_level: str = Field(description="The standardized education level")
    marks_percentage: float = Field(description="The standardized marks percentage")
    annual_income: float = Field(description="The standardized annual income")
    country_preference: str = Field(description="The standardized country preference")
    error_message: str = Field(default="", description="Error details if profile is invalid")

profile_agent = Agent(
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
