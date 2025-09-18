"""
Security Configuration Service for Cartrita AI OS
Enforces secure configurations across all services
"""

import json
import os
import ssl
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import structlog
from pydantic import BaseModel, Field, validator

logger = structlog.get_logger(__name__)


@dataclass
class SecurityPolicy:
    """Security policy configuration"""

    name: str
    enabled: bool = True
    severity: str = "HIGH"
    auto_fix: bool = True
    description: str = ""


class SecureConfiguration(BaseModel):
    """Secure configuration settings for services"""

    # HTTPS/TLS Configuration
    use_https: bool = Field(
        default=True, description="Enforce HTTPS for all connections"
    )
    tls_version: str = Field(default="TLSv1.3", description="Minimum TLS version")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    ssl_cert_path: Optional[str] = Field(
        default=None, description="Path to SSL certificate"
    )
    ssl_key_path: Optional[str] = Field(
        default=None, description="Path to SSL private key"
    )

    # CORS Configuration
    cors_enabled: bool = Field(default=True, description="Enable CORS")
    cors_origins: List[str] = Field(
        default_factory=lambda: ["https://localhost:3000"],
        description="Allowed CORS origins",
    )
    cors_credentials: bool = Field(
        default=True, description="Allow credentials in CORS"
    )
    cors_methods: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed CORS methods",
    )
    cors_headers: List[str] = Field(
        default_factory=lambda: ["Content-Type", "Authorization", "X-Request-ID"],
        description="Allowed CORS headers",
    )

    # Security Headers
    security_headers: Dict[str, str] = Field(
        default_factory=lambda: {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        },
        description="Security headers to add to responses",
    )

    # Rate Limiting
    rate_limiting_enabled: bool = Field(
        default=True, description="Enable rate limiting"
    )
    rate_limit_requests: int = Field(default=100, description="Max requests per window")
    rate_limit_window: int = Field(
        default=60, description="Rate limit window in seconds"
    )
    rate_limit_by_ip: bool = Field(default=True, description="Rate limit by IP address")

    # Authentication & Authorization
    auth_enabled: bool = Field(default=True, description="Enable authentication")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiry_minutes: int = Field(
        default=60, description="JWT token expiry in minutes"
    )
    session_timeout_minutes: int = Field(
        default=30, description="Session timeout in minutes"
    )
    password_min_length: int = Field(default=12, description="Minimum password length")
    password_require_special: bool = Field(
        default=True, description="Require special characters"
    )
    password_require_numbers: bool = Field(default=True, description="Require numbers")
    password_require_uppercase: bool = Field(
        default=True, description="Require uppercase"
    )
    mfa_enabled: bool = Field(
        default=False, description="Enable multi-factor authentication"
    )

    # Input Validation
    input_validation_enabled: bool = Field(
        default=True, description="Enable input validation"
    )
    max_request_size: int = Field(
        default=10485760, description="Max request size in bytes (10MB)"
    )
    max_upload_size: int = Field(
        default=104857600, description="Max upload size in bytes (100MB)"
    )
    allowed_file_extensions: Set[str] = Field(
        default_factory=lambda: {
            ".pdf",
            ".txt",
            ".json",
            ".csv",
            ".png",
            ".jpg",
            ".jpeg",
        },
        description="Allowed file upload extensions",
    )
    sql_injection_protection: bool = Field(
        default=True, description="Enable SQL injection protection"
    )
    xss_protection: bool = Field(default=True, description="Enable XSS protection")

    # Database Security
    db_ssl_mode: str = Field(default="require", description="Database SSL mode")
    db_connection_timeout: int = Field(
        default=30, description="Database connection timeout"
    )
    db_pool_size: int = Field(default=20, description="Database connection pool size")
    db_encrypted_connections: bool = Field(
        default=True, description="Use encrypted DB connections"
    )

    # Logging & Monitoring
    log_sensitive_data: bool = Field(default=False, description="Log sensitive data")
    log_rotation_enabled: bool = Field(default=True, description="Enable log rotation")
    log_retention_days: int = Field(default=30, description="Log retention in days")
    audit_logging_enabled: bool = Field(
        default=True, description="Enable audit logging"
    )
    performance_monitoring: bool = Field(
        default=True, description="Enable performance monitoring"
    )

    # Container Security
    run_as_non_root: bool = Field(
        default=True, description="Run containers as non-root"
    )
    read_only_filesystem: bool = Field(
        default=False, description="Use read-only filesystem"
    )
    drop_capabilities: bool = Field(
        default=True, description="Drop unnecessary capabilities"
    )
    security_opt_no_new_privileges: bool = Field(
        default=True, description="No new privileges flag"
    )

    # Network Security
    network_segmentation: bool = Field(
        default=True, description="Enable network segmentation"
    )
    internal_network_only: List[str] = Field(
        default_factory=lambda: ["redis", "postgres"],
        description="Services only accessible internally",
    )

    @validator("cors_origins")
    def validate_cors_origins(cls, v):
        """Ensure no wildcard CORS origins in production"""
        if "*" in v and os.getenv("ENV", "development") == "production":
            raise ValueError("Wildcard CORS origin not allowed in production")
        return v

    @validator("tls_version")
    def validate_tls_version(cls, v):
        """Ensure minimum TLS version"""
        allowed_versions = ["TLSv1.2", "TLSv1.3"]
        if v not in allowed_versions:
            raise ValueError(f"TLS version must be one of {allowed_versions}")
        return v


