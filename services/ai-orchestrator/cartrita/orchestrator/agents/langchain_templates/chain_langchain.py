"""
LangChain Chain Template for Cartrita
Implements chain patterns for composable workflows
"""

from typing import Any, Dict, List, Optional
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import BasePromptTemplate
from langchain.callbacks.manager import CallbackManagerForChainRun, AsyncCallbackManagerForChainRun
from langchain.base_language import BaseLanguageModel
from pydantic import BaseModel, Field

class CartritaChain(LLMChain):
    """Custom chain for Cartrita following LangChain patterns"""

    chain_type: str = Field(default="cartrita", description="Chain type identifier")

    @classmethod
    def from_prompt(
        cls,
        llm: BaseLanguageModel,
        prompt: BasePromptTemplate,
        **kwargs: Any
    ) -> "CartritaChain":
        """Create chain from prompt template"""
        return cls(llm=llm, prompt=prompt, **kwargs)

    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """Execute the chain"""
        # Log chain execution
        if run_manager:
            run_manager.on_text(f"Executing {self.chain_type} chain\n")

        # Prepare inputs
        prompt_value = self.prompt.format_prompt(**inputs)

        # Execute LLM
        if run_manager:
            response = self.llm.generate_prompt(
                [prompt_value],
                callbacks=run_manager.get_child()
            )
        else:
            response = self.llm.generate_prompt([prompt_value])

        # Extract output
        output = self.output_parser.parse(response.generations[0][0].text)

        # Log output
        if run_manager:
            run_manager.on_text(f"Chain output: {output}\n", color="green")

        return {self.output_key: output}

    async def _acall(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[AsyncCallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """Async execute the chain"""
        if run_manager:
            await run_manager.on_text(f"Executing {self.chain_type} chain\n")

        prompt_value = self.prompt.format_prompt(**inputs)

        if run_manager:
            response = await self.llm.agenerate_prompt(
                [prompt_value],
                callbacks=run_manager.get_child()
            )
        else:
            response = await self.llm.agenerate_prompt([prompt_value])

        output = self.output_parser.parse(response.generations[0][0].text)

        if run_manager:
            await run_manager.on_text(f"Chain output: {output}\n", color="green")

        return {self.output_key: output}

    @property
    def _chain_type(self) -> str:
        """Return chain type"""
        return self.chain_type

class CartritaSequentialChain:
    """Sequential chain for multi-step workflows"""

    def __init__(self, chains: List[LLMChain], **kwargs):
        self.chains = chains
        self.return_all = kwargs.get("return_all", False)

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run chains sequentially"""
        results = {}
        current_inputs = inputs.copy()

        for i, chain in enumerate(self.chains):
            output = chain.run(current_inputs)

            if self.return_all:
                results[f"step_{i}"] = output

            # Update inputs for next chain
            current_inputs.update(output)

        if self.return_all:
            return results
        return output

    async def arun(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Async run chains sequentially"""
        results = {}
        current_inputs = inputs.copy()

        for i, chain in enumerate(self.chains):
            output = await chain.arun(current_inputs)

            if self.return_all:
                results[f"step_{i}"] = output

            current_inputs.update(output)

        if self.return_all:
            return results
        return output
