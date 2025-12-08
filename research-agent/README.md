# Multi-Modal Research Agent

A powerful AI agent capable of performing research using **text**, **documents (PDFs)**, and **audio**. It leverages Google's Gemini models for multi-modal understanding, performs **grounded Google Searches**, and provides an interactive terminal interface.

## Features

-   **Interactive Chat**: A continuous terminal session for querying and file analysis.
-   **Multi-Modal Context**: Upload and analyze PDF documents and audio files (`.mp3`, `.wav`) seamlessly.
-   **Grounded Search**: Use `/search` to perform Google Searches that return structured data with verified citations (`[1](url)`).
-   **Context-Aware**: Combine file uploads with web search (e.g., "Compare this PDF with online news").
-   **Audio Output**: Generate speech from text using the `/speak` command.
-   **Structured Output**: Returns research findings as consistent JSON objects, parsing unstructed data into `ResearchPoint`s.
-   **Observability**: Integrated with **Laminar** for real-time tracing.

## Prerequisites

-   Python 3.10+
-   `uv` (fast Python package installer)
-   `ffmpeg` (required for audio processing)

## Installation

1.  **Navigate to the directory**:
    ```bash
    cd research-agent
    ```

2.  **Install dependencies**:
    ```bash
    uv sync
    ```

3.  **Set up Environment Variables**:
    Create a `.env` file and add your keys:
    ```bash
    GEMINI_API_KEY=your_key_here
    LAMINAR_API_KEY=your_key_here
    ```

## Usage

Start the interactive agent:

```bash
uv run main.py
```

### Commands

Once inside the interactive loop:

-   **/search <query>**: Perform a Google Search.
    -   *Example*: `/search What is the capital of Australia?`
    -   *Returns*: Key points with citations and a list of sources.
-   **/file <path>**: Upload a file (PDF or Audio) to the context.
    -   *Example*: `/file ./doc.pdf`
-   **/speak <text>**: text-to-speech generation.
    -   *Example*: `/speak Research complete.`
-   **Text Query**: Any other input is treated as a question about the active context.

## Project Structure

-   `main.py`: Core logic, interactive loop, and Gemini client setup.
-   `tools.py`: Utilities for Google Search grounding, audio processing, and file handling.
