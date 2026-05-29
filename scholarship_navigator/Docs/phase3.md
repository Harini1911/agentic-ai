# Phase 3: Details, Architecture, and Concepts Learned (Router Workflow Pattern)

This document keeps track of the architecture, concepts learned, routing rules, and execution walkthrough for Phase 3 of the Scholarship Navigator Agent.

---

## What Is a Router Agent?

A **Router Agent** (or Triage Agent) acts as a high-level classifier and delegator. It analyzes the user's input context (the student profile) and routes the request to a highly specialized, domain-specific worker agent.

It does **not** solve the problem itself—instead, it makes routing decisions and delegates execution.

---

## Why Router Workflows Matter

### Without a Router (Single Agent Pattern)
As the scope of an application grows, a single agent is expected to handle every single domain (e.g. school, undergraduate, postgraduate, PhD, international study).
* **Bloated Instructions:** The prompt is overwhelmed with complex rules for every domain.
* **Hard to Scale:** Adding a new category of scholarship requires rewriting the entire system prompt.
* **Hallucination Risk:** The LLM struggles to maintain domain context, resulting in incorrect tool call selections.

### With a Router
The routing pattern splits a monolithic agent into a coordinated hierarchy of specialists:
```text
Router Agent (Decides)
  ↓
Specialized Agents (Execute)
```
* **Domain Specialization:** Each sub-agent is a master of its own field (e.g. `UGScholarshipAgent` only needs to know about undergraduate structures).
* **Better Organization:** Decoupled codebase where prompt files remain small, focused, and maintainable.
* **Easier Expansion:** To support a new category (e.g., "Vocational Training"), you simply add a new sub-agent and add a single routing rule to the parent.

---

## Architecture Diagram

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
     Tool Layer (Deterministic Search Tools)
        ↓
  Scholarship Dataset (scholarships.json)
```

---

## ADK Concepts Learned

### 1. Router Agent
* **Request Classification:** The router parses the input student profile and selects the correct destination category.
* **Delegation:** The parent `LlmAgent` automatically exposes its `sub_agents` as executable transfer tools.
* **Dynamic Routing:** Routing is performed dynamically by the LLM reasoning loop matching the user context with the sub-agent descriptions.

### 2. Specialized Agents
* **Single Responsibility:** Each sub-agent is dedicated to a single educational tier.
* **Domain Ownership:** The specialists own their respective system instructions, output styling, and semantic reasoning.

### 3. Routing Rules

The `ScholarshipRouterAgent` executes routing based on this deterministic ruleset:

| Route | Condition | Destination |
| :--- | :--- | :--- |
| **International** | `country_preference != "India"` (Takes highest priority) | `InternationalScholarshipAgent` |
| **School** | `education_level` in `["Class 6", "Class 7", "Class 8", "Class 9", "Class 10", "Class 11", "Class 12"]` | `SchoolScholarshipAgent` |
| **Undergraduate** | `education_level` in `["B.E.", "B.Tech.", "B.Sc.", "BA", "B.Com."]` | `UGScholarshipAgent` |
| **Postgraduate** | `education_level` in `["M.Tech.", "MBA", "M.Sc.", "MA"]` | `PGScholarshipAgent` |
| **PhD** | `education_level` in `["PhD", "Doctorate", "Research Scholar"]` | `PhDScholarshipAgent` |

---

## Execution Walkthrough

1. **User submits profile:** The user provides their B.Tech student profile.
2. **Router evaluates profile:** The `ScholarshipRouterAgent` reviews the fields and identifies `education_level` as `"B.Tech"` and `country_preference` as `"India"`.
3. **Router selects destination agent:** Based on the undergraduate routing rule, the router delegates by calling the `UGScholarshipAgent` sub-agent tool.
4. **Specialized agent invokes tools:** `UGScholarshipAgent` takes over, invokes the Phase 2 filtering tools (`search_by_education`, `search_by_income`, `search_by_marks`), and computes their mathematical intersection.
5. **Results returned:** The specialist fetches final scholarship names, structures the final response, and delivers it to the user.
