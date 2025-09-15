"""
LangChain Memory Template for Cartrita
Implements memory patterns for conversation management
"""

from typing import Any, Dict, List, Optional
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field

class CartritaMemory(ConversationBufferMemory):
    """Custom memory implementation for Cartrita"""

    max_token_limit: int = Field(default=2000, description="Maximum tokens to store")
    summarize_after: int = Field(default=10, description="Summarize after N messages")

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Save conversation context"""
        # Convert to messages
        if "input" in inputs:
            self.chat_memory.add_user_message(inputs["input"])
        if "output" in outputs:
            self.chat_memory.add_ai_message(outputs["output"])

        # Check if summarization needed
        if len(self.chat_memory.messages) > self.summarize_after:
            self._summarize_old_messages()

    def _summarize_old_messages(self) -> None:
        """Summarize old messages to save tokens"""
        # Keep recent messages, summarize old ones
        recent_messages = self.chat_memory.messages[-5:]
        old_messages = self.chat_memory.messages[:-5]

        if old_messages:
            # Create summary (simplified for template)
            summary = f"Previous conversation summary: {len(old_messages)} messages exchanged"

            # Clear and rebuild memory
            self.chat_memory.clear()
            self.chat_memory.add_ai_message(summary)
            for msg in recent_messages:
                self.chat_memory.messages.append(msg)

class CartritaEntityMemory:
    """Entity memory for tracking entities in conversation"""

    def __init__(self):
        self.entities: Dict[str, Dict[str, Any]] = {}

    def add_entity(self, entity_type: str, entity_name: str, attributes: Dict[str, Any]) -> None:
        """Add or update an entity"""
        if entity_type not in self.entities:
            self.entities[entity_type] = {}
        self.entities[entity_type][entity_name] = attributes

    def get_entity(self, entity_type: str, entity_name: str) -> Optional[Dict[str, Any]]:
        """Get entity information"""
        if entity_type in self.entities:
            return self.entities[entity_type].get(entity_name)
        return None

    def get_all_entities(self, entity_type: Optional[str] = None) -> Dict[str, Any]:
        """Get all entities or entities of a specific type"""
        if entity_type:
            return self.entities.get(entity_type, {})
        return self.entities

    def clear_entities(self, entity_type: Optional[str] = None) -> None:
        """Clear entities"""
        if entity_type:
            if entity_type in self.entities:
                del self.entities[entity_type]
        else:
            self.entities.clear()

    def to_context_string(self) -> str:
        """Convert entities to context string for prompts"""
        context_parts = []
        for entity_type, entities in self.entities.items():
            context_parts.append(f"{entity_type}:")
            for name, attrs in entities.items():
                attrs_str = ", ".join(f"{k}={v}" for k, v in attrs.items())
                context_parts.append(f"  - {name}: {attrs_str}")
        return "\n".join(context_parts)
