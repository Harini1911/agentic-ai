# Phase 1, 2, 3, 4 & 5: Scholarship Navigator Agent

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
Runs a pre-loaded B.Tech student profile to showcase undergraduate routing, sequential checking, and parallel source lookups:
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

## Further Documentation

Detailed information and conceptual breakdowns of each phase:
* **[Phase 1 Documentation](file:///4TBHD/harini/agentic-ai/scholarship_navigator/Docs/phase1.md)**: Conceptual guide covering the single agent data retrieval model.
* **[Phase 2 Documentation](file:///4TBHD/harini/agentic-ai/scholarship_navigator/Docs/phase2.md)**: Deep dive into the Tool Calling Pattern and modular tools.
* **[Phase 3 Documentation](file:///4TBHD/harini/agentic-ai/scholarship_navigator/Docs/phase3.md)**: Conceptual guide covering the multi-agent Router Workflow pattern.
* **[Phase 4 Documentation](file:///4TBHD/harini/agentic-ai/scholarship_navigator/Docs/phase4.md)**: Conceptual guide covering the Sequential Workflow pipeline and early exits.
* **[Phase 5 Documentation](file:///4TBHD/harini/agentic-ai/scholarship_navigator/Docs/phase5.md)**: Conceptual guide covering the Parallel Workflow database search and deduplication.
