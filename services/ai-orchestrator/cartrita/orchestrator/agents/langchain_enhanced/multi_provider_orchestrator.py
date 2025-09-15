"""
Multi-Provider AI Orchestrator with LangChain
Leverages both OpenAI and Hugging Face APIs for optimal performance and cost
"""

import asyncio
import os
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum
from datetime import datetime
import json
from dataclasses import dataclass, field

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool, StructuredTool
from langchain_openai import OpenAIEmbeddings
from langchain_community.llms import HuggingFacePipeline
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.pydantic_v1 import BaseModel, Field
from langchain.pydantic_v1 import BaseModel as LangChainBaseModel, Field as LangChainField
import tiktoken


class ModelProvider(str, Enum):
    """AI model providers"""
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"


class TaskComplexity(str, Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    CRITICAL = "critical"


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    provider: ModelProvider
    cost_per_1k_tokens: float
    max_tokens: int
    supports_streaming: bool = True
    supports_function_calling: bool = False
    expertise_areas: List[str] = field(default_factory=list)
    quality_score: float = 1.0  # 0-1 scale


@dataclass
class TaskRequirements:
    """Requirements for a specific task"""
    complexity: TaskComplexity
    max_cost: float
    max_latency: float  # seconds
    quality_threshold: float  # 0-1 scale
    requires_function_calling: bool = False
    requires_streaming: bool = False
    domain_expertise: List[str] = field(default_factory=list)


class MultiProviderOrchestrator:
    """
    Advanced AI orchestrator that intelligently selects between OpenAI and Hugging Face models
    based on task requirements, cost constraints, and performance characteristics
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        huggingface_api_key: Optional[str] = None,
        cost_optimization: bool = True,
        fallback_strategy: bool = True,
        **kwargs
    ):
        # API Keys
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.huggingface_api_key = huggingface_api_key or os.getenv("HUGGINGFACE_API_KEY")

        # Configuration
        self.cost_optimization = cost_optimization
        self.fallback_strategy = fallback_strategy
        self.session_cost_limit = kwargs.get("session_cost_limit", 50.0)
        self.current_session_cost = 0.0

        # Model configurations
        self.available_models = self._initialize_model_configs()
        self.model_instances: Dict[str, Any] = {}

        # Performance tracking
        self.model_performance: Dict[str, Dict[str, float]] = {}
        self.usage_history: List[Dict[str, Any]] = []

        # Initialize basic LLM for memory if keys available
        basic_llm = None
        if self.openai_api_key:
            try:
                from cartrita.orchestrator.utils.llm_factory import create_chat_openai
                basic_llm = create_chat_openai(api_key=self.openai_api_key, model="gpt-3.5-turbo")
            except:
                pass

        # Memory for context
        if basic_llm:
            self.memory = ConversationSummaryBufferMemory(
                llm=basic_llm,
                memory_key="chat_history",
                return_messages=True,
                max_token_limit=4000
            )
        else:
            from langchain.memory import ConversationBufferMemory
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )

        # Initialize model instances
        self._initialize_models()

    def _initialize_model_configs(self) -> Dict[str, ModelConfig]:
        """Initialize available model configurations"""
        configs = {}

        # OpenAI Models
        if self.openai_api_key:
            configs.update({
                "gpt-4o": ModelConfig(
                    name="gpt-4o",
                    provider=ModelProvider.OPENAI,
                    cost_per_1k_tokens=0.03,
                    max_tokens=128000,
                    supports_streaming=True,
                    supports_function_calling=True,
                    expertise_areas=["reasoning", "coding", "analysis", "creativity"],
                    quality_score=0.95
                ),
                "gpt-4o-mini": ModelConfig(
                    name="gpt-4o-mini",
                    provider=ModelProvider.OPENAI,
                    cost_per_1k_tokens=0.0015,
                    max_tokens=128000,
                    supports_streaming=True,
                    supports_function_calling=True,
                    expertise_areas=["general", "simple_tasks"],
                    quality_score=0.85
                ),
                "gpt-3.5-turbo": ModelConfig(
                    name="gpt-3.5-turbo",
                    provider=ModelProvider.OPENAI,
                    cost_per_1k_tokens=0.001,
                    max_tokens=16385,
                    supports_streaming=True,
                    supports_function_calling=True,
                    expertise_areas=["general", "fast_responses"],
                    quality_score=0.80
                )
            })

        # Hugging Face Models
        if self.huggingface_api_key:
            configs.update({
                "llama-3.1-8b": ModelConfig(
                    name="meta-llama/Meta-Llama-3.1-8B-Instruct",
                    provider=ModelProvider.HUGGINGFACE,
                    cost_per_1k_tokens=0.0005,  # Much cheaper
                    max_tokens=8192,
                    supports_streaming=True,
                    supports_function_calling=False,
                    expertise_areas=["coding", "reasoning", "general"],
                    quality_score=0.90
                ),
                "llama-3.1-8b": ModelConfig(
                    name="meta-llama/Meta-Llama-3.1-8B-Instruct",
                    provider=ModelProvider.HUGGINGFACE,
                    cost_per_1k_tokens=0.0001,
                    max_tokens=8192,
                    supports_streaming=True,
                    supports_function_calling=False,
                    expertise_areas=["general", "fast_responses"],
                    quality_score=0.75
                ),
                "mixtral-8x7b": ModelConfig(
                    name="mistralai/Mixtral-8x7B-Instruct-v0.1",
                    provider=ModelProvider.HUGGINGFACE,
                    cost_per_1k_tokens=0.0003,
                    max_tokens=32768,
                    supports_streaming=True,
                    supports_function_calling=False,
                    expertise_areas=["multilingual", "reasoning"],
                    quality_score=0.85
                ),
                "codellama-34b": ModelConfig(
                    name="codellama/CodeLlama-34b-Instruct-hf",
                    provider=ModelProvider.HUGGINGFACE,
                    cost_per_1k_tokens=0.0002,
                    max_tokens=4096,
                    supports_streaming=True,
                    supports_function_calling=False,
                    expertise_areas=["coding", "debugging", "code_review"],
                    quality_score=0.90
                )
            })

        return configs

    def _initialize_models(self):
        """Initialize model instances"""
        for model_id, config in self.available_models.items():
            try:
                if config.provider == ModelProvider.OPENAI:
                    from cartrita.orchestrator.utils.llm_factory import create_chat_openai
                    self.model_instances[model_id] = create_chat_openai(
                        model=config.name,
                        api_key=self.openai_api_key,
                        temperature=0.7,
                        max_tokens=2048,
                        streaming=config.supports_streaming
                    )

                elif config.provider == ModelProvider.HUGGINGFACE:
                    # Use Hugging Face Inference API
                    from langchain_community.llms import HuggingFaceEndpoint
                    from langchain_community.chat_models import ChatHuggingFace

                    # Create endpoint with your token
                    endpoint = HuggingFaceEndpoint(
                        repo_id=config.name,
                        huggingfacehub_api_token=self.huggingface_api_key,
                        max_new_tokens=1024,
                        temperature=0.7,
                        timeout=60,
                        streaming=config.supports_streaming
                    )

                    # Wrap in chat interface
                    self.model_instances[model_id] = ChatHuggingFace(
                        llm=endpoint,
                        verbose=False
                    )

            except Exception as e:
                print(f"Failed to initialize model {model_id}: {e}")
                continue

    def select_optimal_model(
        self,
        task_requirements: TaskRequirements,
        context_length: Optional[int] = None
    ) -> Optional[str]:
        """
        Select the optimal model based on task requirements and constraints
        """
        candidates = []

        for model_id, config in self.available_models.items():
            # Skip if model not initialized
            if model_id not in self.model_instances:
                continue

            # Check hard requirements
            if task_requirements.requires_function_calling and not config.supports_function_calling:
                continue

            if task_requirements.requires_streaming and not config.supports_streaming:
                continue

            # Check context length
            if context_length and context_length > config.max_tokens:
                continue

            # Estimate cost
            estimated_tokens = context_length or 1000
            estimated_cost = (estimated_tokens / 1000) * config.cost_per_1k_tokens

            # Check cost constraint
            if estimated_cost > task_requirements.max_cost:
                continue

            # Check quality threshold
            if config.quality_score < task_requirements.quality_threshold:
                continue

            # Check domain expertise
            expertise_match = 0.0
            if task_requirements.domain_expertise:
                matches = set(config.expertise_areas) & set(task_requirements.domain_expertise)
                expertise_match = len(matches) / len(task_requirements.domain_expertise)

            # Calculate suitability score
            suitability = self._calculate_suitability_score(
                config, task_requirements, estimated_cost, expertise_match
            )

            candidates.append({
                "model_id": model_id,
                "config": config,
                "suitability": suitability,
                "estimated_cost": estimated_cost,
                "expertise_match": expertise_match
            })

        if not candidates:
            return None

        # Sort by suitability score
        candidates.sort(key=lambda x: x["suitability"], reverse=True)

        # If cost optimization is enabled, prefer cheaper models when quality is close
        if self.cost_optimization and len(candidates) > 1:
            best = candidates[0]
            for candidate in candidates[1:]:
                if candidate["suitability"] >= best["suitability"] * 0.95 and candidate["estimated_cost"] < best["estimated_cost"] * 0.8:
                    best = candidate
                    break
            return best["model_id"]

        return candidates[0]["model_id"]

    def _calculate_suitability_score(
        self,
        config: ModelConfig,
        requirements: TaskRequirements,
        estimated_cost: float,
        expertise_match: float
    ) -> float:
        """Calculate model suitability score"""

        # Base quality score
        score = config.quality_score

        # Expertise bonus
        score += expertise_match * 0.2

        # Cost penalty (higher cost = lower score)
        cost_penalty = min(estimated_cost / requirements.max_cost, 1.0) * 0.1
        score -= cost_penalty

        # Complexity matching
        complexity_scores = {
            TaskComplexity.SIMPLE: 0.7,
            TaskComplexity.MEDIUM: 0.8,
            TaskComplexity.COMPLEX: 0.9,
            TaskComplexity.CRITICAL: 1.0
        }

        required_quality = complexity_scores[requirements.complexity]
        if config.quality_score >= required_quality:
            score += 0.1  # Bonus for meeting complexity requirements
        else:
            score -= 0.2  # Penalty for not meeting complexity

        # Historical performance bonus
        if config.name in self.model_performance:
            avg_performance = sum(self.model_performance[config.name].values()) / len(self.model_performance[config.name])
            score += (avg_performance - 0.5) * 0.1

        return max(0.0, min(1.0, score))

    async def execute_with_optimal_model(
        self,
        query: str,
        task_requirements: Optional[TaskRequirements] = None,
        context: Optional[str] = None,
        callbacks: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Execute query with optimally selected model
        """
        start_time = datetime.now()

        # Default task requirements
        if not task_requirements:
            task_requirements = TaskRequirements(
                complexity=TaskComplexity.MEDIUM,
                max_cost=5.0,
                max_latency=30.0,
                quality_threshold=0.8
            )

        # Estimate context length
        context_length = self._estimate_token_count(query, context)

        # Select optimal model
        selected_model = self.select_optimal_model(task_requirements, context_length)

        if not selected_model:
            # Fallback strategy
            if self.fallback_strategy:
                selected_model = self._get_fallback_model()

            if not selected_model:
                return {
                    "success": False,
                    "error": "No suitable model available for task requirements",
                    "selected_model": None,
                    "execution_time": 0.0,
                    "cost": 0.0
                }

        try:
            # Get model instance
            model = self.model_instances[selected_model]
            config = self.available_models[selected_model]

            # Prepare messages
            messages = self._prepare_messages(query, context)

            # Execute with model
            if hasattr(model, 'ainvoke'):
                response = await model.ainvoke(messages, callbacks=callbacks)
            else:
                response = model.invoke(messages, callbacks=callbacks)

            # Calculate execution time and cost
            execution_time = (datetime.now() - start_time).total_seconds()
            estimated_tokens = self._estimate_response_tokens(response.content if hasattr(response, 'content') else str(response))
            cost = (estimated_tokens / 1000) * config.cost_per_1k_tokens

            # Update session cost
            self.current_session_cost += cost

            # Record performance
            self._record_performance(selected_model, execution_time, cost, True)

            # Update memory
            self.memory.save_context(
                {"input": query},
                {"output": response.content if hasattr(response, 'content') else str(response)}
            )

            return {
                "success": True,
                "response": response.content if hasattr(response, 'content') else str(response),
                "selected_model": selected_model,
                "provider": config.provider.value,
                "execution_time": execution_time,
                "cost": cost,
                "session_total_cost": self.current_session_cost
            }

        except Exception as e:
            # Record failure
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_performance(selected_model, execution_time, 0.0, False)

            # Try fallback if enabled
            if self.fallback_strategy and selected_model != self._get_fallback_model():
                fallback_model = self._get_fallback_model()
                if fallback_model and fallback_model in self.model_instances:
                    try:
                        model = self.model_instances[fallback_model]
                        messages = self._prepare_messages(query, context)
                        response = await model.ainvoke(messages) if hasattr(model, 'ainvoke') else model.invoke(messages)

                        fallback_time = (datetime.now() - start_time).total_seconds()
                        config = self.available_models[fallback_model]
                        estimated_tokens = self._estimate_response_tokens(response.content if hasattr(response, 'content') else str(response))
                        cost = (estimated_tokens / 1000) * config.cost_per_1k_tokens

                        self.current_session_cost += cost
                        self._record_performance(fallback_model, fallback_time - execution_time, cost, True)

                        return {
                            "success": True,
                            "response": response.content if hasattr(response, 'content') else str(response),
                            "selected_model": fallback_model,
                            "provider": config.provider.value,
                            "execution_time": fallback_time,
                            "cost": cost,
                            "session_total_cost": self.current_session_cost,
                            "used_fallback": True,
                            "original_error": str(e)
                        }
                    except Exception:
                                pass

            return {
                "success": False,
                "error": str(e),
                "selected_model": selected_model,
                "execution_time": execution_time,
                "cost": 0.0
            }

    def _get_fallback_model(self) -> Optional[str]:
        """Get the most reliable fallback model"""
        # Prefer GPT-3.5 Turbo as fallback (reliable and cheap)
        if "gpt-3.5-turbo" in self.model_instances:
            return "gpt-3.5-turbo"

        # Or any available OpenAI model
        for model_id, config in self.available_models.items():
            if config.provider == ModelProvider.OPENAI and model_id in self.model_instances:
                return model_id

        # Or any available model
        available_models = list(self.model_instances.keys())
        return available_models[0] if available_models else None

    def _prepare_messages(self, query: str, context: Optional[str] = None) -> List[BaseMessage]:
        """Prepare messages for model execution"""
        messages = []

        # Add system message with context
        system_content = "You are Cartrita, an advanced AI assistant."
        if context:
            system_content += f"\n\nContext: {context}"

        messages.append(SystemMessage(content=system_content))

        # Add conversation history
        if self.memory:
            memory_vars = self.memory.load_memory_variables({})
            if "chat_history" in memory_vars:
                messages.extend(memory_vars["chat_history"][-5:])  # Last 5 messages

        # Add current query
        messages.append(HumanMessage(content=query))

        return messages

    def _estimate_token_count(self, query: str, context: Optional[str] = None) -> int:
        """Estimate token count for query and context"""
        try:
            # Use tiktoken for more accurate estimation
            encoding = tiktoken.get_encoding("cl100k_base")

            text = query
            if context:
                text = f"{context}\n{text}"

            # Add memory context
            if self.memory:
                memory_vars = self.memory.load_memory_variables({})
                if "chat_history" in memory_vars:
                    for msg in memory_vars["chat_history"][-5:]:
                        text += f"\n{msg.content}"

            return len(encoding.encode(text))
        except Exception:
            # Fallback estimation (4 characters per token average)
            total_length = len(query)
            if context:
                total_length += len(context)
            return total_length // 4

    def _estimate_response_tokens(self, response: str) -> int:
        """Estimate tokens in response"""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(response))
        except Exception:
            return len(response) // 4

    def _record_performance(self, model_id: str, execution_time: float, cost: float, success: bool):
        """Record model performance metrics"""
        if model_id not in self.model_performance:
            self.model_performance[model_id] = {}

        # Record performance
        timestamp = datetime.now().isoformat()
        self.model_performance[model_id][timestamp] = {
            "execution_time": execution_time,
            "cost": cost,
            "success": success
        }

        # Keep only recent performance data (last 100 entries)
        if len(self.model_performance[model_id]) > 100:
            oldest_key = min(self.model_performance[model_id].keys())
            del self.model_performance[model_id][oldest_key]

        # Record in usage history
        self.usage_history.append({
            "timestamp": datetime.now(),
            "model_id": model_id,
            "execution_time": execution_time,
            "cost": cost,
            "success": success
        })

    # Public interface methods
    def chat(self, message: str, **kwargs) -> str:
        """Simple synchronous chat interface"""
        result = asyncio.run(self.execute_with_optimal_model(message, **kwargs))
        return result.get("response", f"Error: {result.get('error', 'Unknown error')}")

    async def achat(self, message: str, **kwargs) -> str:
        """Simple asynchronous chat interface"""
        result = await self.execute_with_optimal_model(message, **kwargs)
        return result.get("response", f"Error: {result.get('error', 'Unknown error')}")

    def get_available_models(self) -> Dict[str, Any]:
        """Get information about available models"""
        return {
            model_id: {
                "name": config.name,
                "provider": config.provider.value,
                "cost_per_1k": config.cost_per_1k_tokens,
                "max_tokens": config.max_tokens,
                "quality_score": config.quality_score,
                "expertise_areas": config.expertise_areas,
                "available": model_id in self.model_instances
            }
            for model_id, config in self.available_models.items()
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all models"""
        metrics = {}
        for model_id, performances in self.model_performance.items():
            if not performances:
                continue

            success_count = sum(1 for p in performances.values() if p["success"])
            total_count = len(performances)
            avg_time = sum(p["execution_time"] for p in performances.values()) / total_count
            avg_cost = sum(p["cost"] for p in performances.values()) / total_count

            metrics[model_id] = {
                "success_rate": success_count / total_count if total_count > 0 else 0,
                "average_execution_time": avg_time,
                "average_cost": avg_cost,
                "total_calls": total_count
            }

        return {
            "individual_models": metrics,
            "session_cost": self.current_session_cost,
            "session_limit": self.session_cost_limit,
            "total_calls": len(self.usage_history)
        }

    def reset_session(self):
        """Reset session metrics"""
        self.current_session_cost = 0.0
        self.usage_history = []
        self.memory.clear()

    def export_configuration(self) -> Dict[str, Any]:
        """Export current configuration"""
        return {
            "available_models": {
                k: {
                    "name": v.name,
                    "provider": v.provider.value,
                    "cost_per_1k": v.cost_per_1k_tokens,
                    "quality_score": v.quality_score,
                    "expertise_areas": v.expertise_areas
                }
                for k, v in self.available_models.items()
            },
            "configuration": {
                "cost_optimization": self.cost_optimization,
                "fallback_strategy": self.fallback_strategy,
                "session_cost_limit": self.session_cost_limit
            },
            "performance_metrics": self.get_performance_metrics()
        }
