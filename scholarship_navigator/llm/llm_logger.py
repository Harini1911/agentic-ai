"""
llm/llm_logger.py — Structured LLM Request/Response Logger

Writes to both console and a rotating log file under logs/llm.log.
All entries follow the format:
    [LEVEL] timestamp | Provider | Model | Latency | Message
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Resolve the logs/ directory relative to this file's location
_LOG_DIR = Path(__file__).parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)
_LOG_FILE = _LOG_DIR / "llm.log"

# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------
llm_logger = logging.getLogger("scholarship_navigator.llm")
llm_logger.setLevel(logging.DEBUG)

# Avoid adding handlers multiple times in interactive/reload environments
if not llm_logger.handlers:
    _fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Console handler — INFO and above
    _console = logging.StreamHandler()
    _console.setLevel(logging.INFO)
    _console.setFormatter(_fmt)
    llm_logger.addHandler(_console)

    # Rotating file handler — DEBUG and above, max 5 MB × 3 backups
    _file = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    _file.setLevel(logging.DEBUG)
    _file.setFormatter(_fmt)
    llm_logger.addHandler(_file)
