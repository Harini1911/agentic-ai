# Scholarship Navigator Agent

A production-quality AI agent built using **Google's Agent Development Kit (ADK)** to navigate, filter, and match student profiles with eligible local scholarships.

---

## Project Overview

### The Problem
Finding and applying for scholarships is a complex and highly fragmented process. Millions of students miss out on financial aid opportunities every year because:
1. **Discovery is Hard:** Scholarship listings are scattered across dozens of unorganized sites.
2. **Criteria are Complex:** Each scholarship has distinct combinations of age, education level, state of residency, academic performance, and income limits.
3. **Manual Matching fails:** Manually comparing profile attributes to dozens of eligibility criteria is time-consuming, prone to calculation errors, and discouraging for students.

### The Solution: Why AI Agents?
AI agents represent a paradigm shift from keyword searches to smart assistance. By using **Google's Agent Development Kit (ADK)**:
* **Natural Understanding:** The AI agent acts as a smart counselor that understands unstructured or semi-structured user profiles instantly.
* **Coordinated Tool Execution:** Instead of hardcoding all business and query logic inside the LLM itself, the agent leverages specialized deterministic tools to fetch accurate, validated data.
* **Empathetic Explanations:** The agent translates rigid logic checks into encouraging, clear, and context-rich descriptions of *why* the student qualifies, helping boost applicant confidence.

---
## Installation & Execution

### Prerequisites
* Python 3.10 or higher.
* A Gemini API key (set in your environment as `GEMINI_API_KEY`).

### Step 1: Install Dependencies
Install all package dependencies in your virtual environment:
```bash
pip install -r requirements.txt
```

### Step 2: Set Environment Variables
Create a `.env` file at the project root or set it directly in your shell:
```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

### Step 3: Run the Demo Application
You can run the program in two different modes.

#### A. Standard Demo Mode (Default)
Runs an incomplete student profile to showcase the **Loop Workflow Pattern** dynamically asking questions, validating them, updating the profile, and proceeding to route and parallel search:
```bash
uv run python3 app.py
```

#### B. Interactive CLI Mode
Allows you to enter your own custom name, educational level, country preference, marks, and income to run the multi-agent parallel pipeline:
```bash
uv run python3 app.py -i
# OR
uv run python3 app.py --interactive
```

---

## Phase 2 – Tool Calling Pattern

### What Problem Does Tool Calling Solve?
* **Without Tools:** The agent contains all data and comparison logic. This bloats the LLM context, introduces calculation errors, and fails to scale.
* **With Tools:** The agent delegates specialized tasks to deterministic Python functions. It stays focused on reasoning, orchestration, and natural communication.

---

## Phase 3 – Router Workflow Pattern

### What Is a Router Agent?
A **Router Agent** acts as an intelligent receptionist. It reviews user input, decides which specialized agent is best equipped to handle the task, and delegates execution entirely.

---

## Phase 4 – Sequential Workflow Pattern

### What Is a Sequential Workflow?
A **Sequential Workflow** executes multiple specialized agents in a fixed, predefined order. The output of one agent becomes the input of the next agent, creating a robust data pipeline.

---

## Phase 5 – Parallel Workflow Pattern

### What Is a Parallel Workflow?
A **Parallel Workflow** executes multiple independent tasks simultaneously and merges their results into a single response.

### Why Parallel Workflows Matter
* **Without Parallel Workflow (Sequential Search):** Searching four different database providers (National, State, University, Private) sequentially multiplies network/disk latency, resulting in a sluggish user experience.
* **With Parallel Workflow:** The four database source agents are launched concurrently. Total search latency is capped at the speed of the single slowest lookup.

**Benefits:**
* **Fast Execution:** Executes all lookup processes concurrently.
* **Better Scalability:** Additional search providers can be integrated and queried concurrently without affecting overall system latency.

### Architecture

```text
Profile Agent
 ↓
Eligibility Agent
 ↓

Parallel Search (Orchestrated by ParallelScholarshipSearchAgent)

 ├── NSP Agent (reads nsp_scholarships.json)
 ├── State Agent (reads state_scholarships.json)
 ├── University Agent (reads university_scholarships.json)
 └── Private Agent (reads private_scholarships.json)

 ↓ (Wait for all to finish)

Merge & Deduplicate (Removes duplicates by name/id)
 ↓
