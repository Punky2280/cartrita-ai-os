# Cartrita Memory Agent - MCP Memory Integration
"""
Memory Agent with MCP Protocol Integration.
Implements persistent memory across conversations using knowledge graph.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import structlog
from pydantic import Field

# No base class needed - following pattern of other agents
from cartrita.orchestrator.agents.cartrita_core.mcp_protocol import (
    CartritaMCPProtocol,
    MCPMessage,
    MCPTool,
)


# Simple response class for memory agent
@dataclass
class MemoryResponse:
    """Simple response from memory agent."""

    content: str
    model: str = "memory-agent"


logger = structlog.get_logger(__name__)


@dataclass
class MemoryEntity:
    """Knowledge graph entity."""

    name: str
    entity_type: str
    observations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class MemoryRelation:
    """Relationship between entities."""

    from_entity: str
    to_entity: str
    relation_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class MemoryMCPTool(MCPTool):
    """Extended MCP tool for memory operations."""

    memory_operation: str = Field(..., description="Type of memory operation")


class MemoryAgent:
    """
    Memory Agent with MCP Protocol Integration.

    Provides persistent memory across conversations using a knowledge graph approach.
    Integrates with the existing MCP protocol for tool management.
    """

    def __init__(self, api_key_manager):
        """Initialize the Memory Agent."""
        self.api_key_manager = api_key_manager
        self.agent_type = "memory"
        self.model_preference = ["gpt-4-turbo-preview", "gpt-3.5-turbo"]

        # Setup logger
        self.logger = structlog.get_logger(__name__)

        # Memory storage
        self.entities: Dict[str, MemoryEntity] = {}
        self.relations: List[MemoryRelation] = []

        # MCP integration
        self.mcp_protocol = CartritaMCPProtocol(api_key_manager)
        self._register_memory_tools()

        logger.info(
            "Memory Agent initialized",
            agent_type=self.agent_type,
            tools_registered=len(self.mcp_protocol.tools),
        )

    def _register_memory_tools(self):
        """Register memory-specific MCP tools."""

        # Entity management tools
        create_entity_tool = MemoryMCPTool(
            name="create_entity",
            description="Create a new entity in memory",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Entity name"},
                    "entity_type": {"type": "string", "description": "Entity type"},
                    "observations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Initial observations about the entity",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata",
                    },
                },
                "required": ["name", "entity_type"],
            },
            hierarchy_level=2,
            safety_level=1,
            memory_operation="create_entity",
        )

        # Add entity observation tool
        add_observation_tool = MemoryMCPTool(
            name="add_observation",
            description="Add an observation to an existing entity",
            input_schema={
                "type": "object",
                "properties": {
                    "entity_name": {"type": "string", "description": "Entity name"},
                    "observation": {"type": "string", "description": "New observation"},
                },
                "required": ["entity_name", "observation"],
            },
            hierarchy_level=2,
            safety_level=1,
            memory_operation="add_observation",
        )

        # Create relation tool
        create_relation_tool = MemoryMCPTool(
            name="create_relation",
            description="Create a relationship between two entities",
            input_schema={
                "type": "object",
                "properties": {
                    "from_entity": {
                        "type": "string",
                        "description": "Source entity name",
                    },
                    "to_entity": {
                        "type": "string",
                        "description": "Target entity name",
                    },
                    "relation_type": {
                        "type": "string",
                        "description": "Type of relationship",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata",
                    },
                },
                "required": ["from_entity", "to_entity", "relation_type"],
            },
            hierarchy_level=2,
            safety_level=1,
            memory_operation="create_relation",
        )

        # Search entities tool
        search_entities_tool = MemoryMCPTool(
            name="search_entities",
            description="Search for entities in memory",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "entity_type": {
                        "type": "string",
                        "description": "Filter by entity type",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Max results",
                    },
                },
                "required": ["query"],
            },
            hierarchy_level=1,
            safety_level=1,
            memory_operation="search_entities",
        )

        # Get entity details tool
        get_entity_tool = MemoryMCPTool(
            name="get_entity",
            description="Get detailed information about a specific entity",
            input_schema={
                "type": "object",
                "properties": {
                    "entity_name": {"type": "string", "description": "Entity name"},
                },
                "required": ["entity_name"],
            },
            hierarchy_level=1,
            safety_level=1,
            memory_operation="get_entity",
        )

        # List all entities tool
        list_entities_tool = MemoryMCPTool(
            name="list_entities",
            description="List all entities in memory",
            input_schema={
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "description": "Filter by entity type",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "Max results",
                    },
                },
            },
            hierarchy_level=1,
            safety_level=1,
            memory_operation="list_entities",
        )

        # Delete entity tool
        delete_entity_tool = MemoryMCPTool(
            name="delete_entity",
            description="Delete an entity from memory",
            input_schema={
                "type": "object",
                "properties": {
                    "entity_name": {"type": "string", "description": "Entity name"},
                },
                "required": ["entity_name"],
            },
            hierarchy_level=3,
            safety_level=2,
            memory_operation="delete_entity",
        )

        # Register all tools with executors
        tools_with_executors = [
            (create_entity_tool, self._execute_create_entity),
            (add_observation_tool, self._execute_add_observation),
            (create_relation_tool, self._execute_create_relation),
            (search_entities_tool, self._execute_search_entities),
            (get_entity_tool, self._execute_get_entity),
            (list_entities_tool, self._execute_list_entities),
            (delete_entity_tool, self._execute_delete_entity),
        ]

        for tool, executor in tools_with_executors:
            self.mcp_protocol.register_tool(tool, executor)

    async def process_request(
        self, message: str, context: Optional[dict] = None
    ) -> MemoryResponse:
        """Process memory-related requests using MCP protocol."""
        try:
            # Parse command if it's a /memo command
            if message.startswith("/memo"):
                return await self._handle_memo_command(message, context)

            # Standard memory processing
            response = await self._process_memory_request(message, context)
            if response:
                return response

        except Exception as e:
            self.logger.warning(f"Memory processing failed: {e}")

        # Fallback response for non-memory requests
        return MemoryResponse(
            content="I'm the memory agent. Use `/memo help` to see available memory commands."
        )

    async def _handle_memo_command(
        self, message: str, context: Optional[dict] = None
    ) -> MemoryResponse:
        """Handle /memo commands."""
        try:
            parts = message.split(maxsplit=2)

            if len(parts) < 2:
                return MemoryResponse(
                    content=self._get_memo_help(), model="memory-agent"
                )

            command = parts[1].lower()

            if command == "help":
                return MemoryResponse(
                    content=self._get_memo_help(), model="memory-agent"
                )

            elif command == "create" and len(parts) >= 3:
                return await self._handle_memo_create(parts[2])

            elif command == "search" and len(parts) >= 3:
                return await self._handle_memo_search(parts[2])

            elif command == "get" and len(parts) >= 3:
                return await self._handle_memo_get(parts[2])

            elif command == "list":
                return await self._handle_memo_list()

            elif command == "delete" and len(parts) >= 3:
                return await self._handle_memo_delete(parts[2])

            elif command == "relate" and len(parts) >= 3:
                return await self._handle_memo_relate(parts[2])

            else:
                return MemoryResponse(
                    content="Invalid /memo command. Use `/memo help` for available commands.",
                    model="memory-agent",
                )

        except Exception as e:
            return MemoryResponse(
                content=f"Error processing memo command: {str(e)}", model="memory-agent"
            )

    async def _handle_memo_create(self, args: str) -> MemoryResponse:
        """Handle /memo create command."""
        try:
            # Parse arguments: name:type:observation
            parts = args.split(":", 2)
            if len(parts) < 2:
                return MemoryResponse(
                    content="Usage: /memo create name:type:observation",
                    model="memory-agent",
                )

            name = parts[0].strip()
            entity_type = parts[1].strip()
            observation = parts[2].strip() if len(parts) > 2 else ""

            # Create entity using MCP tool
            mcp_message = MCPMessage(
                method="tools/call",
                params={
                    "name": "create_entity",
                    "arguments": {
                        "name": name,
                        "entity_type": entity_type,
                        "observations": [observation] if observation else [],
                    },
                },
            )

            response = await self.mcp_protocol.handle_message(mcp_message)

            if response.error:
                return MemoryResponse(
                    content=f"Error creating entity: {response.error['message']}",
                    model="memory-agent",
                )

            return MemoryResponse(
                content=f"Created entity '{name}' of type '{entity_type}'"
                + (f" with observation: {observation}" if observation else ""),
                model="memory-agent",
            )

        except Exception as e:
            return MemoryResponse(
                content=f"Error creating entity: {str(e)}", model="memory-agent"
            )

    async def _handle_memo_search(self, query: str) -> MemoryResponse:
        """Handle /memo search command."""
        try:
            mcp_message = MCPMessage(
                method="tools/call",
                params={
                    "name": "search_entities",
                    "arguments": {"query": query},
                },
            )

            response = await self.mcp_protocol.handle_message(mcp_message)

            if response.error:
                return MemoryResponse(
                    content=f"Search error: {response.error['message']}",
                    model="memory-agent",
                )

            result = response.result
            entities = result.get("result", {}).get("entities", [])

            if not entities:
                content = f"No entities found matching '{query}'"
            else:
                content = f"Found {len(entities)} entities matching '{query}':\n\n"
                for entity in entities:
                    content += f"• **{entity['name']}** ({entity['entity_type']})\n"
                    if entity.get("observations"):
                        content += f"  - {entity['observations'][0][:100]}...\n"
                    content += "\n"

            return MemoryResponse(content=content, model="memory-agent")

        except Exception as e:
            return MemoryResponse(
                content=f"Search error: {str(e)}", model="memory-agent"
            )

    async def _handle_memo_get(self, entity_name: str) -> MemoryResponse:
        """Handle /memo get command."""
        try:
            mcp_message = MCPMessage(
                method="tools/call",
                params={
                    "name": "get_entity",
                    "arguments": {"entity_name": entity_name},
                },
            )

            response = await self.mcp_protocol.handle_message(mcp_message)

            if response.error:
                return MemoryResponse(
                    content=f"Error getting entity: {response.error['message']}",
                    model="memory-agent",
                )

            result = response.result
            entity_data = result.get("result", {}).get("entity")

            if not entity_data:
                content = f"Entity '{entity_name}' not found"
            else:
                content = (
                    f"**{entity_data['name']}** ({entity_data['entity_type']})\n\n"
                )
                content += f"Created: {time.ctime(entity_data['created_at'])}\n"
                content += f"Updated: {time.ctime(entity_data['updated_at'])}\n\n"

                if entity_data.get("observations"):
                    content += "**Observations:**\n"
                    for i, obs in enumerate(entity_data["observations"], 1):
                        content += f"{i}. {obs}\n"

                if entity_data.get("metadata"):
                    content += f"\n**Metadata:** {json.dumps(entity_data['metadata'], indent=2)}"

            return MemoryResponse(content=content, model="memory-agent")

        except Exception as e:
            return MemoryResponse(
                content=f"Error getting entity: {str(e)}", model="memory-agent"
            )

    async def _handle_memo_list(self) -> MemoryResponse:
        """Handle /memo list command."""
        try:
            mcp_message = MCPMessage(
                method="tools/call",
                params={
                    "name": "list_entities",
                    "arguments": {},
                },
            )

            response = await self.mcp_protocol.handle_message(mcp_message)

            if response.error:
                return MemoryResponse(
                    content=f"Error listing entities: {response.error['message']}",
                    model="memory-agent",
                )

            result = response.result
            entities = result.get("result", {}).get("entities", [])

            if not entities:
                content = "No entities in memory"
            else:
                content = f"**Memory contains {len(entities)} entities:**\n\n"

                # Group by type
                by_type = {}
                for entity in entities:
                    entity_type = entity["entity_type"]
                    if entity_type not in by_type:
                        by_type[entity_type] = []
                    by_type[entity_type].append(entity)

                for entity_type, type_entities in by_type.items():
                    content += f"**{entity_type.title()}:**\n"
                    for entity in type_entities:
                        content += f"  • {entity['name']}\n"
                    content += "\n"

            return MemoryResponse(content=content, model="memory-agent")

        except Exception as e:
            return MemoryResponse(
                content=f"Error listing entities: {str(e)}", model="memory-agent"
            )

    async def _handle_memo_delete(self, entity_name: str) -> MemoryResponse:
        """Handle /memo delete command."""
        try:
            mcp_message = MCPMessage(
                method="tools/call",
                params={
                    "name": "delete_entity",
                    "arguments": {"entity_name": entity_name},
                },
            )

            response = await self.mcp_protocol.handle_message(mcp_message)

            if response.error:
                return MemoryResponse(
                    content=f"Error deleting entity: {response.error['message']}",
                    model="memory-agent",
                )

            return MemoryResponse(
                content=f"Deleted entity '{entity_name}' from memory",
                model="memory-agent",
            )

        except Exception as e:
            return MemoryResponse(
                content=f"Error deleting entity: {str(e)}", model="memory-agent"
            )

    async def _handle_memo_relate(self, args: str) -> MemoryResponse:
        """Handle /memo relate command."""
        try:
            # Parse arguments: from_entity:to_entity:relation_type
            parts = args.split(":", 2)
            if len(parts) < 3:
                return MemoryResponse(
                    content="Usage: /memo relate from_entity:to_entity:relation_type",
                    model="memory-agent",
                )

            from_entity = parts[0].strip()
            to_entity = parts[1].strip()
            relation_type = parts[2].strip()

            mcp_message = MCPMessage(
                method="tools/call",
                params={
                    "name": "create_relation",
                    "arguments": {
                        "from_entity": from_entity,
                        "to_entity": to_entity,
                        "relation_type": relation_type,
                    },
                },
            )

            response = await self.mcp_protocol.handle_message(mcp_message)

            if response.error:
                return MemoryResponse(
                    content=f"Error creating relation: {response.error['message']}",
                    model="memory-agent",
                )

            return MemoryResponse(
                content=f"Created relation: {from_entity} --{relation_type}--> {to_entity}",
                model="memory-agent",
            )

        except Exception as e:
            return MemoryResponse(
                content=f"Error creating relation: {str(e)}", model="memory-agent"
            )

    def _get_memo_help(self) -> str:
        """Get help text for /memo commands."""
        return """
