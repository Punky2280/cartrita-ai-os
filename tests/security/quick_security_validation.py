#!/usr/bin/env python3
"""
Quick Security Validation Test
=============================

Simple test to verify the core security features are working:
1. Hardcoded secrets have been removed
2. Placeholder detection works
3. Environment variable validation works
"""

import os
import sys
import re
from pathlib import Path


def test_hardcoded_secrets_removed():
    """Test that hardcoded secrets have been removed from scripts"""
    print("🔍 Testing hardcoded secrets removal...")

    # Get the correct path to the script file
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent
    script_file = project_root / "scripts" / "test_final_integration.py"

    if not script_file.exists():
        print("   ⚠️  Script file not found")
        return False

    content = script_file.read_text()

    # Patterns that should NOT be found (actual hardcoded secrets)
    # Using partial patterns to avoid triggering security scanners
    forbidden_patterns = [
        r"sk-proj-gpz",  # Pattern fragment for leaked key detection
        r"hf_oLSnXk",  # Pattern fragment for leaked token detection
        r"lsv2_pt_5a",  # Pattern fragment for leaked key detection
    ]

    secrets_found = []
    for pattern in forbidden_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            secrets_found.extend(matches)

    if secrets_found:
        print(f"   ❌ Found {len(secrets_found)} hardcoded secrets!")
        for secret in secrets_found:
            print(f"      - {secret[:10]}...")
        return False
    else:
        print("   ✅ No hardcoded secrets found")
        return True


def test_secure_environment_exists():
    """Test that secure environment module exists"""
    print("🔍 Testing secure environment module...")

    # Get the correct path to the secure environment file
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent
    secure_env_file = (
        project_root / "services" / "shared" / "config" / "secure_environment.py"
    )

    if not secure_env_file.exists():
        print("   ❌ Secure environment module not found")
        return False

    content = secure_env_file.read_text()

    # Check for key security features
    required_features = [
        "API_KEY_PATTERNS",
        "PLACEHOLDER_PATTERNS",
        "SecurityError",
        "ValidationResult",
        "get_secure_api_key",
    ]

    missing_features = []
    for feature in required_features:
        if feature not in content:
            missing_features.append(feature)

    if missing_features:
        print(f"   ❌ Missing security features: {missing_features}")
        return False
    else:
        print("   ✅ Secure environment module has all required features")
        return True


def test_env_templates_exist():
    """Test that secure environment templates exist"""
    print("🔍 Testing environment templates...")

    # Get the correct path to the project root
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent

    files_to_check = [
        (".env.template", "Secure environment template"),
        (".env.example", "Environment example with security warnings"),
    ]

    all_exist = True
    for filename, description in files_to_check:
        file_path = project_root / filename

        if not file_path.exists():
            print(f"   ❌ {description} not found: {filename}")
            all_exist = False
        else:
            content = file_path.read_text()
            if "SECURITY WARNING" in content or "REPLACE_WITH_" in content:
                print(f"   ✅ {description} exists with security warnings")
            else:
                print(f"   ⚠️  {description} exists but may lack security warnings")

    return all_exist


def test_documentation_exists():
    """Test that security documentation exists"""
    print("🔍 Testing security documentation...")

    # Get the correct path to the documentation file
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent
    doc_file = project_root / "docs" / "security" / "SECRETS_MANAGEMENT_SECURITY.md"

    if not doc_file.exists():
        print("   ❌ Security documentation not found")
        return False

    content = doc_file.read_text()

    required_sections = [
        "SECURITY IMPLEMENTATION SUMMARY",
        "SECURITY VALIDATION SYSTEM",
        "SECRETS ROTATION POLICY",
        "CRITICAL SECURITY WARNINGS",
    ]

    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)

    if missing_sections:
        print(f"   ❌ Missing documentation sections: {missing_sections}")
        return False
    else:
        print("   ✅ Security documentation is comprehensive")
        return True


def test_placeholder_detection():
    """Test basic placeholder detection functionality"""
    print("🔍 Testing placeholder detection...")

    try:
        # Add the services directory to path dynamically
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent
        services_path = str(project_root / "services")

        if services_path not in sys.path:
            sys.path.insert(0, services_path)

        from shared.config.secure_environment import SecureEnvironmentConfig

        config = SecureEnvironmentConfig()

        # Test placeholder detection
        test_cases = [
            ("REPLACE_WITH_YOUR_KEY", True),
            ("your_api_key_here", True),
            ("test_placeholder_key", True),
            ("test_valid_format_key_123456789", False),  # Valid format
            ("actual_secret_key_123", False),  # Not a placeholder pattern
        ]

        all_passed = True
        for value, should_be_placeholder in test_cases:
            validation = config._validate_env_var("TEST_KEY", value)

            is_placeholder = (
                validation.validation_result.value == "placeholder_detected"
            )

            if is_placeholder != should_be_placeholder:
                print(f"   ❌ Placeholder detection failed for '{value[:20]}'")
                all_passed = False

        if all_passed:
            print("   ✅ Placeholder detection working correctly")
            return True
        else:
            return False

    except ImportError as e:
        print(f"   ❌ Failed to import security module: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error testing placeholder detection: {e}")
        return False


def main():
    """Run all security validation tests"""
    print("🔒 Quick Environment Variables & Secrets Security Validation")
    print("=" * 60)

    tests = [
        ("Hardcoded Secrets Removal", test_hardcoded_secrets_removed),
        ("Secure Environment Module", test_secure_environment_exists),
        ("Environment Templates", test_env_templates_exist),
        ("Security Documentation", test_documentation_exists),
        ("Placeholder Detection", test_placeholder_detection),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        result = test_func()
        results.append((test_name, result))

    print("\n" + "=" * 60)
    print("🔒 Security Validation Summary:")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")

    print(f"\n📊 Overall Result: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All critical security validations PASSED!")
        print(
            "✅ Task 8: Environment Variables & Secrets Management Security - COMPLETE"
        )
        return True
    else:
        print(f"\n⚠️  {total - passed} security issues found - please review above")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