Response
```

### ADK Concepts Learned

* **Parallel Agents:** Concurrent execution of nested sub-agents one after another using `ParallelAgent`.
* **Result Aggregation:** Accessing and combining individual sub-agent structured output variables in the parent orchestrator.
* **Deduplication:** Filtering multi-sourced items (e.g. `National Merit Scholarship` appearing in both NSP and University listings) to display only once in the final card.

### Execution Walkthrough

1. **User submits profile:** The student profile is routed to `UGScholarshipAgent`.
2. **Sequential checks execute:** The profile is validated by `Profile Agent` and marked as eligible by `Eligibility Agent`.
3. **Parallel Search starts:** `ParallelScholarshipSearchAgent` concurrently triggers `NSPScholarshipAgent`, `StateScholarshipAgent`, `UniversityScholarshipAgent`, and `PrivateScholarshipAgent`.
4. **Contextvars isolate sources:** Async context variables ensure each agent queries its own `.json` database file safely.
5. **Results aggregated & deduplicated:** Combined results are merged, duplicate IDs are removed, and the unified group breakdown is rendered.

---

## Phase 6 – Loop Workflow Pattern

### What Is a Loop Workflow?
A **Loop Workflow** repeatedly executes a set of tasks (checking conditions, prompting for user action, and validating outputs) in a loop until a specific termination condition is satisfied (e.g., the student's profile is complete).

### Why Loop Workflows Matter
* **Without a Loop Workflow:** If the student's profile is incomplete, the workflow fails because critical search parameters (income, marks, etc.) are missing.
* **With a Loop Workflow:** The system dynamically intercepts the profile, identifies missing fields, asks precise questions, validates and normalizes inputs, updates the profile state, and loops until all required fields are complete.

**Benefits:**
* **Better User Experience:** Dynamically gathers only what is missing.
* **Adaptive Workflows:** Gracefully handles invalid inputs and continues prompting without losing previous state.

### Architecture

```text
User
 ↓
Profile Completion Loop (Orchestrated by workflows/loop_workflow.py)
 ├── Inspect Profile (Detects missing fields)
 ├── ProfileCompletionAgent (ADK Agent generates precise question)
 ├── Terminal Prompt (Collects user input)
 ├── Strict Validation (Checks constraints: Marks 0-100, Income numeric, etc.)
 └── Profile Update (Applies normalizations: CGPA/percentage, B.Tech casing)
 ↓ (Until all fields are complete)
 
ScholarshipRouterAgent (Router Agent)
 ↓ (Routes based on completed country_preference & education_level)
ProfileAgent (Normalizes Profile Input)
 ↓
EligibilityAgent (Validates Marks & Income Limits)
 ↓
ParallelScholarshipSearchAgent (Concurrent search NSP/State/Uni/Private)
 ↓
Unified Deduplicated Response
```

### ADK Concepts Learned
* **Loop Workflow Pattern:** Dynamic evaluation and execution of steps repeatedly until an exit condition is met.
* **State Updates:** Preserving previously gathered profile values while updating missing fields interactively.
* **Input Validation & Normalization:** Standardizing user responses (e.g. "abroad" -> "International", casing, range constraints) to prevent downstream failures.

### Execution Walkthrough
1. **User submits incomplete profile:** Profile is loaded with missing `annual_income`, `marks_percentage`, and `country_preference`.
2. **Missing fields identified:** Loop workflow detects outstanding required fields.
3. **Interactive prompts execute:** `ProfileCompletionAgent` generates exact follow-up questions.
4. **Validation and update:** User answers are validated (e.g., numeric checks, range checks), normalized, and profile is updated.
5. **Loop termination:** When all 5 fields are present, the loop exits.
6. **Scholarship pipeline proceeds:** The completed profile is sent through routing, profiling, eligibility verification, and concurrent searching.

---

## Phase 7 – Coordinator / Orchestration Pattern

### What Is a Coordinator Agent?
A **Coordinator Agent** manages other agents and workflows. It does not solve the task directly; it decides who should, representing the single entry point for all operations.

### Why Coordinator Agents Matter
* **Without a Coordinator:** The user must manually interface and coordinate between the Loop, Router, Sequential, and Parallel workflows.
* **With a Coordinator:** The user interacts only with the `ScholarshipCoordinatorAgent`, which manages all workflows internally.

### Architecture

```text
User
 ↓
Coordinator Agent (ScholarshipCoordinatorAgent)
 ├── Loop Workflow
 ├── Router Workflow
 ├── Sequential Workflow
 └── Parallel Workflow
 ↓
