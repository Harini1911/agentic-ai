# Phase 1 & 2: Scholarship Navigator Agent

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

**Benefits:**
* **Reusability:** Tools can be reused across different UI/UX clients or systems.
* **Separation of Concerns:** Filtering math and file indexing live in Python, not in English instructions.
* **Scalability:** Easily integrates with huge databases without overwhelming the LLM's context window.

### Architecture

```text
User
  ↓
Scholarship Agent (ADK LLM Agent)
  ↓
Tool Layer
  ├── Education Tool (search_by_education)
  ├── Income Tool (search_by_income)
  ├── Marks Tool (search_by_marks)
  └── Details Tool (get_scholarship_details)
  ↓
Scholarship Dataset (scholarships.json)
```

### ADK Concepts Learned

* **Tool Calling:** Wrapping standard Python functions as agent actions. The ADK parses functions to create JSON Schemas, letting the agent call them dynamically.
* **Agent Responsibilities:** Decoupling *Decision-making* (Agent) from *Execution* (Tools).
* **Separation of Concerns:** Enforcing that "Search Logic" is completely independent from "Agent instructions".

### Execution Walkthrough

1. **User submits profile:** The student profile (Class 12, ₹2.5L income, 92% marks) is parsed by the agent.
2. **Agent selects tools:** The agent calls `search_by_education()`, `search_by_income()`, and `search_by_marks()`.
3. **Tools retrieve data:** The tools search the database and return candidate lists containing scholarship IDs.
4. **Agent combines results:** The agent intersects these candidate lists to find scholarships matching all criteria.
5. **Agent retrieves details:** The agent calls `get_scholarship_details()` for each matched ID to extract amounts and names.
6. **Agent generates response:** The agent presents the final elegibility list.

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
Runs a pre-loaded student profile (John, Class 12, 92% marks, family income 250,000 INR) to showcase the matching logic:
```bash
uv run python3 app.py
```

#### B. Interactive CLI Mode
Allows you to enter your own custom name, age, educational level, income, and marks to find matched results in real time:
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
