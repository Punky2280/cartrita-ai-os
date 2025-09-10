# Deepgram WebSocket Streaming Integration Patterns (2025)

## Overview
This document outlines modern integration patterns for Deepgram's WebSocket streaming audio transcription API, including real-time implementation strategies, best practices, and production deployment patterns.

## Core WebSocket Integration Architecture

### Basic Connection Pattern
```python
import asyncio
import websockets
import json
import base64
from typing import Optional, Callable

class DeepgramStreamer:
    def __init__(self, api_key: str, model: str = "nova-2"):
        self.api_key = api_key
        self.model = model
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.keep_alive_task: Optional[asyncio.Task] = None
        
    async def connect(self, 
                     language: str = "en-US",
                     punctuate: bool = True,
                     interim_results: bool = True):
        """Establish WebSocket connection to Deepgram"""
        
        url = "wss://api.deepgram.com/v1/listen"
        params = {
            "model": self.model,
            "language": language,
            "punctuate": punctuate,
            "interim_results": interim_results,
            "encoding": "linear16",
            "sample_rate": 16000,
            "channels": 1
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{url}?{query_string}"
        
        headers = {"Authorization": f"Token {self.api_key}"}
        
        try:
            self.websocket = await websockets.connect(
                full_url, 
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10
            )
            
            # Start keep-alive mechanism
            self.keep_alive_task = asyncio.create_task(self._keep_alive())
            
            return True
            
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    async def _keep_alive(self):
        """Send keep-alive messages to maintain connection"""
        while self.websocket and not self.websocket.closed:
            try:
                await asyncio.sleep(5)  # Send every 5 seconds
                if self.websocket:
                    await self.websocket.send(json.dumps({"type": "KeepAlive"}))
            except Exception as e:
                print(f"Keep-alive failed: {e}")
                break
    
    async def send_audio(self, audio_data: bytes):
        """Send audio data to Deepgram"""
        if self.websocket and not self.websocket.closed:
            await self.websocket.send(audio_data)
    
    async def receive_transcription(self, callback: Callable[[dict], None]):
        """Receive and process transcription results"""
        if not self.websocket:
            return
            
        try:
            async for message in self.websocket:
                try:
                    result = json.loads(message)
                    await callback(result)
                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
        except Exception as e:
            print(f"Receive error: {e}")
    
    async def close(self):
        """Gracefully close the connection"""
        if self.websocket:
            # Send close stream message
            await self.websocket.send(json.dumps({"type": "CloseStream"}))
            await self.websocket.close()
            
        if self.keep_alive_task:
            self.keep_alive_task.cancel()
```

