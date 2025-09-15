"""
LangChain Tool Template for Cartrita
Standard tool implementation following LangChain patterns
"""

from typing import Any, Optional, Type
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from pydantic import BaseModel, Field

class CartritaToolInput(BaseModel):
    """Input schema for Cartrita tools"""
    query: str = Field(..., description="Input query or command")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Additional parameters")

class CartritaBaseTool(BaseTool):
    """Base tool class for Cartrita following LangChain patterns"""

    name: str = "cartrita_tool"
    description: str = "Base Cartrita tool"
    args_schema: Type[BaseModel] = CartritaToolInput
    return_direct: bool = False

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> str:
        """
        Execute the tool synchronously

        Args:
            query: Input query
            run_manager: Callback manager
            **kwargs: Additional arguments

        Returns:
            Tool output as string
        """
        try:
            # Log tool execution
            if run_manager:
                run_manager.on_text(f"Executing {self.name} with query: {query}\n")

            # Execute tool logic
            result = self._execute(query, **kwargs)

            # Log result
            if run_manager:
                run_manager.on_text(f"Result: {result}\n")

            return result

        except Exception as e:
            error_msg = f"Error in {self.name}: {str(e)}"
            if run_manager:
                run_manager.on_text(f"Error: {error_msg}\n", color="red")
            return error_msg

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> str:
        """
        Execute the tool asynchronously

        Args:
            query: Input query
            run_manager: Async callback manager
            **kwargs: Additional arguments

        Returns:
            Tool output as string
        """
        try:
            if run_manager:
                await run_manager.on_text(f"Executing {self.name} with query: {query}\n")

            result = await self._aexecute(query, **kwargs)

            if run_manager:
                await run_manager.on_text(f"Result: {result}\n")

            return result

        except Exception as e:
            error_msg = f"Error in {self.name}: {str(e)}"
            if run_manager:
                await run_manager.on_text(f"Error: {error_msg}\n", color="red")
            return error_msg

    def _execute(self, query: str, **kwargs: Any) -> str:
        """Execute tool logic - override in subclasses"""
        raise NotImplementedError(f"{self.name} must implement _execute method")

    async def _aexecute(self, query: str, **kwargs: Any) -> str:
        """Async execute tool logic - override in subclasses"""
        # Default to sync execution
        return self._execute(query, **kwargs)

    @classmethod
    def from_function(
        cls,
        func: Callable,
        name: str,
        description: str,
        args_schema: Optional[Type[BaseModel]] = None,
        return_direct: bool = False
    ) -> "CartritaBaseTool":
        """Create tool from a function"""
        class FunctionTool(cls):
            def _execute(self, query: str, **kwargs: Any) -> str:
                return str(func(query, **kwargs))

        return FunctionTool(
            name=name,
            description=description,
            args_schema=args_schema or CartritaToolInput,
            return_direct=return_direct
        )
