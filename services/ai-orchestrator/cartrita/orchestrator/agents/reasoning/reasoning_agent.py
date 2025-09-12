"""
Advanced Reasoning Agent for Cartrita AI OS.
Handles complex problem-solving, mathematical reasoning, and deep analysis using O-series models.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

import structlog
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# ============================================
# Reasoning Models
# ============================================

class ReasoningMode(str, Enum):
    """Reasoning modes for different problem types."""
    MATHEMATICAL = "mathematical"
    LOGICAL = "logical"
    SCIENTIFIC = "scientific"
    STRATEGIC = "strategic"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    RESEARCH = "research"
    
class ComplexityLevel(str, Enum):
    """Problem complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate" 
    COMPLEX = "complex"
    EXPERT = "expert"

class ReasoningRequest(BaseModel):
    """Reasoning task request model."""
    
    problem: str = Field(..., description="Problem statement or question")
    mode: ReasoningMode = Field(ReasoningMode.ANALYTICAL, description="Reasoning mode")
    complexity: ComplexityLevel = Field(ComplexityLevel.MODERATE, description="Problem complexity")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    constraints: List[str] = Field(default_factory=list, description="Problem constraints")
    time_limit: int | None = Field(None, description="Time limit in minutes")
    step_by_step: bool = Field(True, description="Show reasoning steps")
    
class ReasoningStep(BaseModel):
    """Individual reasoning step."""
    
    step_number: int = Field(..., description="Step number")
    description: str = Field(..., description="Step description")
    reasoning: str = Field(..., description="Reasoning explanation")
    result: str | None = Field(None, description="Intermediate result")
    confidence: float = Field(..., description="Confidence in this step")
    
class ReasoningResponse(BaseModel):
    """Reasoning task response model."""
    
    solution: str = Field(..., description="Final solution or answer")
    reasoning_steps: List[ReasoningStep] = Field(default_factory=list)
    confidence_score: float = Field(..., description="Overall confidence")
    processing_time: float = Field(..., description="Processing duration")
    model_used: str = Field(..., description="Model used for reasoning")
    complexity_assessment: str = Field(..., description="Assessed problem complexity")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================
# Reasoning Agent
# ============================================