**Memory Agent Commands:**

• `/memo help` - Show this help
• `/memo create name:type:observation` - Create new entity
• `/memo search query` - Search entities by name/content
• `/memo get entity_name` - Get detailed entity information
• `/memo list` - List all entities in memory
• `/memo delete entity_name` - Delete entity from memory
• `/memo relate from:to:relation_type` - Create relationship

**Examples:**
• `/memo create John:person:Software engineer who loves Python`
• `/memo search Python`
• `/memo get John`
• `/memo relate John:Python:knows`

**Entity Types:** person, project, skill, task, note, etc.
**Relation Types:** knows, works_on, likes, related_to, etc.
        """.strip()

    async def _process_memory_request(
        self, message: str, context: Optional[dict] = None
    ) -> Optional[MemoryResponse]:
        """Process general memory-related requests."""
        # Extract memory-related intent from natural language
        memory_keywords = ["remember", "recall", "forget", "memory", "store", "save"]

        if any(keyword in message.lower() for keyword in memory_keywords):
            # Use AI to process the request and convert to MCP tool calls
            try:
                # For now, provide a simple response directing to /memo commands
                return MemoryResponse(
                    content="I can help with memory operations! Use `/memo help` to see available commands for managing entities and relationships in memory.",
                    model="memory-agent",
                )
            except Exception as e:
                self.logger.error(f"Memory request processing failed: {e}")

        return None

    # MCP Tool Executors
    async def _execute_create_entity(self, **kwargs) -> Dict[str, Any]:
        """Execute create entity operation."""
        name = kwargs.get("name")
        entity_type = kwargs.get("entity_type")
        observations = kwargs.get("observations", [])
        metadata = kwargs.get("metadata", {})

        if name in self.entities:
            return {"error": f"Entity '{name}' already exists"}

        entity = MemoryEntity(
            name=name,
            entity_type=entity_type,
            observations=observations,
            metadata=metadata,
        )

        self.entities[name] = entity

        logger.info("Entity created", entity_name=name, entity_type=entity_type)

        return {
            "success": True,
            "entity": {
                "name": entity.name,
                "entity_type": entity.entity_type,
                "observations": entity.observations,
                "metadata": entity.metadata,
                "created_at": entity.created_at,
            },
        }

    async def _execute_add_observation(self, **kwargs) -> Dict[str, Any]:
        """Execute add observation operation."""
        entity_name = kwargs.get("entity_name")
        observation = kwargs.get("observation")

        if entity_name not in self.entities:
            return {"error": f"Entity '{entity_name}' not found"}

        entity = self.entities[entity_name]
        entity.observations.append(observation)
        entity.updated_at = time.time()

        logger.info(
            "Observation added", entity_name=entity_name, observation=observation
        )

        return {
            "success": True,
            "entity_name": entity_name,
            "observation_added": observation,
            "total_observations": len(entity.observations),
        }

    async def _execute_create_relation(self, **kwargs) -> Dict[str, Any]:
        """Execute create relation operation."""
        from_entity = kwargs.get("from_entity")
        to_entity = kwargs.get("to_entity")
        relation_type = kwargs.get("relation_type")
        metadata = kwargs.get("metadata", {})

        # Check if entities exist
        if from_entity not in self.entities:
            return {"error": f"Entity '{from_entity}' not found"}
        if to_entity not in self.entities:
            return {"error": f"Entity '{to_entity}' not found"}

        relation = MemoryRelation(
            from_entity=from_entity,
            to_entity=to_entity,
            relation_type=relation_type,
            metadata=metadata,
        )

        self.relations.append(relation)

        logger.info(
            "Relation created",
            from_entity=from_entity,
            to_entity=to_entity,
            relation_type=relation_type,
        )

        return {
            "success": True,
            "relation": {
                "from_entity": relation.from_entity,
                "to_entity": relation.to_entity,
                "relation_type": relation.relation_type,
                "metadata": relation.metadata,
                "created_at": relation.created_at,
            },
        }

    async def _execute_search_entities(self, **kwargs) -> Dict[str, Any]:
        """Execute search entities operation."""
        query = kwargs.get("query", "").lower()
        entity_type = kwargs.get("entity_type")
        limit = kwargs.get("limit", 10)

        matches = []

        for entity in self.entities.values():
            # Check if entity matches search criteria
            if entity_type and entity.entity_type != entity_type:
                continue

            # Search in name, observations, and metadata
            search_text = " ".join(
                [
                    entity.name.lower(),
                    " ".join(entity.observations).lower(),
                    json.dumps(entity.metadata).lower(),
                ]
            )

            if query in search_text:
                matches.append(
                    {
                        "name": entity.name,
                        "entity_type": entity.entity_type,
                        "observations": entity.observations,
                        "metadata": entity.metadata,
                        "created_at": entity.created_at,
                        "updated_at": entity.updated_at,
                    }
                )

        # Sort by relevance (name matches first, then recent updates)
        matches.sort(key=lambda x: (query not in x["name"].lower(), -x["updated_at"]))

        return {
            "query": query,
            "entity_type": entity_type,
            "entities": matches[:limit],
            "total_found": len(matches),
        }

    async def _execute_get_entity(self, **kwargs) -> Dict[str, Any]:
        """Execute get entity operation."""
        entity_name = kwargs.get("entity_name")

        if entity_name not in self.entities:
            return {"error": f"Entity '{entity_name}' not found"}

        entity = self.entities[entity_name]

        # Get related entities
        related = []
        for relation in self.relations:
            if relation.from_entity == entity_name:
                related.append(
                    {
                        "entity": relation.to_entity,
                        "relation": relation.relation_type,
                        "direction": "outgoing",
                    }
                )
            elif relation.to_entity == entity_name:
                related.append(
                    {
                        "entity": relation.from_entity,
                        "relation": relation.relation_type,
                        "direction": "incoming",
                    }
                )

        return {
            "entity": {
                "name": entity.name,
                "entity_type": entity.entity_type,
                "observations": entity.observations,
                "metadata": entity.metadata,
                "created_at": entity.created_at,
                "updated_at": entity.updated_at,
                "related_entities": related,
            }
        }

    async def _execute_list_entities(self, **kwargs) -> Dict[str, Any]:
        """Execute list entities operation."""
        entity_type = kwargs.get("entity_type")
        limit = kwargs.get("limit", 20)

        entities = []
        for entity in self.entities.values():
            if entity_type and entity.entity_type != entity_type:
                continue

            entities.append(
                {
                    "name": entity.name,
                    "entity_type": entity.entity_type,
                    "observation_count": len(entity.observations),
                    "created_at": entity.created_at,
                    "updated_at": entity.updated_at,
                }
            )

        # Sort by most recently updated
        entities.sort(key=lambda x: -x["updated_at"])

        return {
            "entities": entities[:limit],
            "total_count": len(entities),
            "entity_type_filter": entity_type,
        }

    async def _execute_delete_entity(self, **kwargs) -> Dict[str, Any]:
        """Execute delete entity operation."""
        entity_name = kwargs.get("entity_name")

        if entity_name not in self.entities:
            return {"error": f"Entity '{entity_name}' not found"}

        # Remove entity
        del self.entities[entity_name]

        # Remove related relations
        self.relations = [
            r
            for r in self.relations
            if r.from_entity != entity_name and r.to_entity != entity_name
        ]

        logger.info("Entity deleted", entity_name=entity_name)

        return {
            "success": True,
            "entity_name": entity_name,
            "deleted_at": time.time(),
        }
