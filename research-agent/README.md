# Multi-Modal Research Agent

A powerful AI agent capable of performing research using **text**, **documents (PDFs)**, and **audio**. It leverages Google's Gemini models for multi-modal understanding and outputs structured, machine-readable data.

## Features

-   **Multi-Modal Input**: Accepts text queries, PDF documents, and audio files (WAV, MP3, etc.).
-   **Structured Output**: Returns research findings as consistent JSON objects (Dictionary keyed by topic), making it easy to integrate into other applications.
-   **Audio Processing**: Automatically converts and uploads audio files for analysis.
-   **Observability**: Integrated with **Laminar** for real-time tracing and debugging of agent execution.
-   **Type Safety**: Built with **Pydantic** for robust data validation and schema definition.

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
    Copy the example file and add your API keys:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` and fill in:
    -   `GEMINI_API_KEY`: Your Google Gemini API key.
    -   `LAMINAR_API_KEY`: Your Laminar project API key (for tracing).

## Usage

### Basic Run
To run the agent with the default test query and sample PDF (if present):

```bash
uv run main.py
```

This will:
1.  Analyze a simple text query ("What is the capital of France?").
2.  Look for `sample_research.pdf`.
3.  If found, upload it to Gemini, analyze it ("Applications of AI in healthcare"), and print the structured results.
4.  Clean up the uploaded file.

### Generating a Sample PDF
If you don't have a PDF to test with, generate one:

```bash
uv run create_sample_pdf.py
```

## Project Structure

-   `main.py`: Core logic, Pydantic schemas, and Gemini client setup.
-   `tools.py`: Utilities for file uploading and audio processing.