class ReasoningAgent:
    """
    Advanced Reasoning Agent using O-series models for complex problem-solving.
    
    Model Selection:
    - O3-mini: General reasoning tasks (200K TPM, 500 RPM, 2M TPD)
    - O4-mini: Most advanced reasoning (200K TPM, 500 RPM, 2M TPD) 
    - O4-mini-deep-research: Deep research analysis (200K TPM, 500 RPM, 200K TPD)
    - O1-pro: Professional-level reasoning (30K TPM, 500 RPM, 90K TPD)
    """

    def __init__(
        self,
        default_model: str | None = None,
        research_model: str | None = None, 
        pro_model: str | None = None,
        api_key: str | None = None,
    ):
        """Initialize the reasoning agent with optimal models."""
        # Get settings with proper initialization
        from cartrita.orchestrator.utils.config import get_settings
        _settings = get_settings()
        
        self.default_model = default_model or _settings.ai.reasoning_model  # o3-mini
        self.research_model = research_model or _settings.ai.deep_research_model  # o4-mini-deep-research
        self.pro_model = pro_model or "o1-pro"  # For highest complexity tasks
        self.api_key = api_key or _settings.ai.openai_api_key.get_secret_value()

        # Initialize reasoning models
        self.reasoning_llm = ChatOpenAI(
            model=self.default_model,
            temperature=0.1,  # Very low temperature for precise reasoning
            max_completion_tokens=8192,  # High token limit for detailed reasoning
            openai_api_key=self.api_key,
        )
        
        self.research_llm = ChatOpenAI(
            model=self.research_model,
            temperature=0.0,  # Zero temperature for research precision
            max_completion_tokens=16384,  # Very high limit for deep analysis
            openai_api_key=self.api_key,
        )
        
        self.pro_llm = ChatOpenAI(
            model=self.pro_model, 
            temperature=0.0,  # Zero temperature for professional reasoning
            max_completion_tokens=32768,  # Maximum tokens for complex solutions
            openai_api_key=self.api_key,
        )

        # Agent state
        self.is_active = False
        self.reasoning_history: List[Dict[str, Any]] = []
        self.performance_stats = {
            "problems_solved": 0,
            "average_confidence": 0.0,
            "total_reasoning_time": 0.0,
            "complexity_distribution": {
                "simple": 0,
                "moderate": 0, 
                "complex": 0,
                "expert": 0
            }
        }

        logger.info("Reasoning Agent initialized", 
                   default_model=self.default_model,
                   research_model=self.research_model,
                   pro_model=self.pro_model)

    async def start(self) -> None:
        """Start the reasoning agent."""
        self.is_active = True
        logger.info("Reasoning Agent started")

    async def stop(self) -> None:
        """Stop the reasoning agent."""
        self.is_active = False
        logger.info("Reasoning Agent stopped")

    async def health_check(self) -> bool:
        """Perform health check on reasoning agent."""
        return self.is_active and self.reasoning_llm is not None

    async def solve_problem(self, request: ReasoningRequest) -> ReasoningResponse:
        """Solve complex problems with appropriate model selection."""
        start_time = time.time()
        
        try:
            # Select appropriate model based on complexity and mode
            selected_model, llm = self._select_model(request)
            
            # Generate system prompt based on reasoning mode
            system_prompt = self._generate_system_prompt(request)
            
            # Create reasoning prompt
            reasoning_prompt = self._create_reasoning_prompt(request)
            
            # Execute reasoning
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": reasoning_prompt}
            ]
            
            response = await llm.ainvoke(messages)
            
            # Parse response and extract reasoning steps if requested
            reasoning_steps = []
            if request.step_by_step:
                reasoning_steps = self._extract_reasoning_steps(response.content)
            
            # Assess confidence and complexity
            confidence_score = self._assess_confidence(response.content, request)
            complexity_assessment = self._assess_complexity(request, response.content)
            
            processing_time = time.time() - start_time
            
            # Update statistics
            self._update_stats(request, confidence_score, processing_time)
            
            reasoning_response = ReasoningResponse(
                solution=response.content,
                reasoning_steps=reasoning_steps,
                confidence_score=confidence_score,
                processing_time=processing_time,
                model_used=selected_model,
                complexity_assessment=complexity_assessment,
                metadata={
                    "mode": request.mode,
                    "original_complexity": request.complexity,
                    "constraints": request.constraints,
                    "time_limit": request.time_limit
                }
            )
            
            # Store in reasoning history
            self.reasoning_history.append({
                "timestamp": time.time(),
                "request": request.dict(),
                "response": reasoning_response.dict()
            })
            
            return reasoning_response

        except Exception as e:
            logger.error("Problem solving failed", error=str(e), problem=request.problem[:100])
            raise

    def _select_model(self, request: ReasoningRequest) -> Tuple[str, ChatOpenAI]:
        """Select appropriate model based on request parameters."""
        
        # Use research model for research mode or high complexity
        if request.mode == ReasoningMode.RESEARCH or request.complexity == ComplexityLevel.EXPERT:
            if "research" in request.problem.lower():
                return self.research_model, self.research_llm
        
        # Use pro model for most complex problems
        if request.complexity == ComplexityLevel.EXPERT and request.mode in [
            ReasoningMode.MATHEMATICAL, ReasoningMode.SCIENTIFIC, ReasoningMode.STRATEGIC
        ]:
            return self.pro_model, self.pro_llm
        
        # Use default reasoning model for most cases
        return self.default_model, self.reasoning_llm

    def _generate_system_prompt(self, request: ReasoningRequest) -> str:
        """Generate system prompt based on reasoning mode."""
        
        base_prompt = "You are an advanced reasoning system designed to solve complex problems with precision and clarity."
        
        mode_prompts = {
            ReasoningMode.MATHEMATICAL: "Focus on mathematical rigor, show all calculations, and verify results. Use proper mathematical notation.",
            ReasoningMode.LOGICAL: "Apply formal logic principles. Identify premises, validate arguments, and check for logical fallacies.",
            ReasoningMode.SCIENTIFIC: "Use scientific method principles. Form hypotheses, analyze evidence, and draw evidence-based conclusions.",
            ReasoningMode.STRATEGIC: "Think strategically about goals, constraints, and trade-offs. Consider multiple scenarios and outcomes.",
            ReasoningMode.CREATIVE: "Explore innovative solutions while maintaining logical coherence. Think outside conventional approaches.",
            ReasoningMode.ANALYTICAL: "Break down complex problems into components. Analyze relationships and synthesize insights.",
            ReasoningMode.RESEARCH: "Conduct thorough analysis of available information. Cite sources and identify knowledge gaps."
        }
        
        complexity_guidance = {
            ComplexityLevel.SIMPLE: "Provide clear, concise explanations suitable for general audiences.",
            ComplexityLevel.MODERATE: "Include sufficient detail and reasoning steps for informed audiences.",
            ComplexityLevel.COMPLEX: "Provide comprehensive analysis with advanced concepts and detailed reasoning.",
            ComplexityLevel.EXPERT: "Use expert-level analysis with full technical depth and sophisticated reasoning."
        }
        
        return f"{base_prompt} {mode_prompts[request.mode]} {complexity_guidance[request.complexity]}"

    def _create_reasoning_prompt(self, request: ReasoningRequest) -> str:
        """Create detailed reasoning prompt."""
        
        prompt_parts = [
            f"Problem: {request.problem}",
        ]
        
        if request.context:
            prompt_parts.append(f"Context: {request.context}")
        
        if request.constraints:
            prompt_parts.append(f"Constraints: {', '.join(request.constraints)}")
        
        if request.time_limit:
            prompt_parts.append(f"Time limit: {request.time_limit} minutes")
        
        if request.step_by_step:
            prompt_parts.append("\nPlease show your reasoning step-by-step, including:")
            prompt_parts.append("1. Problem analysis and understanding")
            prompt_parts.append("2. Solution approach and methodology")  
            prompt_parts.append("3. Detailed reasoning steps")
            prompt_parts.append("4. Final solution and verification")
            prompt_parts.append("5. Confidence assessment and limitations")
        
        return "\n\n".join(prompt_parts)

    def _extract_reasoning_steps(self, response: str) -> List[ReasoningStep]:
        """Extract reasoning steps from response."""
        # Simple implementation - could be enhanced with better parsing
        steps = []
        lines = response.split('\n')
        
        step_num = 1
        current_step = ""
        
        for line in lines:
            if any(marker in line.lower() for marker in ['step', 'phase', 'stage', '1.', '2.', '3.']):
                if current_step:
                    steps.append(ReasoningStep(
                        step_number=step_num,
                        description=f"Step {step_num}",
                        reasoning=current_step.strip(),
                        confidence=0.8  # Default confidence
                    ))
                    step_num += 1
                current_step = line
            else:
                current_step += f"\n{line}"
        
        # Add final step
        if current_step:
            steps.append(ReasoningStep(
                step_number=step_num,
                description=f"Step {step_num}",
                reasoning=current_step.strip(),
                confidence=0.8
            ))
        
        return steps

    def _assess_confidence(self, response: str, request: ReasoningRequest) -> float:
        """Assess confidence in the reasoning and solution."""
        
        # Factors that increase confidence
        confidence_factors = {
            "has_verification": 0.1 if "verify" in response.lower() or "check" in response.lower() else 0,
            "shows_steps": 0.1 if request.step_by_step and len(response.split('\n')) > 5 else 0,
            "acknowledges_limitations": 0.1 if "limitation" in response.lower() or "assumption" in response.lower() else 0,
            "uses_examples": 0.1 if "example" in response.lower() or "instance" in response.lower() else 0,
            "mathematical_rigor": 0.1 if request.mode == ReasoningMode.MATHEMATICAL and any(
                symbol in response for symbol in ['=', '+', '-', '*', '/', '^', '∫', '∑', '∏']
            ) else 0
        }
        
        # Base confidence by complexity
        base_confidence = {
            ComplexityLevel.SIMPLE: 0.8,
            ComplexityLevel.MODERATE: 0.7,
            ComplexityLevel.COMPLEX: 0.6, 
            ComplexityLevel.EXPERT: 0.5
        }[request.complexity]
        
        # Calculate final confidence
        bonus = sum(confidence_factors.values())
        return min(1.0, base_confidence + bonus)

    def _assess_complexity(self, request: ReasoningRequest, response: str) -> str:
        """Assess the actual complexity of the solved problem."""
        
        # Analyze response characteristics
        response_length = len(response.split())
        has_math = any(symbol in response for symbol in ['=', '∫', '∑', '∏', '∂'])
        has_advanced_concepts = any(term in response.lower() for term in [
            'algorithm', 'optimization', 'probability', 'statistics', 'differential',
            'hypothesis', 'methodology', 'framework', 'paradigm'
        ])
        
        if response_length > 1000 or has_advanced_concepts:
            assessed = "Expert level - requires specialized knowledge and deep analysis"
        elif response_length > 500 or has_math:
            assessed = "Complex - involves multiple concepts and detailed reasoning"
        elif response_length > 200:
            assessed = "Moderate - requires structured thinking and analysis"
        else:
            assessed = "Simple - straightforward problem with clear solution path"
        
        return assessed

    def _update_stats(self, request: ReasoningRequest, confidence: float, processing_time: float) -> None:
        """Update performance statistics."""
        
        self.performance_stats["problems_solved"] += 1
        self.performance_stats["total_reasoning_time"] += processing_time
        self.performance_stats["complexity_distribution"][request.complexity] += 1
        
        # Update rolling average confidence
        current_avg = self.performance_stats["average_confidence"]
        total_problems = self.performance_stats["problems_solved"]
        self.performance_stats["average_confidence"] = (
            (current_avg * (total_problems - 1) + confidence) / total_problems
        )

    async def analyze_reasoning_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in reasoning history."""
        
        if not self.reasoning_history:
            return {"message": "No reasoning history available"}
        
        # Analyze common problem types, success patterns, etc.
        mode_distribution = {}
        avg_time_by_complexity = {}
        
        for entry in self.reasoning_history:
            mode = entry["request"]["mode"]
            complexity = entry["request"]["complexity"]
            processing_time = entry["response"]["processing_time"]
            
            mode_distribution[mode] = mode_distribution.get(mode, 0) + 1
            
            if complexity not in avg_time_by_complexity:
                avg_time_by_complexity[complexity] = []
            avg_time_by_complexity[complexity].append(processing_time)
        
        # Calculate averages
        for complexity in avg_time_by_complexity:
            times = avg_time_by_complexity[complexity]
            avg_time_by_complexity[complexity] = sum(times) / len(times)
        
        return {
            "total_problems_solved": len(self.reasoning_history),
            "mode_distribution": mode_distribution,
            "average_processing_time_by_complexity": avg_time_by_complexity,
            "performance_stats": self.performance_stats
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get reasoning agent capabilities and limits."""
        return {
            "models": {
                "default": self.default_model,
                "research": self.research_model,
                "professional": self.pro_model
            },
            "rate_limits": {
                "o3_mini": "200K TPM, 500 RPM, 2M TPD",
                "o4_mini": "200K TPM, 500 RPM, 2M TPD",
                "o4_mini_deep_research": "200K TPM, 500 RPM, 200K TPD",
                "o1_pro": "30K TPM, 500 RPM, 90K TPD"
            },
            "reasoning_modes": [mode.value for mode in ReasoningMode],
            "complexity_levels": [level.value for level in ComplexityLevel],
            "capabilities": [
                "mathematical_problem_solving",
                "logical_reasoning", 
                "scientific_analysis",
                "strategic_planning",
                "creative_problem_solving",
                "deep_research_analysis",
                "step_by_step_reasoning",
                "confidence_assessment",
                "pattern_analysis"
            ],
            "statistics": self.performance_stats
        }