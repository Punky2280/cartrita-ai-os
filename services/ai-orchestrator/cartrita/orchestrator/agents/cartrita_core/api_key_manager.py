# Cartrita AI OS - API Key Manager
# Secure key vault and permission management system

"""
API Key Manager for Cartrita AI OS.
Manages all API keys, permissions, and tool access delegation with secure vault operations.
"""

import base64
import hashlib
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import structlog
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class PermissionLevel(str, Enum):
    """Permission levels for API key access."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class KeyStatus(str, Enum):
    """API key status states."""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


@dataclass
class ToolPermission:
    """Tool access permission configuration."""

    tool_name: str
    required_keys: List[str]
    permission_level: PermissionLevel
    rate_limit: Optional[int] = None
    expires_at: Optional[float] = None
    allowed_agents: Set[str] = field(default_factory=set)


@dataclass
class KeyUsageRecord:
    """Record of API key usage for auditing."""

    agent_id: str
    tool_name: str
    key_hash: str
    timestamp: float
    success: bool
    error_message: Optional[str] = None


class APIKeyInfo(BaseModel):
    """API key information model."""

    key_id: str = Field(..., description="Unique key identifier")
    service: str = Field(..., description="Service name (openai, google, etc.)")
    permissions: List[PermissionLevel] = Field(default_factory=list)
    status: KeyStatus = Field(default=KeyStatus.ACTIVE)
    created_at: float = Field(default_factory=time.time)
    last_used: Optional[float] = None
    usage_count: int = 0
    rate_limit: Optional[int] = None
    expires_at: Optional[float] = None
    allowed_agents: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SecureKeyVault:
    """Encrypted storage for API keys with secure access patterns."""

    def __init__(self, vault_password: str):
        """Initialize the secure vault with encryption."""
        self.vault_password = vault_password
        self._salts: Dict[str, bytes] = {}  # Store salts per key
        self._keys: Dict[str, bytes] = {}  # Encrypted keys
        self._key_info: Dict[str, APIKeyInfo] = {}
        self._access_log: List[KeyUsageRecord] = []

    def _create_cipher(self, password: str, salt: bytes) -> Fernet:
        """Create encryption cipher from password and salt."""
        password_bytes = password.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return Fernet(key)

    def store_key(self, key_id: str, api_key: str, key_info: APIKeyInfo) -> bool:
        """Store encrypted API key in vault."""
        try:
            salt = os.urandom(16)
            self._salts[key_id] = salt
            cipher = self._create_cipher(self.vault_password, salt)
            encrypted_key = cipher.encrypt(api_key.encode())
            self._keys[key_id] = encrypted_key
            self._key_info[key_id] = key_info

            logger.info(
                "API key stored in vault", key_id=key_id, service=key_info.service
            )
            return True
        except Exception as e:
            logger.error("Failed to store API key", key_id=key_id, error=str(e))
            return False

    def retrieve_key(self, key_id: str, agent_id: str) -> Optional[str]:
        """Retrieve and decrypt API key if permissions allow."""
        try:
            if (
                key_id not in self._keys
                or key_id not in self._key_info
                or key_id not in self._salts
            ):
                return None

            key_info = self._key_info[key_id]

            # Check permissions
            if key_info.status != KeyStatus.ACTIVE:
                logger.warning(
                    "Attempted access to inactive key",
                    key_id=key_id,
                    status=key_info.status,
                )
                return None

            if key_info.allowed_agents and agent_id not in key_info.allowed_agents:
                logger.warning(
                    "Agent not authorized for key", key_id=key_id, agent_id=agent_id
                )
                return None

            if key_info.expires_at and time.time() > key_info.expires_at:
                logger.warning("Key expired", key_id=key_id)
                self._key_info[key_id].status = KeyStatus.EXPIRED
                return None

            # Decrypt and return key
            salt = self._salts[key_id]
            cipher = self._create_cipher(self.vault_password, salt)
            encrypted_key = self._keys[key_id]
            api_key = cipher.decrypt(encrypted_key).decode()

            # Update usage stats
            self._key_info[key_id].last_used = time.time()
            self._key_info[key_id].usage_count += 1

            return api_key

        except Exception as e:
            logger.error("Failed to retrieve API key", key_id=key_id, error=str(e))
            return None

    def revoke_key(self, key_id: str) -> bool:
        """Revoke API key access."""
        if key_id in self._key_info:
            self._key_info[key_id].status = KeyStatus.REVOKED
            logger.info("API key revoked", key_id=key_id)
            return True
        return False

    def list_keys(self) -> List[APIKeyInfo]:
        """List all key information (without actual keys)."""
        return list(self._key_info.values())


class APIKeyManager:
    """
    Centralized API Key Manager for Cartrita AI OS.

    Manages all API keys, permissions, and tool access with secure delegation.
    All agents must request keys through this manager for tool access.
    """

    def __init__(self):
        """Initialize the API Key Manager."""
        self.vault_password = os.getenv(
            "CARTRITA_VAULT_PASSWORD", "cartrita-secure-vault-2025"
        )
        self.vault = SecureKeyVault(self.vault_password)

        # Tool permission registry
        self.tool_permissions: Dict[str, ToolPermission] = {}

        # Active key checkouts (agent_id -> key_id -> checkout_time)
        self.active_checkouts: Dict[str, Dict[str, float]] = {}
        self._checkout_expiry_seconds = 3600  # 1 hour expiry for checkouts

        # Rate limiting tracking
        self.rate_limits: Dict[str, List[float]] = {}

        # Initialize with default permissions
        self._setup_default_permissions()

        # Load API keys from environment/config
        self._load_initial_keys()

        logger.info(
            "API Key Manager initialized", vault_keys=len(self.vault.list_keys())
        )

    def _setup_default_permissions(self):
        """Setup default tool permissions."""
        default_tools = {
            "web_search": ToolPermission(
                tool_name="web_search",
                required_keys=["tavily", "serper"],
                permission_level=PermissionLevel.READ,
                rate_limit=100,
            ),
            "openai_completion": ToolPermission(
                tool_name="openai_completion",
                required_keys=["openai"],
                permission_level=PermissionLevel.EXECUTE,
                rate_limit=50,
            ),
            "google_search": ToolPermission(
                tool_name="google_search",
                required_keys=["google"],
                permission_level=PermissionLevel.READ,
                rate_limit=100,
            ),
            "huggingface_inference": ToolPermission(
                tool_name="huggingface_inference",
                required_keys=["huggingface"],
                permission_level=PermissionLevel.EXECUTE,
                rate_limit=20,
            ),
        }

        self.tool_permissions.update(default_tools)

    def _load_initial_keys(self):
        """Load API keys from environment variables."""
        # Get settings with proper initialization
        from cartrita.orchestrator.utils.config import get_settings

        _settings = get_settings()

        key_mappings = {
            "openai": (
                _settings.ai.openai_api_key.get_secret_value()
                if _settings.ai.openai_api_key
                else None
            ),
            "google": os.getenv("GOOGLE_API_KEY"),
            "tavily": os.getenv("TAVILY_API_KEY"),
            "serper": os.getenv("SERPER_API_KEY"),
            "huggingface": os.getenv("HUGGINGFACE_API_KEY"),
        }

        for service, api_key in key_mappings.items():
            if api_key:
                key_info = APIKeyInfo(
                    key_id=f"{service}_primary",
                    service=service,
                    permissions=[PermissionLevel.READ, PermissionLevel.EXECUTE],
                    allowed_agents={"cartrita_core", "research", "code", "knowledge"},
                )
                self.vault.store_key(key_info.key_id, api_key, key_info)

    async def register_tool(self, tool_permission: ToolPermission) -> bool:
        """Register a new tool with permission requirements."""
        try:
            self.tool_permissions[tool_permission.tool_name] = tool_permission
            logger.info("Tool registered", tool_name=tool_permission.tool_name)
            return True
        except Exception as e:
            logger.error(
                "Failed to register tool",
                tool_name=tool_permission.tool_name,
                error=str(e),
            )
            return False

    async def request_key_access(
        self, agent_id: str, tool_name: str, duration_minutes: int = 60
    ) -> Optional[Dict[str, Any]]:
        """
        Agent requests access to API key for specific tool.

        Returns:
            Dict with key access info or None if denied
        """
        try:
            # Validate tool exists
            if tool_name not in self.tool_permissions:
                logger.warning(
                    "Unknown tool requested", tool_name=tool_name, agent_id=agent_id
                )
                return None

            tool_permission = self.tool_permissions[tool_name]

            # Check agent permissions
            if (
                tool_permission.allowed_agents
                and agent_id not in tool_permission.allowed_agents
            ):
                logger.warning(
                    "Agent not authorized for tool",
                    agent_id=agent_id,
                    tool_name=tool_name,
                )
                return None

            # Check rate limits
            if not self._check_rate_limit(agent_id, tool_permission):
                logger.warning(
                    "Rate limit exceeded", agent_id=agent_id, tool_name=tool_name
                )
                return None

            # Find available key for required services
            available_keys = {}
            for required_service in tool_permission.required_keys:
                key_info = self._find_available_key(required_service, agent_id)
                if not key_info:
                    logger.warning(
                        "No available key for service",
                        service=required_service,
                        agent_id=agent_id,
                    )
                    return None

                api_key = self.vault.retrieve_key(key_info.key_id, agent_id)
                if not api_key:
                    continue

                available_keys[required_service] = {
                    "key": api_key,
                    "key_id": key_info.key_id,
                    "service": key_info.service,
                }

            if not available_keys:
                logger.warning(
                    "No keys available for tool", tool_name=tool_name, agent_id=agent_id
                )
                return None

            # Create checkout record
            checkout_time = time.time()
            expires_at = checkout_time + (duration_minutes * 60)

            if agent_id not in self.active_checkouts:
                self.active_checkouts[agent_id] = {}

            for service, key_info in available_keys.items():
                self.active_checkouts[agent_id][key_info["key_id"]] = checkout_time

            # Record usage
            for service, key_info in available_keys.items():
                usage_record = KeyUsageRecord(
                    agent_id=agent_id,
                    tool_name=tool_name,
                    key_hash=self._hash_key(key_info["key"]),
                    timestamp=checkout_time,
                    success=True,
                )
                self.vault._access_log.append(usage_record)

            logger.info(
                "API key access granted",
                agent_id=agent_id,
                tool_name=tool_name,
                services=list(available_keys.keys()),
                expires_at=expires_at,
            )

            return {
                "tool_name": tool_name,
                "keys": available_keys,
                "expires_at": expires_at,
                "checkout_id": f"{agent_id}_{tool_name}_{int(checkout_time)}",
            }

        except Exception as e:
            logger.error(
                "Key access request failed",
                agent_id=agent_id,
                tool_name=tool_name,
                error=str(e),
            )
            return None

    async def return_key_access(self, agent_id: str, checkout_id: str) -> bool:
        """Agent returns key access after tool usage."""
        try:
            if agent_id in self.active_checkouts:
                # Clean up checkouts
                current_time = time.time()
                expired_keys = []

                for key_id, checkout_time in self.active_checkouts[agent_id].items():
                    if current_time - checkout_time > self._checkout_expiry_seconds:
                        expired_keys.append(key_id)

                for key_id in expired_keys:
                    del self.active_checkouts[agent_id][key_id]

                if not self.active_checkouts[agent_id]:
                    del self.active_checkouts[agent_id]

            logger.info(
                "Key access returned", agent_id=agent_id, checkout_id=checkout_id
            )
            # Periodically clean up all expired checkouts
            self._cleanup_expired_checkouts()
            return True

        except Exception as e:
            logger.error(
                "Failed to return key access",
                agent_id=agent_id,
                checkout_id=checkout_id,
                error=str(e),
            )
            return False

    def _find_available_key(self, service: str, agent_id: str) -> Optional[APIKeyInfo]:
        """Find an available key for the given service."""
        for key_info in self.vault.list_keys():
            if (
                key_info.service == service
                and key_info.status == KeyStatus.ACTIVE
                and (not key_info.allowed_agents or agent_id in key_info.allowed_agents)
            ):
                return key_info
        return None

    def _cleanup_expired_checkouts(self):
        """Periodically clean up expired checkouts to avoid memory leaks."""
        current_time = time.time()
        expired_agents = []
        for agent_id, checkouts in self.active_checkouts.items():
            expired_keys = [
                key_id
                for key_id, checkout_time in checkouts.items()
                if current_time - checkout_time > self._checkout_expiry_seconds
            ]
            for key_id in expired_keys:
                del checkouts[key_id]
            if not checkouts:
                expired_agents.append(agent_id)
        for agent_id in expired_agents:
            del self.active_checkouts[agent_id]

    def _check_rate_limit(self, agent_id: str, tool_permission: ToolPermission) -> bool:
        """Check if agent is within rate limits."""
        if not tool_permission.rate_limit:
            return True

        current_time = time.time()
        rate_key = f"{agent_id}_{tool_permission.tool_name}"

        if rate_key not in self.rate_limits:
            self.rate_limits[rate_key] = []

        # Clean old requests (older than 1 hour)
        self.rate_limits[rate_key] = [
            req_time
            for req_time in self.rate_limits[rate_key]
            if current_time - req_time < 3600
        ]

        # Check if under limit
        if len(self.rate_limits[rate_key]) >= tool_permission.rate_limit:
            return False

        self.rate_limits[rate_key].append(current_time)
        return True

    # Note: Truncating the SHA256 hash to 16 characters reduces storage size and log verbosity,
    # but increases the risk of hash collisions compared to using the full hash.
    # This is acceptable for non-critical logging/auditing, but should not be used for security-sensitive operations.
    def _hash_key(self, api_key: str) -> str:
        """Create secure hash of API key for logging (truncated to 16 characters for brevity)."""
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]

    @asynccontextmanager
    async def key_access_context(self, agent_id: str, tool_name: str):
        """Context manager for automatic key checkout/return."""
        access_info = await self.request_key_access(agent_id, tool_name)
        if not access_info:
            raise PermissionError(f"Access denied for {tool_name}")

        try:
            yield access_info
        finally:
            try:
                await self.return_key_access(agent_id, access_info["checkout_id"])
            except Exception as e:
                logger.error(
                    "Error returning key access in context manager",
                    agent_id=agent_id,
                    checkout_id=access_info["checkout_id"],
                    error=str(e),
                )

    async def get_agent_permissions(self, agent_id: str) -> Dict[str, Any]:
        """Get current permissions for an agent."""
        permissions = {
            "agent_id": agent_id,
            "available_tools": [],
            "active_checkouts": self.active_checkouts.get(agent_id, {}),
            "rate_limits": {},
        }

        for tool_name, tool_permission in self.tool_permissions.items():
            if (
                not tool_permission.allowed_agents
                or agent_id in tool_permission.allowed_agents
            ):
                permissions["available_tools"].append(
                    {
                        "tool_name": tool_name,
                        "permission_level": tool_permission.permission_level,
                        "required_keys": tool_permission.required_keys,
                    }
                )

        return permissions

    async def audit_key_usage(self, hours: int = 24) -> List[KeyUsageRecord]:
        """Get key usage audit for specified time period."""
        cutoff_time = time.time() - (hours * 3600)
        return [
            record
            for record in self.vault._access_log
            if record.timestamp > cutoff_time
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Health check for the key manager."""
        return {
            "status": "healthy",
            "total_keys": len(self.vault.list_keys()),
            "active_checkouts": sum(
                len(checkouts) for checkouts in self.active_checkouts.values()
            ),
            "registered_tools": len(self.tool_permissions),
            "vault_operational": len(self.vault.list_keys()) > 0,
        }
