#!/usr/bin/env python3
"""
Analyze critical security issues from the audit file and group them for fixing.
"""

import json
import os
from collections import defaultdict
from typing import Dict, List, Any


def load_audit_data() -> Dict[str, Any]:
    """Load the security audit data."""
    audit_file = "/home/robbie/cartrita-ai-os/config_security_audit.json"
    with open(audit_file, "r") as f:
        return json.load(f)


def extract_critical_issues(audit_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all critical severity issues."""
    critical_issues = []
    for finding in audit_data.get("findings", []):
        if finding.get("severity") == "critical":
            critical_issues.append(finding)
    return critical_issues


def group_issues_by_file(
    issues: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """Group issues by file for efficient fixing."""
    grouped = defaultdict(list)
    for issue in issues:
        file_path = issue.get("file", "unknown")
        grouped[file_path].append(issue)
    return dict(grouped)


def analyze_issue_types(issues: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze the types of critical issues."""
    type_counts = defaultdict(int)
    for issue in issues:
        issue_type = issue.get("type", "unknown")
        type_counts[issue_type] += 1
    return dict(type_counts)


def print_analysis(
    critical_issues: List[Dict[str, Any]],
    grouped_issues: Dict[str, List[Dict[str, Any]]],
    issue_types: Dict[str, int],
):
    """Print detailed analysis of critical issues."""
    print(f"=== CRITICAL SECURITY ISSUES ANALYSIS ===")
    print(f"Total critical issues: {len(critical_issues)}")
    print(f"Files affected: {len(grouped_issues)}")
    print()

    print("Issue types breakdown:")
    for issue_type, count in sorted(issue_types.items()):
        print(f"  {issue_type}: {count}")
    print()

    print("Files with critical issues:")
    for file_path, issues in sorted(grouped_issues.items()):
        print(f"  {file_path}: {len(issues)} issues")
        for issue in issues[:3]:  # Show first 3 issues per file
            print(
                f"    - Line {issue.get('line', '?')}: {issue.get('type', '?')} - {issue.get('description', '?')}"
            )
        if len(issues) > 3:
            print(f"    ... and {len(issues) - 3} more")
        print()


def main():
    """Main analysis function."""
    try:
        print("Loading security audit data...")
        audit_data = load_audit_data()

        print("Extracting critical issues...")
        critical_issues = extract_critical_issues(audit_data)

        print("Grouping issues by file...")
        grouped_issues = group_issues_by_file(critical_issues)

        print("Analyzing issue types...")
        issue_types = analyze_issue_types(critical_issues)

        print_analysis(critical_issues, grouped_issues, issue_types)

        # Save analysis for reference
        analysis_data = {
            "total_critical": len(critical_issues),
            "files_affected": list(grouped_issues.keys()),
            "issue_types": issue_types,
            "grouped_issues": grouped_issues,
        }

        with open("critical_issues_analysis.json", "w") as f:
            json.dump(analysis_data, f, indent=2)

        print("Analysis saved to critical_issues_analysis.json")

    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
