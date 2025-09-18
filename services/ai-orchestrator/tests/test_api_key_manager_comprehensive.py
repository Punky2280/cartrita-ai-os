"""
Comprehensive tests for API Key Manager and secure vault functionality.
"""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from cartrita.orchestrator.agents.cartrita_core.api_key_manager import (
    APIKeyInfo,
    APIKeyManager,
    KeyStatus,
    SecureKeyVault,
)


@pytest.mark.unit
@pytest.mark.security
class TestSecureKeyVault:
    """Test SecureKeyVault functionality."""

    @pytest.fixture
    def temp_vault_dir(self):
        """Create temporary directory for vault."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def vault(self):
        """Create SecureKeyVault instance."""
        return SecureKeyVault("test_password")

    @pytest.fixture
    def sample_key_info(self):
        """Create sample APIKeyInfo."""
        return APIKeyInfo(
            key_id="test_key",
            service="test_service",
            status=KeyStatus.ACTIVE,
            allowed_agents=["test_agent"],
        )

    def test_vault_initialization(self, vault):
        """Test vault initialization with password."""
        assert vault.vault_password == "test_password"
        assert hasattr(vault, "_salts")
        assert hasattr(vault, "_keys")
        assert hasattr(vault, "_key_info")

    def test_store_and_retrieve_key(self, vault, sample_key_info):
        """Test storing and retrieving API keys."""
        key_id = "test_key"
        test_key = "test_api_key_value"
        agent_id = "test_agent"

        # Store key
        stored = vault.store_key(key_id, test_key, sample_key_info)
        assert stored is True

        # Retrieve key
        retrieved_key = vault.retrieve_key(key_id, agent_id)
        assert retrieved_key == test_key

    def test_key_encryption(self, vault, sample_key_info):
        """Test that keys are encrypted in storage."""
        key_id = "test_key"
        test_key = "test_api_key_value"

        vault.store_key(key_id, test_key, sample_key_info)

        # Raw encrypted data should not match original
        encrypted_data = vault._keys[key_id]
        assert encrypted_data != test_key.encode()
        assert len(encrypted_data) > len(test_key)

    def test_retrieve_nonexistent_key(self, vault):
        """Test retrieving non-existent key returns None."""
        result = vault.retrieve_key("nonexistent_key", "test_agent")
        assert result is None

    def test_list_keys(self, vault, sample_key_info):
        """Test listing stored keys."""
        keys = ["key1", "key2", "key3"]

        # Store multiple keys
        for key in keys:
            vault.store_key(key, f"value-{key}", sample_key_info)

        # Check keys are stored
        stored_keys = list(vault._keys.keys())
        assert set(keys).issubset(set(stored_keys))


@pytest.mark.unit
@pytest.mark.security
class TestAPIKeyManager:
    """Test APIKeyManager functionality."""

    @pytest.fixture
    def mock_vault(self):
        """Create mock vault for testing."""
        vault = Mock(spec=SecureKeyVault)
        vault.store_key = Mock(return_value="test-key-id")
        vault.retrieve_key = Mock(return_value="test-api-key")
        vault.list_keys = Mock(return_value=["openai_primary", "anthropic_primary"])
        vault.revoke_key = Mock()
        return vault

    @pytest.fixture
    def manager(self, mock_vault):
        """Create APIKeyManager with mocked vault."""
        with patch(
            "cartrita.orchestrator.agents.cartrita_core.api_key_manager.SecureKeyVault"
        ) as mock_vault_class:
            mock_vault_class.return_value = mock_vault
            return APIKeyManager()

    def test_manager_initialization(self, manager):
        """Test API key manager initialization."""
        assert manager.vault is not None
        assert manager.permissions == {}
        assert manager.usage_stats == {}
        assert manager.rate_limits == {}

    def test_register_tool(self, manager):
        """Test tool registration."""
        tool_name = "test_tool"
        required_keys = ["openai_api_key", "anthropic_api_key"]

        manager.register_tool(tool_name, required_keys)

        assert tool_name in manager.permissions
        assert manager.permissions[tool_name] == required_keys

    @pytest.mark.asyncio
    async def test_request_key_access_success(self, manager):
        """Test successful key access request."""
        tool_name = "test_tool"
        key_type = "openai_api_key"

        # Register tool first
        manager.register_tool(tool_name, [key_type])

        # Request access
        key = await manager.request_key_access(tool_name, key_type)

        assert key == "test-api-key"
        assert tool_name in manager.usage_stats

    @pytest.mark.asyncio
    async def test_request_key_access_unauthorized(self, manager):
        """Test unauthorized key access request."""
        tool_name = "unauthorized_tool"
        key_type = "openai_api_key"

        # Don't register tool
        with pytest.raises(PermissionError):
            await manager.request_key_access(tool_name, key_type)

    @pytest.mark.asyncio
    async def test_request_key_access_nonexistent_key(self, manager):
        """Test request for nonexistent key."""
        tool_name = "test_tool"
        key_type = "nonexistent_key"

        manager.register_tool(tool_name, [key_type])
        manager.vault.retrieve_key.return_value = None

        with pytest.raises(KeyError):
            await manager.request_key_access(tool_name, key_type)

    @pytest.mark.asyncio
    async def test_return_key_access(self, manager):
        """Test returning key access."""
        tool_name = "test_tool"
        key_type = "openai_api_key"

        # Setup initial state
        manager.register_tool(tool_name, [key_type])
        await manager.request_key_access(tool_name, key_type)

        # Return access
        await manager.return_key_access(tool_name, key_type)

        # Verify cleanup
        assert (
            tool_name not in manager.usage_stats
            or key_type not in manager.usage_stats.get(tool_name, {})
        )

    @pytest.mark.asyncio
    async def test_rate_limiting(self, manager):
        """Test rate limiting functionality."""
        tool_name = "rate_limited_tool"
        key_type = "openai_api_key"

        manager.register_tool(tool_name, [key_type])

        # Set aggressive rate limit
        manager.rate_limits[f"{tool_name}:{key_type}"] = {
            "max_requests": 1,
            "window_seconds": 60,
            "requests": [],
            "current_count": 0,
        }

        # First request should succeed
        key1 = await manager.request_key_access(tool_name, key_type)
        assert key1 == "test-api-key"

        # Second request should be rate limited
        with pytest.raises(Exception):  # Rate limit exception
            await manager.request_key_access(tool_name, key_type)

    def test_usage_tracking(self, manager):
        """Test usage statistics tracking."""
        tool_name = "tracked_tool"
        key_type = "openai_api_key"

        manager.register_tool(tool_name, [key_type])
        manager._track_usage(tool_name, key_type, 150)  # 150 tokens

        assert tool_name in manager.usage_stats
        assert key_type in manager.usage_stats[tool_name]
        assert manager.usage_stats[tool_name][key_type]["total_tokens"] == 150
        assert manager.usage_stats[tool_name][key_type]["request_count"] == 1

    def test_get_usage_stats(self, manager):
        """Test getting usage statistics."""
        # Setup some usage data
        manager.usage_stats = {
            "tool1": {
                "openai_api_key": {
                    "total_tokens": 1000,
                    "request_count": 10,
                    "last_used": "2025-09-17T04:00:00Z",
                }
            }
        }

        stats = manager.get_usage_stats()
        assert "tool1" in stats
        assert stats["tool1"]["openai_api_key"]["total_tokens"] == 1000

    def test_security_audit(self, manager):
        """Test security audit functionality."""
        # Setup test data
        manager.usage_stats = {
            "suspicious_tool": {
                "openai_api_key": {
                    "total_tokens": 1000000,  # Suspiciously high
                    "request_count": 10000,
                    "last_used": "2025-09-17T04:00:00Z",
                }
            }
        }

        audit_results = manager.security_audit()

        assert "high_usage_tools" in audit_results
        assert len(audit_results["high_usage_tools"]) > 0

    @pytest.mark.asyncio
    async def test_key_rotation(self, manager):
        """Test API key rotation."""
        key_type = "openai_api_key"
        old_key = "sk-old-key"
        new_key = "sk-new-key"

        # Setup old key
        manager.vault.retrieve_key.return_value = old_key

        # Rotate key
        manager.vault.store_key.return_value = "new-key-id"
        manager.vault.retrieve_key.return_value = new_key

        await manager.rotate_key(key_type, new_key)

        # Verify new key is stored
        manager.vault.store_key.assert_called()
        manager.vault.revoke_key.assert_called()

    def test_emergency_lockdown(self, manager):
        """Test emergency lockdown functionality."""
        # Setup normal operation
        manager.permissions["tool1"] = ["openai_api_key"]
        manager.emergency_mode = False

        # Trigger lockdown
        manager.emergency_lockdown("Security breach detected")

        assert manager.emergency_mode is True
        assert len(manager.permissions) == 0  # All permissions revoked

    def test_backup_and_restore(self, manager):
        """Test backup and restore functionality."""
        # Setup test data
        manager.permissions = {"tool1": ["key1"]}
        manager.usage_stats = {"tool1": {"key1": {"count": 5}}}

        # Create backup
        backup_data = manager.create_backup()

        # Clear data
        manager.permissions = {}
        manager.usage_stats = {}

        # Restore from backup
        manager.restore_from_backup(backup_data)

        assert "tool1" in manager.permissions
        assert "tool1" in manager.usage_stats


@pytest.mark.integration
@pytest.mark.security
class TestAPIKeyManagerIntegration:
    """Integration tests for API Key Manager."""

    @pytest.fixture
    def real_manager(self, temp_dir):
        """Create real API key manager for integration testing."""
        return APIKeyManager(vault_dir=temp_dir)

    @pytest.mark.asyncio
    async def test_end_to_end_key_lifecycle(self, real_manager):
        """Test complete key lifecycle."""
        tool_name = "integration_tool"
        key_type = "test_api_key"
        api_key = "sk-integration-test-key"

        # 1. Register tool
        real_manager.register_tool(tool_name, [key_type])

        # 2. Store API key
        key_id = real_manager.vault.store_key(f"{key_type}_primary", api_key)
        assert key_id is not None

        # 3. Request access
        retrieved_key = await real_manager.request_key_access(tool_name, key_type)
        assert retrieved_key == api_key

        # 4. Track usage
        real_manager._track_usage(tool_name, key_type, 100)

        # 5. Return access
        await real_manager.return_key_access(tool_name, key_type)

        # 6. Verify statistics
        stats = real_manager.get_usage_stats()
        assert tool_name in stats

    @pytest.mark.asyncio
    async def test_concurrent_key_access(self, real_manager):
        """Test concurrent key access requests."""
        import asyncio

        tool_names = [f"concurrent_tool_{i}" for i in range(5)]
        key_type = "concurrent_test_key"

        # Setup
        for tool_name in tool_names:
            real_manager.register_tool(tool_name, [key_type])

        real_manager.vault.store_key(f"{key_type}_primary", "sk-concurrent-test")

        # Concurrent access
        tasks = [
            real_manager.request_key_access(tool_name, key_type)
            for tool_name in tool_names
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed (or some may be rate limited)
        successful_results = [r for r in results if isinstance(r, str)]
        assert len(successful_results) > 0

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_rate_limiting_over_time(self, real_manager):
        """Test rate limiting behavior over time."""
        import asyncio

        tool_name = "rate_test_tool"
        key_type = "rate_test_key"

        real_manager.register_tool(tool_name, [key_type])
        real_manager.vault.store_key(f"{key_type}_primary", "sk-rate-test")

        # Set strict rate limit
        real_manager.set_rate_limit(
            tool_name, key_type, max_requests=2, window_seconds=1
        )

        # Rapid requests
        results = []
        for i in range(5):
            try:
                key = await real_manager.request_key_access(tool_name, key_type)
                results.append("success")
                await real_manager.return_key_access(tool_name, key_type)
            except Exception:
                results.append("rate_limited")

            if i < 4:  # Don't sleep after last request
                await asyncio.sleep(0.2)

        # Should have some rate limiting
        assert "rate_limited" in results

    def test_security_compliance(self, real_manager):
        """Test security compliance features."""
        # Test that keys are encrypted at rest
        test_key = "sk-security-test-key"
        real_manager.vault.store_key("security_test", test_key)

        # Verify key file is encrypted
        key_files = os.listdir(real_manager.vault.vault_dir)
        for key_file in key_files:
            if key_file.endswith(".key"):
                file_path = os.path.join(real_manager.vault.vault_dir, key_file)
                with open(file_path, "rb") as f:
                    content = f.read()
                assert test_key.encode() not in content

    def test_audit_logging(self, real_manager):
        """Test that security events are logged."""
        import logging
        from unittest.mock import patch

        with patch(
            "cartrita.orchestrator.agents.cartrita_core.api_key_manager.logger"
        ) as mock_logger:
            # Trigger security event
            real_manager.emergency_lockdown("Test security event")

            # Verify logging
            mock_logger.warning.assert_called()
            mock_logger.error.assert_called()


@pytest.mark.performance
class TestAPIKeyManagerPerformance:
    """Performance tests for API Key Manager."""

    @pytest.fixture
    def performance_manager(self, temp_dir):
        """Create manager for performance testing."""
        return APIKeyManager(vault_dir=temp_dir)

    def test_key_storage_performance(self, performance_manager):
        """Test key storage and retrieval performance."""
        import time

        # Store multiple keys and measure time
        start_time = time.time()

        for i in range(100):
            key_id = f"perf_test_key_{i}"
            api_key = f"sk-performance-test-key-{i:03d}"
            performance_manager.vault.store_key(key_id, api_key)

        storage_time = time.time() - start_time

        # Retrieve keys and measure time
        start_time = time.time()

        for i in range(100):
            key_id = f"perf_test_key_{i}"
            retrieved_key = performance_manager.vault.retrieve_key(key_id)
            assert retrieved_key is not None

        retrieval_time = time.time() - start_time

        # Performance assertions
        assert storage_time < 5.0  # Should store 100 keys in under 5 seconds
        assert retrieval_time < 2.0  # Should retrieve 100 keys in under 2 seconds

    @pytest.mark.asyncio
    async def test_concurrent_access_performance(self, performance_manager):
        """Test performance under concurrent access."""
        import asyncio
        import time

        # Setup
        tool_name = "perf_tool"
        key_type = "perf_key"
        performance_manager.register_tool(tool_name, [key_type])
        performance_manager.vault.store_key(f"{key_type}_primary", "sk-perf-test")

        # Concurrent access test
        start_time = time.time()

        tasks = [
            performance_manager.request_key_access(tool_name, key_type)
            for _ in range(50)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Cleanup
        for _ in range(len([r for r in results if isinstance(r, str)])):
            await performance_manager.return_key_access(tool_name, key_type)

        # Performance checks
        total_time = end_time - start_time
        assert (
            total_time < 10.0
        )  # Should handle 50 concurrent requests in under 10 seconds

    def test_memory_usage_efficiency(self, performance_manager):
        """Test memory usage remains efficient."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Store many keys
        for i in range(1000):
            key_id = f"memory_test_key_{i}"
            api_key = f"sk-memory-test-{i:04d}-{'x' * 50}"  # Longer keys
            performance_manager.vault.store_key(key_id, api_key)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable
        assert memory_increase < 50  # Less than 50MB for 1000 keys
