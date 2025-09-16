"""
Production-ready fallback provider implementing multiple fallback strategies:
1. OpenAI API (when available)
2. HuggingFace Transformers (local inference)
3. Rule-based finite state machine
4. Template-based emergency responses

Based on LangChain fallback patterns and research findings.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("HuggingFace Transformers not available. Install with: pip install transformers torch")

try:
    from cartrita.orchestrator.utils.llm_factory import create_chat_openai
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available. Install with: pip install langchain langchain-openai")

logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    """Finite state machine state for conversation tracking"""
    current_state: str = "greeting"
    conversation_context: List[Dict] = None
    user_intent: Optional[str] = None
    last_response_type: str = "none"

    def __post_init__(self):
        if self.conversation_context is None:
            self.conversation_context = []


class FiniteStateChatbot:
    """
    Rule-based finite state machine chatbot for reliable fallback responses.
    Based on patterns from Rasa documentation and finite state machine theory.
    """

    def __init__(self):
        self.states = {
            "greeting": {
                "patterns": [
                    r"\b(hi|hello|hey|greetings)\b",
                    r"\b(good morning|good afternoon|good evening)\b",
                    r"\b(start|begin|help)\b"
                ],
                "responses": [
                    "Hello! I'm Cartrita, your AI assistant. How can I help you today?",
                    "Hi there! I'm ready to assist you with your questions and tasks.",
                    "Greetings! I'm Cartrita, here to help with information, analysis, and problem-solving."
                ],
                "next_states": ["task_inquiry", "general_help"]
            },
            "task_inquiry": {
                "patterns": [
                    r"\b(analyze|research|find|search)\b",
                    r"\b(code|programming|development)\b",
                    r"\b(write|create|generate)\b",
                    r"\b(explain|understand|learn)\b"
                ],
                "responses": [
                    "I can help you with research, analysis, coding, and creative tasks. What specific area would you like assistance with?",
                    "I'm equipped to handle various tasks including data analysis, programming, writing, and research. What's your project about?",
                    "I can assist with technical analysis, creative writing, problem-solving, and research. What would you like to work on?"
                ],
                "next_states": ["detailed_assistance", "clarification"]
            },
            "general_help": {
                "patterns": [
                    r"\b(what can you do|capabilities|features)\b",
                    r"\b(how do you work|explain yourself)\b",
                    r"\b(what are you|who are you)\b"
                ],
                "responses": [
                    "I'm Cartrita, an advanced AI assistant with multi-agent capabilities. I can help with research, analysis, coding, writing, and complex problem-solving tasks.",
                    "I operate using multiple specialized AI agents that work together: research agents for finding information, code agents for programming tasks, and analysis agents for data insights.",
                    "My capabilities include web research, data analysis, code generation, creative writing, and orchestrating complex multi-step tasks using specialized AI agents."
                ],
                "next_states": ["task_inquiry", "detailed_assistance"]
            },
            "detailed_assistance": {
                "patterns": [
                    r"\b(specifically|details|more about)\b",
                    r"\b(step by step|guide|tutorial)\b",
                    r"\b(example|show me|demonstrate)\b"
                ],
                "responses": [
                    "I'll break this down into manageable steps and coordinate the appropriate specialized agents to help you achieve your goal.",
                    "Let me analyze your requirements and determine the best approach using my research, coding, and analysis capabilities.",
                    "I'll orchestrate a multi-agent approach to provide you with comprehensive assistance on this topic."
                ],
                "next_states": ["execution", "clarification"]
            },
            "clarification": {
                "patterns": [
                    r"\b(not sure|unclear|confused)\b",
                    r"\b(what do you mean|explain)\b",
                    r"\b(different|alternative|other)\b"
                ],
                "responses": [
                    "Let me clarify that for you. Could you provide more specific details about what you're looking for?",
                    "I understand you need more information. What specific aspect would you like me to explain further?",
                    "To better assist you, could you describe your goal or what you're trying to accomplish?"
                ],
                "next_states": ["task_inquiry", "detailed_assistance"]
            },
            "execution": {
                "patterns": [
                    r"\b(do it|proceed|continue|yes)\b",
                    r"\b(start|begin|go ahead)\b",
                    r"\b(execute|run|perform)\b"
                ],
                "responses": [
                    "I'm coordinating my specialized agents to handle your request. This may involve research, analysis, and synthesis of information.",
                    "Executing your request using my multi-agent system. I'll gather information and provide comprehensive results.",
                    "Processing your request through my agent orchestration system for optimal results."
                ],
                "next_states": ["completion", "task_inquiry"]
            },
            "completion": {
                "patterns": [
                    r"\b(thank|thanks|appreciate)\b",
                    r"\b(done|finished|complete)\b",
                    r"\b(good|great|excellent)\b"
                ],
                "responses": [
                    "You're welcome! I'm glad I could help. Is there anything else you'd like assistance with?",
                    "Happy to help! Feel free to ask if you need any additional support or have other questions.",
                    "Pleased to assist! My multi-agent system is always ready for your next challenge."
                ],
                "next_states": ["greeting", "task_inquiry"]
            },
            "default": {
                "patterns": [r".*"],
                "responses": [
                    "I understand you have a question or request. Let me help you with that using my specialized AI agents.",
                    "I'm here to assist with research, analysis, coding, and creative tasks. How can I help you today?",
                    "My multi-agent system is ready to tackle your challenge. Could you provide more details about what you need?"
                ],
                "next_states": ["task_inquiry", "clarification"]
            }
        }

        self.conversation_state = ConversationState()

    def classify_intent(self, user_input: str) -> tuple[str, str]:
        """Classify user intent using pattern matching"""
        user_input_lower = user_input.lower()

        for state_name, state_config in self.states.items():
            for pattern in state_config["patterns"]:
                if re.search(pattern, user_input_lower, re.IGNORECASE):
                    return state_name, pattern

        return "default", ".*"

    def get_response(self, user_input: str) -> str:
        """Generate response using finite state machine logic"""
        try:
            # Classify intent
            intent_state, matched_pattern = self.classify_intent(user_input)

            # Get state configuration
            state_config = self.states.get(intent_state, self.states["default"])

            # Select response (simple round-robin for now)
            responses = state_config["responses"]
            response_index = len(self.conversation_state.conversation_context) % len(responses)
            response = responses[response_index]

            # Update conversation state
            self.conversation_state.current_state = intent_state
            self.conversation_state.user_intent = intent_state
            self.conversation_state.last_response_type = "rule_based"
            self.conversation_state.conversation_context.append({
                "user_input": user_input,
                "matched_pattern": matched_pattern,
                "response": response,
                "state": intent_state,
                "timestamp": datetime.now().isoformat()
            })

            logger.info(f"Rule-based response generated for state: {intent_state}")
            return response

        except Exception as e:
            logger.error(f"Error in finite state chatbot: {e}")
            return "I'm here to help! Could you please rephrase your question or tell me what you'd like assistance with?"


class HuggingFaceLocalProvider:
    """
    Local inference using HuggingFace Transformers.
    Provides offline LLM capabilities without API dependencies.
    """

    def __init__(self, model_name: str = "microsoft/DialoGPT-small"):
        self.model_name = model_name
        self.pipeline = None
        self.tokenizer = None
        self.model = None
        self.is_initialized = False

        if TRANSFORMERS_AVAILABLE:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize local model with error handling"""
        try:
            logger.info(f"Initializing HuggingFace model: {self.model_name}")

            # Use smaller model for faster loading
            if "DialoGPT" in self.model_name:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForCausalLM.from_pretrained(self.model_name)

                # Set padding token
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token

                self.is_initialized = True
                logger.info("HuggingFace model initialized successfully")
            else:
                # Fallback to text generation pipeline
                self.pipeline = pipeline(
                    "text-generation",
                    model=self.model_name,
                    max_length=150,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=50256  # GPT-2 pad token
                )
                self.is_initialized = True
                logger.info("HuggingFace pipeline initialized successfully")

        except Exception as e:
            logger.warning(f"Failed to initialize HuggingFace model: {e}")
            self.is_initialized = False

    def generate_response(self, user_input: str, conversation_history: List[str] = None) -> str:
        """Generate response using local HuggingFace model"""
        if not self.is_initialized or not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("HuggingFace model not available")

        try:
            if self.pipeline:
                # Use text generation pipeline
                prompt = f"Human: {user_input}\nAssistant:"
                if conversation_history:
                    # Include recent context
                    context = "\n".join(conversation_history[-3:])  # Last 3 exchanges
                    prompt = f"{context}\nHuman: {user_input}\nAssistant:"

                result = self.pipeline(prompt, max_new_tokens=100, do_sample=True, temperature=0.7)
                response = result[0]['generated_text'].split("Assistant:")[-1].strip()
                return response[:500]  # Limit response length

            elif self.tokenizer and self.model:
                # Use DialoGPT-style conversation
                if conversation_history:
                    # Build conversation context
                    conversation = " ".join(conversation_history[-5:])  # Last 5 exchanges
                    full_input = f"{conversation} {user_input}"
                else:
                    full_input = user_input

                # Encode input
                inputs = self.tokenizer.encode(full_input + self.tokenizer.eos_token, return_tensors="pt")

                # Generate response
                with torch.no_grad():
                    outputs = self.model.generate(
                        inputs,
                        max_length=inputs.shape[1] + 100,
                        num_return_sequences=1,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id
                    )

                # Decode response
                response = self.tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
                return response.strip()[:500]  # Limit response length

        except Exception as e:
            logger.error(f"Error generating HuggingFace response: {e}")
            raise RuntimeError(f"HuggingFace generation failed: {e}")

        raise RuntimeError("No valid generation method available")


