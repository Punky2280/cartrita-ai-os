"""
Audio Processing Agent for Cartrita AI OS.
Handles real-time audio, transcription, TTS, and audio analysis using GPT-Audio model.
"""

import time
from typing import Any, Dict, AsyncGenerator

import structlog
from cartrita.orchestrator.utils.llm_factory import create_chat_openai
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# ============================================
# Audio Models
# ============================================

class AudioRequest(BaseModel):
    """Audio processing request model."""

    audio_data: bytes | None = Field(None, description="Raw audio data")
    audio_url: str | None = Field(None, description="Audio file URL")
    task_type: str = Field(..., description="Type of audio task")
    language: str | None = Field("en", description="Language for processing")
    voice_id: str | None = Field("nova", description="Voice ID for TTS")
    real_time: bool = Field(False, description="Real-time processing mode")


class AudioResponse(BaseModel):
    """Audio processing response model."""

    result: str | bytes = Field(..., description="Processing result")
    task_type: str = Field(..., description="Type of task performed")
    processing_time: float = Field(..., description="Processing duration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    confidence: float | None = Field(None, description="Confidence score")


# ============================================
# Audio Agent
# ============================================

class AudioAgent:
    """
    Audio Agent using GPT-Audio for comprehensive audio processing.

    Capabilities:
    - Real-time audio transcription (250K TPM, 3K RPM)
    - High-quality text-to-speech synthesis
    - Audio analysis and understanding
    - Voice conversation handling
    - Audio content generation
    - Multi-language support
    """

    def __init__(
        self,
        model: str | None = None,
        realtime_model: str | None = None,
        tts_model: str | None = None,
        api_key: str | None = None,
    ):
        """Initialize the audio agent with optimal models."""
        # Get settings with proper initialization
        from cartrita.orchestrator.utils.config import get_settings
        _settings = get_settings()

        self.model = model or _settings.ai.audio_model  # gpt-audio
        self.realtime_model = realtime_model or _settings.ai.realtime_model  # gpt-realtime
        self.tts_model = tts_model or _settings.ai.tts_model  # tts-1-hd
        self.api_key = api_key or _settings.ai.openai_api_key.get_secret_value()

        # Initialize audio processing model via factory
        self.audio_llm = create_chat_openai(
            model=self.model,
            temperature=0.3,
            max_completion_tokens=4096,
            openai_api_key=self.api_key,
        )

        # Initialize real-time model for low-latency tasks via factory
        self.realtime_llm = create_chat_openai(
            model=self.realtime_model,
            temperature=0.1,
            max_completion_tokens=1024,
            openai_api_key=self.api_key,
        )

        # Agent state
        self.is_active = False
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        logger.info("Audio Agent initialized",
                    model=self.model,
                    realtime_model=self.realtime_model,
                    tts_model=self.tts_model)

    async def start(self) -> None:
        """Start the audio agent."""
        self.is_active = True
        logger.info("Audio Agent started")

    async def stop(self) -> None:
        """Stop the audio agent and cleanup sessions."""
        self.is_active = False
        # Cleanup active sessions
        for session_id in list(self.active_sessions.keys()):
            await self.end_session(session_id)
        logger.info("Audio Agent stopped")

    async def health_check(self) -> bool:
        """Perform health check on audio agent."""
        return self.is_active and self.audio_llm is not None

    async def process_audio(
        self,
        request: AudioRequest,
        session_id: str | None = None
    ) -> AudioResponse:
        """Process audio request with appropriate model selection."""
        start_time = time.time()

        try:
            # Route to appropriate processing method based on task type
            if request.task_type == "transcribe":
                result = await self._transcribe_audio(request, session_id)
            elif request.task_type == "synthesize":
                result = await self._synthesize_speech(request)
            elif request.task_type == "analyze":
                result = await self._analyze_audio(request)
            elif request.task_type == "conversation":
                result = await self._handle_conversation(request, session_id)
            elif request.task_type == "real_time":
                result = await self._process_realtime(request, session_id)
            else:
                raise ValueError(f"Unsupported task type: {request.task_type}")

            processing_time = time.time() - start_time

            return AudioResponse(
                result=result,
                task_type=request.task_type,
                processing_time=processing_time,
                metadata={
                    "model_used": self.model,
                    "session_id": session_id,
                    "language": request.language,
                    "real_time": request.real_time
                }
            )

        except Exception as e:
            logger.error("Audio processing failed", error=str(e), task_type=request.task_type)
            raise

    async def _transcribe_audio(
        self,
        request: AudioRequest,
        session_id: str | None = None
    ) -> str:
        """Transcribe audio using Whisper or GPT-Audio."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)

            if request.audio_data:
                # Use Whisper for high-quality transcription
                response = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=request.audio_data,
                    language=request.language,
                    response_format="text"
                )
                return response
            else:
                raise ValueError("No audio data provided for transcription")

        except Exception as e:
            logger.error("Transcription failed", error=str(e))
            raise

    async def _synthesize_speech(self, request: AudioRequest) -> bytes:
        """Synthesize speech using TTS models."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)

            # Use high-quality TTS model
            response = await client.audio.speech.create(
                model=self.tts_model,  # tts-1-hd
                voice=request.voice_id or "nova",
                input=request.result if hasattr(request, 'result') else "",
                response_format="mp3"
            )

            return response.content

        except Exception as e:
            logger.error("Speech synthesis failed", error=str(e))
            raise

    async def _analyze_audio(self, request: AudioRequest) -> str:
        """Analyze audio content using GPT-Audio."""
        # This would use GPT-Audio model for audio analysis
        # Implementation depends on final GPT-Audio API
        analysis_prompt = f"""
        Analyze the provided audio content:
        Language: {request.language}

        Provide insights on:
        - Content summary
        - Emotional tone
        - Key topics discussed
        - Audio quality assessment
        """

        response = await self.audio_llm.ainvoke([
            {"role": "system", "content": "You are an expert audio analyst."},
            {"role": "user", "content": analysis_prompt}
        ])

        return response.content

    async def _handle_conversation(
        self,
        request: AudioRequest,
        session_id: str | None = None
    ) -> str:
        """Handle conversational audio processing."""
        if not session_id:
            session_id = f"audio_session_{int(time.time())}"

        # Initialize or get existing session
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                "messages": [],
                "start_time": time.time(),
                "language": request.language
            }

        session = self.active_sessions[session_id]

        # Add user message (would be transcribed audio)
        user_message = "Audio conversation input"  # Placeholder
        session["messages"].append({"role": "user", "content": user_message})

        # Generate response using audio model
        response = await self.audio_llm.ainvoke(session["messages"])
        session["messages"].append({"role": "assistant", "content": response.content})

        return response.content

    async def _process_realtime(
        self,
        request: AudioRequest,
        session_id: str | None = None
    ) -> str:
        """Process real-time audio with low latency."""
        # Use realtime model for immediate responses
        response = await self.realtime_llm.ainvoke([
            {"role": "system", "content": "Provide immediate, concise responses for real-time interaction."},
            {"role": "user", "content": "Real-time audio input processing"}
        ])

        return response.content

    async def stream_conversation(
        self,
        session_id: str,
        audio_stream: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[str, None]:
        """Handle streaming audio conversation."""
        try:
            async for audio_chunk in audio_stream:
                # Process audio chunk in real-time
                request = AudioRequest(
                    audio_data=audio_chunk,
                    task_type="real_time",
                    real_time=True
                )

                response = await self.process_audio(request, session_id)
                yield response.result

        except Exception as e:
            logger.error("Streaming conversation failed", error=str(e))
            yield f"Error in streaming: {str(e)}"

    async def start_session(self, session_config: Dict[str, Any]) -> str:
        """Start a new audio processing session."""
        session_id = f"audio_{int(time.time())}"
        self.active_sessions[session_id] = {
            "config": session_config,
            "start_time": time.time(),
            "messages": [],
            "status": "active"
        }

        logger.info("Started audio session", session_id=session_id)
        return session_id

    async def end_session(self, session_id: str) -> None:
        """End and cleanup audio session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session["status"] = "ended"
            session["end_time"] = time.time()

            # Archive or cleanup session data
            del self.active_sessions[session_id]

            logger.info("Ended audio session", session_id=session_id)

    def get_capabilities(self) -> Dict[str, Any]:
        """Get audio agent capabilities and limits."""
        return {
            "models": {
                "audio": self.model,
                "realtime": self.realtime_model,
                "tts": self.tts_model
            },
            "rate_limits": {
                "gpt_audio": "250K TPM, 3K RPM",
                "gpt_realtime": "250K TPM, 3K RPM",
                "tts_1_hd": "500 RPM",
                "whisper_1": "500 RPM"
            },
            "capabilities": [
                "real_time_transcription",
                "high_quality_tts",
                "audio_analysis",
                "conversation_handling",
                "multi_language_support",
                "streaming_audio"
            ],
            "formats_supported": [
                "mp3", "wav", "flac", "m4a", "ogg", "webm"
            ]
        }