### FastAPI Integration Pattern

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
import json

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.deepgram_connections: Dict[WebSocket, DeepgramStreamer] = {}

    async def connect(self, websocket: WebSocket, deepgram_api_key: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Create Deepgram connection
        deepgram = DeepgramStreamer(deepgram_api_key)
        if await deepgram.connect():
            self.deepgram_connections[websocket] = deepgram
            return deepgram
        return None

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        if websocket in self.deepgram_connections:
            deepgram = self.deepgram_connections.pop(websocket)
            asyncio.create_task(deepgram.close())

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    # Get API key from query params or headers
    api_key = websocket.query_params.get("api_key")
    if not api_key:
        await websocket.close(code=1008, reason="API key required")
        return
    
    deepgram = await manager.connect(websocket, api_key)
    if not deepgram:
        await websocket.close(code=1011, reason="Failed to connect to Deepgram")
        return
    
    async def transcription_handler(result: dict):
        """Handle transcription results from Deepgram"""
        if "channel" in result:
            transcript_data = {
                "type": "transcription",
                "is_final": result.get("is_final", False),
                "speech_final": result.get("speech_final", False),
                "transcript": result["channel"]["alternatives"][0]["transcript"],
                "confidence": result["channel"]["alternatives"][0]["confidence"],
                "words": result["channel"]["alternatives"][0].get("words", [])
            }
            await manager.send_personal_message(
                json.dumps(transcript_data), 
                websocket
            )
    
    # Start receiving transcriptions
    transcription_task = asyncio.create_task(
        deepgram.receive_transcription(transcription_handler)
    )
    
    try:
        while True:
            # Receive audio data from client
            data = await websocket.receive_bytes()
            
            # Send to Deepgram for transcription
            await deepgram.send_audio(data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        transcription_task.cancel()
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
        transcription_task.cancel()
```

### React Frontend Integration Pattern

```typescript
// DeepgramStreamingClient.ts
import { useCallback, useEffect, useRef, useState } from 'react';

interface TranscriptionResult {
  type: 'transcription';
  is_final: boolean;
  speech_final: boolean;
  transcript: string;
  confidence: number;
  words: Array<{
    word: string;
    start: number;
    end: number;
    confidence: number;
  }>;
}

interface UseDeepgramStreamingOptions {
  apiKey: string;
  language?: string;
  onTranscription?: (result: TranscriptionResult) => void;
  onError?: (error: Error) => void;
  onConnectionStateChange?: (state: 'connecting' | 'connected' | 'disconnected') => void;
}

export const useDeepgramStreaming = (options: UseDeepgramStreamingOptions) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  
  const websocketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);

  const connect = useCallback(async () => {
    try {
      setConnectionState('connecting');
      options.onConnectionStateChange?.('connecting');

      const wsUrl = `wss://localhost:8000/ws/transcribe?api_key=${options.apiKey}`;
      const websocket = new WebSocket(wsUrl);

      websocket.onopen = () => {
        setIsConnected(true);
        setConnectionState('connected');
        options.onConnectionStateChange?.('connected');
        console.log('Connected to Deepgram WebSocket');
      };

      websocket.onmessage = (event) => {
        try {
          const result = JSON.parse(event.data) as TranscriptionResult;
          if (result.type === 'transcription') {
            options.onTranscription?.(result);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        options.onError?.(new Error('WebSocket connection error'));
      };

      websocket.onclose = () => {
        setIsConnected(false);
        setConnectionState('disconnected');
        options.onConnectionStateChange?.('disconnected');
        console.log('Disconnected from Deepgram WebSocket');
      };

      websocketRef.current = websocket;

    } catch (error) {
      setConnectionState('disconnected');
      options.onConnectionStateChange?.('disconnected');
      options.onError?.(error as Error);
    }
  }, [options]);

  const startRecording = useCallback(async () => {
    if (!isConnected || isRecording) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });

      audioStreamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 16000,
      });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && websocketRef.current?.readyState === WebSocket.OPEN) {
          // Convert to the format expected by Deepgram
          const reader = new FileReader();
          reader.onload = () => {
            const arrayBuffer = reader.result as ArrayBuffer;
            websocketRef.current?.send(arrayBuffer);
          };
          reader.readAsArrayBuffer(event.data);
        }
      };

      mediaRecorder.start(100); // Send data every 100ms
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);

    } catch (error) {
      options.onError?.(error as Error);
    }
  }, [isConnected, isRecording, options]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }

    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => track.stop());
      audioStreamRef.current = null;
    }

    setIsRecording(false);
  }, [isRecording]);

  const disconnect = useCallback(() => {
    stopRecording();
    
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
  }, [stopRecording]);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    isRecording,
    connectionState,
    connect,
    startRecording,
    stopRecording,
    disconnect,
  };
};

