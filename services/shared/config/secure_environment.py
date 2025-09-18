"""
Secure Environment Configuration with Security Validation
=========================================================

Enhanced environment configuration with security validation, secret format checking,
and comprehensive error handling. Addresses OWASP A07 (Authentication Failures)
and A02 (Cryptographic Failures).

Security Features:
- API key format validation
- Placeholder detection and rejection
- Minimum security requirements enforcement
- Secure fallback handling
- Audit logging for security events
"""

import os
import re
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Configure security logging
security_logger = logging.getLogger("cartrita.security")


class ValidationResult(Enum):
    """Environment variable validation results"""

    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    PLACEHOLDER_DETECTED = "placeholder_detected"
    INSUFFICIENT_ENTROPY = "insufficient_entropy"
    MISSING = "missing"


@dataclass
class SecurityValidation:
    """Security validation result for environment variables"""

    key: str
    value_present: bool
    validation_result: ValidationResult
    error_message: Optional[str] = None
    security_level: str = "unknown"


class SecureEnvironmentConfig:
    """Secure environment configuration with validation"""

    # Security patterns for different API key types
    API_KEY_PATTERNS = {
        "OPENAI_API_KEY": {
            "pattern": r"^sk-[a-zA-Z0-9]{20,}$",
            "min_length": 45,
            "description": "OpenAI API key (starts with sk-)",
        },
        "ANTHROPIC_API_KEY": {
            "pattern": r"^sk-ant-[a-zA-Z0-9\-_]{20,}$",
            "min_length": 30,
            "description": "Anthropic API key (starts with sk-ant-)",
        },
        "HUGGINGFACE_TOKEN": {
            "pattern": r"^hf_[a-zA-Z0-9]{20,}$",
            "min_length": 30,
            "description": "HuggingFace token (starts with hf_)",
        },
        "DEEPGRAM_API_KEY": {
            "pattern": r"^[a-f0-9]{32}$|^[a-zA-Z0-9]{40,}$",
            "min_length": 32,
            "description": "Deepgram API key",
        },
        "TAVILY_API_KEY": {
            "pattern": r"^tvly-[a-zA-Z0-9]{20,}$",
            "min_length": 25,
            "description": "Tavily API key (starts with tvly-)",
        },
        "GITHUB_TOKEN": {
            "pattern": r"^gh[ps]_[a-zA-Z0-9]{36,}$|^github_pat_[a-zA-Z0-9_]{20,}$",
            "min_length": 40,
            "description": "GitHub token (ghs_, ghp_, or github_pat_)",
        },
        "LANGCHAIN_API_KEY": {
            "pattern": r"^lsv2_[a-zA-Z0-9_]{20,}$",
            "min_length": 25,
            "description": "LangChain API key (starts with lsv2_)",
        },
        "JWT_SECRET_KEY": {
            "pattern": r"^[a-zA-Z0-9+/=]{64,}$",
            "min_length": 64,
            "description": "JWT secret (minimum 64 characters)",
        },
    }

    # Placeholder patterns that should be rejected
    PLACEHOLDER_PATTERNS = [
        r"REPLACE_WITH_",
        r"YOUR_.*_HERE",
        r"your_.*_key",
        r"sk-proj-your_",
        r"lsv2_pt_your_",
        r"hf_your_",
        r"INSERT_YOUR_",
        r"CHANGE_THIS_",
        r"PLACEHOLDER_",
        r"EXAMPLE_",
        r"TEST_KEY_",
        r"DEMO_",
    ]

    def __init__(self):
        self.validation_results: List[SecurityValidation] = []
        self.critical_failures: List[str] = []

    def load_env_file(self, env_file: str = ".env") -> Dict[str, str]:
        """
        Securely load environment variables from file with validation.

        Args:
            env_file: Path to environment file

        Returns:
            Dictionary of loaded and validated environment variables
        """
        env_vars = {}

        # Try multiple possible paths
        possible_paths = [
            Path.cwd() / env_file,
            Path(__file__).parent.parent.parent / env_file,
            Path("/home/robbie/cartrita-ai-os") / env_file,
        ]

        env_path = None
        for path in possible_paths:
            if path.exists():
                env_path = path
                break

        if not env_path:
            security_logger.warning(
                f"Environment file {env_file} not found in any expected location"
            )
            return env_vars

        try:
            with open(env_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip("\"'")  # Remove quotes

                        # Validate the environment variable
                        validation = self._validate_env_var(key, value)
                        self.validation_results.append(validation)

                        if validation.validation_result == ValidationResult.VALID:
                            if not os.getenv(key):  # Don't override existing env vars
                                os.environ[key] = value
                            env_vars[key] = value
                        else:
                            if key in self.API_KEY_PATTERNS:
                                self.critical_failures.append(
                                    f"Critical security failure for {key}: {validation.error_message}"
                                )

        except Exception as e:
            security_logger.error(f"Failed to load environment file {env_path}: {e}")

        return env_vars

    def _validate_env_var(self, key: str, value: str) -> SecurityValidation:
        """
        Validate an individual environment variable for security compliance.

        Args:
            key: Environment variable key
            value: Environment variable value

        Returns:
            SecurityValidation result
        """
        if not value:
            return SecurityValidation(
                key=key,
                value_present=False,
                validation_result=ValidationResult.MISSING,
                error_message="Environment variable is empty or missing",
            )

        # Check for placeholder patterns
        for pattern in self.PLACEHOLDER_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return SecurityValidation(
                    key=key,
                    value_present=True,
                    validation_result=ValidationResult.PLACEHOLDER_DETECTED,
                    error_message=f"Placeholder pattern detected: {pattern}",
                    security_level="critical",
                )

        # Validate API key formats
        if key in self.API_KEY_PATTERNS:
            pattern_info = self.API_KEY_PATTERNS[key]

            # Check minimum length
            if len(value) < pattern_info["min_length"]:
                return SecurityValidation(
                    key=key,
                    value_present=True,
                    validation_result=ValidationResult.INSUFFICIENT_ENTROPY,
                    error_message=f"Value too short (min {pattern_info['min_length']} chars)",
                    security_level="high",
                )

            # Check pattern match
            if not re.match(pattern_info["pattern"], value):
                return SecurityValidation(
                    key=key,
                    value_present=True,
                    validation_result=ValidationResult.INVALID_FORMAT,
                    error_message=f"Invalid format for {pattern_info['description']}",
                    security_level="high",
                )

        return SecurityValidation(
            key=key,
            value_present=True,
            validation_result=ValidationResult.VALID,
            security_level="low",
        )

    def get_secure_api_key(self, key_name: str, required: bool = True) -> Optional[str]:
        """
        Get API key with security validation.

        Args:
            key_name: API key environment variable name
            required: Whether the key is required (will raise error if missing)

        Returns:
            Validated API key or None if optional and missing

        Raises:
            SecurityError: If required key is missing or invalid
        """
        value = os.getenv(key_name)

        if not value:
            if required:
                raise SecurityError(
                    f"Required API key {key_name} is missing from environment"
                )
            return None

        validation = self._validate_env_var(key_name, value)

        if validation.validation_result != ValidationResult.VALID:
            if required:
                raise SecurityError(
                    f"Invalid API key {key_name}: {validation.error_message}"
                )
            security_logger.warning(
                f"Optional API key {key_name} is invalid: {validation.error_message}"
            )
            return None

        return value

    def validate_all_environment_vars(self) -> Tuple[bool, List[str]]:
        """
        Validate all environment variables and return security status.

        Returns:
            Tuple of (is_secure, list_of_errors)
        """
        errors = []

        # Check critical API keys
        critical_keys = ["OPENAI_API_KEY", "JWT_SECRET_KEY", "DATABASE_PASSWORD"]

        for key in critical_keys:
            try:
                self.get_secure_api_key(key, required=True)
            except SecurityError as e:
                errors.append(str(e))

        # Add any critical failures from loading
        errors.extend(self.critical_failures)

        is_secure = len(errors) == 0

        if not is_secure:
            security_logger.critical(
                f"Environment security validation failed: {len(errors)} critical issues"
            )
            for error in errors:
                security_logger.critical(error)

        return is_secure, errors

    def get_validation_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report.

        Returns:
            Dictionary containing validation report
        """
        report = {
            "total_variables": len(self.validation_results),
            "valid_variables": len(
                [
                    r
                    for r in self.validation_results
                    if r.validation_result == ValidationResult.VALID
                ]
            ),
            "critical_failures": len(self.critical_failures),
            "security_issues": [],
            "recommendations": [],
        }

        for result in self.validation_results:
            if result.validation_result != ValidationResult.VALID:
                report["security_issues"].append(
                    {
                        "key": result.key,
                        "issue": result.validation_result.value,
                        "message": result.error_message,
                        "level": result.security_level,
                    }
                )

        # Generate recommendations
        if report["critical_failures"] > 0:
            report["recommendations"].append(
                "Immediately replace placeholder values with actual credentials"
            )

        if report["security_issues"]:
            report["recommendations"].append(
                "Review and fix all security issues before production deployment"
            )

        return report


class SecurityError(Exception):
    """Exception raised for environment security violations"""

    pass


# Global secure environment instance
secure_env = SecureEnvironmentConfig()


def load_secure_environment(env_file: str = ".env") -> bool:
    """
    Load and validate environment with security checks.

    Args:
        env_file: Environment file to load

    Returns:
        True if environment is secure, False otherwise
    """
    secure_env.load_env_file(env_file)
    is_secure, errors = secure_env.validate_all_environment_vars()

    if not is_secure:
        print("🚨 CRITICAL SECURITY ISSUES DETECTED:")
        for error in errors:
            print(f"   ❌ {error}")
        print("\n⚠️  Application startup blocked due to security violations.")
        print("📋 Please fix these issues before continuing.")

    return is_secure


# Secure helper functions with validation
def get_validated_api_key(key_name: str, required: bool = True) -> Optional[str]:
    """Get validated API key"""
    return secure_env.get_secure_api_key(key_name, required)


def get_database_url() -> str:
    """Get validated database URL"""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SecurityError("DATABASE_URL is required but not set")
    return url


def get_jwt_secret() -> str:
    """Get validated JWT secret"""
    return get_validated_api_key("JWT_SECRET_KEY", required=True)


# Export main functions
__all__ = [
    "SecureEnvironmentConfig",
    "load_secure_environment",
    "get_validated_api_key",
    "get_database_url",
    "get_jwt_secret",
    "SecurityError",
]
