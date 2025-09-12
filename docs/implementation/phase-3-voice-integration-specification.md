# Phase 3: Voice Integration Specification

## Overview

This document outlines the implementation of Phase 3 voice integration for Cartrita AI OS, leveraging Deepgram's comprehensive voice capabilities including real-time streaming, text-to-speech, and voice agent functionality.

## Architecture

### Core Components

1. **Voice Input System**
   - Real-time speech-to-text transcription
   - WebSocket-based streaming
   - Interim results for low-latency feedback
   - Multiple language support

2. **Voice Output System**
   - Text-to-speech synthesis
   - Multiple voice models (Aura series)
   - Streaming audio output
   - Real-time audio playback

3. **Voice Agent Integration**
   - Conversational AI with voice
   - WebSocket-based agent communication
   - Context-aware responses
   - Multi-turn conversation support

## Technical Implementation

### Frontend Integration (React/TypeScript)

#### Dependencies

```json
{
  "deepgram-react": "^1.0.0",
  "@deepgram/sdk": "^3.0.0"
}
```

#### Voice Input Component

```tsx
import React, { useRef, useState, useCallback } from 'react';
import { DeepgramVoiceInteraction } from 'deepgram-react';
import type { DeepgramVoiceInteractionHandle, TranscriptResponse } from 'deepgram-react';

interface VoiceInputProps {
  onTranscript: (transcript: string, isFinal: boolean) => void;
  onError: (error: Error) => void;
  apiKey: string;
}

export const VoiceInput: React.FC<VoiceInputProps> = ({
  onTranscript,
  onError,
  apiKey
}) => {
  const deepgramRef = useRef<DeepgramVoiceInteractionHandle>(null);
  const [isListening, setIsListening] = useState(false);

  const handleTranscriptUpdate = useCallback((transcript: TranscriptResponse) => {
    if (transcript.is_final && transcript.channel?.alternatives?.[0]) {
      const text = transcript.channel.alternatives[0].transcript;
      onTranscript(text, true);
    } else if (transcript.channel?.alternatives?.[0]) {
      const text = transcript.channel.alternatives[0].transcript;
      onTranscript(text, false);
    }
  }, [onTranscript]);

  const startListening = () => {
    deepgramRef.current?.start();
    setIsListening(true);
  };

  const stopListening = () => {
    deepgramRef.current?.stop();
    setIsListening(false);
  };

  return (
    <div>
      <DeepgramVoiceInteraction
        ref={deepgramRef}
        apiKey={apiKey}
        transcriptionOptions={{
          model: 'nova-2',
          language: 'en-US',
          interim_results: true,
          smart_format: true,
        }}
        onReady={(ready) => console.log('Voice input ready:', ready)}
        onTranscriptUpdate={handleTranscriptUpdate}
        onError={onError}
        debug={true}
      />

      <button
        onClick={isListening ? stopListening : startListening}
        disabled={!apiKey}
      >
        {isListening ? 'Stop Listening' : 'Start Listening'}
      </button>
    </div>
  );
};
```

#### Voice Output Component

```tsx
import React, { useRef, useState, useCallback } from 'react';
import { DeepgramVoiceInteraction } from 'deepgram-react';
import type { DeepgramVoiceInteractionHandle, LLMResponse } from 'deepgram-react';

interface VoiceOutputProps {
  text: string;
  onPlaybackStart: () => void;
  onPlaybackEnd: () => void;
  onError: (error: Error) => void;
  apiKey: string;
  voice?: string;
}

export const VoiceOutput: React.FC<VoiceOutputProps> = ({
  text,
  onPlaybackStart,
  onPlaybackEnd,
  onError,
  apiKey,
  voice = 'aura-asteria-en'
}) => {
  const deepgramRef = useRef<DeepgramVoiceInteractionHandle>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const handleAgentUtterance = useCallback((utterance: LLMResponse) => {
    if (utterance.text) {
      onPlaybackStart();
      setIsPlaying(true);
    }
  }, [onPlaybackStart]);

  const handlePlaybackStateChange = useCallback((playing: boolean) => {
    setIsPlaying(playing);
    if (!playing) {
      onPlaybackEnd();
    }
  }, [onPlaybackEnd]);

  const speak = () => {
    if (text && deepgramRef.current) {
      deepgramRef.current.injectAgentMessage(text);
    }
  };

  return (
    <div>
      <DeepgramVoiceInteraction
        ref={deepgramRef}
        apiKey={apiKey}
        agentOptions={{
          instructions: `You are a voice assistant. When given text, convert it to speech using the ${voice} voice. Respond only with the spoken text.`,
          voice: voice,
          thinkModel: 'gpt-4o-mini',
        }}
        onReady={(ready) => console.log('Voice output ready:', ready)}
        onAgentUtterance={handleAgentUtterance}
        onPlaybackStateChange={handlePlaybackStateChange}
        onError={onError}
        debug={true}
      />

      <button
        onClick={speak}
        disabled={!text || isPlaying || !apiKey}
      >
        {isPlaying ? 'Speaking...' : 'Speak Text'}
      </button>
    </div>
  );
};
```

