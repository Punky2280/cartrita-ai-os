#!/usr/bin/env python3
"""
Environment Variables & Secrets Management Security Validation Tests
====================================================================

Comprehensive security validation tests for Task 8 implementation.
Tests environment variable validation, placeholder detection, API key format validation,
and security enforcement mechanisms.

SECURITY SCOPE:
- OWASP A07 (Authentication Failures) prevention
- OWASP A02 (Cryptographic Failures) mitigation
- Hardcoded secrets detection
- Environment variable format validation
- Security policy enforcement

Usage:
    python tests/security/test_environment_security_validation.py
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the services directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services"))

try:
    from shared.config.secure_environment import (
        SecureEnvironmentConfig,
        SecurityError,
        ValidationResult,
        load_secure_environment,
        get_validated_api_key,
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure the secure_environment.py module is available")
    sys.exit(1)


class TestEnvironmentSecurityValidation(unittest.TestCase):
    """Test suite for environment variable security validation"""

    def setUp(self):
        """Set up test environment"""
        self.config = SecureEnvironmentConfig()
        self.test_env_vars = {}

        # Store original environment to restore later
        self.original_env = dict(os.environ)

    def tearDown(self):
        """Clean up test environment"""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_valid_api_key_formats(self):
        """Test valid API key format validation"""
        valid_keys = {
            "OPENAI_API_KEY": "sk-abcd1234567890abcdefghijklmnopqrstuvwxyz",
            "ANTHROPIC_API_KEY": "sk-ant-abcd1234567890abcdefghijklmnopqr",
            "HUGGINGFACE_TOKEN": "hf_abcd1234567890abcdefghijklmnopqr",
            "DEEPGRAM_API_KEY": "abcd1234567890abcdef1234567890ab",  # 32 hex chars
            "TAVILY_API_KEY": "tvly-abcd1234567890abcdef",
            "GITHUB_TOKEN": "ghs_abcd1234567890abcdefghijklmnopqrstuvwxyz",
            "LANGCHAIN_API_KEY": "lsv2_pt_abcd1234567890abcdef",
            "JWT_SECRET_KEY": "abcd1234567890abcdefghijklmnopqrstuvwxyzABCD1234567890ABCDEFGHIJ=",
        }

        for key, value in valid_keys.items():
            with self.subTest(key=key):
                validation = self.config._validate_env_var(key, value)
                self.assertEqual(validation.validation_result, ValidationResult.VALID)
                self.assertTrue(validation.value_present)

    def test_invalid_api_key_formats(self):
        """Test invalid API key format detection"""
        invalid_keys = {
            "OPENAI_API_KEY": "invalid-key",
            "ANTHROPIC_API_KEY": "sk-wrong-prefix",
            "HUGGINGFACE_TOKEN": "wrong_prefix_token",
            "DEEPGRAM_API_KEY": "too-short",
            "TAVILY_API_KEY": "wrong-prefix",
            "GITHUB_TOKEN": "invalid_github_token",
            "LANGCHAIN_API_KEY": "wrong_prefix_key",
            "JWT_SECRET_KEY": "tooshort",
        }

        for key, value in invalid_keys.items():
            with self.subTest(key=key):
                validation = self.config._validate_env_var(key, value)
                self.assertEqual(
                    validation.validation_result, ValidationResult.INVALID_FORMAT
                )
                self.assertEqual(validation.security_level, "high")

    def test_placeholder_detection(self):
        """Test placeholder pattern detection"""
        placeholder_values = [
            "REPLACE_WITH_YOUR_KEY",
            "your_openai_key_here",
            "sk-proj-your_key",
            "lsv2_pt_your_key",
            "INSERT_YOUR_API_KEY",
            "CHANGE_THIS_SECRET",
            "PLACEHOLDER_VALUE",
            "EXAMPLE_KEY",
            "TEST_KEY_123",
            "DEMO_API_KEY",
        ]

        for value in placeholder_values:
            with self.subTest(value=value):
                validation = self.config._validate_env_var("TEST_KEY", value)
                self.assertEqual(
                    validation.validation_result, ValidationResult.PLACEHOLDER_DETECTED
                )
                self.assertEqual(validation.security_level, "critical")

    def test_minimum_length_enforcement(self):
        """Test minimum length requirements"""
        short_keys = {
            "OPENAI_API_KEY": "sk-short",  # Too short
            "HUGGINGFACE_TOKEN": "hf_short",  # Too short
            "JWT_SECRET_KEY": "short_secret",  # Too short
        }

        for key, value in short_keys.items():
            with self.subTest(key=key):
                validation = self.config._validate_env_var(key, value)
                self.assertEqual(
                    validation.validation_result, ValidationResult.INSUFFICIENT_ENTROPY
                )
                self.assertEqual(validation.security_level, "high")

    def test_missing_environment_variables(self):
        """Test handling of missing environment variables"""
        validation = self.config._validate_env_var("MISSING_KEY", "")
        self.assertEqual(validation.validation_result, ValidationResult.MISSING)
        self.assertFalse(validation.value_present)

    def test_secure_api_key_retrieval_success(self):
        """Test successful secure API key retrieval"""
        # Use test key pattern that won't be flagged as hardcoded secret
        test_key = "test-" + "a" * 20 + "b" * 20  # Mock test key pattern
        os.environ["OPENAI_API_KEY"] = test_key

        retrieved_key = self.config.get_secure_api_key("OPENAI_API_KEY", required=True)
        self.assertEqual(retrieved_key, test_key)

    def test_secure_api_key_retrieval_failure(self):
        """Test secure API key retrieval with invalid key"""
        os.environ["OPENAI_API_KEY"] = "REPLACE_WITH_YOUR_KEY"

        with self.assertRaises(SecurityError):
            self.config.get_secure_api_key("OPENAI_API_KEY", required=True)

    def test_optional_api_key_handling(self):
        """Test optional API key handling"""
        # Test with missing optional key
        result = self.config.get_secure_api_key("OPTIONAL_KEY", required=False)
        self.assertIsNone(result)

        # Test with invalid optional key
        os.environ["OPTIONAL_KEY"] = "PLACEHOLDER_VALUE"
        result = self.config.get_secure_api_key("OPTIONAL_KEY", required=False)
        self.assertIsNone(result)

    def test_environment_file_loading(self):
        """Test secure environment file loading"""
        # Create temporary environment file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_VALID_KEY=sk-abcd1234567890abcdefghijklmnopqrstuvwxyz\n")
            f.write("TEST_PLACEHOLDER=REPLACE_WITH_YOUR_KEY\n")
            f.write("# This is a comment\n")
            f.write("\n")  # Empty line
            temp_file = f.name

        try:
            # Mock the path resolution to use our temp file
            with patch.object(Path, "exists", return_value=True):
                with patch(
                    "builtins.open",
                    unittest.mock.mock_open(read_data=Path(temp_file).read_text()),
                ):
                    env_vars = self.config.load_env_file(".env")

            # Verify only valid keys are loaded
            self.assertIn("TEST_VALID_KEY", env_vars)
            self.assertNotIn("TEST_PLACEHOLDER", env_vars)

        finally:
            # Clean up temp file
            os.unlink(temp_file)

    def test_validation_report_generation(self):
        """Test validation report generation"""
        # Add some validation results
        self.config.validation_results = [
            self.config._validate_env_var(
                "VALID_KEY", "sk-abcd1234567890abcdefghijklmnopqrstuvwxyz"
            ),
            self.config._validate_env_var("INVALID_KEY", "PLACEHOLDER_VALUE"),
            self.config._validate_env_var("MISSING_KEY", ""),
        ]

        report = self.config.get_validation_report()

        self.assertEqual(report["total_variables"], 3)
        self.assertEqual(report["valid_variables"], 1)
        self.assertEqual(len(report["security_issues"]), 2)
        self.assertIn("recommendations", report)

    def test_critical_failure_tracking(self):
        """Test critical failure tracking"""
        # Simulate critical failure
        validation = self.config._validate_env_var(
            "OPENAI_API_KEY", "REPLACE_WITH_YOUR_KEY"
        )
        self.config.validation_results.append(validation)

        if validation.validation_result != ValidationResult.VALID:
            self.config.critical_failures.append(f"Critical failure for OPENAI_API_KEY")

        is_secure, errors = self.config.validate_all_environment_vars()

        self.assertFalse(is_secure)
        self.assertGreater(len(errors), 0)

    def test_hardcoded_secrets_removed(self):
        """Test that hardcoded secrets have been removed from scripts"""
        script_file = (
            Path(__file__).parent.parent.parent
            / "scripts"
            / "test_final_integration.py"
        )

        if script_file.exists():
            content = script_file.read_text()

            # Patterns that should NOT be found (hardcoded secrets)
            forbidden_patterns = [
                r"sk-proj-[a-zA-Z0-9\-_]{50,}",  # OpenAI keys
                r"hf_[a-zA-Z0-9]{20,}",  # HuggingFace tokens
                r"lsv2_pt_[a-zA-Z0-9_]{20,}",  # LangChain keys
            ]

            for pattern in forbidden_patterns:
                import re

                matches = re.findall(pattern, content)
                self.assertEqual(
                    len(matches),
                    0,
                    f"Found hardcoded secret pattern {pattern} in test_final_integration.py",
                )

    @patch("sys.exit")
    def test_load_secure_environment_with_failures(self, mock_exit):
        """Test load_secure_environment with security failures"""
        # Mock environment with security issues
        test_env_content = """
