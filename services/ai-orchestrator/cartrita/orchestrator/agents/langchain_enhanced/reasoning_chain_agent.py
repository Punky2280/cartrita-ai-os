"""
Advanced Reasoning Chain Agent with LangChain
Implements chain-of-thought reasoning using LangChain patterns
"""

@dataclass
class TaskRequirements:
    """Requirements for a specific task"""
    complexity: TaskComplexity
    max_cost: float
    max_latency: float  # seconds
    quality_threshold: float  # 0-1 scale
    requires_function_calling: bool = False
    requires_streaming: bool = False
    domain_expertise: List[str] = field(default_factory=list)


import asyncio
from typing import Any, Dict, List, Optional, Sequence, Union
from enum import Enum

from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.schema import BaseOutputParser, OutputParserException
from langchain.callbacks.manager import CallbackManagerForChainRun
from cartrita.orchestrator.utils.llm_factory import create_chat_openai
from langchain.memory import ConversationBufferWindowMemory
from pydantic import BaseModel, Field
from langchain.pydantic_v1 import BaseModel as LangChainBaseModel, Field as LangChainField, validator
import json
import re


class ReasoningStep(BaseModel):
    """Individual reasoning step"""
    step_number: int = Field(description="Step number in reasoning chain")
    question: str = Field(description="Question or problem to address")
    approach: str = Field(description="Reasoning approach")
    analysis: str = Field(description="Detailed analysis")
    conclusion: str = Field(description="Step conclusion")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence level")
    dependencies: List[int] = Field(default_factory=list, description="Dependent step numbers")


class ReasoningResult(BaseModel):
    """Complete reasoning result"""
    query: str = Field(description="Original query")
    reasoning_chain: List[ReasoningStep] = Field(description="Chain of reasoning steps")
    final_answer: str = Field(description="Final synthesized answer")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Overall confidence")
    reasoning_time: float = Field(description="Time taken for reasoning")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Token usage stats")


class ReasoningType(str, Enum):
    """Types of reasoning approaches"""
    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    ANALOGICAL = "analogical"
    CAUSAL = "causal"
    PROBABILISTIC = "probabilistic"


class ReasoningOutputParser(BaseOutputParser[ReasoningStep]):
    """Parser for reasoning step outputs"""

    def parse(self, text: str) -> ReasoningStep:
        """Parse LLM output into ReasoningStep"""
        try:
            # Try to parse as JSON first
            if text.strip().startswith('{'):
                data = json.loads(text)
                return ReasoningStep(**data)

            # Parse structured text format
            lines = text.strip().split('\n')
            parsed_data = {
                "step_number": 1,
                "question": "",
                "approach": "",
                "analysis": "",
                "conclusion": "",
                "confidence": 0.8
            }

            current_field = None
            for line in lines:
                line = line.strip()
                if line.startswith("Step:"):
                    parsed_data["step_number"] = int(re.findall(r'\d+', line)[0])
                elif line.startswith("Question:"):
                    current_field = "question"
                    parsed_data["question"] = line.replace("Question:", "").strip()
                elif line.startswith("Approach:"):
                    current_field = "approach"
                    parsed_data["approach"] = line.replace("Approach:", "").strip()
                elif line.startswith("Analysis:"):
                    current_field = "analysis"
                    parsed_data["analysis"] = line.replace("Analysis:", "").strip()
                elif line.startswith("Conclusion:"):
                    current_field = "conclusion"
                    parsed_data["conclusion"] = line.replace("Conclusion:", "").strip()
                elif line.startswith("Confidence:"):
                    conf_match = re.findall(r'0?\.\d+|[01]\.?\d*', line)
                    if conf_match:
                        parsed_data["confidence"] = float(conf_match[0])
                elif current_field and line:
                    # Continue previous field content
                    parsed_data[current_field] += " " + line

            return ReasoningStep(**parsed_data)

        except Exception as e:
            raise OutputParserException(f"Failed to parse reasoning step: {e}")

    @property
    def _type(self) -> str:
        return "reasoning_step"


