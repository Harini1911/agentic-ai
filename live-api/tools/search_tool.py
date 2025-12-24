"""
Google Search tool using Gemini's built-in grounding capability.

This tool leverages Gemini's native Google Search integration
for real-time information retrieval.
"""

from typing import Dict, Any


# Google Search is built into Gemini Live API
# We just need to configure it in the session config
GOOGLE_SEARCH_TOOL = {"google_search": {}}


def parse_search_results(response) -> Dict[str, Any]:
    """
    Parse search results from Gemini response.
    
    Args:
        response: Response object from Live API
        
    Returns:
        Parsed search results with queries and code execution
    """
    results = {
        "search_performed": False,
        "queries": [],
        "code_executed": [],
        "results": [],
    }
    
    if not response.server_content:
        return results
    
    model_turn = response.server_content.model_turn
    if not model_turn:
        return results
    
    for part in model_turn.parts:
        # Check for executable code (search queries)
        if part.executable_code is not None:
            results["search_performed"] = True
            results["code_executed"].append({
                "language": part.executable_code.language,
                "code": part.executable_code.code,
            })
        
        # Check for code execution results
        if part.code_execution_result is not None:
            results["results"].append({
                "outcome": part.code_execution_result.outcome,
                "output": part.code_execution_result.output,
            })
    
    return results


def format_search_summary(search_results: Dict[str, Any]) -> str:
    """
    Format search results into a readable summary.
    
    Args:
        search_results: Parsed search results
        
    Returns:
        Formatted string summary
    """
    if not search_results["search_performed"]:
        return "No search performed"
    
    summary = "🔍 Google Search Results:\n\n"
    
    for i, code in enumerate(search_results["code_executed"], 1):
        summary += f"Query {i}:\n{code['code']}\n\n"
    
    for i, result in enumerate(search_results["results"], 1):
        summary += f"Result {i}:\n"
        summary += f"Status: {result['outcome']}\n"
        summary += f"Output: {result['output'][:200]}...\n\n"
    
    return summary


# Note: Google Search doesn't require function calling setup
# It's automatically invoked by the model when needed
# Just include GOOGLE_SEARCH_TOOL in the session config
