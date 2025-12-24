"""
Laminar integration for Live API observability.

Provides comprehensive tracing for session lifecycle, latency,
token usage, and tool invocations.
"""

import os
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager
from dotenv import load_dotenv

try:
    from lmnr import Laminar as L, observe
    LAMINAR_AVAILABLE = True
except ImportError:
    LAMINAR_AVAILABLE = False
    print("⚠️  Laminar not available. Install with: pip install lmnr")

load_dotenv()


class LaminarTracer:
    """
    Laminar observability integration for Live API.
    
    Features:
    - Session lifecycle event tracking
    - Latency measurement per turn
    - Token usage tracking
    - Tool invocation timing
    - Error capture and recovery tracking
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize Laminar tracer.
        
        Args:
            enabled: Whether to enable tracing
        """
        self.enabled = enabled and LAMINAR_AVAILABLE
        
        if self.enabled:
            api_key = os.getenv("LAMINAR_API_KEY")
            if api_key:
                L.initialize(project_api_key=api_key)
                print("✅ Laminar tracing initialized")
            else:
                self.enabled = False
                print("⚠️  LAMINAR_API_KEY not set, tracing disabled")
        
        self._session_id: Optional[str] = None
        self._turn_count = 0
        self._turn_start_time: Optional[float] = None
    
    def set_session_id(self, session_id: str):
        """Set the current session ID for grouping traces."""
        self._session_id = session_id
    
    @contextmanager
    def trace_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for tracing an entire session.
        
        Args:
            session_id: Unique session identifier
            metadata: Optional metadata to attach
        """
        self.set_session_id(session_id)
        start_time = time.time()
        
        if self.enabled:
            with L.start_as_current_span(
                name="live_api_session",
                input={"session_id": session_id, **(metadata or {})},
            ) as span:
                try:
                    yield span
                finally:
                    duration = time.time() - start_time
                    span.set_attribute("duration_seconds", duration)
                    span.set_attribute("total_turns", self._turn_count)
        else:
            yield None
    
    @contextmanager
    def trace_turn(self, turn_number: int, input_text: Optional[str] = None):
        """
        Context manager for tracing a single conversation turn.
        
        Args:
            turn_number: Turn number in conversation
            input_text: Optional user input text
        """
        self._turn_count = turn_number
        self._turn_start_time = time.time()
        
        if self.enabled:
            with L.start_as_current_span(
                name="conversation_turn",
                input={
                    "turn_number": turn_number,
                    "session_id": self._session_id,
                    "input_text": input_text,
                },
            ) as span:
                try:
                    yield span
                finally:
                    if self._turn_start_time:
                        latency = time.time() - self._turn_start_time
                        span.set_attribute("latency_ms", latency * 1000)
        else:
            yield None
    
    @contextmanager
    def trace_tool_call(self, tool_name: str, arguments: Dict[str, Any]):
        """
        Context manager for tracing tool execution.
        
        Args:
            tool_name: Name of the tool being called
            arguments: Tool arguments
        """
        start_time = time.time()
        
        if self.enabled:
            with L.start_as_current_span(
                name=f"tool_call_{tool_name}",
                input={
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "session_id": self._session_id,
                },
            ) as span:
                try:
                    yield span
                finally:
                    duration = time.time() - start_time
                    span.set_attribute("execution_time_ms", duration * 1000)
        else:
            yield None
    
    def track_token_usage(self, input_tokens: int, output_tokens: int):
        """
        Track token usage for the current turn.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        if self.enabled:
            try:
                span = L.get_current_span()
                if span:
                    span.set_attribute("input_tokens", input_tokens)
                    span.set_attribute("output_tokens", output_tokens)
                    span.set_attribute("total_tokens", input_tokens + output_tokens)
            except:
                pass
    
    def track_audio_metrics(self, audio_duration_ms: float, chunk_count: int):
        """
        Track audio streaming metrics.
        
        Args:
            audio_duration_ms: Duration of audio in milliseconds
            chunk_count: Number of audio chunks
        """
        if self.enabled:
            try:
                span = L.get_current_span()
                if span:
                    span.set_attribute("audio_duration_ms", audio_duration_ms)
                    span.set_attribute("audio_chunk_count", chunk_count)
            except:
                pass
    
    def track_error(self, error: Exception, context: Optional[str] = None):
        """
        Track an error occurrence.
        
        Args:
            error: Exception that occurred
            context: Optional context description
        """
        if self.enabled:
            try:
                span = L.get_current_span()
                if span:
                    span.set_attribute("error", True)
                    span.set_attribute("error_type", type(error).__name__)
                    span.set_attribute("error_message", str(error))
                    if context:
                        span.set_attribute("error_context", context)
            except:
                pass
    
    def track_state_change(self, old_state: str, new_state: str):
        """
        Track session state changes.
        
        Args:
            old_state: Previous state
            new_state: New state
        """
        if self.enabled:
            try:
                span = L.get_current_span()
                if span:
                    span.add_event(
                        "state_change",
                        attributes={
                            "from_state": old_state,
                            "to_state": new_state,
                        }
                    )
            except:
                pass
    
    def track_interruption(self):
        """Track when user interrupts the model."""
        if self.enabled:
            try:
                span = L.get_current_span()
                if span:
                    span.add_event("user_interruption")
                    span.set_attribute("interrupted", True)
            except:
                pass


# Global tracer instance
_tracer: Optional[LaminarTracer] = None


def get_tracer() -> LaminarTracer:
    """Get or create global tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = LaminarTracer()
    return _tracer


def initialize_tracing(enabled: bool = True):
    """
    Initialize Laminar tracing.
    
    Args:
        enabled: Whether to enable tracing
    """
    global _tracer
    _tracer = LaminarTracer(enabled=enabled)
    return _tracer
