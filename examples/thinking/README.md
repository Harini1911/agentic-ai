# Gemini Thinking Examples

This directory contains examples of using the Gemini Thinking model capabilities, replicated from the [official documentation](https://ai.google.dev/gemini-api/docs/thinking).

## Setup

1.  Ensure you have the `google-genai` library installed:
    ```bash
    uv add google-genai
    ```
2.  Set your `GOOGLE_API_KEY` environment variable or ensure it's configured in `config.py`.

## Examples

### 1. Basic Thinking
Generates content using the thinking model.
```bash
uv run basic_thinking.py
```
Logs are written to `logs/basic_thinking.log`.

### 2. Thought Summaries (Streaming)
Demonstrates how to access thought chains during streaming.
```bash
uv run thought_summaries.py
```
Logs are written to `logs/thought_summaries.log`.

### 3. Thinking Budgets
Shows how to control the thinking process with a token budget.
```bash
uv run thinking_budget.py
```
Logs are written to `logs/thinking_budget.log`.
