"""
Tool executor for orchestrating function calls during Live API sessions.

Handles tool registration, execution, and result formatting.
"""

import asyncio
import inspect
from typing import Callable, Dict, Any, Optional
from google.genai import types


class ToolExecutor:
    """
    Orchestrates tool execution for Live API function calling.
    
    Features:
    - Decorator-based tool registration
    - Async tool execution
    - Result formatting for Live API
    - Error handling and timeouts
    """
    
    def __init__(self, timeout: float = 30.0):
        """
        Initialize tool executor.
        
        Args:
            timeout: Maximum execution time for tools (seconds)
        """
        self.timeout = timeout
        self._tools: Dict[str, Callable] = {}
        self._tool_declarations: list = []
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Optional[dict] = None,
    ):
        """
        Decorator to register a tool function.
        
        Args:
            name: Tool function name
            description: Tool description for the model
            parameters: JSON schema for parameters
            
        Example:
            @executor.register_tool(
                name="get_weather",
                description="Get weather for a location",
                parameters={
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    }
                }
            )
            async def get_weather(location: str) -> dict:
                return {"temperature": 72}
        """
        def decorator(func: Callable):
            # Store the function
            self._tools[name] = func
            
            # Create function declaration for Gemini
            declaration = {
                "name": name,
                "description": description,
            }
            
            if parameters:
                declaration["parameters"] = parameters
            
            self._tool_declarations.append(declaration)
            
            return func
        
        return decorator
    
    def get_tool_declarations(self) -> list:
        """
        Get tool declarations for Live API configuration.
        
        Returns:
            List of function declarations
        """
        return [{"function_declarations": self._tool_declarations}]
    
    async def execute_tool(
        self,
        function_call: Any,
    ) -> types.FunctionResponse:
        """
        Execute a tool function call.
        
        Args:
            function_call: FunctionCall object from Live API
            
        Returns:
            FunctionResponse with execution result
        """
        func_name = function_call.name
        
        if func_name not in self._tools:
            return types.FunctionResponse(
                id=function_call.id,
                name=func_name,
                response={
                    "error": f"Unknown function: {func_name}"
                }
            )
        
        try:
            # Get the function
            func = self._tools[func_name]
            
            # Parse arguments
            args = function_call.args or {}
            
            # Execute with timeout
            if inspect.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(**args),
                    timeout=self.timeout
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(func, **args),
                    timeout=self.timeout
                )
            
            return types.FunctionResponse(
                id=function_call.id,
                name=func_name,
                response={"result": result}
            )
            
        except asyncio.TimeoutError:
            return types.FunctionResponse(
                id=function_call.id,
                name=func_name,
                response={
                    "error": f"Function execution timed out after {self.timeout}s"
                }
            )
        except Exception as e:
            return types.FunctionResponse(
                id=function_call.id,
                name=func_name,
                response={
                    "error": f"Function execution failed: {str(e)}"
                }
            )
    
    async def execute_multiple(
        self,
        function_calls: list,
    ) -> list:
        """
        Execute multiple tool calls in parallel.
        
        Args:
            function_calls: List of FunctionCall objects
            
        Returns:
            List of FunctionResponse objects
        """
        tasks = [
            self.execute_tool(fc)
            for fc in function_calls
        ]
        
        return await asyncio.gather(*tasks)
