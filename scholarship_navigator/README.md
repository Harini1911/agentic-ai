# Phase 1, 2 & 3: Scholarship Navigator Agent

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

## Phase 3 – Router Workflow Pattern

### What Is a Router Agent?
A **Router Agent** acts as an intelligent receptionist. It reviews user input, decides which specialized agent is best equipped to handle the task, and delegates execution entirely.

### Why Router Workflows Matter
* **Without a Router:** A single agent tries to handle school, college, PG, PhD, and international requirements, leading to prompt bloat, mathematical errors, and poor scaling.
* **With a Router:** Complex monolithic prompts are divided into small, domain-specific sub-agents, guaranteeing specialization and better maintainability.

### Architecture

```text
User
  ↓
Router Agent (ScholarshipRouterAgent)
  │
  ├── School Agent (SchoolScholarshipAgent)
  ├── UG Agent (UGScholarshipAgent)
  ├── PG Agent (PGScholarshipAgent)
  ├── PhD Agent (PhDScholarshipAgent)
  └── International Agent (InternationalScholarshipAgent)
        ↓
     Tool Layer (Deterministic Tools)
        ↓
 Scholarship Dataset (scholarships.json)
```

### ADK Concepts Learned

* **Router Agent:** Classifies user context and delegates tasks using sub-agents exposed as tools.
* **Specialized Agents:** Sub-agents representing single domain ownership and responsibilities.
* **Routing Rules:** Deterministic rulesets deciding the execution path (e.g. routing based on `education_level` and prioritizing `country_preference != "India"` for international routing).

### Execution Walkthrough

1. **User submits profile:** The student profile (B.Tech, India) is passed to the `ScholarshipRouterAgent`.
2. **Router evaluates profile:** The router reviews the rules and classifies the category as *Undergraduate*.
3. **Router delegates:** The router transfers control by invoking `UGScholarshipAgent` as a tool.
4. **Specialist executes:** `UGScholarshipAgent` calls search tools and intersects results.
5. **Results returned:** Recommended scholarships are printed in a structured layout.

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
Runs a pre-loaded B.Tech student profile to showcase undergraduate routing:
```bash
uv run python3 app.py
```

#### B. Interactive CLI Mode
Allows you to enter your own custom name, educational level, country preference, marks, and income to route your request:
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
