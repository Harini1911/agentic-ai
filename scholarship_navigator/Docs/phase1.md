# Phase 1: Details, Architecture, and Concepts Learned

This document keeps track of the architecture, concepts learned, schemas, and future roadmap elements for Phase 1 of the Scholarship Navigator Agent.

---

## Architecture & Flow

### System Architecture
The following diagram showcases how a student profile flows from user input through the AI agent to deterministic database retrieval and back.

```text
       User Input (Student Profile)
                  ↓
          ScholarshipAgent (ADK LLM Agent)
                  ↓ (Automatic Tool Call)
       search_scholarships() (Search Tool)
                  ↓ (Local File Read)
         scholarships.json (Database)
```

### Agent Flow Sequence
1. **User submits profile:** The user submits a student profile (either via command-line interactive prompts or default JSON payload).
2. **Agent receives profile:** The `ScholarshipAgent` receives the profile text and parses the student's credentials.
3. **Agent calls search tool:** Under the hood, the agent dynamically decides to call the `search_scholarships()` tool with structured parameters extracted from the user's input.
4. **Tool filters scholarships:** The python search tool reads `data/scholarships.json` and performs deterministic math comparisons to verify exact eligibility (education level, marks boundaries, income limits).
5. **Agent summarizes results:** The tool returns a list of eligible scholarships. The agent consumes this data, matches it with its instructions, and synthesizes a user-friendly response.
6. **Response returned:** The finalized and formatted scholarship recommendations are streamed back to the user.

---

## ADK Concepts Learned

### 1. Agent (`Agent` / `LlmAgent`)
An **ADK Agent** is the core cognitive component of the framework. It encapsulates an LLM's reasoning loop.
* **Why use one?** Instead of coding complex logic state-machines, an agent allows us to write declaratively. The agent is responsible for understanding developer instructions, maintaining execution context, making decisions about which tools to call, and formatting the output.
* **Role of ScholarshipAgent:** In this application, `ScholarshipAgent` serves as the front-of-house coordinator. It parses user profiles and handles user-facing explanation logic.

### 2. Instructions (`system_instruction`)
Instructions define the agent's identity, system prompts, operational boundaries, and formatting requirements.
* **Why instructions matter:** They ensure the LLM behaves consistently, respects constraints (such as refusing to guess data it doesn't have), and formats outputs exactly as expected (e.g. matching a specific output layout) rather than responding with generic text.

### 3. Tools (`Callable` / `BaseTool`)
Tools are standard python functions that the agent can execute to interact with external environments, databases, or local files.
* **Why tools are used instead of hardcoding logic:** LLMs excel at language understanding but struggle with precise mathematics (such as checking if `250000 <= 300000`) and lack direct access to local files. Passing `search_scholarships()` as a tool allows the agent to delegate precise filtering to deterministic Python code.
* **How search_scholarships() works:** The tool takes structured parameters (`education_level`, `annual_income`, `marks_percentage`) extracted automatically from the user input by the LLM, reads `data/scholarships.json`, filters out ineligible records, and outputs JSON-like lists of matching opportunities.

### 4. Structured Data Schemas
To guarantee reliable communication between the agent, tools, and user interface, strict structural contracts are defined:

#### Scholarship Dataset Schema (`data/scholarships.json`)
```json
{
  "name": "string",
  "min_marks": "int (min score percentage to qualify)",
  "max_income": "int (maximum annual family income in INR)",
  "education_level": "string",
  "amount": "int (scholarship award amount in INR)"
}
```

#### Tool Input Schema (`search_scholarships()`)
```json
{
  "education_level": "string",
  "annual_income": "number",
  "marks_percentage": "number"
}
```

#### Tool Output Schema
```json
[
  {
    "name": "string",
    "amount": "number",
    "reason": "string"
  }
]
```

---

## Future Roadmap

* **Phase 2: Multi-Agent Orchestration**
  * Introduce separate agents for different stages: `Profile Parsing Agent`, `Eligibility Verification Agent`, and a `Coordinator Agent` to route traffic.
* **Phase 3: Parallel Search Agents**
  * Execute multiple scholarship search routines in parallel using ADK's `ParallelAgent` class to crawl different datastores simultaneously.
* **Phase 4: Database Integration**
  * Migrate from static JSON files to structured relational SQL databases (PostgreSQL/Supabase) to support scalable querying.
* **Phase 5: Memory Management**
  * Integrate conversational and persistent memory to track user profile updates, past matches, and application statuses across sessions.
* **Phase 6: OCR Document Processing**
  * Support document uploads (transcripts, tax forms, residency certificates) and analyze them using multi-modal capabilities to verify claims.
* **Phase 7: Deadline Tracking & Notifications**
  * Add automatic scheduling engines to send email alerts, tracking upcoming scholarship close dates and deadlines.
