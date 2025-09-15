#!/usr/bin/env python3
"""
Cartrita AI OS - Comprehensive Project Analysis Tool
Uses Sentry integration and code analysis to identify and fix issues.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class CodeIssue:
    """Represents a code issue found during analysis."""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    suggested_fix: Optional[str] = None
    rule: Optional[str] = None

@dataclass
class AnalysisReport:
    """Complete analysis report."""
    timestamp: datetime = field(default_factory=datetime.now)
    total_files_analyzed: int = 0
    issues_found: List[CodeIssue] = field(default_factory=list)
    security_issues: List[CodeIssue] = field(default_factory=list)
    performance_issues: List[CodeIssue] = field(default_factory=list)
    code_quality_issues: List[CodeIssue] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

class ProjectAnalyzer:
    """Comprehensive project analyzer with Sentry integration."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.report = AnalysisReport()

        # File extensions to analyze
        self.python_files = []
        self.typescript_files = []
        self.javascript_files = []

    async def run_full_analysis(self) -> AnalysisReport:
        """Run comprehensive project analysis."""
        logger.info("🔍 Starting comprehensive project analysis...")

        try:
            # Discover files
            await self._discover_files()

            # Run various analysis tools
            await self._run_security_analysis()
            await self._run_code_quality_analysis()
            await self._run_performance_analysis()
            await self._run_dependency_analysis()
            await self._analyze_sentry_integration()

            # Generate summary
            self._generate_summary()

            # Save report
            await self._save_report()

            logger.info("✅ Analysis complete!")
            return self.report

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

    async def _discover_files(self):
        """Discover all relevant files for analysis."""
        logger.info("📁 Discovering files...")

        # Python files
        for pattern in ["**/*.py"]:
            self.python_files.extend(self.project_root.glob(pattern))

        # TypeScript/JavaScript files
        for pattern in ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"]:
            ts_js_files = list(self.project_root.glob(pattern))
            if pattern.endswith(('.ts', '.tsx')):
                self.typescript_files.extend(ts_js_files)
            else:
                self.javascript_files.extend(ts_js_files)

        # Filter out node_modules, .git, etc.
        exclude_dirs = {'.git', 'node_modules', '__pycache__', '.venv', '.mypy_cache', 'htmlcov'}

        self.python_files = [f for f in self.python_files
                           if not any(part in exclude_dirs for part in f.parts)]
        self.typescript_files = [f for f in self.typescript_files
                               if not any(part in exclude_dirs for part in f.parts)]
        self.javascript_files = [f for f in self.javascript_files
                               if not any(part in exclude_dirs for part in f.parts)]

        total_files = len(self.python_files) + len(self.typescript_files) + len(self.javascript_files)
        self.report.total_files_analyzed = total_files

        logger.info(f"Found {len(self.python_files)} Python, {len(self.typescript_files)} TypeScript, "
                   f"{len(self.javascript_files)} JavaScript files")

    async def _run_security_analysis(self):
        """Run security analysis using bandit and semgrep."""
        logger.info("🔒 Running security analysis...")

        # Bandit for Python security
        if self.python_files:
            try:
                result = subprocess.run([
                    'bandit', '-r', str(self.project_root),
                    '-f', 'json', '-o', 'bandit-report.json'
                ], capture_output=True, text=True, timeout=300)

                if os.path.exists('bandit-report.json'):
                    with open('bandit-report.json') as f:
                        bandit_data = json.load(f)

                    for result_item in bandit_data.get('results', []):
                        issue = CodeIssue(
                            file_path=result_item['filename'],
                            line_number=result_item['line_number'],
                            issue_type='security',
                            severity=result_item['issue_severity'].lower(),
                            description=result_item['issue_text'],
                            rule=result_item['test_name'],
                            suggested_fix=f"Review {result_item['test_name']} security pattern"
                        )
                        self.report.security_issues.append(issue)
                        self.report.issues_found.append(issue)

            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                logger.warning(f"Bandit analysis failed: {e}")

        # Semgrep for broader security analysis (already configured in Codacy)
        try:
            result = subprocess.run([
                'semgrep', '--config=auto', '--json', str(self.project_root)
            ], capture_output=True, text=True, timeout=300)

            if result.stdout:
                semgrep_data = json.loads(result.stdout)
                for finding in semgrep_data.get('results', []):
                    issue = CodeIssue(
                        file_path=finding['path'],
                        line_number=finding['start']['line'],
                        issue_type='security',
                        severity=self._map_semgrep_severity(finding.get('severity', 'INFO')),
                        description=finding['message'],
                        rule=finding['check_id'],
                        suggested_fix=finding.get('fix', 'Review and address security finding')
                    )
                    self.report.security_issues.append(issue)
                    self.report.issues_found.append(issue)

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Semgrep analysis failed: {e}")

    async def _run_code_quality_analysis(self):
        """Run code quality analysis using pylint, mypy, eslint."""
        logger.info("📊 Running code quality analysis...")

        # Pylint for Python
        if self.python_files:
            try:
                result = subprocess.run([
                    'pylint', '--output-format=json',
                    *[str(f) for f in self.python_files[:10]]  # Limit for performance
                ], capture_output=True, text=True, timeout=300)

                if result.stdout:
                    try:
                        pylint_data = json.loads(result.stdout)
                        for item in pylint_data:
                            issue = CodeIssue(
                                file_path=item['path'],
                                line_number=item['line'],
                                issue_type='code_quality',
                                severity=self._map_pylint_severity(item['type']),
                                description=item['message'],
                                rule=item['message-id'],
                                suggested_fix=f"Address {item['type']}: {item['symbol']}"
                            )
                            self.report.code_quality_issues.append(issue)
                            self.report.issues_found.append(issue)
                    except json.JSONDecodeError:
                        logger.warning("Could not parse pylint output")

            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                logger.warning(f"Pylint analysis failed: {e}")

        # ESLint for TypeScript/JavaScript
        if self.typescript_files or self.javascript_files:
            try:
                result = subprocess.run([
                    'npx', 'eslint', '--format=json',
                    str(self.project_root / 'frontend/src')
                ], capture_output=True, text=True, timeout=300)

                if result.stdout:
                    try:
                        eslint_data = json.loads(result.stdout)
                        for file_result in eslint_data:
                            for message in file_result.get('messages', []):
                                issue = CodeIssue(
                                    file_path=file_result['filePath'],
                                    line_number=message['line'],
                                    issue_type='code_quality',
                                    severity=self._map_eslint_severity(message['severity']),
                                    description=message['message'],
                                    rule=message.get('ruleId', 'unknown'),
                                    suggested_fix=message.get('fix', 'Review ESLint rule')
                                )
                                self.report.code_quality_issues.append(issue)
                                self.report.issues_found.append(issue)
                    except json.JSONDecodeError:
                        logger.warning("Could not parse ESLint output")

            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                logger.warning(f"ESLint analysis failed: {e}")

    async def _run_performance_analysis(self):
        """Analyze performance patterns and anti-patterns."""
        logger.info("⚡ Running performance analysis...")

        # Analyze Python files for performance issues
        for py_file in self.python_files[:20]:  # Limit for performance
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)

                # Look for common performance anti-patterns
                for node in ast.walk(tree):
                    # Inefficient loops
                    if isinstance(node, ast.For):
                        if self._has_nested_loops(node):
                            issue = CodeIssue(
                                file_path=str(py_file),
                                line_number=node.lineno,
                                issue_type='performance',
                                severity='medium',
                                description='Nested loops detected - consider optimization',
                                suggested_fix='Consider using list comprehensions or vectorization'
                            )
                            self.report.performance_issues.append(issue)
                            self.report.issues_found.append(issue)

                    # Global variable access in loops
                    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                        # This is a simplified check - could be enhanced
                        pass

            except (SyntaxError, UnicodeDecodeError) as e:
                logger.warning(f"Could not analyze {py_file}: {e}")

    async def _run_dependency_analysis(self):
        """Analyze dependencies for security vulnerabilities."""
        logger.info("📦 Running dependency analysis...")

        # Python dependencies
        if (self.project_root / 'requirements.txt').exists():
            try:
                result = subprocess.run([
                    'pip-audit', '--format=json', '--requirement', 'requirements.txt'
                ], capture_output=True, text=True, timeout=300)

                if result.stdout:
                    try:
                        audit_data = json.loads(result.stdout)
                        for vuln in audit_data.get('vulnerabilities', []):
                            issue = CodeIssue(
                                file_path='requirements.txt',
                                line_number=1,
                                issue_type='dependency_vulnerability',
                                severity='high',
                                description=f"Vulnerable dependency: {vuln['package']} {vuln['installed_version']}",
                                suggested_fix=f"Update to version {vuln.get('fixed_version', 'latest')}"
                            )
                            self.report.security_issues.append(issue)
                            self.report.issues_found.append(issue)
                    except json.JSONDecodeError:
                        logger.warning("Could not parse pip-audit output")

            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                logger.warning(f"pip-audit failed: {e}")

        # Node.js dependencies
        if (self.project_root / 'package.json').exists():
            try:
                result = subprocess.run([
                    'npm', 'audit', '--json'
                ], capture_output=True, text=True, timeout=300, cwd=self.project_root)

                if result.stdout:
                    try:
                        audit_data = json.loads(result.stdout)
                        for advisory_id, advisory in audit_data.get('advisories', {}).items():
                            issue = CodeIssue(
                                file_path='package.json',
                                line_number=1,
                                issue_type='dependency_vulnerability',
                                severity=advisory['severity'],
                                description=f"Vulnerable dependency: {advisory['module_name']}",
                                suggested_fix=f"Run 'npm audit fix' or update to safe version"
                            )
                            self.report.security_issues.append(issue)
                            self.report.issues_found.append(issue)
                    except json.JSONDecodeError:
                        logger.warning("Could not parse npm audit output")

            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                logger.warning(f"npm audit failed: {e}")

    async def _analyze_sentry_integration(self):
        """Analyze Sentry integration completeness."""
        logger.info("🔍 Analyzing Sentry integration...")

        sentry_files = []
        sentry_imports = []

        # Check for Sentry usage across Python files
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'sentry' in content.lower():
                    sentry_files.append(str(py_file))

                if 'import sentry' in content or 'from sentry' in content:
                    sentry_imports.append(str(py_file))

            except UnicodeDecodeError:
                continue

        # Check if Sentry is properly configured
        config_files = ['config.py', 'settings.py', 'main.py']
        has_sentry_config = any(
            (self.project_root / 'services/ai-orchestrator/cartrita/orchestrator/utils' / f).exists()
            for f in ['sentry_config.py']
        )

        if not has_sentry_config:
            issue = CodeIssue(
                file_path='services/ai-orchestrator',
                line_number=1,
                issue_type='monitoring',
                severity='medium',
                description='Sentry configuration not found or incomplete',
                suggested_fix='Implement comprehensive Sentry integration'
            )
            self.report.issues_found.append(issue)

        self.report.summary['sentry_integration'] = {
            'files_with_sentry': len(sentry_files),
            'files_with_imports': len(sentry_imports),
            'has_config': has_sentry_config,
            'sentry_files': sentry_files[:5]  # Limit output
        }

    def _generate_summary(self):
        """Generate analysis summary."""
        total_issues = len(self.report.issues_found)

        severity_counts = {
            'critical': len([i for i in self.report.issues_found if i.severity == 'critical']),
            'high': len([i for i in self.report.issues_found if i.severity == 'high']),
            'medium': len([i for i in self.report.issues_found if i.severity == 'medium']),
            'low': len([i for i in self.report.issues_found if i.severity == 'low']),
        }

        type_counts = {
            'security': len(self.report.security_issues),
            'performance': len(self.report.performance_issues),
            'code_quality': len(self.report.code_quality_issues),
        }

        self.report.summary.update({
            'total_issues': total_issues,
            'severity_breakdown': severity_counts,
            'type_breakdown': type_counts,
            'files_analyzed': {
                'python': len(self.python_files),
                'typescript': len(self.typescript_files),
                'javascript': len(self.javascript_files),
            }
        })

    async def _save_report(self):
        """Save analysis report to file."""
        report_data = {
            'timestamp': self.report.timestamp.isoformat(),
            'total_files_analyzed': self.report.total_files_analyzed,
            'summary': self.report.summary,
            'issues': [
                {
                    'file_path': issue.file_path,
                    'line_number': issue.line_number,
                    'issue_type': issue.issue_type,
                    'severity': issue.severity,
                    'description': issue.description,
                    'suggested_fix': issue.suggested_fix,
                    'rule': issue.rule,
                }
                for issue in self.report.issues_found
            ]
        }

        with open('cartrita_analysis_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)

        logger.info("📄 Analysis report saved to cartrita_analysis_report.json")

    # Helper methods
    def _map_semgrep_severity(self, severity: str) -> str:
        mapping = {'ERROR': 'high', 'WARNING': 'medium', 'INFO': 'low'}
        return mapping.get(severity.upper(), 'low')

    def _map_pylint_severity(self, msg_type: str) -> str:
        mapping = {'error': 'high', 'warning': 'medium', 'refactor': 'low', 'convention': 'low'}
        return mapping.get(msg_type, 'medium')

    def _map_eslint_severity(self, severity: int) -> str:
        return 'high' if severity == 2 else 'medium' if severity == 1 else 'low'

    def _has_nested_loops(self, node: ast.For) -> bool:
        """Check if a for loop contains nested loops."""
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While)) and child != node:
                return True
        return False


async def main():
    """Main entry point."""
    analyzer = ProjectAnalyzer()

    try:
        report = await analyzer.run_full_analysis()

        print(f"\n🎯 Analysis Summary:")
        print(f"Files analyzed: {report.total_files_analyzed}")
        print(f"Total issues found: {len(report.issues_found)}")
        print(f"Security issues: {len(report.security_issues)}")
        print(f"Performance issues: {len(report.performance_issues)}")
        print(f"Code quality issues: {len(report.code_quality_issues)}")

        # Show top issues
        print(f"\n🔥 Top Issues:")
        critical_high = [i for i in report.issues_found if i.severity in ['critical', 'high']]
        for issue in critical_high[:10]:
            print(f"  {issue.severity.upper()}: {issue.file_path}:{issue.line_number} - {issue.description[:80]}...")

        print(f"\n📊 See cartrita_analysis_report.json for detailed report")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())