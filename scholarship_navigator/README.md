# Phase 1, 2, 3 & 4: Scholarship Navigator Agent

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

### Why Sequential Workflows Matter
* **Without Sequential Workflow:** A monolithic agent is responsible for input validation, threshold verification, tool calling, and output styling.
* **With Sequential Workflow:** The pipeline splits the responsibility into a modular chain of three distinct agents: `Profile Agent` -> `Eligibility Agent` -> `Scholarship Search Agent`.

**Benefits:**
* **Modular Design:** Easier debugging and testing of individual stages.
* **Early Exit:** If the `Eligibility Agent` determines the student does not satisfy minimum criteria (e.g. marks < 60%), the pipeline exits immediately to conserve tokens.

### Architecture

```text
User
 ↓
Router Agent (ScholarshipRouterAgent)
 ↓
Profile Agent (Normalizes Profile Input)
 ↓
Eligibility Agent (Validates Marks & Income Limits)
 ↓
Scholarship Search Agent (Retrieves Scholarships via Tools)
 ↓
Response
```

### ADK Concepts Learned

* **Sequential Execution:** Linear orchestration of nested sub-agents one after another using `SequentialAgent`.
* **Agent Chaining:** Sharing states between steps in the execution pipeline via `output_key` context references.
* **Early Exit:** Terminating the workflow early if eligibility rules fail.

### Execution Walkthrough

1. **User submits profile:** The B.Tech profile is routed to `UGScholarshipAgent`.
2. **Profile Agent validates:** The agent normalizes values and writes valid status to the context.
3. **Eligibility Agent evaluates:** The agent checks eligibility boundaries (marks >= 60%, income <= 10L).
4. **Scholarship Search Agent retrieves:** If eligible, calls tools to compile the matching list. If ineligible, exits early with a specialized rejection card.

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
Runs a pre-loaded B.Tech student profile to showcase undergraduate routing and sequential execution:
```bash
uv run python3 app.py
```

#### B. Interactive CLI Mode
Allows you to enter your own custom name, educational level, country preference, marks, and income to run the sequential validation pipeline:
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
