# Cartrita AI OS - Deepgram Service
# Deepgram integration for voice processing and transcription

"""
Deepgram service for Cartrita AI OS.
Handles voice transcription, real-time audio processing, and speech analysis.
"""

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import structlog
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions, PrerecordedOptions

from cartrita.orchestrator.utils.config import settings

logger = structlog.get_logger(__name__)


class DeepgramService:
    """Deepgram service for voice processing and transcription."""

    def __init__(self):
        """Initialize Deepgram service."""
        self.api_key = settings.ai.deepgram_api_key.get_secret_value()
        self.client = DeepgramClient(self.api_key)
        self.model = "nova-2"  # Latest general purpose model
        self.language = "en-US"

        logger.info("Deepgram service initialized", model=self.model, language=self.language)

    async def transcribe_audio(
        self,
        audio_data: bytes,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe pre-recorded audio data.

        Args:
            audio_data: Raw audio bytes
            options: Additional transcription options

        Returns:
            Transcription result
        """
        try:
            # Prepare options
            transcription_options = PrerecordedOptions(
                model=self.model,
                language=self.language,
                smart_format=True,
                punctuate=True,
                diarize=True,
                **(options or {})
            )

            logger.info("Starting audio transcription", audio_size=len(audio_data))

            # Create source from audio data
            source = {"buffer": audio_data, "mimetype": "audio/wav"}

            # Transcribe
            response = await self.client.listen.prerecorded.v("1").transcribe_file(
                source, transcription_options
            )

            # Extract transcription
            if response and response.results and response.results.channels:
                channel = response.results.channels[0]
                if channel.alternatives:
                    alternative = channel.alternatives[0]

                    result = {
                        "transcript": alternative.transcript,
                        "confidence": alternative.confidence,
                        "words": [
                            {
                                "word": word.word,
                                "start": word.start,
                                "end": word.end,
                                "confidence": word.confidence,
                                "speaker": getattr(word, "speaker", None)
                            }
                            for word in alternative.words
                        ] if alternative.words else [],
                        "duration": getattr(response.metadata, "duration", None),
                        "channels": len(response.results.channels)
                    }

                    logger.info(
                        "Transcription completed",
                        transcript_length=len(result["transcript"]),
                        confidence=result["confidence"],
                        word_count=len(result["words"])
                    )

                    return result

            return {"transcript": "", "confidence": 0.0, "words": [], "error": "No transcription results"}

        except Exception as e:
            logger.error("Audio transcription failed", error=str(e))
            return {"transcript": "", "confidence": 0.0, "words": [], "error": str(e)}

    async def start_live_transcription(
        self,
        websocket_url: str,
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Start live transcription session.

        Args:
            websocket_url: WebSocket URL for live audio
            options: Additional live transcription options

        Yields:
            Live transcription results
        """
        try:
            # Prepare live options
            live_options = LiveOptions(
                model=self.model,
                language=self.language,
                smart_format=True,
                punctuate=True,
                interim_results=True,
                diarize=True,
                **(options or {})
            )

            logger.info("Starting live transcription session")

            # Create live client
            dg_connection = self.client.listen.live.v("1")

            # Set up event handlers
            async def on_message(result):
                if result and result.channel and result.channel.alternatives:
                    alternative = result.channel.alternatives[0]
                    yield {
                        "type": "transcript",
                        "transcript": alternative.transcript,
                        "confidence": alternative.confidence,
                        "is_final": result.is_final,
                        "speech_final": getattr(result, "speech_final", False),
                        "words": [
                            {
                                "word": word.word,
                                "start": word.start,
                                "end": word.end,
                                "confidence": word.confidence,
                                "speaker": getattr(word, "speaker", None)
                            }
                            for word in alternative.words
                        ] if alternative.words else []
                    }

            async def on_metadata(metadata):
                yield {
                    "type": "metadata",
                    "request_id": metadata.request_id,
                    "channels": metadata.channels,
                    "duration": metadata.duration,
                    "models": metadata.models
                }

            async def on_error(error):
                yield {
                    "type": "error",
                    "error": str(error)
                }

            # Register handlers
            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
            dg_connection.on(LiveTranscriptionEvents.Error, on_error)

            # Start connection
            await dg_connection.start(live_options)

            logger.info("Live transcription session started")

            # Keep connection alive and yield results
            try:
                while True:
                    # This would be replaced with actual WebSocket handling
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                logger.info("Live transcription session cancelled")
            finally:
                await dg_connection.finish()

        except Exception as e:
            logger.error("Live transcription failed", error=str(e))
            yield {"type": "error", "error": str(e)}

    async def analyze_audio_quality(
        self,
        audio_data: bytes
    ) -> Dict[str, Any]:
        """
        Analyze audio quality and provide recommendations.

        Args:
            audio_data: Raw audio bytes

        Returns:
            Audio quality analysis
        """
        try:
            # This would use Deepgram's audio intelligence features
            # For now, return basic analysis
            analysis = {
                "quality_score": 0.85,  # Placeholder
                "noise_level": "low",
                "clarity": "good",
                "recommendations": [
                    "Audio quality is good for transcription",
                    "Consider using noise reduction if background noise is present"
                ]
            }

            logger.info("Audio quality analysis completed", quality_score=analysis["quality_score"])
            return analysis

        except Exception as e:
            logger.error("Audio quality analysis failed", error=str(e))
            return {"error": str(e)}

    async def get_supported_languages(self) -> List[Dict[str, Any]]:
        """
        Get list of supported languages for transcription.

        Returns:
            List of supported languages
        """
        try:
            # Deepgram supports many languages
            languages = [
                {"code": "en-US", "name": "English (US)", "model": "nova-2"},
                {"code": "en-GB", "name": "English (UK)", "model": "nova-2"},
                {"code": "es", "name": "Spanish", "model": "nova-2"},
                {"code": "fr", "name": "French", "model": "nova-2"},
                {"code": "de", "name": "German", "model": "nova-2"},
                {"code": "it", "name": "Italian", "model": "nova-2"},
                {"code": "pt", "name": "Portuguese", "model": "nova-2"},
                {"code": "ja", "name": "Japanese", "model": "nova-2"},
                {"code": "ko", "name": "Korean", "model": "nova-2"},
                {"code": "zh", "name": "Chinese", "model": "nova-2"}
            ]

            return languages

        except Exception as e:
            logger.error("Failed to get supported languages", error=str(e))
            return []

    async def health_check(self) -> Dict[str, Any]:
        """Check Deepgram service health."""
        try:
            # Test API connectivity
            response = await self.client.listen.prerecorded.v("1").get_balance()
            return {
                "status": "healthy",
                "balance": getattr(response, "balance", "unknown"),
                "model": self.model,
                "language": self.language
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
