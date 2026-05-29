# Phase 7: Details, Architecture, and Concepts Learned (Coordinator / Orchestration Pattern)

This document keeps track of the architecture, concepts learned, selection logic, and execution walkthrough for Phase 7 of the Scholarship Navigator Agent.

---

## What Is a Coordinator Agent?

A **Coordinator Agent** (or Orchestrator Agent) acts as a high-level manager that oversees, directs, and schedules other agents and workflows instead of doing worker tasks directly. It represents the single entry point for the user, hiding the system's underlying complexity and determining dynamically which specialist sub-agents or sub-workflows to trigger based on the user's current context.

---

## Why Coordinator Agents Matter

### Without a Coordinator Agent
The user or application front-end has to interact with multiple independent workflows, managing when to run profile completion, when to route, and how to execute the search:
```text
User
 ├── Loop Workflow (Interactive prompts)
 ├── Router Workflow (Selecting domain)
 ├── Sequential Workflow (Verifying limits)
 └── Parallel Workflow (Searching databases)
```
* **High Client Complexity:** The client/user has to coordinate multiple API calls and manage state transitions manually.
* **Tight Coupling:** If the sequence of steps changes, the user interface or top-level application code must be rewritten.

### With a Coordinator Agent
The user submits their profile to a single entry point. The coordinator evaluates the state and orchestrates everything internally:
```text
User
 ↓
Coordinator Agent
 ├── Loop Workflow (Runs if incomplete)
 ├── Router Workflow (Selects specialist agent)
 ├── Sequential Workflow (Runs verification pipeline)
 └── Parallel Workflow (Executes concurrent search & merges results)
 ↓
Response
```
* **Unified Interface:** The user has a single interaction point, providing an extremely simple and clean interface.
* **Separation of Responsibilities:** The coordinator manages the high-level business flow and delegation logic, leaving specialized database queries, eligibility checks, and profile completions to dedicated workers.
* **Seamless Composition:** Complex workflows (Looping, Routing, Sequential checks, Parallel queries) are combined into a single, cohesive, self-healing system.

---

## Architecture Diagram

```text
User
 ↓

ScholarshipCoordinatorAgent (Unified Entry Point)
 │
 ├── [Profile Incomplete?] ──► Loop Workflow (Iterative questions & validation)
 │                                    ↓ (Updates profile state until complete)
 ├── [Profile Complete]
 │
 ├── Router Workflow logic (Selects School, UG, PG, PhD, or International Agent)
 │
 └── Selected Sequential Agent (e.g. UGScholarshipAgent)
       │
       ├── ProfileAgent (Normalizes input parameters)
       │     ↓
       ├── EligibilityAgent (Validates marks >= 60% and income <= 10 Lakh)
       │     ↓
       └── ParallelScholarshipSearchAgent (Orchestrates concurrent searches)
             │
             ├── NSPScholarshipAgent
             ├── StateScholarshipAgent
             ├── UniversityScholarshipAgent
             └── PrivateScholarshipAgent
             │
             ↓ (Deduplicates listings by name/id)
             Merged Final Card Recommendation

 ↓
Response (Premium Breakdown)
```

---

## ADK Concepts Learned

### 1. Orchestration
* **Workflow Management:** The coordinator decides when and how to delegate to specific workflows, acting as the brain that directs the flow of execution.
* **Dynamic Decision Making:** If a student profile is already complete, the coordinator bypasses the Loop Workflow entirely and proceeds directly to routing, showing adaptive execution.

### 2. Separation of Responsibilities
* **Coordinator vs. Workers:** The coordinator agent does not perform database filtering or eligibility mathematics. It maintains high-level awareness, while specialized workers (like `ProfileAgent` and `EligibilityAgent`) run the concrete calculations.

### 3. Workflow Composition
* **Hierarchical Organization:** Multiple different agentic architectures (Loop, Router, Sequential, Parallel) are composed hierarchically under a single parent coordinator, satisfying ADK design guidelines.

---

## Execution Walkthrough

1. **User Submits Query:** The user submits a profile to the `ScholarshipCoordinatorAgent`.
2. **Step 1: Check Profile Completeness:**
   - The coordinator inspects the profile. If any required fields (e.g. `annual_income`, `marks_percentage`, `country_preference`) are missing, it triggers the **Loop Workflow**.
   - The Loop Workflow interactively prompts the user for missing fields, validates and normalizes answers, and updates the profile state until all 5 required fields are present.
3. **Step 2: Router Workflow Execution:**
   - Once the profile is complete, the coordinator triggers the **Router Workflow** logic to select the specialized educational/geographical domain (e.g. `UGScholarshipAgent`).
4. **Step 3: Sequential & Parallel Search Workflow:**
   - The coordinator invokes the runner for the selected category-specific agent (e.g. `UGScholarshipAgent`), which is a `SequentialAgent` pipeline:
     - **ProfileAgent** normalizes the parameters.
     - **EligibilityAgent** verifies minimum thresholds (e.g. Marks >= 60%, Income <= 10 Lakh).
     - **ParallelSearchAgent** concurrently queries all 4 databases (NSP, State, University, Private) in parallel.
     - Merges, deduplicates, and formats the matching results.
5. **Final Output Generated:** The aggregated response is streamed back to the user under a single, unified discovery transaction.