Response
```

### ADK Concepts Learned
* **Orchestration:** Workflow management, dynamic delegation, and high-level decision routing.
* **Separation of Responsibilities:** The coordinator manages execution flows while specialized workers execute task details.
* **Workflow Composition:** Seamless integration of Loop, Router, Sequential, and Parallel models into a single, cohesive discovery engine.

### Execution Walkthrough
1. **User submits request:** The profile is passed to the `ScholarshipCoordinatorAgent`.
2. **Completeness check:** Coordinator checks completeness; triggers Loop Workflow if any fields are missing.
3. **Router selection:** Invokes router logic to select the specialized educational/country route (e.g. UG route).
4. **Sequential execution:** Triggers category-specific sequential agent validation (Profile, Eligibility limits, Parallel Search).
5. **Parallel search & deduplication:** Concurrent lookups are made, merged, and duplicate listings are filtered out.
6. **Response returned:** Consolidated results are sent back to the user.

---

## Phase 8 – Memory Pattern

### What Is Agent Memory?
**Agent Memory** allows an agent to store, retrieve, and use information from previous interactions within the same conversation session, enabling continuous, adaptive, and highly relevant multi-turn dialogue.

### Why Session Continuity Matters
* **Without Memory:** Every conversational turn is treated as a separate reboot. The agent loses all previous context, leading to confusion and forcing redundant user entries.
* **With Memory:** The agent remembers the student profile, previous recommendations, and user preferences within the same session. This allows for continuous discovery, exclusions, and document generation without repetitive profile prompts.

### Memory Demonstration

#### Scenario A: Agent WITH Memory
* **Turn 1:** Finds and returns B.Tech scholarships in Tamil Nadu, recording them in memory.
* **Turn 2:** Receives *"I am not interested in private scholarships."* and filters out corporate private listings from the session memory, returning a revised list.
* **Turn 3:** Receives *"Tell me the required documents."* and lists exact document requirements specifically for the remaining scholarships in memory without re-requesting profile details.

#### Scenario B: Agent WITHOUT Memory
* **Turn 1:** Finds scholarships normally.
* **Turn 2:** Receives *"I am not interested in private scholarships."* under a new session. Responds: *"Please provide more context."*
* **Turn 3:** Receives *"Tell me the required documents."* under a new session. Responds: *"Which scholarship are you referring to?"*

### Architecture

```text
User
 ↓
Coordinator Agent (ScholarshipCoordinatorAgent)
 ├── Reads & Updates Session Memory (memory/scholarship_memory.py)
 └── Workflow execution (Loop, Router, Sequential, Parallel)
 ↓
Response
```

### ADK Concepts Learned
* **Session State:** Associating conversation state with unique session IDs to isolate memory context across concurrent users.
* **Context Retention:** Short-term persistence of conversation contexts and recommendations.
* **Adaptive Responses:** Adapting future responses based on prior outcomes stored in memory (e.g. generating documents specifically for filtered listings).

---

## Further Documentation

Detailed information and conceptual breakdowns of each phase:
* **[Phase 1 Documentation](file:///4TBHD/harini/agentic-ai/scholarship_navigator/Docs/phase1.md)**: Conceptual guide covering the single agent data retrieval model.
* **[Phase 2 Documentation](file:///4TBHD/harini/agentic-ai/scholarship_navigator/Docs/phase2.md)**: Deep dive into the Tool Calling Pattern and modular tools.
* **[Phase 3 Documentation](file:///4TBHD/harini/agentic-ai/scholarship_navigator/Docs/phase3.md)**: Conceptual guide covering the multi-agent Router Workflow pattern.
* **[Phase 4 Documentation](file:///4TBHD/harini/agentic-ai/scholarship_navigator/Docs/phase4.md)**: Conceptual guide covering the Sequential Workflow pipeline and early exits.
* **[Phase 5 Documentation](file:///4TBHD/harini/agentic-ai/scholarship_navigator/Docs/phase5.md)**: Conceptual guide covering the Parallel Workflow database search and deduplication.
* **[Phase 6 Documentation](file:///4TBHD/harini/agentic-ai/scholarship_navigator/Docs/phase6.md)**: Conceptual guide covering the Loop Workflow interactive information gathering.
* **[Phase 7 Documentation](file:///4TBHD/harini/agentic-ai/scholarship_navigator/Docs/phase7.md)**: Conceptual guide covering the Coordinator Orchestration Pattern.
* **[Phase 8 Documentation](file:///4TBHD/harini/agentic-ai/scholarship_navigator/Docs/phase8.md)**: Conceptual guide covering Session Memory and continuous multi-turn dialogue.
