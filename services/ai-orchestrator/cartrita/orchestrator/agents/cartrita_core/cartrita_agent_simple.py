"""
Simple CartritaAgent for backward compatibility
"""


class CartritaAgent:
    """Simple Cartrita agent for backward compatibility"""

    def __init__(self, **kwargs):
        self.name = "cartrita"
        self.description = "Simple Cartrita agent"

    def process_request(self, request: str) -> str:
        return f"Processed: {request}"

    async def aprocess_request(self, request: str) -> str:
        return self.process_request(request)
