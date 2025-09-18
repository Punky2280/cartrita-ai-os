#!/usr/bin/env python3
"""
Configuration Security Audit Script for Cartrita AI OS
======================================================

Performs comprehensive security audit of all configuration files, environment
variables, and security settings to identify potential vulnerabilities.
"""

import os
import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security risk levels for configuration issues"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityFinding:
    """Represents a security configuration finding"""

    file_path: str
    line_number: int
    issue_type: str
    severity: SecurityLevel
    description: str
    recommendation: str
    code_snippet: Optional[str] = None


class ConfigurationSecurityAuditor:
    """Comprehensive configuration security auditor"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.findings: List[SecurityFinding] = []

        # Patterns for security issues
        self.hardcoded_secret_patterns = [
            (
                r'(api_key|apikey|api-key)\s*[=:]\s*["\'][^"\']{20,}["\']',
                SecurityLevel.HIGH,
            ),
            (r'password\s*[=:]\s*["\'][^"\']{5,}["\']', SecurityLevel.HIGH),
            (r'secret\s*[=:]\s*["\'][^"\']{10,}["\']', SecurityLevel.HIGH),
            (r'token\s*[=:]\s*["\'][^"\']{15,}["\']', SecurityLevel.HIGH),
            (r"sk-[a-zA-Z0-9]{20,}", SecurityLevel.CRITICAL),
            (r"ghp_[a-zA-Z0-9]{36}", SecurityLevel.CRITICAL),
            (r"hf_[a-zA-Z0-9]{20,}", SecurityLevel.CRITICAL),
        ]

        self.insecure_config_patterns = [
            (r"debug\s*[=:]\s*true", SecurityLevel.MEDIUM),
            (r"ssl_verify\s*[=:]\s*false", SecurityLevel.HIGH),
            (r"verify_ssl\s*[=:]\s*false", SecurityLevel.HIGH),
            (r'allow_origin\s*[=:]\s*["\'][*]["\']', SecurityLevel.HIGH),
            (r"cors_origins?\s*[=:]\s*.*[*]", SecurityLevel.HIGH),
        ]

        # File patterns to scan
        self.config_file_patterns = [
            "**/*.py",
            "**/*.js",
            "**/*.ts",
            "**/*.json",
            "**/*.yaml",
            "**/*.yml",
            "**/*.env*",
            "**/config*",
            "**/*.config.*",
            "**/settings*",
        ]

        # Exclude patterns
        self.exclude_patterns = [
            "**/node_modules/**",
            "**/venv/**",
            "**/.venv/**",
            "**/dist/**",
            "**/build/**",
            "**/__pycache__/**",
            "**/*.pyc",
            "**/.*",
        ]

    def scan_project(self) -> None:
        """Perform comprehensive security scan of the project"""
        logger.info("🔍 Starting configuration security audit...")

        # Scan all configuration files
        config_files = self._find_config_files()
        logger.info(f"📁 Found {len(config_files)} configuration files to scan")

        for file_path in config_files:
            self._scan_file(file_path)

        # Additional specific checks
        self._check_environment_files()
        self._check_docker_security()
        self._check_cors_configuration()
        self._check_ssl_configuration()

        logger.info(f"✅ Security audit complete. Found {len(self.findings)} issues")

    def _find_config_files(self) -> List[Path]:
        """Find all configuration files to scan"""
        files = []
        for pattern in self.config_file_patterns:
            for file_path in self.project_root.rglob(pattern):
                if self._should_scan_file(file_path):
                    files.append(file_path)
        return files

    def _should_scan_file(self, file_path: Path) -> bool:
        """Determine if a file should be included in security scan."""
        # Skip if it's a directory
        if file_path.is_dir():
            return False

        skip_patterns = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".next",
            ".venv",
            "venv",
            "env",
            ".env.local",
            ".mypy_cache",
            ".coverage",
            "dist",
            "build",
            "*.egg-info",
            "logs",
            ".DS_Store",
        }

        # Skip binary files, logs, or non-text files
        if any(pattern in str(file_path) for pattern in skip_patterns):
            return False

        # Only scan text files that might contain configuration
        if file_path.suffix.lower() in {".pyc", ".pyo", ".so", ".dll", ".exe", ".bin"}:
            return False

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                # Read first few bytes to check if it's likely a text file
                sample = f.read(512)
                if "\0" in sample:  # Binary file indicator
                    return False
        except (OSError, IOError, UnicodeDecodeError):
            return False

        return True

    def _scan_file(self, file_path: Path) -> None:
        """Scan individual file for security issues"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.splitlines()

            # Check for hardcoded secrets
            self._check_hardcoded_secrets(file_path, lines)

            # Check for insecure configurations
            self._check_insecure_configs(file_path, lines)

            # File-specific checks
            if file_path.suffix in [".py"]:
                self._check_python_security(file_path, lines)
            elif file_path.suffix in [".js", ".ts"]:
                self._check_javascript_security(file_path, lines)
            elif file_path.name.startswith(".env"):
                self._check_env_file_security(file_path, lines)

        except Exception as e:
            logger.warning(f"Failed to scan {file_path}: {e}")

    def _check_hardcoded_secrets(self, file_path: Path, lines: List[str]) -> None:
        """Check for hardcoded secrets in file"""
        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower()

            # Skip comments and examples
            if any(
                skip in line_lower
                for skip in ["example", "placeholder", "your_", "replace_with"]
            ):
                continue

            for pattern, severity in self.hardcoded_secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.findings.append(
                        SecurityFinding(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="hardcoded_secret",
                            severity=severity,
                            description=f"Potential hardcoded secret detected",
                            recommendation="Move secret to environment variables or secure vault",
                            code_snippet=line.strip()[:100],
                        )
                    )

    def _check_insecure_configs(self, file_path: Path, lines: List[str]) -> None:
        """Check for insecure configuration patterns"""
        for line_num, line in enumerate(lines, 1):
            for pattern, severity in self.insecure_config_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.findings.append(
                        SecurityFinding(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="insecure_config",
                            severity=severity,
                            description=f"Insecure configuration detected",
                            recommendation="Review and secure configuration setting",
                            code_snippet=line.strip()[:100],
                        )
                    )

    def _check_python_security(self, file_path: Path, lines: List[str]) -> None:
        """Python-specific security checks"""
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Check for dangerous functions
            dangerous_patterns = [
                (r"eval\s*\(", "Use of eval() function"),
                (r"exec\s*\(", "Use of exec() function"),
                (r"os\.system\s*\(", "Use of os.system()"),
                (r"subprocess\.call\s*\([^)]*shell\s*=\s*True", "Shell injection risk"),
            ]

            for pattern, desc in dangerous_patterns:
                if re.search(pattern, line):
                    self.findings.append(
                        SecurityFinding(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="dangerous_function",
                            severity=SecurityLevel.HIGH,
                            description=desc,
                            recommendation="Use safer alternatives or input validation",
                            code_snippet=line_stripped[:100],
                        )
                    )

    def _check_javascript_security(self, file_path: Path, lines: List[str]) -> None:
        """JavaScript/TypeScript-specific security checks"""
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Check for dangerous patterns
            dangerous_patterns = [
                (r"eval\s*\(", "Use of eval() function"),
                (r"innerHTML\s*=", "Potential XSS with innerHTML"),
                (r"document\.write\s*\(", "Use of document.write()"),
                (r"dangerouslySetInnerHTML", "React dangerouslySetInnerHTML usage"),
            ]

            for pattern, desc in dangerous_patterns:
                if re.search(pattern, line):
                    severity = (
                        SecurityLevel.HIGH
                        if "eval" in pattern
                        else SecurityLevel.MEDIUM
                    )
                    self.findings.append(
                        SecurityFinding(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="dangerous_function",
                            severity=severity,
                            description=desc,
                            recommendation="Use safer alternatives or input sanitization",
                            code_snippet=line_stripped[:100],
                        )
                    )

    def _check_env_file_security(self, file_path: Path, lines: List[str]) -> None:
        """Environment file specific security checks"""
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Check for weak secrets
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("\"'")

                # Check for placeholder values
                if any(
                    placeholder in value.lower()
                    for placeholder in [
                        "your_",
                        "replace_with",
                        "changeme",
                        "example",
                        "placeholder",
                    ]
                ):
                    self.findings.append(
                        SecurityFinding(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="placeholder_value",
                            severity=SecurityLevel.MEDIUM,
                            description=f"Placeholder value detected for {key}",
                            recommendation="Replace with actual secure value",
                            code_snippet=f"{key}=***REDACTED***",
                        )
                    )

    def _check_environment_files(self) -> None:
        """Check environment file permissions and existence"""
        env_files = [".env", ".env.local", ".env.production", ".env.development"]

        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                # Check file permissions
                stat = env_path.stat()
                permissions = oct(stat.st_mode)[-3:]

                if permissions != "600":
                    self.findings.append(
                        SecurityFinding(
                            file_path=env_file,
                            line_number=0,
                            issue_type="file_permissions",
                            severity=SecurityLevel.MEDIUM,
                            description=f"Environment file has permissions {permissions}, should be 600",
                            recommendation="Run: chmod 600 " + env_file,
                        )
                    )

    def _check_docker_security(self) -> None:
        """Check Docker security configuration"""
        docker_files = ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"]

        for docker_file in docker_files:
            docker_path = self.project_root / docker_file
            if docker_path.exists():
                self._scan_docker_file(docker_path)

    def _scan_docker_file(self, file_path: Path) -> None:
        """Scan Docker file for security issues"""
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip().upper()

                # Check for security issues
                if line_stripped.startswith("USER ROOT"):
                    self.findings.append(
                        SecurityFinding(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="docker_security",
                            severity=SecurityLevel.HIGH,
                            description="Running as root user in Docker",
                            recommendation="Use non-root user in container",
                            code_snippet=line.strip(),
                        )
                    )

                if "LATEST" in line_stripped and "FROM" in line_stripped:
                    self.findings.append(
                        SecurityFinding(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="docker_security",
                            severity=SecurityLevel.MEDIUM,
                            description="Using latest tag for base image",
                            recommendation="Pin to specific version for reproducible builds",
                            code_snippet=line.strip(),
                        )
                    )

        except Exception as e:
            logger.warning(f"Failed to scan Docker file {file_path}: {e}")

    def _check_cors_configuration(self) -> None:
        """Check CORS configuration for security"""
        cors_files = list(self.project_root.rglob("*cors*"))

        for cors_file in cors_files:
            if cors_file.suffix in [".py", ".js", ".ts"]:
                self._scan_file(cors_file)

    def _check_ssl_configuration(self) -> None:
        """Check SSL/TLS configuration"""
        # This would check SSL cert files, TLS configs, etc.
        pass

    def generate_report(self, output_file: Optional[str] = None) -> Dict:
        """Generate security audit report"""
        severity_counts = {level.value: 0 for level in SecurityLevel}
        issue_types = {}

        for finding in self.findings:
            severity_counts[finding.severity.value] += 1
            if finding.issue_type not in issue_types:
                issue_types[finding.issue_type] = 0
            issue_types[finding.issue_type] += 1

        report = {
            "timestamp": "2025-09-17T04:00:00.000000",
            "total_findings": len(self.findings),
            "severity_breakdown": severity_counts,
            "issue_type_breakdown": issue_types,
            "findings": [
                {
                    "file": finding.file_path,
                    "line": finding.line_number,
                    "type": finding.issue_type,
                    "severity": finding.severity.value,
                    "description": finding.description,
                    "recommendation": finding.recommendation,
                    "code": finding.code_snippet,
                }
                for finding in self.findings
            ],
        }

        if output_file:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)

        return report


def main():
    """Main function to run security audit"""
    project_root = os.getcwd()
    auditor = ConfigurationSecurityAuditor(project_root)

    # Run the audit
    auditor.scan_project()

    # Generate report
    report = auditor.generate_report("config_security_audit.json")

    # Print summary
    print("\\n🔒 Configuration Security Audit Results:")
    print(f"  Total findings: {report['total_findings']}")
    print("  Severity breakdown:")
    for severity, count in report["severity_breakdown"].items():
        if count > 0:
            print(f"    {severity.upper()}: {count}")

    print("\\n  Issue types:")
    for issue_type, count in report["issue_type_breakdown"].items():
        print(f"    {issue_type}: {count}")

    # Show critical/high issues
    critical_high = [
        f
        for f in auditor.findings
        if f.severity in [SecurityLevel.CRITICAL, SecurityLevel.HIGH]
    ]

    if critical_high:
        print("\\n🚨 Critical/High Severity Issues:")
        for finding in critical_high[:10]:  # Show first 10
            print(
                f"  {finding.severity.value.upper()}: {finding.file_path}:{finding.line_number}"
            )
            print(f"    {finding.description}")
            print(f"    Recommendation: {finding.recommendation}")
            print()


if __name__ == "__main__":
    main()