#### Voice Agent Component

```tsx
import React, { useRef, useState, useCallback } from 'react';
import { DeepgramVoiceInteraction } from 'deepgram-react';
import type {
  DeepgramVoiceInteractionHandle,
  AgentState,
  LLMResponse,
  UserMessageResponse
} from 'deepgram-react';

interface VoiceAgentProps {
  instructions: string;
  onAgentResponse: (response: string) => void;
  onUserMessage: (message: string) => void;
  onError: (error: Error) => void;
  apiKey: string;
  voice?: string;
}

export const VoiceAgent: React.FC<VoiceAgentProps> = ({
  instructions,
  onAgentResponse,
  onUserMessage,
  onError,
  apiKey,
  voice = 'aura-asteria-en'
}) => {
  const deepgramRef = useRef<DeepgramVoiceInteractionHandle>(null);
  const [agentState, setAgentState] = useState<AgentState>('idle');
  const [isActive, setIsActive] = useState(false);

  const handleAgentStateChange = useCallback((state: AgentState) => {
    setAgentState(state);
  }, []);

  const handleAgentUtterance = useCallback((utterance: LLMResponse) => {
    if (utterance.text) {
      onAgentResponse(utterance.text);
    }
  }, [onAgentResponse]);

  const handleUserMessage = useCallback((message: UserMessageResponse) => {
    if (message.text) {
      onUserMessage(message.text);
    }
  }, [onUserMessage]);

  const startAgent = () => {
    deepgramRef.current?.start();
    setIsActive(true);
  };

  const stopAgent = () => {
    deepgramRef.current?.stop();
    setIsActive(false);
  };

  const interruptAgent = () => {
    deepgramRef.current?.interruptAgent();
  };

  return (
    <div>
      <DeepgramVoiceInteraction
        ref={deepgramRef}
        apiKey={apiKey}
        agentOptions={{
          instructions,
          listenModel: 'nova-2',
          voice,
          thinkModel: 'gpt-4o-mini',
        }}
        onReady={(ready) => console.log('Voice agent ready:', ready)}
        onAgentStateChange={handleAgentStateChange}
        onAgentUtterance={handleAgentUtterance}
        onUserMessage={handleUserMessage}
        onError={onError}
        debug={true}
      />

      <div>
        <button onClick={isActive ? stopAgent : startAgent}>
          {isActive ? 'Stop Agent' : 'Start Agent'}
        </button>
        <button onClick={interruptAgent} disabled={!isActive}>
          Interrupt
        </button>
      </div>

      <div>Agent State: {agentState}</div>
    </div>
  );
};
```

### Backend Integration (Python)

#### Python Dependencies

```txt
deepgram-sdk==3.2.0
websockets==12.0
asyncio
numpy
pyaudio  # For local audio handling
```

#### Voice Service Implementation

