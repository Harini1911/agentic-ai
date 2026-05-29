from google.adk.agents import Agent
from pydantic import BaseModel, Field
from typing import List
from tools.search_by_education import search_by_education
from tools.search_by_income import search_by_income
from tools.search_by_marks import search_by_marks
from tools.scholarship_details import get_scholarship_details

class ScholarshipItem(BaseModel):
    id: str = Field(description="The unique ID of the scholarship")
    name: str = Field(description="The name of the scholarship")
    amount: float = Field(description="The scholarship amount in INR")

class SourceScholarshipOutput(BaseModel):
    scholarships: List[ScholarshipItem] = Field(default=[], description="List of eligible scholarships found")

nsp_agent = Agent(
    name="NSPScholarshipAgent",
    model="gemini-2.5-flash",
    description="Searches national-level scholarships on the National Scholarship Portal.",
    instruction="""
You are the NSPScholarshipAgent. Your job is to search the National Scholarship Portal (NSP) database using your tools.

Read the student's profile from the context key 'profile_data':
- `education_level`
- `annual_income`
- `marks_percentage`

Execute these steps:
1. Call `search_by_education` using `education_level`.
2. Call `search_by_income` using `annual_income`.
3. Call `search_by_marks` using `marks_percentage`.
4. Compute the mathematical intersection of the matching scholarship IDs.
5. For each ID in the intersection, call `get_scholarship_details` to get its name and amount.
6. Compile the list of qualifying scholarships and output them strictly matching the SourceScholarshipOutput schema.
""",
    tools=[search_by_education, search_by_income, search_by_marks, get_scholarship_details],
    output_schema=SourceScholarshipOutput,
    output_key="nsp_results"
)
