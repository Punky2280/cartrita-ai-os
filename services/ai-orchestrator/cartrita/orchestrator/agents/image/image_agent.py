"""
Image Processing Agent for Cartrita AI OS.
Handles image generation, analysis, and vision tasks using DALL-E and GPT-Image models.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
import base64
from io import BytesIO

import structlog
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# ============================================
# Image Models
# ============================================

class ImageRequest(BaseModel):
    """Image processing request model."""
    
    prompt: str | None = Field(None, description="Text prompt for generation/analysis")
    image_data: bytes | None = Field(None, description="Raw image data")
    image_url: str | None = Field(None, description="Image URL")
    task_type: str = Field(..., description="Type of image task")
    size: str = Field("1024x1024", description="Image size for generation")
    quality: str = Field("standard", description="Image quality (standard/hd)")
    style: str = Field("natural", description="Image style (natural/vivid)")
    n: int = Field(1, description="Number of images to generate")
    
class ImageResponse(BaseModel):
    """Image processing response model."""
    
    result: str | bytes | List[str] = Field(..., description="Processing result")
    task_type: str = Field(..., description="Type of task performed")
    processing_time: float = Field(..., description="Processing duration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    urls: List[str] = Field(default_factory=list, description="Generated image URLs")


# ============================================
# Image Agent
# ============================================

class ImageAgent:
    """
    Image Agent using DALL-E and GPT-Image for comprehensive visual processing.
    
    Capabilities:
    - High-quality image generation (DALL-E 3: 500 RPM, 5 images/min)
    - Image analysis and understanding (GPT-Image: 100K TPM, 5 images/min)
    - Visual content creation
    - Image editing and manipulation
    - Multi-modal visual reasoning
    """

    def __init__(
        self,
        vision_model: str | None = None,
        generation_model: str = "dall-e-3",
        api_key: str | None = None,
    ):
        """Initialize the image agent with optimal models."""
        # Get settings with proper initialization
        from cartrita.orchestrator.utils.config import get_settings
        _settings = get_settings()
        
        # Use gpt-image-1 for vision tasks (100K TPM, 5 images/min)
        self.vision_model = vision_model or "gpt-image-1"
        self.generation_model = generation_model  # dall-e-3 for high quality
        self.api_key = api_key or _settings.ai.openai_api_key.get_secret_value()

        # Initialize vision model for image analysis
        self.vision_llm = ChatOpenAI(
            model=self.vision_model,
            temperature=0.2,  # Low temperature for accurate analysis
            max_completion_tokens=4096,
            openai_api_key=self.api_key,
        )

        # Agent state
        self.is_active = False
        self.generation_queue: List[Dict[str, Any]] = []
        self.processing_stats = {
            "images_generated": 0,
            "images_analyzed": 0,
            "total_processing_time": 0.0
        }

        logger.info("Image Agent initialized", 
                   vision_model=self.vision_model,
                   generation_model=self.generation_model)

    async def start(self) -> None:
        """Start the image agent."""
        self.is_active = True
        logger.info("Image Agent started")

    async def stop(self) -> None:
        """Stop the image agent."""
        self.is_active = False
        logger.info("Image Agent stopped")

    async def health_check(self) -> bool:
        """Perform health check on image agent."""
        return self.is_active and self.vision_llm is not None

    async def process_image(self, request: ImageRequest) -> ImageResponse:
        """Process image request with appropriate model selection."""
        start_time = time.time()
        
        try:
            # Route to appropriate processing method based on task type
            if request.task_type == "generate":
                result = await self._generate_image(request)
                self.processing_stats["images_generated"] += 1
            elif request.task_type == "analyze":
                result = await self._analyze_image(request)
                self.processing_stats["images_analyzed"] += 1
            elif request.task_type == "edit":
                result = await self._edit_image(request)
            elif request.task_type == "describe":
                result = await self._describe_image(request)
                self.processing_stats["images_analyzed"] += 1
            elif request.task_type == "compare":
                result = await self._compare_images(request)
                self.processing_stats["images_analyzed"] += 1
            else:
                raise ValueError(f"Unsupported task type: {request.task_type}")

            processing_time = time.time() - start_time
            self.processing_stats["total_processing_time"] += processing_time
            
            return ImageResponse(
                result=result,
                task_type=request.task_type,
                processing_time=processing_time,
                metadata={
                    "model_used": self.vision_model if "analyze" in request.task_type else self.generation_model,
                    "quality": request.quality,
                    "size": request.size,
                    "style": request.style
                }
            )

        except Exception as e:
            logger.error("Image processing failed", error=str(e), task_type=request.task_type)
            raise

    async def _generate_image(self, request: ImageRequest) -> List[str]:
        """Generate images using DALL-E models."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            
            # Use DALL-E 3 for high quality or DALL-E 2 for faster generation
            response = await client.images.generate(
                model=self.generation_model,
                prompt=request.prompt,
                size=request.size,
                quality=request.quality,
                style=request.style,
                n=min(request.n, 5),  # Respect rate limits
                response_format="url"
            )
            
            urls = [image.url for image in response.data]
            logger.info("Generated images", count=len(urls), model=self.generation_model)
            return urls
            
        except Exception as e:
            logger.error("Image generation failed", error=str(e))
            raise

    async def _analyze_image(self, request: ImageRequest) -> str:
        """Analyze image content using GPT-Image."""
        try:
            if not request.image_data and not request.image_url:
                raise ValueError("No image data or URL provided for analysis")
            
            # Prepare image for vision model
            if request.image_data:
                # Convert bytes to base64 for API
                image_b64 = base64.b64encode(request.image_data).decode('utf-8')
                image_url = f"data:image/jpeg;base64,{image_b64}"
            else:
                image_url = request.image_url

            # Add temporal awareness for context
            from datetime import datetime
            import pytz
            
            miami_tz = pytz.timezone('America/New_York')
            current_time = datetime.now(miami_tz).strftime('%A, %B %d, %Y at %I:%M %p %Z')
            
            analysis_prompt = request.prompt or f"""# IMAGE ANALYSIS - CARTRITA AI OS 🖼️

You are Cartrita's specialized Image Agent with advanced visual intelligence capabilities.

## CORE IDENTITY
- **Agent Type**: Image Analysis & Generation Specialist
- **Models**: GPT-4o Vision + DALL-E 3 Generation
- **Capabilities**: Visual analysis, image generation, artistic creation
- **Current Time**: {current_time} - Consider temporal context for relevance

## ANALYSIS FRAMEWORK
Analyze this image comprehensively using this structure:

### 🎯 **Visual Summary** (2-3 sentences)
[Key elements and overall scene description]

### 🖼️ **Technical Assessment**
- **Composition**: Rule of thirds, balance, focal points
- **Lighting**: Type, direction, mood, shadows
- **Color Palette**: Dominant colors, harmony, temperature
- **Quality**: Resolution, clarity, artistic technique

### 📝 **Content Analysis**
- **Main Subjects**: People, objects, landmarks
- **Setting**: Location, environment, context
- **Text/Signs**: Any visible text or symbols
- **Actions**: What's happening in the scene

### 🎭 **Emotional & Aesthetic**
- **Mood**: Feeling conveyed by the image
- **Style**: Artistic approach, genre, influences
- **Impact**: Visual effectiveness, memorable elements

### 💡 **Contextual Insights**
[Cultural references, historical significance, or practical applications]

## PERSONALITY TOUCH
- Use brief Miami/visual metaphors when natural ("This composition flows like Ocean Drive")
- Professional expertise with warmth
- Enthusiastic about artistic discoveries
- Clear about what you can and cannot determine

Remember: You're providing professional-grade visual analysis that Cartrita can trust and use for decision-making."""

            # Use vision model for image analysis
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": analysis_prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ]
            
            response = await self.vision_llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logger.error("Image analysis failed", error=str(e))
            raise

    async def _describe_image(self, request: ImageRequest) -> str:
        """Generate detailed description of image."""
        description_prompt = """
        Provide a detailed, natural description of this image as if describing it to someone who cannot see it.
        Include:
        - What you see in the image
        - The setting and environment
        - People, objects, and their relationships
        - Actions or activities taking place
        - Notable details or interesting elements
        """
        
        # Use the analyze function with a description-specific prompt
        request.prompt = description_prompt
        return await self._analyze_image(request)

    async def _edit_image(self, request: ImageRequest) -> str:
        """Edit image using DALL-E edit capabilities."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            
            # Note: DALL-E edit requires image + mask + prompt
            # This is a placeholder for the edit functionality
            if not request.image_data:
                raise ValueError("Image data required for editing")
            
            # For now, return a message about edit capabilities
            return "Image editing functionality requires additional implementation of mask handling and edit-specific prompts."
            
        except Exception as e:
            logger.error("Image editing failed", error=str(e))
            raise

    async def _compare_images(self, request: ImageRequest) -> str:
        """Compare multiple images."""
        compare_prompt = request.prompt or """
        Compare these images and provide:
        - Similarities and differences
        - Which image might be better for specific purposes
        - Quality assessment
        - Compositional analysis
        - Any notable observations
        """
        
        # This would require multiple image inputs
        # For now, use single image analysis
        request.prompt = compare_prompt
        return await self._analyze_image(request)

    async def batch_generate(
        self, 
        prompts: List[str], 
        **kwargs
    ) -> List[ImageResponse]:
        """Generate multiple images with rate limit handling."""
        results = []
        
        for i, prompt in enumerate(prompts):
            try:
                request = ImageRequest(
                    prompt=prompt,
                    task_type="generate",
                    **kwargs
                )
                
                response = await self.process_image(request)
                results.append(response)
                
                # Rate limiting: DALL-E 3 has 5 images per minute limit
                if i < len(prompts) - 1:  # Don't delay after last image
                    await asyncio.sleep(12)  # 12 seconds between requests
                    
            except Exception as e:
                logger.error(f"Batch generation failed for prompt {i}", error=str(e))
                results.append(None)
        
        return results

    async def analyze_batch(
        self, 
        images: List[Tuple[bytes, str]], 
        prompt: str | None = None
    ) -> List[ImageResponse]:
        """Analyze multiple images."""
        results = []
        
        for i, (image_data, image_name) in enumerate(images):
            try:
                request = ImageRequest(
                    image_data=image_data,
                    prompt=prompt,
                    task_type="analyze"
                )
                
                response = await self.process_image(request)
                response.metadata["image_name"] = image_name
                results.append(response)
                
            except Exception as e:
                logger.error(f"Batch analysis failed for image {image_name}", error=str(e))
                results.append(None)
        
        return results

    def get_capabilities(self) -> Dict[str, Any]:
        """Get image agent capabilities and limits."""
        return {
            "models": {
                "vision": self.vision_model,
                "generation": self.generation_model
            },
            "rate_limits": {
                "dall_e_3": "500 RPM, 5 images per minute",
                "dall_e_2": "500 RPM, 5 images per minute", 
                "gpt_image_1": "100K TPM, 5 images per minute"
            },
            "capabilities": [
                "high_quality_image_generation",
                "detailed_image_analysis",
                "visual_reasoning",
                "image_description", 
                "content_moderation",
                "batch_processing"
            ],
            "generation_sizes": [
                "1024x1024", "1792x1024", "1024x1792"
            ],
            "generation_qualities": [
                "standard", "hd"
            ],
            "generation_styles": [
                "natural", "vivid"
            ],
            "supported_formats": [
                "jpg", "png", "webp", "gif"
            ],
            "statistics": self.processing_stats
        }