class SecurityConfigManager:
    """Manages security configuration and enforcement"""

    SECURITY_POLICIES = [
        SecurityPolicy(
            name="enforce_https",
            description="All connections must use HTTPS",
            severity="HIGH",
        ),
        SecurityPolicy(
            name="validate_ssl_certs",
            description="SSL certificate validation must be enabled",
            severity="HIGH",
        ),
        SecurityPolicy(
            name="secure_cors",
            description="CORS must be properly configured without wildcards",
            severity="HIGH",
        ),
        SecurityPolicy(
            name="rate_limiting",
            description="Rate limiting must be enabled",
            severity="MEDIUM",
        ),
        SecurityPolicy(
            name="security_headers",
            description="Security headers must be present",
            severity="HIGH",
        ),
        SecurityPolicy(
            name="input_validation",
            description="Input validation must be enabled",
            severity="HIGH",
        ),
        SecurityPolicy(
            name="database_encryption",
            description="Database connections must be encrypted",
            severity="HIGH",
        ),
        SecurityPolicy(
            name="container_security",
            description="Containers must follow security best practices",
            severity="MEDIUM",
        ),
        SecurityPolicy(
            name="authentication",
            description="Authentication must be enabled",
            severity="HIGH",
        ),
        SecurityPolicy(
            name="audit_logging",
            description="Audit logging must be enabled",
            severity="MEDIUM",
        ),
    ]

    def __init__(self, service_name: str = "ai-orchestrator"):
        """Initialize the security configuration manager"""
        self.service_name = service_name
        self.config = self._load_config()
        self.violations: List[Dict[str, Any]] = []

        logger.info("Security configuration manager initialized", service=service_name)

    def _load_config(self) -> SecureConfiguration:
        """Load security configuration from environment and files"""
        config_data = {}

        # Load from environment variables
        env_mappings = {
            "CARTRITA_USE_HTTPS": "use_https",
            "CARTRITA_VERIFY_SSL": "verify_ssl",
            "CARTRITA_CORS_ORIGINS": "cors_origins",
            "CARTRITA_RATE_LIMIT": "rate_limiting_enabled",
            "CARTRITA_AUTH_ENABLED": "auth_enabled",
            "CARTRITA_DB_SSL_MODE": "db_ssl_mode",
        }

        for env_key, config_key in env_mappings.items():
            value = os.getenv(env_key)
            if value:
                if config_key == "cors_origins":
                    config_data[config_key] = (
                        json.loads(value) if value.startswith("[") else [value]
                    )
                elif value.lower() in ["true", "false"]:
                    config_data[config_key] = value.lower() == "true"
                else:
                    config_data[config_key] = value

        # Load from config file if exists
        config_file = Path("config/security.json")
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    file_config = json.load(f)
                    config_data.update(file_config)
            except Exception as e:
                logger.error("Failed to load security config file", error=str(e))

        return SecureConfiguration(**config_data)

    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the current configuration against security policies

        Returns:
            Validation results with violations and fixes
        """
        results: Dict[str, Any] = {
            "valid": True,
            "violations": [],
            "fixes_applied": [],
            "warnings": [],
        }

        # Check each security policy
        for policy in self.SECURITY_POLICIES:
            if not policy.enabled:
                continue

            violation = self._check_policy(policy)
            if violation:
                results["violations"].append(violation)
                results["valid"] = False

                if policy.auto_fix:
                    fix = self._apply_fix(policy)
                    if fix:
                        results["fixes_applied"].append(fix)

        # Log results
        logger.info(
            "Security configuration validation completed",
            valid=results["valid"],
            violations=len(results["violations"]),
            fixes=len(results["fixes_applied"]),
        )

        return results

    def _check_policy(self, policy: SecurityPolicy) -> Optional[Dict[str, Any]]:
        """Check a specific security policy"""
        violation = None

        if policy.name == "enforce_https" and not self.config.use_https:
            violation = {
                "policy": policy.name,
                "severity": policy.severity,
                "message": "HTTPS is not enforced",
                "current_value": False,
                "expected_value": True,
            }
        elif policy.name == "validate_ssl_certs" and not self.config.verify_ssl:
            violation = {
                "policy": policy.name,
                "severity": policy.severity,
                "message": "SSL certificate validation is disabled",
                "current_value": False,
                "expected_value": True,
            }
        elif policy.name == "secure_cors" and "*" in self.config.cors_origins:
            violation = {
                "policy": policy.name,
                "severity": policy.severity,
                "message": "CORS allows wildcard origin",
                "current_value": self.config.cors_origins,
                "expected_value": "Specific origins only",
            }
        elif policy.name == "rate_limiting" and not self.config.rate_limiting_enabled:
            violation = {
                "policy": policy.name,
                "severity": policy.severity,
                "message": "Rate limiting is disabled",
                "current_value": False,
                "expected_value": True,
            }
        elif (
            policy.name == "input_validation"
            and not self.config.input_validation_enabled
        ):
            violation = {
                "policy": policy.name,
                "severity": policy.severity,
                "message": "Input validation is disabled",
                "current_value": False,
                "expected_value": True,
            }
        elif (
            policy.name == "database_encryption"
            and self.config.db_ssl_mode == "disable"
        ):
            violation = {
                "policy": policy.name,
                "severity": policy.severity,
                "message": "Database connections are not encrypted",
                "current_value": self.config.db_ssl_mode,
                "expected_value": "require",
            }
        elif policy.name == "authentication" and not self.config.auth_enabled:
            violation = {
                "policy": policy.name,
                "severity": policy.severity,
                "message": "Authentication is disabled",
                "current_value": False,
                "expected_value": True,
            }
        elif policy.name == "audit_logging" and not self.config.audit_logging_enabled:
            violation = {
                "policy": policy.name,
                "severity": policy.severity,
                "message": "Audit logging is disabled",
                "current_value": False,
                "expected_value": True,
            }

        return violation

    def _apply_fix(self, policy: SecurityPolicy) -> Optional[Dict[str, Any]]:
        """Apply automatic fix for a policy violation"""
        fix = None

        if policy.name == "enforce_https":
            self.config.use_https = True
            fix = {"policy": policy.name, "action": "Enabled HTTPS enforcement"}
        elif policy.name == "validate_ssl_certs":
            self.config.verify_ssl = True
            fix = {
                "policy": policy.name,
                "action": "Enabled SSL certificate validation",
            }
        elif policy.name == "secure_cors":
            if "*" in self.config.cors_origins:
                self.config.cors_origins = ["https://localhost:3000"]
                fix = {"policy": policy.name, "action": "Removed wildcard CORS origin"}
        elif policy.name == "rate_limiting":
            self.config.rate_limiting_enabled = True
            fix = {"policy": policy.name, "action": "Enabled rate limiting"}
        elif policy.name == "input_validation":
            self.config.input_validation_enabled = True
            fix = {"policy": policy.name, "action": "Enabled input validation"}
        elif policy.name == "database_encryption":
            self.config.db_ssl_mode = "require"
            fix = {"policy": policy.name, "action": "Enabled database encryption"}
        elif policy.name == "authentication":
            self.config.auth_enabled = True
            fix = {"policy": policy.name, "action": "Enabled authentication"}
        elif policy.name == "audit_logging":
            self.config.audit_logging_enabled = True
            fix = {"policy": policy.name, "action": "Enabled audit logging"}

        if fix:
            logger.info("Security fix applied", fix=fix)

        return fix

    def get_ssl_context(self) -> ssl.SSLContext:
        """
        Get a secure SSL context for connections

        Returns:
            Configured SSL context
        """
        context = ssl.create_default_context()

        # Set minimum TLS version
        if self.config.tls_version == "TLSv1.3":
            context.minimum_version = ssl.TLSVersion.TLSv1_3
        else:
            context.minimum_version = ssl.TLSVersion.TLSv1_2

        # Set verification mode
        if self.config.verify_ssl:
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
        else:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        # Load certificates if provided
        if self.config.ssl_cert_path and self.config.ssl_key_path:
            context.load_cert_chain(self.config.ssl_cert_path, self.config.ssl_key_path)

        return context

    def get_cors_config(self) -> Dict[str, Any]:
        """
        Get CORS configuration for middleware

        Returns:
            CORS configuration dictionary
        """
        return {
            "allow_origins": self.config.cors_origins,
            "allow_credentials": self.config.cors_credentials,
            "allow_methods": self.config.cors_methods,
            "allow_headers": self.config.cors_headers,
        }

    def get_security_headers(self) -> Dict[str, str]:
        """
        Get security headers for responses

        Returns:
            Security headers dictionary
        """
        return self.config.security_headers

    def export_config(self, safe_mode: bool = True) -> Dict[str, Any]:
        """
        Export configuration for reporting

        Args:
            safe_mode: Exclude sensitive values

        Returns:
            Configuration dictionary
        """
        config_dict = self.config.dict()

        if safe_mode:
            # Remove sensitive paths
            config_dict.pop("ssl_cert_path", None)
            config_dict.pop("ssl_key_path", None)

        return config_dict


# Singleton instance
_security_config_manager: Optional[SecurityConfigManager] = None


def get_security_config(service_name: str = "ai-orchestrator") -> SecurityConfigManager:
    """
    Get or create the security configuration manager

    Args:
        service_name: Name of the service

    Returns:
        SecurityConfigManager instance
    """
    global _security_config_manager

    if _security_config_manager is None:
        _security_config_manager = SecurityConfigManager(service_name)

    return _security_config_manager


def validate_security() -> bool:
    """
    Validate security configuration

    Returns:
        True if configuration is valid
    """
    manager = get_security_config()
    results = manager.validate_configuration()
    return results["valid"]
