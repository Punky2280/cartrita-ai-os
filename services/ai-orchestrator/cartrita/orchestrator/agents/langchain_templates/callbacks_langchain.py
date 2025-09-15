"""
LangChain Callbacks Template for Cartrita
Implements callback patterns for monitoring and debugging
"""

from typing import Any, Dict, List, Optional, Union
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult
import logging
from datetime import datetime

class CartritaCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for Cartrita agents"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None
        self.metrics = {
            "llm_calls": 0,
            "tool_calls": 0,
            "errors": 0,
            "tokens_used": 0
        }

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Called when LLM starts"""
        self.metrics["llm_calls"] += 1
        self.logger.debug(f"LLM started with {len(prompts)} prompts")

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM ends"""
        # Track tokens if available
        if hasattr(response, "llm_output") and response.llm_output:
            if "token_usage" in response.llm_output:
                self.metrics["tokens_used"] += response.llm_output["token_usage"].get("total_tokens", 0)

        self.logger.debug("LLM completed successfully")

    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Called when LLM errors"""
        self.metrics["errors"] += 1
        self.logger.error(f"LLM error: {error}")

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Called when tool starts"""
        self.metrics["tool_calls"] += 1
        tool_name = serialized.get("name", "unknown")
        self.logger.debug(f"Tool {tool_name} started with input: {input_str[:100]}")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when tool ends"""
        self.logger.debug(f"Tool completed with output: {output[:100]}")

    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Called when tool errors"""
        self.metrics["errors"] += 1
        self.logger.error(f"Tool error: {error}")

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> None:
        """Called when agent takes an action"""
        self.logger.info(f"Agent action: {action.tool} with input: {action.tool_input}")

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """Called when agent finishes"""
        self.logger.info(f"Agent finished: {finish.return_values}")

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Called when chain starts"""
        self.start_time = datetime.now()
        self.logger.info(f"Chain started: {serialized.get('name', 'unknown')}")

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Called when chain ends"""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            self.logger.info(f"Chain completed in {duration:.2f} seconds")
        self.logger.debug(f"Chain outputs: {outputs}")

    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Called when chain errors"""
        self.metrics["errors"] += 1
        self.logger.error(f"Chain error: {error}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics"""
        return self.metrics.copy()

    def reset_metrics(self) -> None:
        """Reset metrics"""
        self.metrics = {
            "llm_calls": 0,
            "tool_calls": 0,
            "errors": 0,
            "tokens_used": 0
        }

class CartritaStreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming responses"""

    def __init__(self, stream_handler: Callable[[str], None]):
        self.stream_handler = stream_handler

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Called when LLM generates a new token"""
        self.stream_handler(token)

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Stream tool execution start"""
        tool_name = serialized.get("name", "unknown")
        self.stream_handler(f"\n[Executing {tool_name}...]\n")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Stream tool execution end"""
        self.stream_handler(f"\n[Tool result: {output[:100]}...]\n")
