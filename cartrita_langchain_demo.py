
# Cartrita LangChain Integration Demo
# This shows how to use the LangChain integration in your existing system

import os
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain.agents import initialize_agent, Tool

class CartritaLangChainIntegration:
    """Integration class for Cartrita AI OS"""

    def __init__(self):
        # Initialize with your credentials
        self.openai_llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7
        )

        # Could also initialize Hugging Face here
        self.current_provider = "openai"

    def simple_chat(self, message: str) -> str:
        """Simple chat interface"""
        response = self.openai_llm.invoke([HumanMessage(content=message)])
        return response.content

    def chat_with_tools(self, message: str, tools: list = None) -> str:
        """Chat with tool usage"""
        if tools:
            agent = initialize_agent(
                tools=tools,
                llm=self.openai_llm,
                verbose=True
            )
            return agent.run(message)
        else:
            return self.simple_chat(message)

    def switch_provider(self, provider: str):
        """Switch between providers"""
        if provider == "huggingface":
            # Initialize Hugging Face provider
            pass
        self.current_provider = provider

# Usage example:
# cartrita_ai = CartritaLangChainIntegration()
# response = cartrita_ai.simple_chat("Hello, how are you?")
# print(response)