```python
import asyncio
import json
import logging
from typing import Optional, Callable, Any
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import websockets

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.deepgram = DeepgramClient(api_key)
        self.active_connections = {}

    async def start_transcription_stream(
        self,
        stream_id: str,
        on_transcript: Callable[[str, bool], Any],
        on_error: Callable[[Exception], Any]
    ):
        """Start real-time transcription stream"""
        try:
            connection = self.deepgram.listen.live.v("1")

            def handle_transcript(self, result, **kwargs):
                transcript = result.channel.alternatives[0].transcript
                is_final = result.is_final
                on_transcript(transcript, is_final)

            connection.on(LiveTranscriptionEvents.Transcript, handle_transcript)
            connection.on(LiveTranscriptionEvents.Error, lambda error: on_error(error))

            await connection.start(LiveOptions(
                model="nova-2",
                language="en-US",
                interim_results=True,
                smart_format=True,
            ))

            self.active_connections[stream_id] = connection
            return connection

        except Exception as e:
            logger.error(f"Failed to start transcription stream: {e}")
            on_error(e)
            return None

    async def send_audio_data(self, stream_id: str, audio_data: bytes):
        """Send audio data to transcription stream"""
        if stream_id in self.active_connections:
            connection = self.active_connections[stream_id]
            await connection.send(audio_data)

    async def stop_transcription_stream(self, stream_id: str):
        """Stop transcription stream"""
        if stream_id in self.active_connections:
            connection = self.active_connections[stream_id]
            await connection.finish()
            del self.active_connections[stream_id]

    async def text_to_speech(
        self,
        text: str,
        voice: str = "aura-asteria-en",
        model: str = "aura-2-thalia-en"
    ) -> bytes:
        """Convert text to speech"""
        try:
            options = {
                "model": model,
                "voice": voice,
                "encoding": "linear16",
                "sample_rate": 24000,
            }

            response = await self.deepgram.speak.v("1").save(text, options)
            return response

        except Exception as e:
            logger.error(f"TTS failed: {e}")
            raise

    async def start_voice_agent(
        self,
        agent_id: str,
        instructions: str,
        on_agent_response: Callable[[str], Any],
        on_user_message: Callable[[str], Any],
        on_error: Callable[[Exception], Any]
    ):
        """Start voice agent conversation"""
        try:
            connection = self.deepgram.agent.v("1")

            def handle_agent_response(self, result, **kwargs):
                if result.type == "conversation_text":
                    on_agent_response(result.content)

            def handle_user_message(self, result, **kwargs):
                if result.type == "user_message":
                    on_user_message(result.content)

            connection.on("conversation_text", handle_agent_response)
            connection.on("user_message", handle_user_message)
            connection.on("error", lambda error: on_error(error))

            await connection.start({
                "instructions": instructions,
                "voice": "aura-asteria-en",
                "think_model": "gpt-4o-mini",
            })

            self.active_connections[agent_id] = connection
            return connection

        except Exception as e:
            logger.error(f"Failed to start voice agent: {e}")
            on_error(e)
            return None

    async def send_agent_message(self, agent_id: str, message: str):
        """Send message to voice agent"""
        if agent_id in self.active_connections:
            connection = self.active_connections[agent_id]
            await connection.send(message)

    async def stop_voice_agent(self, agent_id: str):
        """Stop voice agent"""
        if agent_id in self.active_connections:
            connection = self.active_connections[agent_id]
            await connection.finish()
            del self.active_connections[agent_id]
```

## WebSocket Streaming Architecture

### Real-time Audio Streaming