// React Component Usage
export const VoiceTranscriptionComponent: React.FC = () => {
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');

  const {
    isConnected,
    isRecording,
    connectionState,
    connect,
    startRecording,
    stopRecording,
    disconnect
  } = useDeepgramStreaming({
    apiKey: process.env.REACT_APP_DEEPGRAM_API_KEY || '',
    language: 'en-US',
    onTranscription: (result) => {
      if (result.is_final || result.speech_final) {
        setTranscript(prev => prev + ' ' + result.transcript);
        setInterimTranscript('');
      } else {
        setInterimTranscript(result.transcript);
      }
    },
    onError: (error) => {
      console.error('Transcription error:', error);
    },
    onConnectionStateChange: (state) => {
      console.log('Connection state:', state);
    }
  });

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-4">
        <div className="flex gap-2 mb-4">
          {!isConnected && (
            <button 
              onClick={connect}
              disabled={connectionState === 'connecting'}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            >
              {connectionState === 'connecting' ? 'Connecting...' : 'Connect'}
            </button>
          )}
          
          {isConnected && !isRecording && (
            <button 
              onClick={startRecording}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              Start Recording
            </button>
          )}
          
          {isRecording && (
            <button 
              onClick={stopRecording}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Stop Recording
            </button>
          )}
          
          {isConnected && (
            <button 
              onClick={disconnect}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              Disconnect
            </button>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${
            connectionState === 'connected' ? 'bg-green-500' : 
            connectionState === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
          }`} />
          <span className="text-sm text-gray-600">
            {connectionState === 'connected' ? 'Connected' : 
             connectionState === 'connecting' ? 'Connecting...' : 'Disconnected'}
          </span>
          {isRecording && (
            <span className="text-sm text-red-600 ml-4">● Recording</span>
          )}
        </div>
      </div>

      <div className="space-y-4">
        <div className="p-4 bg-gray-100 rounded-lg min-h-[100px]">
          <h3 className="font-medium mb-2">Final Transcript:</h3>
          <p className="text-gray-800">{transcript}</p>
        </div>
        
        {interimTranscript && (
          <div className="p-4 bg-blue-50 rounded-lg">
            <h3 className="font-medium mb-2">Interim (Live):</h3>
            <p className="text-gray-600 italic">{interimTranscript}</p>
          </div>
        )}
      </div>
    </div>
  );
};
```

## Advanced Integration Patterns

### Voice Activity Detection (VAD)

```python
import numpy as np
from scipy import signal
import asyncio

class VoiceActivityDetector:
    def __init__(self, 
                 sample_rate: int = 16000,
                 frame_duration: float = 0.02,  # 20ms
                 energy_threshold: float = 0.01,
                 silence_duration: float = 1.0):
        self.sample_rate = sample_rate
        self.frame_size = int(frame_duration * sample_rate)
        self.energy_threshold = energy_threshold
        self.silence_frames_threshold = int(silence_duration / frame_duration)
        self.silence_frame_count = 0
        self.is_speaking = False
        
    def detect_voice_activity(self, audio_frame: np.ndarray) -> dict:
        """Detect voice activity in audio frame"""
        
        # Calculate energy
        energy = np.sum(audio_frame ** 2) / len(audio_frame)
        
        # Determine if voice is active
        voice_active = energy > self.energy_threshold
        
        if voice_active:
            self.silence_frame_count = 0
            if not self.is_speaking:
                self.is_speaking = True
                return {"event": "speech_start", "energy": energy}
        else:
            self.silence_frame_count += 1
            if self.is_speaking and self.silence_frame_count >= self.silence_frames_threshold:
                self.is_speaking = False
                return {"event": "speech_end", "energy": energy}
                
        return {"event": "continue", "energy": energy, "voice_active": voice_active}

class EnhancedDeepgramStreamer(DeepgramStreamer):
    def __init__(self, api_key: str, model: str = "nova-2"):
        super().__init__(api_key, model)
        self.vad = VoiceActivityDetector()
        self.audio_buffer = []
        self.is_speech_active = False
        
    async def process_audio_with_vad(self, audio_data: bytes, 
                                   vad_callback: Optional[Callable] = None):
        """Process audio with voice activity detection"""
        
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Process in frames
        for i in range(0, len(audio_array), self.vad.frame_size):
            frame = audio_array[i:i + self.vad.frame_size]
            if len(frame) < self.vad.frame_size:
                # Pad last frame
                frame = np.pad(frame, (0, self.vad.frame_size - len(frame)))
            
            vad_result = self.vad.detect_voice_activity(frame)
            
            if vad_callback:
                await vad_callback(vad_result)
            
            # Handle speech events
            if vad_result["event"] == "speech_start":
                self.is_speech_active = True
                # Send buffered audio
                if self.audio_buffer:
                    buffered_audio = b''.join(self.audio_buffer)
                    await self.send_audio(buffered_audio)
                    self.audio_buffer = []
                    
            elif vad_result["event"] == "speech_end":
                self.is_speech_active = False
                # Send any remaining audio
                await self.send_audio(audio_data[i-self.vad.frame_size:])
                
            # Buffer audio when not speaking (for context)
            if not self.is_speech_active:
                self.audio_buffer.append(frame.tobytes())
                # Keep only last 500ms of audio
                max_buffer_frames = int(0.5 * self.vad.sample_rate / self.vad.frame_size)
                if len(self.audio_buffer) > max_buffer_frames:
                    self.audio_buffer.pop(0)
            else:
                # Send audio immediately when speaking
                await self.send_audio(frame.tobytes())
```

### Multi-Speaker Detection and Diarization

```python
class SpeakerDiarizationHandler:
    def __init__(self):
        self.speakers = {}
        self.current_speaker = None
        self.speaker_change_threshold = 0.5
        
    def process_diarization_result(self, result: dict) -> dict:
        """Process Deepgram result with speaker information"""
        
        if "channel" not in result:
            return result
            
        alternatives = result["channel"]["alternatives"][0]
        words = alternatives.get("words", [])
        
        if not words:
            return result
            
        # Process speaker changes
        speaker_segments = []
        current_segment = None
        
        for word in words:
            speaker_id = word.get("speaker", 0)
            
            if current_segment is None or current_segment["speaker"] != speaker_id:
                if current_segment:
                    speaker_segments.append(current_segment)
                    
                current_segment = {
                    "speaker": speaker_id,
                    "start": word["start"],
                    "end": word["end"],
                    "words": [word],
                    "text": word["word"]
                }
            else:
                current_segment["end"] = word["end"]
                current_segment["words"].append(word)
                current_segment["text"] += " " + word["word"]
                
        if current_segment:
            speaker_segments.append(current_segment)
            
        # Add speaker information to result
        result["speaker_segments"] = speaker_segments
        return result

# Usage with FastAPI WebSocket
@app.websocket("/ws/transcribe-multi-speaker")
async def websocket_transcribe_multi_speaker(websocket: WebSocket):
    api_key = websocket.query_params.get("api_key")
    if not api_key:
        await websocket.close(code=1008, reason="API key required")
        return
    
    deepgram = EnhancedDeepgramStreamer(api_key)
    diarization_handler = SpeakerDiarizationHandler()
    
    # Connect with diarization enabled
    if not await deepgram.connect(
        language="en-US",
        punctuate=True,
        interim_results=True,
        diarize=True  # Enable speaker diarization
    ):
        await websocket.close(code=1011, reason="Failed to connect to Deepgram")
        return
    
    async def transcription_handler(result: dict):
        """Enhanced handler with speaker diarization"""
        processed_result = diarization_handler.process_diarization_result(result)
        
        if "channel" in processed_result:
            transcript_data = {
                "type": "transcription",
                "is_final": processed_result.get("is_final", False),
                "speech_final": processed_result.get("speech_final", False),
                "transcript": processed_result["channel"]["alternatives"][0]["transcript"],
                "confidence": processed_result["channel"]["alternatives"][0]["confidence"],
                "speaker_segments": processed_result.get("speaker_segments", []),
                "words": processed_result["channel"]["alternatives"][0].get("words", [])
            }
            await websocket.send_text(json.dumps(transcript_data))
    
    await manager.connect(websocket, deepgram, transcription_handler)
```

### Production Deployment Patterns

```yaml
# docker-compose.yml for production deployment
version: '3.8'

services:
  transcription-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://user:pass@postgres:5432/transcription_db
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=transcription_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - transcription-api
    restart: unless-stopped

volumes:
  postgres_data:
```

```nginx
# nginx.conf for production
events {
    worker_connections 1024;
}

http {
    upstream transcription_api {
        server transcription-api:8000;
    }
    
    # WebSocket upgrade configuration
    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }
    
    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name your-domain.com;
        
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        # WebSocket support
        location /ws/ {
            proxy_pass http://transcription_api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket timeout settings
            proxy_read_timeout 86400;
            proxy_send_timeout 86400;
        }
        
        # Regular HTTP endpoints
        location / {
            proxy_pass http://transcription_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## Best Practices and Performance Optimization

### Connection Management
1. **Connection Pooling**: Reuse connections when possible
2. **Graceful Reconnection**: Implement automatic reconnection with exponential backoff
3. **Keep-Alive**: Send periodic keep-alive messages (every 5-10 seconds)
4. **Proper Cleanup**: Always send CloseStream before disconnecting

### Audio Optimization
1. **Buffer Size**: Use 20-250ms audio buffers for optimal performance
2. **Sample Rate**: 16kHz is optimal for speech recognition
3. **Encoding**: Linear PCM 16-bit for best quality
4. **Noise Reduction**: Implement client-side noise suppression

### Error Handling
1. **Network Failures**: Implement retry logic with exponential backoff
2. **Audio Quality**: Monitor audio levels and quality metrics
3. **Rate Limiting**: Respect Deepgram's rate limits and quotas
4. **Fallback Strategies**: Have backup transcription services

### Security Considerations
1. **API Key Protection**: Never expose API keys in frontend code
2. **Proxy Pattern**: Use backend proxy for API key management
3. **Authentication**: Implement proper user authentication
4. **Rate Limiting**: Implement per-user rate limiting

This comprehensive guide provides the foundation for implementing robust, production-ready Deepgram streaming integrations with modern web technologies.