class ReasoningChainAgent:
    """
    Advanced reasoning agent using LangChain chain patterns
    Implements sophisticated reasoning workflows with:
    - Chain-of-thought reasoning
    - Multiple reasoning strategies
    - Step validation and backtracking
    - Confidence tracking
    - Memory integration
    """

    def __init__(
        self,
        llm: Optional[Any] = None,
        max_reasoning_steps: int = 10,
        confidence_threshold: float = 0.7,
        enable_backtracking: bool = True,
        reasoning_types: Optional[List[ReasoningType]] = None,
        **kwargs
    ):
        # Initialize LLM
        self.llm = llm or create_chat_openai(
            model="gpt-4o",
            temperature=0.2,
            max_tokens=2048
        )

        # Configuration
        self.max_reasoning_steps = max_reasoning_steps
        self.confidence_threshold = confidence_threshold
        self.enable_backtracking = enable_backtracking
        self.reasoning_types = reasoning_types or [
            ReasoningType.DEDUCTIVE,
            ReasoningType.INDUCTIVE,
            ReasoningType.CAUSAL
        ]

        # Memory for conversation context
        self.memory = ConversationBufferWindowMemory(
            k=5,
            memory_key="chat_history",
            return_messages=True
        )

        # Initialize reasoning chains
        self._initialize_chains()

    def _initialize_chains(self):
        """Initialize reasoning chains"""

        # Problem analysis chain
        self.problem_analysis_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["query", "context"],
                template="""Analyze the following problem/query for reasoning:

Query: {query}
Context: {context}

Provide:
1. Problem type identification
2. Key components and variables
3. Required reasoning approach(es)
4. Potential challenges
5. Success criteria

Analysis:"""
            ),
            output_key="problem_analysis"
        )

        # Reasoning step chain
        self.reasoning_step_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["query", "previous_steps", "step_number", "reasoning_type"],
                template="""Perform reasoning step {step_number} using {reasoning_type} reasoning:

Original Query: {query}
Previous Steps: {previous_steps}

For this step, provide a structured analysis:

Step: {step_number}
Question: [What specific question does this step address?]
Approach: [What reasoning method will you use?]
Analysis: [Detailed step-by-step analysis]
Conclusion: [What can you conclude from this step?]
Confidence: [Your confidence level 0.0-1.0]

Step Analysis:"""
            ),
            output_key="reasoning_step",
            output_parser=ReasoningOutputParser()
        )

        # Synthesis chain
        self.synthesis_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["query", "reasoning_steps", "step_conclusions"],
                template="""Synthesize the reasoning chain into a final answer:

Original Query: {query}

Reasoning Steps:
{reasoning_steps}

Step Conclusions:
{step_conclusions}

Provide:
1. Final Answer: [Comprehensive answer to the original query]
2. Confidence Score: [Overall confidence 0.0-1.0]
3. Key Supporting Evidence: [Main evidence from reasoning chain]
4. Limitations: [Any limitations or uncertainties]

Final Synthesis:"""
            ),
            output_key="final_synthesis"
        )

        # Validation chain
        self.validation_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["query", "reasoning_step", "previous_context"],
                template="""Validate the following reasoning step for logical consistency:

Original Query: {query}
Previous Context: {previous_context}
Current Step: {reasoning_step}

Validation Criteria:
1. Logical consistency with previous steps
2. Relevance to the original query
3. Soundness of reasoning approach
4. Appropriate confidence level
5. Clarity and completeness

Provide:
- Valid: [Yes/No]
- Issues: [List any logical issues found]
- Suggestions: [Improvements or corrections]

Validation Result:"""
            ),
            output_key="validation_result"
        )

    async def reason(
        self,
        query: str,
        context: Optional[str] = None,
        reasoning_type: Optional[ReasoningType] = None,
        callbacks: Optional[Any] = None
    ) -> ReasoningResult:
        """
        Perform comprehensive reasoning on a query

        Args:
            query: The question or problem to reason about
            context: Additional context for reasoning
            reasoning_type: Specific reasoning approach to use
            callbacks: Callback manager for monitoring

        Returns:
            Complete reasoning result with chain of thought
        """
        import time
        start_time = time.time()

        # Initialize result
        result = ReasoningResult(
            query=query,
            reasoning_chain=[],
            final_answer="",
            confidence_score=0.0,
            reasoning_time=0.0
        )

        try:
            # Step 1: Analyze the problem
            problem_analysis = await self._analyze_problem(query, context or "", callbacks)

            # Step 2: Determine reasoning approach
            if not reasoning_type:
                reasoning_type = self._select_reasoning_type(problem_analysis)

            # Step 3: Perform iterative reasoning
            reasoning_steps = await self._perform_reasoning_chain(
                query, reasoning_type, callbacks
            )
            result.reasoning_chain = reasoning_steps

            # Step 4: Synthesize final answer
            final_answer, confidence = await self._synthesize_answer(
                query, reasoning_steps, callbacks
            )
            result.final_answer = final_answer
            result.confidence_score = confidence

            # Step 5: Update memory
            self._update_memory(query, result)

        except Exception as e:
            result.final_answer = f"Reasoning failed: {str(e)}"
            result.confidence_score = 0.0

        result.reasoning_time = time.time() - start_time
        return result

    async def _analyze_problem(
        self, query: str, context: str, callbacks: Optional[Any] = None
    ) -> str:
        """Analyze the problem structure"""
        return await self.problem_analysis_chain.arun(
            query=query,
            context=context,
            callbacks=callbacks
        )

    def _select_reasoning_type(self, analysis: str) -> ReasoningType:
        """Select appropriate reasoning type based on analysis"""
        analysis_lower = analysis.lower()

        if any(word in analysis_lower for word in ["cause", "effect", "because", "leads to"]):
            return ReasoningType.CAUSAL
        elif any(word in analysis_lower for word in ["pattern", "trend", "examples", "observe"]):
            return ReasoningType.INDUCTIVE
        elif any(word in analysis_lower for word in ["rule", "principle", "logic", "follows"]):
            return ReasoningType.DEDUCTIVE
        elif any(word in analysis_lower for word in ["similar", "like", "compare", "analogy"]):
            return ReasoningType.ANALOGICAL
        elif any(word in analysis_lower for word in ["probable", "likely", "chance", "odds"]):
            return ReasoningType.PROBABILISTIC
        else:
            return ReasoningType.ABDUCTIVE  # Best explanation

    async def _perform_reasoning_chain(
        self,
        query: str,
        reasoning_type: ReasoningType,
        callbacks: Optional[Any] = None
    ) -> List[ReasoningStep]:
        """Perform iterative reasoning steps"""
        reasoning_steps = []
        previous_steps_text = ""

        for step_num in range(1, self.max_reasoning_steps + 1):
            try:
                # Generate reasoning step
                step_result = await self.reasoning_step_chain.arun(
                    query=query,
                    previous_steps=previous_steps_text,
                    step_number=step_num,
                    reasoning_type=reasoning_type.value,
                    callbacks=callbacks
                )

                # Validate step if enabled
                if self.enable_backtracking:
                    is_valid = await self._validate_reasoning_step(
                        query, step_result, previous_steps_text, callbacks
                    )
                    if not is_valid and step_num > 1:
                        # Try alternative approach
                        step_result = await self._retry_reasoning_step(
                            query, previous_steps_text, step_num, callbacks
                        )

                reasoning_steps.append(step_result)

                # Update previous steps context
                previous_steps_text += f"\nStep {step_num}: {step_result.conclusion}"

                # Check if we should continue
                if (step_result.confidence >= self.confidence_threshold and
                    "final" in step_result.conclusion.lower()):
                    break

                # Check for natural stopping points
                if self._should_stop_reasoning(reasoning_steps):
                    break

            except Exception as e:
                print(f"Error in reasoning step {step_num}: {e}")
                break

        return reasoning_steps

    async def _validate_reasoning_step(
        self,
        query: str,
        step: ReasoningStep,
        context: str,
        callbacks: Optional[Any] = None
    ) -> bool:
        """Validate a reasoning step"""
        try:
            validation = await self.validation_chain.arun(
                query=query,
                reasoning_step=step.model_dump_json(),
                previous_context=context,
                callbacks=callbacks
            )
            return "Valid: Yes" in validation or "valid: yes" in validation.lower()
        except:
            return True  # Default to valid if validation fails

    async def _retry_reasoning_step(
        self,
        query: str,
        context: str,
        step_num: int,
        callbacks: Optional[Any] = None
    ) -> ReasoningStep:
        """Retry reasoning step with alternative approach"""
        # Use a different reasoning type for retry
        alternative_types = [t for t in self.reasoning_types
                           if t != ReasoningType.DEDUCTIVE]
        retry_type = alternative_types[0] if alternative_types else ReasoningType.ABDUCTIVE

        return await self.reasoning_step_chain.arun(
            query=query,
            previous_steps=context + "\n[Previous attempt had issues, trying alternative approach]",
            step_number=step_num,
            reasoning_type=retry_type.value,
            callbacks=callbacks
        )

    def _should_stop_reasoning(self, steps: List[ReasoningStep]) -> bool:
        """Determine if reasoning should stop"""
        if not steps:
            return False

        # Stop if last step has high confidence and conclusion indicates completion
        last_step = steps[-1]
        if (last_step.confidence >= 0.9 and
            any(word in last_step.conclusion.lower()
                for word in ["therefore", "thus", "final", "conclude"])):
            return True

        # Stop if we're going in circles (repeated conclusions)
        if len(steps) >= 3:
            recent_conclusions = [step.conclusion.lower()[:50] for step in steps[-3:]]
            if len(set(recent_conclusions)) == 1:  # All identical
                return True

        return False

    async def _synthesize_answer(
        self,
        query: str,
        steps: List[ReasoningStep],
        callbacks: Optional[Any] = None
    ) -> tuple[str, float]:
        """Synthesize final answer from reasoning steps"""
        if not steps:
            return "No reasoning steps completed", 0.0

        # Format reasoning steps
        steps_text = "\n".join([
            f"Step {step.step_number}: {step.conclusion}"
            for step in steps
        ])

        # Format step conclusions
        conclusions_text = "\n".join([
            f"- {step.conclusion} (confidence: {step.confidence:.2f})"
            for step in steps
        ])

        # Generate synthesis
        synthesis = await self.synthesis_chain.arun(
            query=query,
            reasoning_steps=steps_text,
            step_conclusions=conclusions_text,
            callbacks=callbacks
        )

        # Extract final answer and confidence
        lines = synthesis.split('\n')
        final_answer = synthesis
        confidence = sum(step.confidence for step in steps) / len(steps)

        # Try to extract structured output
        for line in lines:
            if line.startswith("Final Answer:"):
                final_answer = line.replace("Final Answer:", "").strip()
            elif line.startswith("Confidence Score:"):
                try:
                    confidence = float(re.findall(r'0?\.\d+|[01]\.?\d*', line)[0])
                except:
                    pass

        return final_answer, confidence

    def _update_memory(self, query: str, result: ReasoningResult):
        """Update conversation memory"""
        self.memory.save_context(
            {"input": query},
            {"output": result.final_answer}
        )

    # Synchronous interface
    def reason_sync(self, query: str, **kwargs) -> ReasoningResult:
        """Synchronous reasoning interface"""
        return asyncio.run(self.reason(query, **kwargs))

    def get_reasoning_stats(self) -> Dict[str, Any]:
        """Get reasoning performance statistics"""
        return {
            "max_steps": self.max_reasoning_steps,
            "confidence_threshold": self.confidence_threshold,
            "backtracking_enabled": self.enable_backtracking,
            "supported_reasoning_types": [t.value for t in self.reasoning_types],
            "memory_length": len(self.memory.chat_memory.messages) if self.memory else 0
        }