class FallbackProvider:
    """
    Production-ready fallback provider implementing multiple fallback strategies.
    Implements LangChain with_fallbacks() pattern with local alternatives.
    """

    def __init__(self):
        self.openai_client = None
        self.hf_provider = None
        self.fsm_chatbot = FiniteStateChatbot()
        self.conversation_history = []

        # Initialize OpenAI if API key is available and valid
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if openai_key and not openai_key.startswith("sk-test-") and LANGCHAIN_AVAILABLE:
            try:
                self.openai_client = create_chat_openai(
                    api_key=openai_key,
                    model="gpt-3.5-turbo",
                    temperature=0.7,
                    max_completion_tokens=1024
                )
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None

        # Initialize HuggingFace local provider
        if TRANSFORMERS_AVAILABLE:
            try:
                self.hf_provider = HuggingFaceLocalProvider("microsoft/DialoGPT-small")
                logger.info("HuggingFace local provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize HuggingFace provider: {e}")
                self.hf_provider = None

    async def generate_response(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        """
        Generate response using fallback chain:
        1. OpenAI API (if available)
        2. HuggingFace local inference
        3. Rule-based finite state machine
        4. Emergency template response
        """

        # Context is reserved for future use (system prompts, user preferences, etc.)
        _ = context  # Mark as intentionally unused for now

        response_metadata = {
            "provider_used": None,
            "fallback_level": 0,
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input
        }

        # Level 1: Try OpenAI API
        if self.openai_client:
            try:
                logger.info("Attempting OpenAI API response")

                messages = [
                    SystemMessage(content="You are Cartrita, an advanced AI assistant with multi-agent capabilities. Provide helpful, accurate, and engaging responses."),
                    HumanMessage(content=user_input)
                ]

                # Add conversation context if available
                if self.conversation_history:
                    recent_history = self.conversation_history[-6:]  # Last 3 exchanges
                    for i, exchange in enumerate(recent_history):
                        if i % 2 == 0:
                            messages.insert(-1, HumanMessage(content=exchange))
                        else:
                            messages.insert(-1, AIMessage(content=exchange))

                response = await self.openai_client.ainvoke(messages)

                response_metadata.update({
                    "provider_used": "openai",
                    "fallback_level": 1,
                    "success": True
                })

                # Update conversation history
                self.conversation_history.extend([user_input, response.content])

                logger.info("OpenAI API response generated successfully")
                return {
                    "response": response.content,
                    "metadata": response_metadata
                }

            except Exception as e:
                logger.warning(f"OpenAI API failed: {e}, falling back to local inference")

        # Level 2: Try HuggingFace local inference
        if self.hf_provider and self.hf_provider.is_initialized:
            try:
                logger.info("Attempting HuggingFace local inference")

                response = self.hf_provider.generate_response(
                    user_input,
                    self.conversation_history[-10:]  # Last 5 exchanges
                )

                if response and len(response.strip()) > 0:
                    response_metadata.update({
                        "provider_used": "huggingface_local",
                        "fallback_level": 2,
                        "success": True
                    })

                    # Update conversation history
                    self.conversation_history.extend([user_input, response])

                    logger.info("HuggingFace local response generated successfully")
                    return {
                        "response": response,
                        "metadata": response_metadata
                    }

            except Exception as e:
                logger.warning(f"HuggingFace local inference failed: {e}, falling back to rule-based")

        # Level 3: Use rule-based finite state machine
        try:
            logger.info("Using rule-based finite state machine")

            response = self.fsm_chatbot.get_response(user_input)

            response_metadata.update({
                "provider_used": "rule_based_fsm",
                "fallback_level": 3,
                "success": True,
                "state": self.fsm_chatbot.conversation_state.current_state
            })

            # Update conversation history
            self.conversation_history.extend([user_input, response])

            logger.info("Rule-based response generated successfully")
            return {
                "response": response,
                "metadata": response_metadata
            }

        except Exception as e:
            logger.error(f"Rule-based system failed: {e}, using emergency response")

        # Level 4: Emergency template response
        emergency_responses = [
            "I'm Cartrita, your AI assistant. I'm currently running in offline mode but I'm here to help! Please tell me what you'd like assistance with.",
            "Hello! I'm operating with local capabilities right now. I can still help with general questions and guidance. What can I do for you?",
            "I'm available to assist you! While some of my advanced features may be limited, I can still provide helpful information and support. How can I help?"
        ]

        import random
        emergency_response = random.choice(emergency_responses)

        response_metadata.update({
            "provider_used": "emergency_template",
            "fallback_level": 4,
            "success": True
        })

        logger.info("Emergency template response used")
        return {
            "response": emergency_response,
            "metadata": response_metadata
        }

    def get_capabilities_info(self) -> Dict[str, Any]:
        """Return information about available capabilities"""
        return {
            "openai_available": self.openai_client is not None,
            "huggingface_available": self.hf_provider is not None and self.hf_provider.is_initialized,
            "rule_based_available": True,
            "emergency_template_available": True,
            "transformers_installed": TRANSFORMERS_AVAILABLE,
            "langchain_installed": LANGCHAIN_AVAILABLE
        }


# Global fallback provider instance

_fallback_provider = None


def get_fallback_provider() -> FallbackProvider:
    """Get or create global fallback provider instance"""
    global _fallback_provider
    if _fallback_provider is None:
        _fallback_provider = FallbackProvider()
    return _fallback_provider


async def generate_fallback_response(user_input: str, context: Dict = None) -> Dict[str, Any]:
    """Convenience function to generate fallback response"""
    provider = get_fallback_provider()
    return await provider.generate_response(user_input, context)
