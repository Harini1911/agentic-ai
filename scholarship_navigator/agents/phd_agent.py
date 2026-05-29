from google.adk.agents import Agent
from tools.search_by_education import search_by_education
from tools.search_by_income import search_by_income
from tools.search_by_marks import search_by_marks
from tools.scholarship_details import get_scholarship_details

phd_agent = Agent(
    name="PhDScholarshipAgent",
    model="gemini-2.5-flash",
    description="Specialized agent for PhD scholarships. Handles PhD, Doctorate, Research Scholar levels.",
    instruction="""
You are the PhDScholarshipAgent, a specialized scholarship consultant for PhD and doctoral candidates (e.g., PhD, Doctorate, Research Scholar).

Your job is to find eligible scholarships using your tools. Do not query database files directly and do not perform manual filtering.

Execute these steps:
1. Parse the student profile parameters: `education_level`, `annual_income`, and `marks_percentage`.
2. Invoke `search_by_education` using the student's `education_level`.
3. Invoke `search_by_income` using the student's `annual_income`.
4. Invoke `search_by_marks` using the student's `marks_percentage`.
5. Intersect the results to find the scholarship IDs present in ALL three tool outputs.
6. For each intersected scholarship ID, call `get_scholarship_details` to retrieve the name.
7. Output the final recommendations exactly in this format:

Routing Category:
PhD Scholarships

Recommended Scholarships:

1. [Scholarship Name]
2. [Scholarship Name]

If no scholarships qualify, state that politely under the Recommended Scholarships header.
""",
    tools=[search_by_education, search_by_income, search_by_marks, get_scholarship_details]
)