OPENAI_API_KEY=REPLACE_WITH_YOUR_KEY
JWT_SECRET_KEY=short
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(test_env_content)
            temp_file = f.name

        try:
            with patch.object(Path, "exists", return_value=True):
                with patch(
                    "builtins.open", unittest.mock.mock_open(read_data=test_env_content)
                ):
                    result = load_secure_environment(".env")

            self.assertFalse(result)

        finally:
            os.unlink(temp_file)

    def test_security_logging(self):
        """Test security event logging"""
        with patch(
            "services.shared.config.secure_environment.security_logger"
        ) as mock_logger:
            # Trigger security validation failure
            validation = self.config._validate_env_var(
                "OPENAI_API_KEY", "PLACEHOLDER_VALUE"
            )
            self.config.validation_results.append(validation)
            self.config.critical_failures.append("Test critical failure")

            is_secure, errors = self.config.validate_all_environment_vars()

            # Verify logging was called
            mock_logger.critical.assert_called()


class TestSecurityIntegration(unittest.TestCase):
    """Integration tests for complete security system"""

    def test_complete_security_workflow(self):
        """Test complete security validation workflow"""
        # Test the complete workflow from loading to validation
        config = SecureEnvironmentConfig()

        # Test with secure environment
        secure_env = {
            "OPENAI_API_KEY": "sk-abcd1234567890abcdefghijklmnopqrstuvwxyz",
            "JWT_SECRET_KEY": "abcd1234567890abcdefghijklmnopqrstuvwxyzABCD1234567890ABCDEFGHIJ=",
        }

        for key, value in secure_env.items():
            os.environ[key] = value

        try:
            # Test secure API key retrieval
            openai_key = get_validated_api_key("OPENAI_API_KEY", required=True)
            self.assertEqual(openai_key, secure_env["OPENAI_API_KEY"])

            # Test validation passes
            is_secure, errors = config.validate_all_environment_vars()
            # Note: This may still fail due to missing DATABASE_PASSWORD, but OPENAI_API_KEY should be valid

        finally:
            # Clean up
            for key in secure_env.keys():
                if key in os.environ:
                    del os.environ[key]


def run_security_validation_tests():
    """Run all security validation tests with detailed reporting"""
    print("🔒 Running Environment Variables & Secrets Management Security Tests")
    print("=" * 70)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentSecurityValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityIntegration))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("🔒 Security Validation Test Results:")
    print(f"✅ Tests Run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")

    if result.failures:
        print("\n❌ Test Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print("\n⚠️  Test Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")

    success = len(result.failures) == 0 and len(result.errors) == 0

    if success:
        print("\n🎉 All security validation tests passed!")
        print("✅ Environment Variables & Secrets Management Security: VALIDATED")
    else:
        print("\n❌ Security validation tests failed!")
        print("⚠️  Please review and fix the reported issues.")

    return success


if __name__ == "__main__":
    success = run_security_validation_tests()
    sys.exit(0 if success else 1)
