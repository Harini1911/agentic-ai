# Phase 5: Details, Architecture, and Concepts Learned (Parallel Workflow Pattern)

This document keeps track of the architecture, concepts learned, source data definitions, and execution walkthrough for Phase 5 of the Scholarship Navigator Agent.

---

## What Is a Parallel Workflow?

A **Parallel Workflow** executes multiple independent tasks at the same time (concurrently) rather than waiting for them to complete sequentially. The outputs of these parallel tasks are then aggregated, deduplicated, and unified into a single coherent response.

---

## Why Parallel Workflows Matter

### Without a Parallel Workflow (Sequential Search Pattern)
When searching multiple independent scholarship databases (such as National, State, University, and Private listings), the agent is forced to process them sequentially:
```text
Search NSP
    ↓
Search State
    ↓
Search University
    ↓
Search Private
```
* **High Latency:** Sequential operations multiply the network/disk latency of each search, resulting in very slow response times.
* **Poor Scalability:** Adding a fifth or sixth database source further slows down the execution linearly.

### With a Parallel Workflow
The search process is executed concurrently across four independent specialist source agents:
```text
          Parallel Search
 ├── NSP Agent (National)
 ├── State Agent (State-specific)
 ├── University Agent (Campus level)
 └── Private Agent (Corporate/NGO)
```
* **Extremely Fast:** All database lookups occur at the same time. The total search latency is capped at the speed of the single slowest lookup.
* **Better Scalability:** Additional search providers can be integrated and queried concurrently without affecting overall system latency.
* **Domain Specialization:** Each source agent is dedicated to a single database schema and dataset format, keeping tool-calling prompts highly specialized.

---

## Architecture Diagram

```text
User
 ↓
Router Agent (ScholarshipRouterAgent)
 ↓ (UG Route)
Profile Agent (Normalizes Profile Input)
 ↓
Eligibility Agent (Validates Marks & Income Limits)
 ↓

 Parallel Search (Orchestrated by ParallelScholarshipSearchAgent)

 ├── NSP Agent (reads nsp_scholarships.json)
 ├── State Agent (reads state_scholarships.json)
 ├── University Agent (reads university_scholarships.json)
 └── Private Agent (reads private_scholarships.json)

 ↓ (Wait for all to finish)

Merge & Deduplicate (Merges items by ID/Name, removing duplicates)
 ↓
Response
```

---

## ADK Concepts Learned

### 1. Parallel Agents
* **Concurrent Execution:** Using ADK's `ParallelAgent`, sub-agents execute concurrently in isolated async multitasking contexts.
* **Contextvars Isolation:** We leverage Python's `contextvars` to dynamically set and isolate the active database file (`nsp_scholarships.json` etc.) for each respective agent, keeping Phase 2 tools completely unchanged and reusable.

### 2. Result Aggregation
* **Structured Outputs:** Each source agent is configured with `SourceScholarshipOutput` which serializes lists of matching scholarships.
* **Cognitive Merge:** The orchestrator reads all serialized outputs from the context, merges them, and formats a clean breakdown.

### 3. Deduplication
* **Logical Deduplication:** Multi-sourced scholarships (e.g. `National Merit Scholarship` appearing in both NSP and University listings) are filtered to appear only once in the final user card using `id` or `name` matching.

---

## Execution Walkthrough

1. **Profile validated & Eligibility verified**: The student profile is evaluated as eligible by the profile and eligibility agents.
2. **Four source agents launched**: The `ParallelScholarshipSearchAgent` triggers `ParallelScholarshipSearchWorkflow`. Under the hood:
   - `NSPScholarshipAgent` executes and sets context source to `"nsp"`.
   - `StateScholarshipAgent` executes and sets context source to `"state"`.
   - `UniversityScholarshipAgent` executes and sets context source to `"university"`.
   - `PrivateScholarshipAgent` executes and sets context source to `"private"`.
3. **Results collected**: The ADK runner waits for all four source lookups to complete and writes their structured results to the context.
4. **Duplicates removed**: The orchestrator merges the lists and filters out any duplicates.
5. **Response generated**: Renders the unified breakdown with clear category groupings.