- **Protocol**: WebSocket (wss://api.deepgram.com/v1/listen)
- **Audio Format**: Raw PCM, WAV, MP3, OGG, etc.
- **Sample Rates**: 8000, 16000, 24000, 44100, 48000 Hz
- **Chunk Size**: 100-1000ms audio chunks for optimal latency

### Control Messages

```json
// Start transcription
{
  "type": "Listen",
  "model": "nova-2",
  "language": "en-US",
  "interim_results": true
}

// Send audio data (binary)
<audio_chunk_bytes>

// Stop transcription
{
  "type": "Close"
}
```

### Response Format

```json
{
  "type": "Results",
  "channel": {
    "alternatives": [
      {
        "transcript": "Hello, world!",
        "confidence": 0.98,
        "words": [
          {
            "word": "Hello",
            "start": 0.1,
            "end": 0.5,
            "confidence": 0.99
          }
        ]
      }
    ]
  },
  "duration": 0.8,
  "is_final": true,
  "speech_final": true
}
```

## Voice Agent Architecture

### Agent Configuration

```json
{
  "instructions": "You are a helpful AI assistant...",
  "voice": "aura-asteria-en",
  "think_model": "gpt-4o-mini",
  "listen_model": "nova-2",
  "language": "en-US"
}
```

### Conversation Flow

1. **User speaks** → Audio captured and streamed to Deepgram
2. **Transcription** → Speech converted to text in real-time
3. **Agent processing** → LLM generates response based on instructions
4. **TTS synthesis** → Response converted to speech
5. **Audio playback** → User hears the response

### Context Management

- **Session state**: Maintain conversation history
- **Memory injection**: Include relevant context from previous interactions
- **Dynamic instructions**: Update agent behavior based on user preferences

## Performance Optimization

### Latency Considerations

- **Audio chunking**: 100-250ms chunks for balance between latency and accuracy
- **Interim results**: Enable for immediate feedback
- **Connection pooling**: Reuse WebSocket connections
- **Caching**: Cache TTS responses for repeated phrases

### Bandwidth Optimization

- **Audio compression**: Use efficient codecs (Opus, MP3)
- **Smart formatting**: Enable punctuation and capitalization
- **Result filtering**: Only process final results for critical actions

### Error Handling

- **Connection recovery**: Automatic reconnection on failures
- **Graceful degradation**: Fallback to text-only mode
- **Rate limiting**: Respect API limits and implement backoff
- **Timeout handling**: Handle network timeouts appropriately

## Security Implementation

### API Key Management

- **Environment variables**: Store keys securely
- **Key rotation**: Regular key updates
- **Access control**: Limit key usage to specific domains

### Data Privacy

- **Audio encryption**: Encrypt audio in transit
- **PII filtering**: Remove sensitive information from transcripts
- **Retention policies**: Define data retention periods
- **Compliance**: GDPR, CCPA compliance measures

### Network Security

- **HTTPS/WSS**: Secure WebSocket connections
- **CORS**: Proper cross-origin resource sharing
- **Rate limiting**: Prevent abuse and control costs

## Testing Strategy

### Unit Tests

- **Component testing**: Test individual voice components
- **Mock services**: Use mock Deepgram services for testing
- **Error scenarios**: Test failure conditions

### Integration Tests

- **End-to-end flows**: Test complete voice interaction cycles
- **WebSocket testing**: Test real-time streaming
- **Cross-browser**: Test across different browsers

### Performance Tests

- **Latency measurement**: Measure end-to-end response times
- **Throughput testing**: Test concurrent voice sessions
- **Resource usage**: Monitor memory and CPU usage

## Deployment Considerations

### Environment Setup

- **API keys**: Configure Deepgram credentials
- **Network access**: Ensure WebSocket connectivity
- **Audio permissions**: Handle microphone/camera permissions

### Scaling

- **Connection limits**: Monitor concurrent connections
- **Resource allocation**: Scale based on usage patterns
- **Caching strategy**: Implement response caching

### Monitoring

- **Usage metrics**: Track API usage and costs
- **Performance monitoring**: Monitor latency and error rates
- **User experience**: Track voice interaction quality

## Integration with Existing Systems

### Chat Interface Integration

- **Seamless switching**: Toggle between text and voice modes
- **Unified UI**: Consistent interface for both input methods
- **Context preservation**: Maintain conversation context across modes

### Multi-agent Coordination

- **Voice routing**: Route voice inputs to appropriate agents
- **Response synthesis**: Combine responses from multiple agents
- **State synchronization**: Keep voice and text states in sync

### File Upload Integration

- **Voice annotations**: Add voice notes to uploaded files
- **Audio transcription**: Transcribe audio files automatically
- **Voice search**: Enable voice-based file search

## Future Enhancements

### Advanced Features

- **Speaker identification**: Identify different speakers
- **Emotion recognition**: Detect emotional tone
- **Language detection**: Auto-detect spoken language
- **Custom voice models**: Train custom TTS voices

### Platform Extensions

- **Mobile support**: Native mobile voice integration
- **Desktop applications**: Voice support for desktop apps
- **IoT devices**: Voice integration for smart devices

### AI Enhancements

- **Context awareness**: Better understanding of conversation context
- **Personality adaptation**: Customize agent personality
- **Multi-modal integration**: Combine voice with vision and text

## Conclusion

This Phase 3 voice integration specification provides a comprehensive framework for implementing Deepgram's voice capabilities in Cartrita AI OS. The implementation focuses on real-time streaming, high-quality TTS, and conversational AI while maintaining security, performance, and user experience standards.

The modular architecture allows for incremental implementation and future enhancements while ensuring compatibility with existing systems and adherence to the project's design principles.
