# Phase 2: Details, Architecture, and Concepts Learned (Tool Calling Pattern)

This document keeps track of the architecture, concepts learned, schemas, and execution walkthrough for Phase 2 of the Scholarship Navigator Agent.

---

## What Problem Does Tool Calling Solve?

### Without Tools (Phase 1 Pattern)
In a naive LLM agent implementation, the agent receives all raw dataset information and does the filtering logic itself (within the context window). 
* **The Pitfall:** The agent's prompt becomes bloated. It struggles with exact mathematical comparisons (e.g. `250000 <= 300000`), is prone to hallucinations, and does not scale as the dataset grows beyond a few entries.

### With Tools (Phase 2 Pattern)
In a production-ready ADK implementation, the agent **delegates specialized tasks** to external Python functions (tools).
* **The Advantage:** The agent acts as a cognitive coordinator rather than an execution engine. It decides *which* tools to call with *what* arguments, but does not perform the heavy lifting, database reads, or business rules itself.

### Key Benefits
* **Reusability:** Tools are standard Python functions that can be reused by other agents, REST APIs, or UI interfaces.
* **Separation of Concerns:** Business and search logic are isolated from agent instructions.
* **Easier Maintenance:** Changes to how database filtering works require no edits to LLM system prompts.
* **Better Scalability:** As the database scales to millions of scholarships, the agent context window remains small and performant because it only receives filtered matching candidate IDs.

---

## Architecture

```text
User
  ↓
Scholarship Agent (ADK LLM Agent)
  ↓
Tool Layer (Programmatic Python Functions)
  ├── Education Tool (search_by_education)
  ├── Income Tool (search_by_income)
  ├── Marks Tool (search_by_marks)
  └── Details Tool (get_scholarship_details)
  ↓
Scholarship Dataset (scholarships.json)
```

---

## ADK Concepts Learned

### 1. Tool Calling
* **What Tools Are:** Standard Python functions wrapped with type hints and docstrings. 
* **How Agents Invoke Tools:** The ADK engine automatically builds a JSON Schema declaration from the function's signature and docstring. During the reasoning loop, the LLM outputs a function call request containing the name of the function and its arguments. The ADK runner intercepts this, executes the Python code locally, and feeds the result back into the conversation.
* **Why Tools Should Own Business Logic:** This keeps the LLM reasoning highly accurate and eliminates mathematical evaluation errors.

### 2. Agent Responsibilities
* **Agent = Decision-Making:** The agent is solely responsible for determining the workflow, parsing user requests, coordinating multiple calls, calculating the intersection, and framing a helpful, natural response.
* **Tool = Execution:** The tools handle data access, math, and filtering rules.

### 3. Separation of Concerns
* **Search Logic ≠ Agent Logic:** The search query, file parsing, and comparison logic are handled entirely by deterministic Python code. The agent's instructions only define the high-level orchestration, ensuring optimal decoupling.

---

## Execution Walkthrough

The following sequence details how the ScholarshipAgent executes a request:

1. **User submits profile:** The user provides student details (e.g., "Find scholarships for a Class 12 student with 92% marks and ₹2.5 lakh income").
2. **Agent selects tools:** The agent decides it needs to determine eligibility across three criteria and invokes:
   - `search_by_education(education_level="Class 12")`
   - `search_by_income(annual_income=250000)`
   - `search_by_marks(marks_percentage=92)`
3. **Tools retrieve data:** Each tool reads `data/scholarships.json` and evaluates its respective criteria, returning lists of matching scholarship IDs (e.g., Tool 1 returns `[{"id": "SCH001", "name": "National Merit Scholarship"}, {"id": "SCH002", "name": "State Excellence Scholarship"}, {"id": "SCH003", "name": "Tech Pioneers Fellowship"}]`).
4. **Agent combines results:** The agent processes the lists and computes the mathematical intersection (identifying that `SCH001`, `SCH002`, and `SCH003` satisfy all requirements).
5. **Agent retrieves details:** For each ID in the intersection, the agent calls `get_scholarship_details(scholarship_id)` to fetch names and award amounts.
6. **Agent generates response:** The agent synthesizes and streams the formatted recommendation list back to the user.
