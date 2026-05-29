# Phase 6: Details, Architecture, and Concepts Learned (Loop Workflow Pattern)

This document keeps track of the architecture, concepts learned, validation rules, and execution walkthrough for Phase 6 of the Scholarship Navigator Agent.

---

## What Is a Loop Workflow?

A **Loop Workflow** repeatedly executes a set of tasks (checking conditions, prompting for user action, and validating outputs) in a loop until a specific termination condition is satisfied. In this phase, the loop continues executing as long as the student's profile contains missing required fields.

---

## Why Loop Workflows Matter

### Without a Loop Workflow (Static Profile Check)
When the student inputs an incomplete profile, the system either crashes, returns a generic error, or fails to find matches because critical parameters (like family income, latest marks, or current state of study) are missing:
```text
Incomplete Profile
       ↓
Workflow Starts
       ↓
Missing Critical Fields (marks_percentage, annual_income, etc.)
       ↓
Workflow Fails / Rejects
```
* **Poor User Experience:** The user is forced to re-submit their entire profile from scratch with all fields correctly specified.
* **Inflexible Integration:** The system cannot adapt to users who do not know the required format or omit key fields.

### With a Loop Workflow (Active Completion Pattern)
The workflow dynamically intercepts the student profile and runs a completing loop before commencing searches:
```text
           Incomplete Profile
                   ↓
      Check: Any Missing Fields?
         ├── Yes: Generate specific prompt using ProfileCompletionAgent
         │        Collect user answer & perform validation
         │        Update profile state & check again
         └── No:  [Exit Loop] -> Pass to sequential & parallel workflows
```
* **Premium User Experience:** The system dynamically asks only for the specific fields that are missing, providing clear examples and normalizations.
* **Resilient Workflows:** Ensure that subsequent agents (Router, ProfileAgent, EligibilityAgent, Parallel Search) receive a 100% complete and validated dataset.
* **Self-Correcting:** Gracefully handles invalid inputs (e.g. non-numeric incomes, invalid percentages) and continues prompting without losing previously entered details.

---

## Architecture Diagram

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

---

## ADK Concepts Learned

### 1. Loop Workflow Pattern
* **Dynamic Evaluation:** The program uses a conditional loop that queries the completion status of the profile state, dynamically shifting prompts as fields are completed.
* **Agentic Question Generation:** Instead of hardcoded strings, we query the ADK-powered `ProfileCompletionAgent` with the current state of the profile. The agent uses LLM capability to detect the next missing field and output the exact user-friendly prompt.

### 2. State Updates
* **State Preservation:** The state of the student profile is continuously mutated and updated across iterations, ensuring previously entered valid inputs are kept while resolving outstanding missing fields.

### 3. Input Validation and Normalization
* **Strict Constraints:** Prevents garbage input from passing through. Enforces numeric checks for income, `0-100` range for marks, and matches strings into valid tiers.
* **Data Normalization:** Translates informal user responses into standard values (e.g. converting `"abroad"` to `"International"`, `"b.tech"` to `"B.Tech"`, and commas in incomes like `"2,50,000"` to float `250000.0`).

---

## Execution Walkthrough

1. **Incomplete Profile Loaded:** The app is executed with an incomplete profile (e.g. missing `annual_income`, `marks_percentage`, and `country_preference`).
2. **Missing Fields Detected:** The workflow identifies `annual_income`, `marks_percentage`, and `country_preference` as missing.
3. **Iteration 1 (Annual Income):**
   - `ProfileCompletionAgent` generates the question: `"What is your annual family income in INR?"`.
   - User inputs an invalid value (e.g. `"abc"`).
   - Validation fails: prints `"Please enter a valid numeric income."` and loops again for `annual_income`.
   - User inputs a valid value (e.g. `"2,50,000"`).
   - Validation succeeds, normalizes value to `250000.0`, and updates the profile.
4. **Iteration 2 (Marks Percentage):**
   - `ProfileCompletionAgent` generates the question: `"What is your latest percentage or CGPA?"`.
   - User inputs `"92"`.
   - Validation succeeds, normalizes value to `92.0`, and updates the profile.
5. **Iteration 3 (Country Preference):**
   - `ProfileCompletionAgent` generates the question: `"Are you looking for scholarships in India or internationally?"`.
   - User inputs `"India"`.
   - Validation succeeds, updates country preference to `"India"`.
6. **Loop Terminated:** The profile contains all 5 required fields. The completion loop exits.
7. **Router and Search Workflow Commences:** The completed profile is passed to the `ScholarshipRouterAgent`, which correctly delegates to `UGScholarshipAgent`, executes Profile normalization, runs Eligibility criteria validation, performs parallel database searches, and returns the unified recommendations.
