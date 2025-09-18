#!/usr/bin/env python3
"""
Admin Authentication Security Validation Script

This script validates the admin authentication implementation against security best practices
and OWASP guidelines. It performs comprehensive security checks for admin endpoints.

OWASP Top 10 Coverage:
- A01: Broken Access Control (Role-based admin access)
- A02: Cryptographic Failures (JWT token security)
- A05: Security Misconfiguration (Admin configuration)
- A07: Identification and Authentication Failures (Admin auth)
- A09: Security Logging and Monitoring Failures (Audit logging)
"""

import os
import sys
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

# Add the project root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from services.ai_orchestrator.cartrita.orchestrator.services.admin_auth import (
        AdminAuthConfig,
        AdminUser,
        admin_config,
        create_admin_token,
        initialize_default_admin,
    )
    from services.ai_orchestrator.cartrita.orchestrator.services.jwt_auth import (
        jwt_manager,
    )

    ADMIN_AUTH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Admin authentication modules not available: {e}")
    ADMIN_AUTH_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("admin_auth_validator")


class AdminAuthSecurityValidator:
    """Validates admin authentication security implementation."""

    def __init__(self):
        self.validation_results = []
        self.security_issues = []
        self.warnings = []

    def log_result(
        self, test_name: str, passed: bool, message: str, severity: str = "info"
    ):
        """Log validation result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            "test": test_name,
            "passed": passed,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.validation_results.append(result)

        if not passed:
            if severity == "critical":
                self.security_issues.append(result)
            else:
                self.warnings.append(result)

        print(f"{status} {test_name}: {message}")

    def validate_environment_configuration(self) -> bool:
        """Validate admin environment configuration."""
        print("\n🔧 Validating Environment Configuration...")
        all_passed = True

        # Check for admin users configuration
        admin_users = os.getenv("ADMIN_USERS", "")
        if admin_users:
            self.log_result(
                "admin_users_configured",
                True,
                f"Admin users configured: {len(admin_users.split(','))} users",
            )
        else:
            self.log_result(
                "admin_users_configured",
                False,
                "No admin users configured in ADMIN_USERS environment variable",
                "critical",
            )
            all_passed = False

        # Check for super admin configuration
        super_admin = os.getenv("SUPER_ADMIN_USER", "")
        if super_admin:
            self.log_result(
                "super_admin_configured", True, f"Super admin configured: {super_admin}"
            )
        else:
            self.log_result(
                "super_admin_configured",
                False,
                "No super admin configured in SUPER_ADMIN_USER",
                "warning",
            )

        # Check admin API key security
        admin_api_key = os.getenv("ADMIN_API_KEY", "")
        if admin_api_key:
            if len(admin_api_key) >= 32:
                self.log_result(
                    "admin_api_key_strength",
                    True,
                    "Admin API key meets minimum length requirements",
                )
            else:
                self.log_result(
                    "admin_api_key_strength",
                    False,
                    f"Admin API key too short ({len(admin_api_key)} chars, need ≥32)",
                    "critical",
                )
                all_passed = False
        else:
            self.log_result(
                "admin_api_key_configured",
                False,
                "No admin API key configured (relying on JWT only)",
                "info",
            )

        # Check HTTPS requirement
        require_https = os.getenv("ADMIN_REQUIRE_HTTPS", "false").lower() == "true"
        if require_https:
            self.log_result(
                "https_required", True, "HTTPS required for admin endpoints"
            )
        else:
            self.log_result(
                "https_required",
                False,
                "HTTPS not required - ensure this is intended for your environment",
                "warning",
            )

        # Check audit logging
        audit_logging = (
            os.getenv("ADMIN_AUDIT_LOGGING_ENABLED", "true").lower() == "true"
        )
        if audit_logging:
            self.log_result(
                "audit_logging_enabled", True, "Admin audit logging enabled"
            )
        else:
            self.log_result(
                "audit_logging_enabled",
                False,
                "Admin audit logging disabled - security compliance issue",
                "critical",
            )
            all_passed = False

        return all_passed

    def validate_admin_permissions(self) -> bool:
        """Validate admin permission configuration."""
        print("\n🔐 Validating Admin Permissions...")
        all_passed = True

        if not ADMIN_AUTH_AVAILABLE:
            self.log_result(
                "admin_auth_module",
                False,
                "Admin authentication module not available",
                "critical",
            )
            return False

        try:
            config = AdminAuthConfig()

            # Validate permission hierarchy
            expected_levels = ["super_admin", "admin", "operator"]
            for level in expected_levels:
                if level in config.ADMIN_PERMISSIONS:
                    self.log_result(
                        f"permission_level_{level}",
                        True,
                        f"Permission level '{level}' configured with {len(config.ADMIN_PERMISSIONS[level])} permissions",
                    )
                else:
                    self.log_result(
                        f"permission_level_{level}",
                        False,
                        f"Permission level '{level}' not configured",
                        "critical",
                    )
                    all_passed = False

            # Validate super admin has all permissions
            super_admin_perms = config.ADMIN_PERMISSIONS.get("super_admin", [])
            if "admin:*" in super_admin_perms:
                self.log_result(
                    "super_admin_wildcard", True, "Super admin has wildcard permissions"
                )
            else:
                self.log_result(
                    "super_admin_wildcard",
                    False,
                    "Super admin missing wildcard permissions",
                    "warning",
                )

            # Validate permission segregation
            admin_perms = set(config.ADMIN_PERMISSIONS.get("admin", []))
            operator_perms = set(config.ADMIN_PERMISSIONS.get("operator", []))

            if not operator_perms.issubset(admin_perms):
                # This is actually good - operator shouldn't have all admin permissions
                self.log_result(
                    "permission_segregation",
                    True,
                    "Proper permission segregation between admin levels",
                )

        except Exception as e:
            self.log_result(
                "admin_permissions_validation",
                False,
                f"Error validating admin permissions: {e}",
                "critical",
            )
            all_passed = False

        return all_passed

    def validate_jwt_integration(self) -> bool:
        """Validate JWT authentication integration."""
        print("\n🎫 Validating JWT Integration...")
        all_passed = True

        if not ADMIN_AUTH_AVAILABLE:
            return False

        try:
            # Test JWT token creation
            test_user_id = "test_admin_validation"
            test_permissions = ["admin:system_stats"]

            # This tests if jwt_manager is properly integrated
            if hasattr(jwt_manager, "create_access_token"):
                token = jwt_manager.create_access_token(test_user_id, test_permissions)
                if token:
                    self.log_result(
                        "jwt_token_creation",
                        True,
                        "JWT token creation working correctly",
                    )
                else:
                    self.log_result(
                        "jwt_token_creation",
                        False,
                        "JWT token creation returned empty token",
                        "critical",
                    )
                    all_passed = False
            else:
                self.log_result(
                    "jwt_manager_available",
                    False,
                    "JWT manager not properly configured",
                    "critical",
                )
                all_passed = False

        except Exception as e:
            self.log_result(
                "jwt_integration_test", False, f"JWT integration error: {e}", "critical"
            )
            all_passed = False

        return all_passed

    def validate_audit_logging(self) -> bool:
        """Validate admin audit logging functionality."""
        print("\n📊 Validating Audit Logging...")
        all_passed = True

        if not ADMIN_AUTH_AVAILABLE:
            return False

        try:
            config = AdminAuthConfig()

            # Create test admin user
            test_admin = AdminUser(
                user_id="audit_test_admin",
                permissions={"admin:system_stats"},
                is_admin=True,
                admin_level="admin",
            )

            # Create mock request object
            class MockRequest:
                def __init__(self):
                    self.client = MockClient()
                    self.headers = {"user-agent": "security-validator"}

            class MockClient:
                def __init__(self):
                    self.host = "127.0.0.1"

            mock_request = MockRequest()

            # Test audit logging
            initial_log_count = len(config.get_audit_logs())

            config.log_admin_access(
                test_admin,
                "security_validation_test",
                mock_request,
                success=True,
                additional_info={"validation": "test"},
            )

            new_log_count = len(config.get_audit_logs())

            if new_log_count > initial_log_count:
                self.log_result(
                    "audit_logging_functional",
                    True,
                    f"Audit logging working - {new_log_count - initial_log_count} new entries",
                )
            else:
                self.log_result(
                    "audit_logging_functional",
                    False,
                    "Audit logging not recording entries",
                    "critical",
                )
                all_passed = False

            # Test audit log retrieval
            recent_logs = config.get_audit_logs(limit=1)
            if recent_logs:
                log_entry = recent_logs[0]
                required_fields = [
                    "timestamp",
                    "user_id",
                    "action",
                    "client_ip",
                    "success",
                ]
                missing_fields = [
                    field for field in required_fields if field not in log_entry
                ]

                if not missing_fields:
                    self.log_result(
                        "audit_log_structure",
                        True,
                        "Audit log entries contain all required fields",
                    )
                else:
                    self.log_result(
                        "audit_log_structure",
                        False,
                        f"Audit log missing fields: {missing_fields}",
                        "warning",
                    )

        except Exception as e:
            self.log_result(
                "audit_logging_test",
                False,
                f"Audit logging validation error: {e}",
                "critical",
            )
            all_passed = False

        return all_passed

    def validate_access_control(self) -> bool:
        """Validate admin access control mechanisms."""
        print("\n🛡️  Validating Access Control...")
        all_passed = True

        if not ADMIN_AUTH_AVAILABLE:
            return False

        try:
            config = AdminAuthConfig()

            # Test different admin levels
            test_cases = [
                {
                    "user_id": "super_admin_test",
                    "permissions": {"admin:*", "admin:system_shutdown"},
                    "expected_level": "super_admin",
                },
                {
                    "user_id": "admin_test",
                    "permissions": {
                        "admin:reload_agents",
                        "admin:system_stats",
                        "admin:user_management",
                    },
                    "expected_level": "admin",
                },
                {
                    "user_id": "operator_test",
                    "permissions": {"admin:system_stats"},
                    "expected_level": "operator",
                },
            ]

            # Configure test admin users
            config.admin_user_ids = {case["user_id"] for case in test_cases}

            for case in test_cases:
                actual_level = config.get_admin_level(
                    case["user_id"], case["permissions"]
                )

                if actual_level == case["expected_level"]:
                    self.log_result(
                        f"access_level_{case['expected_level']}",
                        True,
                        f"Correct admin level assignment for {case['expected_level']}",
                    )
                else:
                    self.log_result(
                        f"access_level_{case['expected_level']}",
                        False,
                        f"Incorrect level for {case['user_id']}: got {actual_level}, expected {case['expected_level']}",
                        "critical",
                    )
                    all_passed = False

            # Test permission validation
            super_admin = AdminUser(
                user_id="super_admin_test",
                permissions={"admin:*"},
                is_admin=True,
                admin_level="super_admin",
            )

            # Super admin should have access to everything
            test_permissions = [
                "admin:reload_agents",
                "admin:system_stats",
                "admin:user_management",
            ]
            for perm in test_permissions:
                has_access = config.validate_admin_permission(super_admin, perm)
                if has_access:
                    self.log_result(
                        f"super_admin_access_{perm.split(':')[1]}",
                        True,
                        f"Super admin has access to {perm}",
                    )
                else:
                    self.log_result(
                        f"super_admin_access_{perm.split(':')[1]}",
                        False,
                        f"Super admin denied access to {perm}",
                        "critical",
                    )
                    all_passed = False

            # Test operator restrictions
            operator = AdminUser(
                user_id="operator_test",
                permissions={"admin:system_stats"},
                is_admin=True,
                admin_level="operator",
            )

            # Operator should NOT have reload access
            has_reload = config.validate_admin_permission(
                operator, "admin:reload_agents"
            )
            if not has_reload:
                self.log_result(
                    "operator_restriction_reload",
                    True,
                    "Operator correctly denied reload access",
                )
            else:
                self.log_result(
                    "operator_restriction_reload",
                    False,
                    "Operator incorrectly granted reload access",
                    "critical",
                )
                all_passed = False

        except Exception as e:
            self.log_result(
                "access_control_test",
                False,
                f"Access control validation error: {e}",
                "critical",
            )
            all_passed = False

        return all_passed

    def validate_security_hardening(self) -> bool:
        """Validate security hardening measures."""
        print("\n🔒 Validating Security Hardening...")
        all_passed = True

        # Check for development/debug settings in production
        debug_indicators = [
            ("DEBUG", "Debug mode"),
            ("DEVELOPMENT", "Development mode"),
            ("TEST_MODE", "Test mode"),
        ]

        for env_var, description in debug_indicators:
            if os.getenv(env_var, "").lower() in ["true", "1", "yes"]:
                self.log_result(
                    f"production_ready_{env_var.lower()}",
                    False,
                    f"{description} enabled - not suitable for production",
                    "warning",
                )

        # Check for secure defaults
        secure_defaults = [
            ("ADMIN_REQUIRE_HTTPS", "true", "HTTPS requirement"),
            ("ADMIN_AUDIT_LOGGING_ENABLED", "true", "Audit logging"),
            ("ADMIN_RATE_LIMIT_ENABLED", "true", "Rate limiting"),
        ]

        for env_var, expected, description in secure_defaults:
            actual = os.getenv(env_var, "false").lower()
            if actual == expected.lower():
                self.log_result(
                    f"secure_default_{env_var.lower()}",
                    True,
                    f"{description} properly configured",
                )
            else:
                severity = "warning" if env_var == "ADMIN_REQUIRE_HTTPS" else "critical"
                self.log_result(
                    f"secure_default_{env_var.lower()}",
                    False,
                    f"{description} not enabled - security risk",
                    severity,
                )
                if severity == "critical":
                    all_passed = False

        # Check for IP restrictions
        allowed_ips = os.getenv("ADMIN_ALLOWED_IPS", "")
        if allowed_ips and allowed_ips.strip() != "0.0.0.0/0":
            self.log_result(
                "ip_restrictions",
                True,
                f"Admin IP restrictions configured: {allowed_ips}",
            )
        else:
            self.log_result(
                "ip_restrictions",
                False,
                "No IP restrictions for admin access - consider limiting access",
                "warning",
            )

        return all_passed

    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation summary."""
        total_tests = len(self.validation_results)
        passed_tests = len([r for r in self.validation_results if r["passed"]])
        failed_tests = total_tests - passed_tests

        critical_issues = len(self.security_issues)
        warnings = len(self.warnings)

        score = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "security_score": round(score, 1),
                "critical_issues": critical_issues,
                "warnings": warnings,
            },
            "validation_results": self.validation_results,
            "security_issues": self.security_issues,
            "warnings": self.warnings,
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on validation results."""
        recommendations = []

        if self.security_issues:
            recommendations.append("🚨 Address all critical security issues immediately")

        if not os.getenv("ADMIN_USERS"):
            recommendations.append("📝 Configure ADMIN_USERS environment variable")

        if not os.getenv("ADMIN_API_KEY") or len(os.getenv("ADMIN_API_KEY", "")) < 32:
            recommendations.append("🔑 Set strong ADMIN_API_KEY (≥32 characters)")

        if os.getenv("ADMIN_REQUIRE_HTTPS", "false").lower() != "true":
            recommendations.append("🔒 Enable HTTPS requirement for production")

        if not os.getenv("ADMIN_ALLOWED_IPS"):
            recommendations.append("🌐 Configure IP restrictions for admin access")

        recommendations.extend(
            [
                "📊 Regularly review admin audit logs",
                "🔄 Rotate admin credentials regularly",
                "👥 Use principle of least privilege for admin roles",
                "🛡️  Consider implementing MFA for admin accounts",
            ]
        )

        return recommendations

    def run_full_validation(self) -> bool:
        """Run complete admin authentication security validation."""
        print("🔐 ADMIN AUTHENTICATION SECURITY VALIDATION")
        print("=" * 60)

        start_time = time.time()

        validation_steps = [
            self.validate_environment_configuration,
            self.validate_admin_permissions,
            self.validate_jwt_integration,
            self.validate_audit_logging,
            self.validate_access_control,
            self.validate_security_hardening,
        ]

        all_passed = True
        for step in validation_steps:
            try:
                step_result = step()
                all_passed = all_passed and step_result
            except Exception as e:
                self.log_result(
                    f"validation_step_{step.__name__}",
                    False,
                    f"Validation step failed: {e}",
                    "critical",
                )
                all_passed = False

        end_time = time.time()
        duration = round(end_time - start_time, 2)

        # Generate and display summary
        summary = self.generate_summary_report()

        print("\n" + "=" * 60)
        print("📋 VALIDATION SUMMARY")
        print("=" * 60)

        print(f"⏱️  Duration: {duration}s")
        print(
            f"📊 Tests: {summary['summary']['passed_tests']}/{summary['summary']['total_tests']} passed"
        )
        print(f"🎯 Security Score: {summary['summary']['security_score']}%")
        print(f"🚨 Critical Issues: {summary['summary']['critical_issues']}")
        print(f"⚠️  Warnings: {summary['summary']['warnings']}")

        if summary["summary"]["security_score"] >= 90:
            print("✅ EXCELLENT: Admin authentication security is well-implemented")
        elif summary["summary"]["security_score"] >= 70:
            print(
                "⚡ GOOD: Admin authentication security is adequate with room for improvement"
            )
        elif summary["summary"]["security_score"] >= 50:
            print("⚠️  NEEDS IMPROVEMENT: Admin authentication has security gaps")
        else:
            print("🚨 CRITICAL: Admin authentication requires immediate attention")

        if summary["recommendations"]:
            print("\n🎯 RECOMMENDATIONS:")
            for rec in summary["recommendations"]:
                print(f"  • {rec}")

        print("\n" + "=" * 60)

        return all_passed


def main():
    """Main validation entry point."""
    validator = AdminAuthSecurityValidator()

    try:
        success = validator.run_full_validation()

        # Save detailed results
        results_file = "admin_auth_validation_results.json"
        try:
            import json

            with open(results_file, "w") as f:
                json.dump(validator.generate_summary_report(), f, indent=2, default=str)
            print(f"\n📄 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Could not save results file: {e}")

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⏹️  Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n🚨 Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
