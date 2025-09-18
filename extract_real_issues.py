#!/usr/bin/env python3
"""
Extract real security issues (excluding the audit file itself which contains examples).
"""

import json
import os


def load_audit_data():
    """Load the security audit data."""
    audit_file = "/home/robbie/cartrita-ai-os/config_security_audit.json"
    with open(audit_file, "r") as f:
        return json.load(f)


def extract_real_issues(audit_data):
    """Extract real security issues, excluding the audit file itself."""
    real_issues = []
    excluded_files = {
        "config_security_audit.json",  # The audit file itself
        "config_security_audit.py",  # The audit script
        "critical_issues_analysis.json",  # Our analysis file
        "analyze_critical_issues.py",  # Our analysis script
        "extract_real_issues.py",  # This script
    }

    for finding in audit_data.get("findings", []):
        file_path = finding.get("file", "")

        # Skip excluded files
        if any(excluded in file_path for excluded in excluded_files):
            continue

        # Focus on high and critical severity issues
        severity = finding.get("severity", "").lower()
        if severity in ["high", "critical"]:
            real_issues.append(finding)

    return real_issues


def group_real_issues(issues):
    """Group real issues by type and file."""
    by_type = {}
    by_file = {}

    for issue in issues:
        issue_type = issue.get("type", "unknown")
        file_path = issue.get("file", "unknown")

        if issue_type not in by_type:
            by_type[issue_type] = []
        by_type[issue_type].append(issue)

        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append(issue)

    return by_type, by_file


def main():
    print("Loading security audit data...")
    audit_data = load_audit_data()

    print("Extracting real security issues...")
    real_issues = extract_real_issues(audit_data)

    print("Grouping issues...")
    by_type, by_file = group_real_issues(real_issues)

    print("\n=== REAL SECURITY ISSUES ===")
    print(f"Total real issues: {len(real_issues)}")
    print(f"Files affected: {len(by_file)}")

    print("\nIssue types:")
    for issue_type, issues in sorted(by_type.items()):
        print(f"  {issue_type}: {len(issues)}")

    print("\nFiles with real issues:")
    for file_path, issues in sorted(by_file.items()):
        print(f"  {file_path}: {len(issues)} issues")
        for issue in issues:
            severity = issue.get("severity", "?")
            issue_type = issue.get("type", "?")
            line = issue.get("line", "?")
            description = issue.get("description", "?")
            print(
                f"    - Line {line}: [{severity.upper()}] {issue_type} - {description}"
            )

    # Save the real issues for processing
    result = {
        "total_real_issues": len(real_issues),
        "by_type": by_type,
        "by_file": by_file,
        "all_issues": real_issues,
    }

    with open("real_security_issues.json", "w") as f:
        json.dump(result, f, indent=2)

    print("\nReal issues saved to real_security_issues.json")


if __name__ == "__main__":
    main()
