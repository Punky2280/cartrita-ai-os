# Cartrita AI OS - OpenAI Service
# OpenAI API integration with streaming and tool support

"""
OpenAI service for Cartrita AI OS.
Handles OpenAI API interactions with streaming, tool use, and error handling.
"""

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import structlog
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from cartrita.orchestrator.models.schemas import (
    ChatRequest,
    ChatResponse,
    Message,
    MessageRole,
)
from cartrita.orchestrator.utils.config import settings

logger = structlog.get_logger(__name__)


class OpenAIService:
    """OpenAI service for handling chat completions and tool interactions."""

    def __init__(self):
        """Initialize OpenAI service."""
        self.client = AsyncOpenAI(
            api_key=settings.ai.openai_api_key.get_secret_value(),
            organization=settings.ai.openai_organization,
            project=settings.ai.openai_project,
        )
        self.model = settings.ai.orchestrator_model
        self.temperature = settings.ai.temperature
        self.max_tokens = settings.ai.max_tokens
        self.top_p = settings.ai.top_p
        self.frequency_penalty = settings.ai.frequency_penalty
        self.presence_penalty = settings.ai.presence_penalty

        logger.info("OpenAI service initialized", model=self.model)

    async def chat_completion(
        self,
        messages: List[ChatCompletionMessageParam],
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate chat completion with optional streaming and tool support.

        Args:
            messages: List of chat messages
            stream: Whether to stream the response
            tools: Optional list of tools/functions
            **kwargs: Additional OpenAI parameters

        Yields:
            Response chunks or final response
        """
        try:
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "top_p": self.top_p,
                "frequency_penalty": self.frequency_penalty,
                "presence_penalty": self.presence_penalty,
                "stream": stream,
                **kwargs
            }

            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = "auto"

            logger.info(
                "Making OpenAI request",
                model=self.model,
                message_count=len(messages),
                stream=stream,
                has_tools=bool(tools)
            )

            if stream:
                # Handle streaming response
                async for chunk in await self.client.chat.completions.create(**request_params):
                    if chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta

                        # Handle tool calls in streaming
                        if hasattr(delta, 'tool_calls') and delta.tool_calls:
                            for tool_call in delta.tool_calls:
                                yield {
                                    "type": "tool_call",
                                    "tool_call": {
                                        "id": tool_call.id,
                                        "function": {
                                            "name": tool_call.function.name,
                                            "arguments": tool_call.function.arguments
                                        }
                                    }
                                }

                        # Handle content
                        if hasattr(delta, 'content') and delta.content:
                            yield {
                                "type": "content",
                                "content": delta.content
                            }

                    # Check if this is the final chunk
                    if chunk.choices and chunk.choices[0].finish_reason:
                        yield {
                            "type": "done",
                            "finish_reason": chunk.choices[0].finish_reason
                        }
                        break
            else:
                # Handle non-streaming response
                response = await self.client.chat.completions.create(**request_params)

                if response.choices and response.choices[0].message:
                    message = response.choices[0].message

                    # Handle tool calls
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        for tool_call in message.tool_calls:
                            yield {
                                "type": "tool_call",
                                "tool_call": {
                                    "id": tool_call.id,
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments
                                    }
                                }
                            }

                    # Handle content
                    if hasattr(message, 'content') and message.content:
                        yield {
                            "type": "content",
                            "content": message.content
                        }

                yield {
                    "type": "done",
                    "finish_reason": response.choices[0].finish_reason if response.choices else None
                }

        except Exception as e:
            logger.error("OpenAI API error", error=str(e), error_type=type(e).__name__)
            yield {
                "type": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat request and return a structured response.

        Args:
            request: Chat request with messages and parameters

        Returns:
            ChatResponse with AI response and metadata
        """
        try:
            # Convert internal messages to OpenAI format
            openai_messages = self._convert_messages(request.messages or [])

            # Add system message if not present
            if not openai_messages or openai_messages[0].get("role") != "system":
                system_message = {
                    "role": "system",
                    "content": "You are Cartrita, an advanced AI assistant with access to various tools and capabilities. Be helpful, accurate, and efficient in your responses."
                }
                openai_messages.insert(0, system_message)

            # Add user message
            if request.message:
                user_message = {
                    "role": "user",
                    "content": request.message
                }
                openai_messages.append(user_message)

            # Prepare tools if requested
            tools = None
            if request.tools:
                tools = self._prepare_tools(request.tools)

            logger.info(
                "Processing chat request",
                conversation_id=request.conversation_id,
                message_count=len(openai_messages),
                has_tools=bool(tools)
            )

            # Collect response
            response_content = ""
            tool_calls = []
            start_time = asyncio.get_event_loop().time()

            async for chunk in self.chat_completion(
                messages=openai_messages,
                stream=request.stream,
                tools=tools,
                temperature=request.temperature or self.temperature,
                max_tokens=request.max_tokens or self.max_tokens
            ):
                if chunk["type"] == "content":
                    response_content += chunk["content"]
                elif chunk["type"] == "tool_call":
                    tool_calls.append(chunk["tool_call"])
                elif chunk["type"] == "error":
                    raise Exception(f"OpenAI API error: {chunk['error']}")

            processing_time = asyncio.get_event_loop().time() - start_time

            # Create response messages
            response_messages = []
            if response_content:
                response_messages.append(Message(
                    role=MessageRole.ASSISTANT,
                    content=response_content
                ))

            # Handle tool calls
            if tool_calls:
                for tool_call in tool_calls:
                    response_messages.append(Message(
                        role=MessageRole.ASSISTANT,
                        content=None,
                        metadata={
                            "tool_call": tool_call
                        }
                    ))

            return ChatResponse(
                response=response_content,
                conversation_id=request.conversation_id or "new",
                agent_type="openai",
                messages=response_messages,
                context=request.context,
                task_result=None,
                metadata={
                    "model": self.model,
                    "tool_calls": tool_calls if tool_calls else None
                },
                processing_time=processing_time,
                token_usage=None  # TODO: Extract from OpenAI response
            )

        except Exception as e:
            logger.error("Chat request processing failed", error=str(e))
            raise

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert internal Message objects to OpenAI format."""
        openai_messages = []

        for message in messages:
            openai_message = {
                "role": message.role.value,
                "content": message.content
            }

            if message.metadata:
                # Handle tool calls and other metadata
                if "tool_call" in message.metadata:
                    tool_call = message.metadata["tool_call"]
                    openai_message["tool_call_id"] = tool_call.get("id")
                    openai_message["content"] = tool_call.get("result", "")

            openai_messages.append(openai_message)

        return openai_messages

    def _prepare_tools(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        """Prepare tool definitions for OpenAI API."""
        # TODO: Implement tool definitions based on tool_names
        # This would map tool names to their OpenAI function definitions
        tools = []

        for tool_name in tool_names:
            if tool_name == "web_search":
                tools.append({
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search the web for information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                })
            # Add more tools as needed

        return tools

    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI service health."""
        try:
            # Simple health check by making a minimal request
            messages = [{"role": "user", "content": "Hello"}]
            async for chunk in self.chat_completion(messages, stream=False, max_tokens=1):
                if chunk["type"] == "error":
                    return {"status": "unhealthy", "error": chunk["error"]}
                break

            return {
                "status": "healthy",
                "model": self.model,
                "temperature": self.temperature
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def conversational_chat(
        self,
        conversation_id: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        voice_mode: bool = False,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Handle conversational chat with context management.

        Args:
            conversation_id: Unique conversation identifier
            user_message: User's message (text or transcribed speech)
            conversation_history: Previous messages in the conversation
            voice_mode: Whether this is a voice conversation
            **kwargs: Additional parameters

        Yields:
            Response chunks with conversation context
        """
        try:
            # Prepare conversation messages
            messages = self._prepare_conversation_messages(
                user_message, conversation_history, voice_mode
            )

            logger.info(
                "Processing conversational request",
                conversation_id=conversation_id,
                message_count=len(messages),
                voice_mode=voice_mode
            )

            # Generate response with conversation context
            async for chunk in self.chat_completion(
                messages=messages,
                stream=True,
                **kwargs
            ):
                yield chunk

        except Exception as e:
            logger.error(
                "Conversational chat failed",
                conversation_id=conversation_id,
                error=str(e)
            )
            yield {
                "type": "error",
                "error": str(e),
                "conversation_id": conversation_id
            }

    def _prepare_conversation_messages(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        voice_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Prepare messages for conversational context.

        Args:
            user_message: Current user message
            conversation_history: Previous conversation messages
            voice_mode: Whether this is voice input

        Returns:
            Formatted messages for OpenAI API
        """
        messages = []

        # Add system message for conversational AI
        system_content = self._get_conversation_system_prompt(voice_mode)
        messages.append({
            "role": "system",
            "content": system_content
        })

        # Add conversation history (limit to prevent context overflow)
        if conversation_history:
            # Keep only recent messages to stay within context limits
            recent_history = self._prune_conversation_history(conversation_history)
            messages.extend(recent_history)

        # Add current user message
        user_content = user_message
        if voice_mode:
            user_content = f"[Voice Input] {user_message}"

        messages.append({
            "role": "user",
            "content": user_content
        })

        return messages

    def _get_conversation_system_prompt(self, voice_mode: bool = False) -> str:
        """Get system prompt for conversational AI."""
        base_prompt = """You are Cartrita, an advanced AI assistant with voice capabilities.
You engage in natural, helpful conversations while maintaining context and providing accurate information.
Be conversational, friendly, and efficient in your responses."""

        if voice_mode:
            base_prompt += """
Since this is a voice conversation:
- Keep responses concise but natural
- Use conversational language
- Acknowledge voice input when appropriate
- Maintain conversation flow"""

        return base_prompt

    def _prune_conversation_history(
        self,
        history: List[Dict[str, Any]],
        max_tokens: int = 100000  # Leave room for response
    ) -> List[Dict[str, Any]]:
        """
        Prune conversation history to fit within context limits.

        Args:
            history: Full conversation history
            max_tokens: Maximum tokens to allow

        Returns:
            Pruned conversation history
        """
        # Simple pruning: keep most recent messages
        # TODO: Implement more sophisticated token-based pruning
        max_messages = 20  # Keep last 20 message pairs
        if len(history) <= max_messages:
            return history

        return history[-max_messages:]

    async def process_voice_conversation(
        self,
        conversation_id: str,
        transcribed_text: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process voice-based conversation with Deepgram integration.

        Args:
            conversation_id: Unique conversation identifier
            transcribed_text: Text transcribed from user's speech
            conversation_history: Previous conversation messages

        Yields:
            AI response chunks optimized for voice output
        """
        try:
            # Process conversational request
            async for chunk in self.conversational_chat(
                conversation_id=conversation_id,
                user_message=transcribed_text,
                conversation_history=conversation_history,
                voice_mode=True,
                temperature=0.7,  # Slightly creative for natural conversation
                max_tokens=150    # Shorter responses for voice
            ):
                yield chunk

        except Exception as e:
            logger.error(
                "Voice conversation processing failed",
                conversation_id=conversation_id,
                error=str(e)
            )
            yield {
                "type": "error",
                "error": f"Voice conversation failed: {str(e)}",
                "conversation_id": conversation_id
            }
