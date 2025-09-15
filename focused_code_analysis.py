#!/usr/bin/env python3
"""
Focused code analysis for Cartrita AI OS - excluding dependencies
"""

import asyncio
import ast
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CodeIssue:
    file_path: str
    line_number: int
    issue_type: str
    severity: str
    description: str
    suggested_fix: Optional[str] = None
    code_snippet: Optional[str] = None

class FocusedAnalyzer:
    """Focused analyzer for actual project code."""

    def __init__(self):
        self.project_root = Path(".")
        self.issues = []

        # Define actual project directories (exclude dependencies)
        self.project_dirs = [
            "services/ai-orchestrator/cartrita",
            "frontend/src",
            "tests",
            "scripts",
            "docs"
        ]

    async def analyze_project_code(self):
        """Analyze only the actual project code."""
        logger.info("🔍 Analyzing project code (excluding dependencies)...")

        # Get project files only
        project_files = []
        for dir_path in self.project_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                # Python files
                project_files.extend(full_path.glob("**/*.py"))
                # TypeScript/JavaScript files
                project_files.extend(full_path.glob("**/*.ts"))
                project_files.extend(full_path.glob("**/*.tsx"))
                project_files.extend(full_path.glob("**/*.js"))
                project_files.extend(full_path.glob("**/*.jsx"))

        logger.info(f"Found {len(project_files)} project files to analyze")

        # Analyze each file
        for file_path in project_files:
            if file_path.suffix == '.py':
                await self._analyze_python_file(file_path)
            elif file_path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
                await self._analyze_typescript_file(file_path)

        return self.issues

    async def _analyze_python_file(self, file_path: Path):
        """Analyze a Python file for issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()

            tree = ast.parse(content)

            # Check for common issues
            async_functions = [node for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)]

            for node in ast.walk(tree):
                # 1. Missing error handling in async functions
                if isinstance(node, ast.AsyncFunctionDef):
                    # Pre-collect try blocks for this function to avoid nested walk
                    function_nodes = list(ast.walk(node))
                    has_try_except = any(isinstance(child, ast.Try) for child in function_nodes)
                    if not has_try_except and self._is_api_or_db_function(node):
                        self.issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            issue_type='error_handling',
                            severity='medium',
                            description=f'Async function "{node.name}" missing error handling',
                            suggested_fix='Add try-except block for proper error handling',
                            code_snippet=lines[node.lineno-1:node.lineno+2] if node.lineno <= len(lines) else None
                        ))

                # 2. SQL injection risks
                if isinstance(node, ast.Call):
                    if (isinstance(node.func, ast.Attribute) and
                        node.func.attr in ['execute', 'executemany'] and
                        any(isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod) for arg in node.args)):
                        self.issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            issue_type='security',
                            severity='high',
                            description='Potential SQL injection risk with string formatting',
                            suggested_fix='Use parameterized queries instead of string formatting',
                            code_snippet=lines[node.lineno-1:node.lineno+1] if node.lineno <= len(lines) else None
                        ))

                # 3. Hardcoded secrets
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and any(secret in target.id.lower()
                                                              for secret in ['password', 'secret', 'token', 'key']):
                            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                if len(node.value.value) > 10:  # Likely a real secret
                                    self.issues.append(CodeIssue(
                                        file_path=str(file_path),
                                        line_number=node.lineno,
                                        issue_type='security',
                                        severity='critical',
                                        description=f'Hardcoded secret detected: {target.id}',
                                        suggested_fix='Move to environment variables or secure configuration',
                                        code_snippet=f'{target.id} = "***REDACTED***"'
                                    ))

                # 4. Missing logging in critical functions
                if isinstance(node, ast.FunctionDef) and node.name.startswith(('create_', 'delete_', 'update_')):
                    has_logging = any(
                        isinstance(child, ast.Call) and
                        isinstance(child.func, ast.Attribute) and
                        child.func.attr in ['info', 'warning', 'error', 'debug']
                        for child in ast.walk(node)
                    )
                    if not has_logging:
                        self.issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            issue_type='observability',
                            severity='low',
                            description=f'Critical function "{node.name}" missing logging',
                            suggested_fix='Add appropriate logging statements',
                            code_snippet=lines[node.lineno-1] if node.lineno <= len(lines) else None
                        ))

                # 5. Inefficient database queries
                if isinstance(node, ast.For):
                    # Check for queries inside loops
                    for child in ast.walk(node):
                        if (isinstance(child, ast.Call) and
                            isinstance(child.func, ast.Attribute) and
                            child.func.attr in ['execute', 'fetch', 'fetchall', 'query']):
                            self.issues.append(CodeIssue(
                                file_path=str(file_path),
                                line_number=node.lineno,
                                issue_type='performance',
                                severity='medium',
                                description='Database query inside loop - potential N+1 problem',
                                suggested_fix='Consider bulk operations or query optimization',
                                code_snippet=lines[node.lineno-1:node.lineno+2] if node.lineno <= len(lines) else None
                            ))

                # 6. Missing Sentry integration
                if isinstance(node, ast.ExceptHandler):
                    has_sentry_capture = any(
                        isinstance(child, ast.Call) and
                        isinstance(child.func, ast.Name) and
                        'sentry' in str(child.func.id).lower()
                        for child in ast.walk(node)
                    )
                    if not has_sentry_capture:
                        self.issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            issue_type='monitoring',
                            severity='low',
                            description='Exception handler missing Sentry error capture',
                            suggested_fix='Add sentry_sdk.capture_exception() or use @track_ai_errors decorator',
                            code_snippet=lines[node.lineno-1:node.lineno+2] if node.lineno <= len(lines) else None
                        ))

        except (SyntaxError, UnicodeDecodeError) as e:
            logger.warning(f"Could not analyze {file_path}: {e}")

    async def _analyze_typescript_file(self, file_path: Path):
        """Analyze TypeScript/JavaScript file for issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()

            # Basic pattern matching for common issues
            for i, line in enumerate(lines):
                line_num = i + 1

                # 1. Console.log in production code
                if 'console.log' in line and 'debug' not in line.lower():
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=line_num,
                        issue_type='code_quality',
                        severity='low',
                        description='console.log statement found - should be removed for production',
                        suggested_fix='Use proper logging or remove debug statements',
                        code_snippet=line.strip()
                    ))

                # 2. Hardcoded API keys or secrets
                secret_patterns = ['apikey', 'secret', 'token', 'password']
                for pattern in secret_patterns:
                    if f'{pattern}:' in line.lower() or f'{pattern} =' in line.lower():
                        if any(quote in line for quote in ['"', "'"]) and len(line) > 30:
                            self.issues.append(CodeIssue(
                                file_path=str(file_path),
                                line_number=line_num,
                                issue_type='security',
                                severity='high',
                                description=f'Potential hardcoded secret detected: {pattern}',
                                suggested_fix='Move to environment variables',
                                code_snippet='// REDACTED - potential secret'
                            ))

                # 3. Missing error handling in async functions
                if 'await' in line and 'try' not in lines[max(0, i-5):i+1]:
                    context_lines = lines[max(0, i-3):min(len(lines), i+3)]
                    if not any('catch' in ctx_line for ctx_line in context_lines):
                        self.issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=line_num,
                            issue_type='error_handling',
                            severity='medium',
                            description='Async operation without error handling',
                            suggested_fix='Wrap in try-catch block',
                            code_snippet=line.strip()
                        ))

                # 4. Direct DOM manipulation (should use React patterns)
                if any(dom_method in line for dom_method in ['getElementById', 'querySelector', 'innerHTML']):
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=line_num,
                        issue_type='code_quality',
                        severity='medium',
                        description='Direct DOM manipulation in React component',
                        suggested_fix='Use React refs or state management instead',
                        code_snippet=line.strip()
                    ))

        except UnicodeDecodeError as e:
            logger.warning(f"Could not analyze {file_path}: {e}")

    def _is_api_or_db_function(self, node):
        """Check if function is likely an API or database function."""
        function_name = node.name.lower()
        api_db_keywords = ['api', 'db', 'database', 'query', 'fetch', 'create', 'update', 'delete', 'get', 'post', 'put']
        return any(keyword in function_name for keyword in api_db_keywords)

    async def generate_patches(self):
        """Generate patches for the found issues."""
        logger.info("🔧 Generating patches for issues...")

        # Group issues by file
        issues_by_file = {}
        for issue in self.issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)

        patches = []
        for file_path, file_issues in issues_by_file.items():
            high_severity_issues = [i for i in file_issues if i.severity in ['critical', 'high']]
            if high_severity_issues:
                patch = await self._create_patch_for_file(file_path, high_severity_issues)
                if patch:
                    patches.append(patch)

        return patches

    async def _create_patch_for_file(self, file_path: str, issues: List[CodeIssue]) -> Optional[Dict[str, Any]]:
        """Create a patch for a specific file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
                lines = original_content.splitlines()

            modified_lines = lines.copy()
            modifications = []

            for issue in sorted(issues, key=lambda x: x.line_number, reverse=True):
                if issue.issue_type == 'security' and 'hardcoded' in issue.description.lower():
                    # Replace hardcoded secrets with environment variables
                    line_idx = issue.line_number - 1
                    if line_idx < len(modified_lines):
                        original_line = modified_lines[line_idx]

                        # Extract variable name
                        if '=' in original_line:
                            var_name = original_line.split('=')[0].strip()
                            env_name = var_name.upper()

                            # Create environment variable reference
                            if file_path.endswith('.py'):
                                new_line = f'{var_name} = os.getenv("{env_name}", "")'
                            else:  # TypeScript/JavaScript
                                new_line = f'{var_name} = process.env.{env_name} || "";'

                            modified_lines[line_idx] = new_line
                            modifications.append({
                                'line': issue.line_number,
                                'original': original_line.strip(),
                                'modified': new_line.strip(),
                                'reason': 'Replaced hardcoded secret with environment variable'
                            })

                elif issue.issue_type == 'error_handling' and file_path.endswith('.py'):
                    # Add basic error handling to async functions
                    line_idx = issue.line_number - 1
                    if line_idx < len(modified_lines):
                        # Find function body and wrap in try-except
                        indent = '    '  # Basic indentation
                        try_line = f'{indent}try:'
                        except_line = f'{indent}except Exception as e:'
                        capture_line = f'{indent}    capture_ai_error(e, {{"function": "{file_path}:{issue.line_number}"}})'
                        raise_line = f'{indent}    raise'

                        # Insert error handling (simplified approach)
                        modified_lines.insert(line_idx + 1, try_line)
                        modified_lines.insert(line_idx + 2, f'{indent}    # Function body goes here')
                        modified_lines.insert(line_idx + 3, except_line)
                        modified_lines.insert(line_idx + 4, capture_line)
                        modified_lines.insert(line_idx + 5, raise_line)

                        modifications.append({
                            'line': issue.line_number,
                            'original': 'Missing error handling',
                            'modified': 'Added try-except with Sentry integration',
                            'reason': 'Added error handling for async function'
                        })

            if modifications:
                return {
                    'file_path': file_path,
                    'modifications': modifications,
                    'patch_content': '\n'.join(modified_lines)
                }

        except Exception as e:
            logger.error(f"Failed to create patch for {file_path}: {e}")

        return None

async def main():
    """Main analysis and patching workflow."""
    analyzer = FocusedAnalyzer()

    # Run analysis
    issues = await analyzer.analyze_project_code()

    # Report findings
    print(f"\n🎯 Focused Analysis Results:")
    print(f"Total issues found: {len(issues)}")

    severity_counts = {}
    type_counts = {}

    for issue in issues:
        severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        type_counts[issue.issue_type] = type_counts.get(issue.issue_type, 0) + 1

    print(f"By severity: {severity_counts}")
    print(f"By type: {type_counts}")

    # Show critical and high severity issues
    critical_high = [i for i in issues if i.severity in ['critical', 'high']]
    if critical_high:
        print(f"\n🔥 Critical/High Issues:")
        for issue in critical_high:
            print(f"  {issue.severity.upper()}: {issue.file_path}:{issue.line_number}")
            print(f"    {issue.description}")
            print(f"    Fix: {issue.suggested_fix}")
            if issue.code_snippet:
                print(f"    Code: {issue.code_snippet}")
            print()

    # Generate patches for high-priority issues
    patches = await analyzer.generate_patches()

    if patches:
        print(f"\n🔧 Generated {len(patches)} patches for critical/high issues")

        # Save patches
        with open('generated_patches.json', 'w') as f:
            json.dump(patches, f, indent=2)

        print("Patches saved to generated_patches.json")
    else:
        print("No patches needed for current issues")

    # Save detailed report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_issues': len(issues),
        'severity_breakdown': severity_counts,
        'type_breakdown': type_counts,
        'issues': [
            {
                'file_path': issue.file_path,
                'line_number': issue.line_number,
                'issue_type': issue.issue_type,
                'severity': issue.severity,
                'description': issue.description,
                'suggested_fix': issue.suggested_fix,
                'code_snippet': issue.code_snippet
            }
            for issue in issues
        ],
        'patches_generated': len(patches)
    }

    with open('focused_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print("Detailed report saved to focused_analysis_report.json")

if __name__ == "__main__":
    asyncio.run(main())
