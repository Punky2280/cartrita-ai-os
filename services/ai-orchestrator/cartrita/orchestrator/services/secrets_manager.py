"""
Centralized Secrets Management Service for Cartrita AI OS
Provides secure storage, retrieval, and rotation of secrets
"""

import base64
import hashlib
import json
import os
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import redis
import structlog
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from pydantic import BaseModel, Field, SecretStr
from redis.lock import Lock

logger = structlog.get_logger(__name__)


class SecretConfig(BaseModel):
    """Configuration for a managed secret"""

    name: str
    type: str = Field(
        default="api_key",
        description="Type of secret: api_key, password, certificate, token",
    )
    rotation_days: int = Field(default=90, description="Days until rotation required")
    encrypted: bool = Field(default=True, description="Whether to encrypt at rest")
    required: bool = Field(
        default=True, description="Whether this secret is required for operation"
    )
    allowed_services: List[str] = Field(
        default_factory=list, description="Services allowed to access this secret"
    )


class SecretsManager:
    """
    Centralized secrets management with encryption, rotation, and access control
    """

    # Define all managed secrets with their configurations
    SECRET_CONFIGS = {
        "OPENAI_API_KEY": SecretConfig(
            name="OPENAI_API_KEY",
            type="api_key",
            rotation_days=90,
            allowed_services=["ai-orchestrator", "test"],
        ),
        "ANTHROPIC_API_KEY": SecretConfig(
            name="ANTHROPIC_API_KEY",
            type="api_key",
            rotation_days=90,
            allowed_services=["ai-orchestrator", "test"],
        ),
        "DEEPGRAM_API_KEY": SecretConfig(
            name="DEEPGRAM_API_KEY",
            type="api_key",
            rotation_days=90,
            allowed_services=["ai-orchestrator", "audio-service"],
        ),
        "TAVILY_API_KEY": SecretConfig(
            name="TAVILY_API_KEY",
            type="api_key",
            rotation_days=90,
            allowed_services=["ai-orchestrator", "search-service"],
        ),
        "LANGCHAIN_API_KEY": SecretConfig(
            name="LANGCHAIN_API_KEY",
            type="api_key",
            rotation_days=90,
            allowed_services=["ai-orchestrator"],
        ),
        "JWT_SECRET_KEY": SecretConfig(
            name="JWT_SECRET_KEY",
            type="token",
            rotation_days=30,
            allowed_services=["api-gateway", "ai-orchestrator", "frontend"],
        ),
        "DATABASE_PASSWORD": SecretConfig(
            name="DATABASE_PASSWORD",
            type="password",
            rotation_days=60,
            allowed_services=["ai-orchestrator", "api-gateway"],
        ),
        "REDIS_PASSWORD": SecretConfig(
            name="REDIS_PASSWORD",
            type="password",
            rotation_days=60,
            allowed_services=["ai-orchestrator", "api-gateway", "cache-service"],
        ),
        "CARTRITA_API_KEY": SecretConfig(
            name="CARTRITA_API_KEY",
            type="api_key",
            rotation_days=90,
            allowed_services=["api-gateway", "frontend", "test"],
        ),
        "ENCRYPTION_KEY": SecretConfig(
            name="ENCRYPTION_KEY",
            type="token",
            rotation_days=180,
            allowed_services=["ai-orchestrator"],
        ),
    }

    def __init__(
        self,
        service_name: str = "ai-orchestrator",
        redis_client: Optional[redis.Redis] = None,
    ):
        """
        Initialize the secrets manager

        Args:
            service_name: Name of the service accessing secrets
            redis_client: Optional Redis client for distributed locking
        """
        self.service_name = service_name
        self.redis_client = redis_client
        self._cipher_suite: Optional[Fernet] = None
        self._secrets_cache: Dict[str, Any] = {}
        self._rotation_check_performed = False

        # Initialize encryption
        self._initialize_encryption()

        # Load secrets from environment
        self._load_secrets()

        logger.info("Secrets manager initialized", service=service_name)

    def _initialize_encryption(self):
        """Initialize encryption using a master key"""
        # Get or generate master encryption key
        master_key = os.environ.get("CARTRITA_MASTER_KEY")

        if not master_key:
            # Generate from machine ID and salt for consistency
            machine_id = self._get_machine_id()
            salt = b"cartrita-salt-2025"
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
            self._cipher_suite = Fernet(key)
            logger.warning(
                "Using derived encryption key. Set CARTRITA_MASTER_KEY for production"
            )
        else:
            try:
                self._cipher_suite = Fernet(master_key.encode())
                logger.info("Using provided master encryption key")
            except Exception as e:
                logger.error("Invalid master key format", error=str(e))
                raise ValueError("Invalid CARTRITA_MASTER_KEY format")

    def _get_machine_id(self) -> str:
        """Get a unique machine identifier"""
        # Try multiple methods to get a stable machine ID
        machine_id = None

        # Try hostname
        import socket

        machine_id = socket.gethostname()

        # Add user for uniqueness
        import getpass

        machine_id = f"{machine_id}-{getpass.getuser()}"

        return machine_id or "default-cartrita-instance"

    def _load_secrets(self):
        """Load secrets from environment variables"""
        loaded_count = 0
        missing_required = []

        for secret_name, config in self.SECRET_CONFIGS.items():
            value = os.environ.get(secret_name)

            if value:
                # Store encrypted if configured
                if config.encrypted and self._cipher_suite:
                    encrypted_value = self._cipher_suite.encrypt(value.encode())
                    self._secrets_cache[secret_name] = encrypted_value
                else:
                    self._secrets_cache[secret_name] = value
                loaded_count += 1
            elif config.required:
                missing_required.append(secret_name)

        logger.info(
            "Secrets loaded",
            loaded=loaded_count,
            total=len(self.SECRET_CONFIGS),
            missing_required=len(missing_required),
        )

        if missing_required:
            logger.warning("Required secrets missing", secrets=missing_required)

    def get_secret(
        self, secret_name: str, service_override: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a secret value with access control

        Args:
            secret_name: Name of the secret to retrieve
            service_override: Override the service name for access control

        Returns:
            Decrypted secret value or None if not found/not authorized
        """
        service = service_override or self.service_name

        # Check if secret exists
        if secret_name not in self.SECRET_CONFIGS:
            logger.warning(
                "Unknown secret requested", secret=secret_name, service=service
            )
            return None

        config = self.SECRET_CONFIGS[secret_name]

        # Check access control
        if config.allowed_services and service not in config.allowed_services:
            logger.warning(
                "Unauthorized secret access attempt",
                secret=secret_name,
                service=service,
                allowed=config.allowed_services,
            )
            return None

        # Get from cache
        value = self._secrets_cache.get(secret_name)

        if not value:
            # Try loading from environment again
            value = os.environ.get(secret_name)
            if value:
                if config.encrypted and self._cipher_suite:
                    encrypted_value = self._cipher_suite.encrypt(value.encode())
                    self._secrets_cache[secret_name] = encrypted_value
                    value = encrypted_value
                else:
                    self._secrets_cache[secret_name] = value

        if value:
            # Decrypt if necessary
            if config.encrypted and self._cipher_suite and isinstance(value, bytes):
                try:
                    decrypted = self._cipher_suite.decrypt(value).decode()
                    logger.debug(
                        "Secret retrieved", secret=secret_name, service=service
                    )
                    return decrypted
                except Exception as e:
                    logger.error(
                        "Failed to decrypt secret", secret=secret_name, error=str(e)
                    )
                    return None
            else:
                logger.debug("Secret retrieved", secret=secret_name, service=service)
                return value if isinstance(value, str) else value.decode()

        logger.warning("Secret not found", secret=secret_name)
        return None

    def set_secret(
        self, secret_name: str, value: str, service_override: Optional[str] = None
    ) -> bool:
        """
        Set or update a secret value

        Args:
            secret_name: Name of the secret
            value: Secret value
            service_override: Override service for access control

        Returns:
            True if successful, False otherwise
        """
        service = service_override or self.service_name

        # Check if secret is managed
        if secret_name not in self.SECRET_CONFIGS:
            logger.warning("Attempt to set unmanaged secret", secret=secret_name)
            return False

        config = self.SECRET_CONFIGS[secret_name]

        # Check access control
        if config.allowed_services and service not in config.allowed_services:
            logger.warning(
                "Unauthorized secret update attempt",
                secret=secret_name,
                service=service,
            )
            return False

        # Encrypt and store
        if config.encrypted and self._cipher_suite:
            encrypted_value = self._cipher_suite.encrypt(value.encode())
            self._secrets_cache[secret_name] = encrypted_value
        else:
            self._secrets_cache[secret_name] = value

        # Also update environment for backward compatibility
        os.environ[secret_name] = value

        logger.info("Secret updated", secret=secret_name, service=service)
        return True

    def rotate_secret(self, secret_name: str, new_value: str) -> bool:
        """
        Rotate a secret with the new value

        Args:
            secret_name: Name of the secret to rotate
            new_value: New secret value

        Returns:
            True if successful
        """
        if secret_name not in self.SECRET_CONFIGS:
            logger.error("Cannot rotate unmanaged secret", secret=secret_name)
            return False

        # Store old value for rollback if needed
        old_value = self.get_secret(secret_name)

        # Set new value
        if self.set_secret(secret_name, new_value):
            logger.info(
                "Secret rotated successfully",
                secret=secret_name,
                rotation_days=self.SECRET_CONFIGS[secret_name].rotation_days,
            )

            # Store rotation metadata if Redis is available
            if self.redis_client:
                rotation_key = f"secret_rotation:{secret_name}"
                self.redis_client.hset(
                    rotation_key,
                    mapping={
                        "last_rotation": datetime.utcnow().isoformat(),
                        "next_rotation": (
                            datetime.utcnow()
                            + timedelta(
                                days=self.SECRET_CONFIGS[secret_name].rotation_days
                            )
                        ).isoformat(),
                    },
                )

            return True

        return False

    def check_rotation_needed(self) -> List[str]:
        """
        Check which secrets need rotation

        Returns:
            List of secret names that need rotation
        """
        needs_rotation: list[str] = []

        if not self.redis_client:
            logger.warning("Cannot check rotation without Redis client")
            return needs_rotation

        for secret_name, config in self.SECRET_CONFIGS.items():
            rotation_key = f"secret_rotation:{secret_name}"
            last_rotation_str = self.redis_client.hget(rotation_key, "last_rotation")

            if last_rotation_str:
                last_rotation = datetime.fromisoformat(last_rotation_str.decode())
                days_since_rotation = (datetime.utcnow() - last_rotation).days

                if days_since_rotation >= config.rotation_days:
                    needs_rotation.append(secret_name)
                    logger.warning(
                        "Secret needs rotation",
                        secret=secret_name,
                        days_since_rotation=days_since_rotation,
                        max_days=config.rotation_days,
                    )
            else:
                # No rotation record, assume it needs rotation
                needs_rotation.append(secret_name)

        return needs_rotation

    def validate_all_secrets(self) -> Dict[str, bool]:
        """
        Validate all required secrets are present and accessible

        Returns:
            Dictionary of secret names and their validation status
        """
        validation_results = {}

        for secret_name, config in self.SECRET_CONFIGS.items():
            if config.required:
                value = self.get_secret(secret_name)
                validation_results[secret_name] = value is not None

        valid_count = sum(1 for v in validation_results.values() if v)
        logger.info(
            "Secrets validation completed",
            valid=valid_count,
            total=len(validation_results),
            results=validation_results,
        )

        return validation_results

    @lru_cache(maxsize=128)
    def get_mock_secret(self, secret_type: str) -> str:
        """
        Get a mock secret for testing purposes

        Args:
            secret_type: Type of secret (api_key, password, token)

        Returns:
            Mock secret value safe for testing
        """
        mock_values = {
            "api_key": "mock-api-key-xxxx-xxxx-xxxx",
            "password": "mock-password-TEST-ONLY",
            "token": "mock.jwt.token.for.testing.only",
            "certificate": "-----BEGIN MOCK CERTIFICATE-----\nMOCK_CERT_DATA\n-----END MOCK CERTIFICATE-----",
        }

        return mock_values.get(secret_type, "mock-secret-value")

    def export_safe_config(self) -> Dict[str, Any]:
        """
        Export configuration without sensitive values

        Returns:
            Safe configuration dictionary
        """
        safe_config = {}

        for secret_name, config in self.SECRET_CONFIGS.items():
            value = self.get_secret(secret_name)
            safe_config[secret_name] = {
                "configured": value is not None,
                "type": config.type,
                "rotation_days": config.rotation_days,
                "allowed_services": config.allowed_services,
            }

        return safe_config


# Singleton instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager(
    service_name: str = "ai-orchestrator", redis_client: Optional[redis.Redis] = None
) -> SecretsManager:
    """
    Get or create the secrets manager singleton

    Args:
        service_name: Name of the service
        redis_client: Optional Redis client

    Returns:
        SecretsManager instance
    """
    global _secrets_manager

    if _secrets_manager is None:
        _secrets_manager = SecretsManager(service_name, redis_client)

    return _secrets_manager


def get_secret(secret_name: str, service: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get a secret

    Args:
        secret_name: Name of the secret
        service: Service requesting the secret

    Returns:
        Secret value or None
    """
    manager = get_secrets_manager(service or "default")
    return manager.get_secret(secret_name)


def validate_secrets() -> bool:
    """
    Validate all required secrets are configured

    Returns:
        True if all required secrets are valid
    """
    manager = get_secrets_manager()
    results = manager.validate_all_secrets()
    return all(results.values())
