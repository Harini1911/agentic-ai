from google.adk.agents import ParallelAgent
from agents.nsp_agent import nsp_agent
from agents.state_agent import state_agent
from agents.university_agent import university_agent
from agents.private_agent import private_agent
from tools.scholarship_repository import set_active_source

# Define execution callbacks to bind the contextvars dynamically before running each agent
def nsp_before(ctx):
    set_active_source("nsp")

def state_before(ctx):
    set_active_source("state")

def university_before(ctx):
    set_active_source("university")

def private_before(ctx):
    set_active_source("private")

# Attach the callbacks to the respective source agents to isolate async states
nsp_agent.before_agent_callback = nsp_before
state_agent.before_agent_callback = state_before
university_agent.before_agent_callback = university_before
private_agent.before_agent_callback = private_before

# Create the ParallelAgent orchestrating concurrent runs
parallel_search_workflow = ParallelAgent(
    name="ParallelScholarshipSearchWorkflow",
    sub_agents=[nsp_agent, state_agent, university_agent, private_agent]
)
