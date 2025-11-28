# Gemini Text-to-Text Bot with Laminar Integration

This project implements a robust text-to-text bot using Google's Gemini models, integrated with Laminar for observability.

## Features

-   **Interactive Chat**: Standard text generation.
-   **Thinking Mode**: Uses Gemini's thinking capabilities for complex reasoning.
-   **Function Calling**: Integrated mock tools (Weather, Calculator) for real-time answers.
-   **Long Context**: Handles large context windows.
-   **Laminar Observability**: Full tracing of requests, responses, and tool usage with session management.

## Setup

1.  **Install Dependencies**:
    ```bash
    uv sync
    ```

2.  **Environment Variables**:
    Ensure you have the following set (or configured in `config.py`):
    -   `GOOGLE_API_KEY`
    -   `LMNR_PROJECT_API_KEY`

## Usage

### Interactive Mode
Run the bot in interactive mode:
```bash
uv run main.py
```

**Commands**:
-   `/think <prompt>`: Use thinking mode.
-   `/tools <prompt>`: Use tools.
-   `/long <prompt>`: Test long context.
-   `/quit`: Exit.

## Project Structure

-   `bot.py`: Core `GeminiBot` class with Laminar instrumentation.
-   `config.py`: Configuration and client initialization.
-   `tools.py`: Mock tool definitions.
-   `main.py`: CLI entry point.
-   `test_bot.py`: Automated verification script.
