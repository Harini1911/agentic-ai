# Phase 4: Details, Architecture, and Concepts Learned (Sequential Workflow Pattern)

This document keeps track of the architecture, concepts learned, early exit rules, and execution walkthrough for Phase 4 of the Scholarship Navigator Agent.

---

## What Is a Sequential Workflow?

A **Sequential Workflow** executes multiple agents in a fixed, predefined order. The output of one agent automatically becomes the input of the next agent (a data pipeline/chain).

Each step in the sequence is dependent on the success of the previous step.

---

## Why Sequential Workflows Matter

### Without Sequential Workflow (Monolithic Agent Pattern)
As domain rules grow (such as validating inputs, checking custom threshold eligibility, performing data searches, and formatting outputs), a single agent tries to do everything in one prompt.
* **Lack of Isolation:** If validation logic fails, the agent might still try to query the search tool or output a malformed recommendation.
* **Testing Difficulty:** You cannot test validation, eligibility checking, or search logic independently.
* **Fragile Prompts:** Changes to eligibility thresholds require modifying a complex system prompt that also does routing and details formatting.

### With Sequential Workflow
The pipeline splits a single specialized agent into an ordered chain of three lightweight agents:
```text
Profile Agent (Normalize)
       ↓
Eligibility Agent (Validate Limits)
       ↓
Scholarship Search Agent (Search & Format)
```
* **Modular Design:** Each agent does exactly one job.
* **Early Exit Execution:** If the `Eligibility Agent` determines that the student is ineligible, the workflow terminates immediately (early exit), saving LLM inference tokens.
* **Reusable Components:** The same `ProfileAgent` and `EligibilityAgent` logic is shared across all category branches.

---

## Architecture Diagram

```text
User
 ↓
Router Agent (ScholarshipRouterAgent)
 ↓ (Routes based on tier)
UG Workflow (UGScholarshipAgent - Sequential Pipeline)
 │
 ├── Profile Agent (Normalizes Profile Input)
 │      ↓ (writes to profile_data key)
 ├── Eligibility Agent (Validates Marks & Income Limits)
 │      ↓ (writes to eligibility_data key)
 └── Scholarship Search Agent (Retrieves Scholarships via Tools)
        ↓
     Tool Layer
        ↓
  Scholarship Dataset
```

---

## ADK Concepts Learned

### 1. Sequential Execution
* **Ordered Execution:** The ADK `SequentialAgent` executes a series of sub-agents one after another in a linear pipeline.
* **Pipeline Design:** Decouples normalization, boundary checks, and tool execution into distinct operational nodes.

### 2. Agent Chaining
* **Shared Session State:** The ADK maintains a shared `InvocationContext` across all sub-agents in a sequential run.
* **Output Context Keys:** We use `output_key="profile_data"` for `ProfileAgent` and `output_key="eligibility_data"` for `EligibilityAgent`. Subsequent agents refer to these keys (e.g. `{profile_data}`) to consume structured data from upstream.

### 3. Early Exit
* **Conditional Interruption:** The `ScholarshipSearchAgent` checks the `eligibility_data` context key first. If `eligible` is false, it immediately stops and prints a specialized failure message, bypassing tool executions.

---

## Execution Walkthrough

### Scenario A: Successful Match (Marks 92%, Income ₹2.5L)
1. **User submits profile**: The B.Tech profile is routed to `UGScholarshipAgent`.
2. **Profile Agent**: Normalizes inputs and writes `"profile_valid": true` to `profile_data`.
3. **Eligibility Agent**: Evaluates `profile_data` against thresholds (Marks 92% >= 60%, Income 2.5L <= 10L) and writes `"eligible": true` to `eligibility_data`.
4. **Scholarship Search Agent**: Sees `"eligible": true`, triggers tool calls to search scholarships, and returns the final recommendations.

### Scenario B: Failure / Early Exit (Marks 45%, Income ₹2.5L)
1. **User submits profile**: The B.Tech profile is routed to `UGScholarshipAgent`.
2. **Profile Agent**: Normalizes inputs and writes `"profile_valid": true` to `profile_data`.
3. **Eligibility Agent**: Evaluates `profile_data` against thresholds (Marks 45% < 60%) and writes `"eligible": false`, `"reason": "Marks below 60%"` to `eligibility_data`.
4. **Scholarship Search Agent**: Sees `"eligible": false` and immediately exits the pipeline, rendering:
   ```text
   Unfortunately you do not meet the minimum scholarship eligibility requirements.

   Reason:
   Marks below 60%.
   ```
