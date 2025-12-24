# Agentic AI with Gemini

This repository contains projects and examples demonstrating Agentic AI capabilities using Google's Gemini API.

## Structure

-   **`t2t-bot/`**: The main Text-to-Text Bot project. A comprehensive, observable, and dynamically capable bot with:
    -   Interactive Chat
    -   Dynamic Thinking Mode
    -   Automatic Tool Usage (Weather)
    -   Long Context Support
    -   Laminar Observability

-   **`examples/`**: Experimental scripts and examples.
    -   `thinking/`: Examples of Gemini's thinking process (Basic, Summaries, Budgeting).
    -   `text2text/`: Earlier experiments with logging and text generation.

## Getting Started

This repository is managed with `uv`.

1.  **Install dependencies**:
    ```bash
    uv sync
    ```

2.  **Run the Bot**:
    ```bash
    cd t2t-bot
    uv run main.py
    ```

3.  **Run Examples**:
    ```bash
    cd examples/thinking
    uv run basic_thinking.py
    ```

## Environment Variables

Create a `.env` file in the project directories (or root if shared) with:
```
GOOGLE_API_KEY=your_gemini_api_key
LMNR_PROJECT_API_KEY=your_laminar_api_key
```
