#!/usr/bin/env python3
"""
LangChain Documentation Analyzer and Agent Comparator
Analyzes extracted LangChain docs and compares with existing agent implementations
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re
from dataclasses import dataclass, field

@dataclass
class LangChainPattern:
    """Represents a LangChain pattern or best practice"""
    category: str
    name: str
    description: str
    code_examples: List[str] = field(default_factory=list)
    key_concepts: List[str] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)
    methods: Set[str] = field(default_factory=set)

@dataclass
class AgentAnalysis:
    """Analysis result for an existing agent"""
    agent_name: str
    file_path: str
    follows_patterns: List[str] = field(default_factory=list)
    missing_patterns: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    langchain_compatible: bool = False

class LangChainAnalyzer:
    def __init__(self):
        self.docs_dir = Path("docs/langchain_extracted")
        self.agents_dir = Path("services/ai-orchestrator/cartrita/orchestrator/agents")
        self.patterns: Dict[str, LangChainPattern] = {}
        self.agent_analyses: List[AgentAnalysis] = []

    def load_documentation(self) -> Dict:
        """Load all extracted LangChain documentation"""
        all_docs = {}
        for category_dir in self.docs_dir.iterdir():
            if category_dir.is_dir():
                category_docs = []
                for json_file in category_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            doc = json.load(f)
                            category_docs.append(doc)
                    except Exception as e:
                        print(f"Error loading {json_file}: {e}")
                all_docs[category_dir.name] = category_docs
        return all_docs

    def extract_patterns(self, docs: Dict) -> None:
        """Extract patterns and best practices from documentation"""

        # Agent patterns
        agent_patterns = self._extract_agent_patterns(docs.get('community', []))
        self.patterns.update(agent_patterns)

        # Chain patterns
        chain_patterns = self._extract_chain_patterns(docs.get('chains', []))
        self.patterns.update(chain_patterns)

        # Tool patterns
        tool_patterns = self._extract_tool_patterns(docs.get('tools', []))
        self.patterns.update(tool_patterns)

        # Core patterns
        core_patterns = self._extract_core_patterns(docs.get('core', []))
        self.patterns.update(core_patterns)

    def _extract_agent_patterns(self, docs: List[Dict]) -> Dict[str, LangChainPattern]:
        """Extract agent-specific patterns"""
        patterns = {}

        for doc in docs:
            if 'agent' in doc.get('title', '').lower():
                pattern = LangChainPattern(
                    category='agent',
                    name=doc.get('title', 'Unknown'),
                    description=self._extract_description(doc)
                )

                # Extract code examples
                if 'code_examples' in doc:
                    pattern.code_examples = doc['code_examples'][:3]

                # Extract imports
                pattern.imports = self._extract_imports(doc)

                # Extract key methods
                pattern.methods = self._extract_methods(doc)

                # Extract key concepts
                for section in doc.get('sections', []):
                    if section.get('type') == 'p':
                        pattern.key_concepts.append(section.get('content', ''))

                patterns[pattern.name] = pattern

        # Add standard agent patterns
        patterns['BaseAgent'] = LangChainPattern(
            category='agent',
            name='BaseAgent',
            description='Standard LangChain agent pattern',
            key_concepts=[
                'Agents use an LLM to determine actions',
                'Agents have access to tools',
                'Agents follow a thought-action-observation loop',
                'Agents should inherit from BaseSingleActionAgent or BaseMultiActionAgent'
            ],
            imports={'from langchain.agents import BaseSingleActionAgent',
                    'from langchain.schema import AgentAction, AgentFinish'},
            methods={'plan', 'aplan', 'return_stopped_response'}
        )

        return patterns

    def _extract_chain_patterns(self, docs: List[Dict]) -> Dict[str, LangChainPattern]:
        """Extract chain-specific patterns"""
        patterns = {}

        patterns['LLMChain'] = LangChainPattern(
            category='chain',
            name='LLMChain',
            description='Basic LangChain chain pattern',
            key_concepts=[
                'Chains combine LLMs with prompts',
                'Chains can be composed together',
                'Use invoke() for synchronous calls',
                'Use ainvoke() for async calls'
            ],
            imports={'from langchain.chains import LLMChain',
                    'from langchain.prompts import PromptTemplate'},
            methods={'invoke', 'ainvoke', 'batch', 'abatch'}
        )

        return patterns

    def _extract_tool_patterns(self, docs: List[Dict]) -> Dict[str, LangChainPattern]:
        """Extract tool-specific patterns"""
        patterns = {}

        patterns['BaseTool'] = LangChainPattern(
            category='tool',
            name='BaseTool',
            description='Standard LangChain tool pattern',
            key_concepts=[
                'Tools are functions agents can use',
                'Tools should inherit from BaseTool',
                'Tools must have name and description',
                'Tools implement _run and _arun methods'
            ],
            imports={'from langchain.tools import BaseTool',
                    'from langchain.pydantic_v1 import BaseModel, Field'},
            methods={'_run', '_arun'}
        )

        return patterns

    def _extract_core_patterns(self, docs: List[Dict]) -> Dict[str, LangChainPattern]:
        """Extract core patterns"""
        patterns = {}

        patterns['Messages'] = LangChainPattern(
            category='core',
            name='Messages',
            description='LangChain message types',
            key_concepts=[
                'Use HumanMessage for user input',
                'Use AIMessage for assistant responses',
                'Use SystemMessage for system prompts',
                'Messages can include additional kwargs'
            ],
            imports={'from langchain.schema import HumanMessage, AIMessage, SystemMessage'}
        )

        patterns['Callbacks'] = LangChainPattern(
            category='core',
            name='Callbacks',
            description='LangChain callback system',
            key_concepts=[
                'Callbacks allow hooking into chain execution',
                'Use CallbackManager for managing callbacks',
                'Implement BaseCallbackHandler for custom callbacks'
            ],
            imports={'from langchain.callbacks import CallbackManager',
                    'from langchain.callbacks.base import BaseCallbackHandler'}
        )

        return patterns

    def _extract_description(self, doc: Dict) -> str:
        """Extract description from document"""
        for section in doc.get('sections', []):
            if section.get('type') == 'p':
                return section.get('content', '')[:200]
        return 'No description available'

    def _extract_imports(self, doc: Dict) -> Set[str]:
        """Extract import statements from code examples"""
        imports = set()
        for example in doc.get('code_examples', []):
            import_matches = re.findall(r'(?:from|import)\s+[\w.]+(?:\s+import\s+[\w,\s]+)?', example)
            imports.update(import_matches)
        return imports

    def _extract_methods(self, doc: Dict) -> Set[str]:
        """Extract method names from documentation"""
        methods = set()
        for signature in doc.get('api_signatures', []):
            method_match = re.search(r'def\s+(\w+)', signature)
            if method_match:
                methods.add(method_match.group(1))
        return methods

    def analyze_existing_agents(self) -> None:
        """Analyze existing agents against LangChain patterns"""

        # Find all agent files
        agent_files = []
        for agent_dir in self.agents_dir.iterdir():
            if agent_dir.is_dir():
                for py_file in agent_dir.glob("*_agent.py"):
                    agent_files.append(py_file)

        print(f"Found {len(agent_files)} agent files to analyze")

        for agent_file in agent_files:
            analysis = self._analyze_agent_file(agent_file)
            self.agent_analyses.append(analysis)

    def _analyze_agent_file(self, file_path: Path) -> AgentAnalysis:
        """Analyze a single agent file"""
        analysis = AgentAnalysis(
            agent_name=file_path.stem,
            file_path=str(file_path)
        )

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for LangChain imports
            has_langchain = 'langchain' in content.lower()
            analysis.langchain_compatible = has_langchain

            # Check for patterns
            for pattern_name, pattern in self.patterns.items():
                if pattern.category == 'agent':
                    # Check if agent follows this pattern
                    if self._check_pattern_compliance(content, pattern):
                        analysis.follows_patterns.append(pattern_name)
                    else:
                        analysis.missing_patterns.append(pattern_name)

            # Generate recommendations
            if not has_langchain:
                analysis.recommendations.append("Consider migrating to LangChain framework")

            if 'BaseAgent' not in analysis.follows_patterns:
                analysis.recommendations.append("Implement standard LangChain agent interface")

            # Check for async support
            if 'async def' not in content:
                analysis.recommendations.append("Add async support with arun/ainvoke methods")

            # Check for proper error handling
            if 'try:' not in content or 'except' not in content:
                analysis.recommendations.append("Add comprehensive error handling")

            # Check for callbacks
            if 'callback' not in content.lower():
                analysis.recommendations.append("Implement callback support for monitoring")

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            analysis.recommendations.append(f"Error during analysis: {e}")

        return analysis

    def _check_pattern_compliance(self, content: str, pattern: LangChainPattern) -> bool:
        """Check if code follows a specific pattern"""
        compliance_score = 0
        total_checks = 0

        # Check for imports
        for imp in pattern.imports:
            total_checks += 1
            if imp in content:
                compliance_score += 1

        # Check for methods
        for method in pattern.methods:
            total_checks += 1
            if f'def {method}' in content or f'async def {method}' in content:
                compliance_score += 1

        # Consider compliant if > 50% of checks pass
        if total_checks == 0:
            return False
        return compliance_score / total_checks > 0.5

    def generate_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        report = {
            'summary': {
                'total_patterns_identified': len(self.patterns),
                'total_agents_analyzed': len(self.agent_analyses),
                'langchain_compatible_agents': sum(1 for a in self.agent_analyses if a.langchain_compatible)
            },
            'patterns': {},
            'agent_analyses': [],
            'recommendations': []
        }

        # Group patterns by category
        for pattern in self.patterns.values():
            if pattern.category not in report['patterns']:
                report['patterns'][pattern.category] = []
            report['patterns'][pattern.category].append({
                'name': pattern.name,
                'description': pattern.description,
                'key_concepts': pattern.key_concepts[:3]
            })

        # Add agent analyses
        for analysis in self.agent_analyses:
            report['agent_analyses'].append({
                'agent': analysis.agent_name,
                'file': analysis.file_path,
                'langchain_compatible': analysis.langchain_compatible,
                'follows_patterns': analysis.follows_patterns[:3],
                'missing_patterns': analysis.missing_patterns[:3],
                'recommendations': analysis.recommendations[:3]
            })

        # Generate overall recommendations
        report['recommendations'] = self._generate_overall_recommendations()

        return report

    def _generate_overall_recommendations(self) -> List[str]:
        """Generate overall project recommendations"""
        recommendations = []

        # Check overall LangChain adoption
        compatible_ratio = sum(1 for a in self.agent_analyses if a.langchain_compatible) / max(len(self.agent_analyses), 1)

        if compatible_ratio < 0.5:
            recommendations.append("Consider full migration to LangChain framework for consistency")

        recommendations.extend([
            "Implement standardized agent base class following LangChain patterns",
            "Add comprehensive tool library using LangChain tool patterns",
            "Implement chain composition for complex workflows",
            "Add callback system for monitoring and debugging",
            "Use LangChain's memory systems for conversation management",
            "Implement proper async support across all agents",
            "Add structured output parsing using LangChain output parsers",
            "Use LangChain's prompt templates for consistency"
        ])

        return recommendations

    def save_report(self, report: Dict, filename: str = "langchain_analysis_report.json"):
        """Save analysis report"""
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {filename}")

def main():
    analyzer = LangChainAnalyzer()

    print("Loading LangChain documentation...")
    docs = analyzer.load_documentation()
    print(f"Loaded documentation from {len(docs)} categories")

    print("Extracting patterns...")
    analyzer.extract_patterns(docs)
    print(f"Extracted {len(analyzer.patterns)} patterns")

    print("Analyzing existing agents...")
    analyzer.analyze_existing_agents()

    print("Generating report...")
    report = analyzer.generate_report()

    analyzer.save_report(report)

    # Print summary
    print("\n=== ANALYSIS SUMMARY ===")
    print(f"Total patterns identified: {report['summary']['total_patterns_identified']}")
    print(f"Total agents analyzed: {report['summary']['total_agents_analyzed']}")
    print(f"LangChain compatible agents: {report['summary']['langchain_compatible_agents']}")
    print("\nTop Recommendations:")
    for i, rec in enumerate(report['recommendations'][:5], 1):
        print(f"{i}. {rec}")

if __name__ == "__main__":
    main()
