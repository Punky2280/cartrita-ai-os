# Audio API

> **Source**: https://platform.openai.com/docs/api-reference/audio
> **Last Updated**: September 17, 2025

## Overview

Learn how to turn audio into text with Whisper and text into audio with TTS (Text-to-Speech). The Audio API provides three main endpoints:

- **Transcriptions**: Convert audio to text using Whisper
- **Translations**: Translate and transcribe foreign language audio to English text using Whisper
- **Speech**: Generate spoken audio from text using TTS models

## Transcriptions

Transcribes audio into the input language.

### HTTP Request
```
POST https://api.openai.com/v1/audio/transcriptions
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | file | Yes | The audio file object (not file name) to transcribe. |
| `model` | string | Yes | ID of the model to use. Only `whisper-1` is currently available. |
| `language` | string | No | The language of the input audio in ISO-639-1 format. |
| `prompt` | string | No | An optional text to guide the model's style or continue a previous audio segment. |
| `response_format` | string | No | The format of the transcript output. Options: `json`, `text`, `srt`, `verbose_json`, `vtt`. |
| `temperature` | number | No | The sampling temperature, between 0 and 1. |

### Supported Audio Formats

- mp3
- mp4
- mpeg
- mpga
- m4a
- wav
- webm

### File Size Limit
Maximum file size is 25 MB.

### Example Requests

#### Basic Transcription
```python
from openai import OpenAI

client = OpenAI()

audio_file = open("/path/to/file/audio.mp3", "rb")
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file
)

print(transcript.text)
```

#### Transcription with Language Hint
```python
from openai import OpenAI

client = OpenAI()

audio_file = open("/path/to/file/spanish_audio.mp3", "rb")
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file,
    language="es"  # Spanish
)

print(transcript.text)
```

#### Detailed Response Format
```python
from openai import OpenAI

client = OpenAI()

audio_file = open("/path/to/file/audio.mp3", "rb")
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file,
    response_format="verbose_json"
)

print(f"Text: {transcript.text}")
print(f"Language: {transcript.language}")
print(f"Duration: {transcript.duration}")
print("Segments:")
for segment in transcript.segments:
    print(f"  {segment.start:.2f}s - {segment.end:.2f}s: {segment.text}")
```

#### SRT Subtitle Format
```python
from openai import OpenAI

client = OpenAI()

audio_file = open("/path/to/file/audio.mp3", "rb")
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file,
    response_format="srt"
)

# Save as SRT file
with open("subtitles.srt", "w") as f:
    f.write(transcript)
```

#### cURL Example
```bash
curl https://api.openai.com/v1/audio/transcriptions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F file="@/path/to/file/audio.mp3" \
  -F model="whisper-1"
```

### Response Formats

#### JSON (Default)
```json
{
  "text": "Imagine the wildest idea that you've ever had, and you're curious about how it might scale to something that's a 100, a 1,000 times bigger."
}
```

#### Verbose JSON
```json
{
  "task": "transcribe",
  "language": "english",
  "duration": 8.470000267028809,
  "text": "The beach was a popular spot on a hot summer day. People were swimming, sunbathing, and playing beach volleyball.",
  "segments": [
    {
      "id": 0,
      "seek": 0,
      "start": 0.0,
      "end": 3.319999933242798,
      "text": " The beach was a popular spot on a hot summer day.",
      "tokens": [
        50364, 440, 7534, 390, 257, 3743, 4008, 322, 257, 2368, 4266, 786, 13, 50590
      ],
      "temperature": 0.0,
      "avg_logprob": -0.2860786020755768,
      "compression_ratio": 1.2363636493682861,
      "no_speech_prob": 0.00985015742480755
    }
  ]
}
```

#### SRT Format
```
1
00:00:00,000 --> 00:00:03,320
The beach was a popular spot on a hot summer day.

2
00:00:03,320 --> 00:00:08,470
People were swimming, sunbathing, and playing beach volleyball.
```

## Translations

Translates audio into English text.

### HTTP Request
```
POST https://api.openai.com/v1/audio/translations
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | file | Yes | The audio file object (not file name) to translate. |
| `model` | string | Yes | ID of the model to use. Only `whisper-1` is currently available. |
| `prompt` | string | No | An optional text to guide the model's style. |
| `response_format` | string | No | The format of the transcript output. Options: `json`, `text`, `srt`, `verbose_json`, `vtt`. |
| `temperature` | number | No | The sampling temperature, between 0 and 1. |

### Example Requests

#### Basic Translation
```python
from openai import OpenAI

client = OpenAI()

audio_file = open("/path/to/file/german_audio.mp3", "rb")
translation = client.audio.translations.create(
    model="whisper-1",
    file=audio_file
)

print(translation.text)
```

#### Translation with Context
```python
from openai import OpenAI

client = OpenAI()

audio_file = open("/path/to/file/french_audio.mp3", "rb")
translation = client.audio.translations.create(
    model="whisper-1",
    file=audio_file,
    prompt="This is a conversation about cooking recipes."
)

print(translation.text)
```

#### cURL Example
```bash
curl https://api.openai.com/v1/audio/translations \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F file="@/path/to/file/german.mp3" \
  -F model="whisper-1"
```

## Text-to-Speech (Speech)

Generates audio from the input text.

### HTTP Request
```
POST https://api.openai.com/v1/audio/speech
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | One of the available TTS models: `tts-1` or `tts-1-hd`. |
| `input` | string | Yes | The text to generate audio for. Maximum length is 4096 characters. |
| `voice` | string | Yes | The voice to use when generating the audio. |
| `response_format` | string | No | The format to audio in. Supported formats are `mp3`, `opus`, `aac`, and `flac`. |
| `speed` | number | No | The speed of the generated audio. Select a value from 0.25 to 4.0. |

### Available Models

#### tts-1
- Optimized for real time use cases
- Lower latency
- Good quality

#### tts-1-hd
- Optimized for quality
- Higher latency
- Superior audio quality

### Available Voices

| Voice | Description |
|-------|-------------|
| `alloy` | Neutral, versatile voice |
| `echo` | Male voice with clear pronunciation |
| `fable` | British accent, storytelling style |
| `onyx` | Deep, authoritative male voice |
| `nova` | Young, energetic female voice |
| `shimmer` | Soft, pleasant female voice |

### Example Requests

#### Basic Speech Generation
```python
from openai import OpenAI
from pathlib import Path

client = OpenAI()

speech_file_path = Path(__file__).parent / "speech.mp3"
response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Today is a wonderful day to build something people love!"
)

response.stream_to_file(speech_file_path)
```

#### High Quality Audio
```python
from openai import OpenAI
from pathlib import Path

client = OpenAI()

speech_file_path = Path(__file__).parent / "speech_hd.mp3"
response = client.audio.speech.create(
    model="tts-1-hd",
    voice="nova",
    input="Welcome to our podcast. Today we'll be discussing artificial intelligence and its impact on society."
)

response.stream_to_file(speech_file_path)
```

#### Different Voice and Speed
```python
from openai import OpenAI

client = OpenAI()

response = client.audio.speech.create(
    model="tts-1",
    voice="onyx",
    input="This is a demonstration of text-to-speech with a deeper voice.",
    speed=0.75  # Slower speech
)

with open("slow_speech.mp3", "wb") as f:
    f.write(response.content)
```

#### Streaming Audio
```python
from openai import OpenAI

client = OpenAI()

def generate_audio_stream(text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
    )

    return response.content

# Usage
audio_data = generate_audio_stream("Hello, this is streaming audio!")
with open("stream_output.mp3", "wb") as f:
    f.write(audio_data)
```

#### Different Audio Formats
```python
from openai import OpenAI

client = OpenAI()

# Generate different formats
formats = ["mp3", "opus", "aac", "flac"]
text = "Testing different audio formats."

for format_type in formats:
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
        response_format=format_type
    )

    with open(f"audio.{format_type}", "wb") as f:
        f.write(response.content)

    print(f"Generated audio.{format_type}")
```

#### cURL Example
```bash
curl https://api.openai.com/v1/audio/speech \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "The quick brown fox jumped over the lazy dog.",
    "voice": "alloy"
  }' \
  --output speech.mp3
```

## Real-time Audio Processing

### Streaming Transcription
```python
import pyaudio
import wave
from openai import OpenAI
import tempfile
import os

client = OpenAI()

class RealTimeTranscriber:
    def __init__(self):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.record_seconds = 5

        self.audio = pyaudio.PyAudio()

    def record_audio(self):
        """Record audio for specified duration"""
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )

        print("Recording...")
        frames = []

        for i in range(0, int(self.rate / self.chunk * self.record_seconds)):
            data = stream.read(self.chunk)
            frames.append(data)

        print("Recording finished.")
        stream.stop_stream()
        stream.close()

        return frames

    def save_audio(self, frames):
        """Save recorded frames to temporary file"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")

        wf = wave.open(temp_file.name, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        return temp_file.name

    def transcribe_audio(self, audio_file_path):
        """Transcribe audio file"""
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return transcript.text

    def cleanup(self, file_path):
        """Clean up temporary file"""
        if os.path.exists(file_path):
            os.unlink(file_path)

    def run(self):
        """Main loop for real-time transcription"""
        try:
            while True:
                input("Press Enter to start recording (Ctrl+C to quit)...")

                # Record audio
                frames = self.record_audio()

                # Save to file
                audio_file = self.save_audio(frames)

                # Transcribe
                try:
                    text = self.transcribe_audio(audio_file)
                    print(f"Transcription: {text}")
                except Exception as e:
                    print(f"Transcription error: {e}")

                # Cleanup
                self.cleanup(audio_file)

        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self.audio.terminate()

# Usage
if __name__ == "__main__":
    transcriber = RealTimeTranscriber()
    transcriber.run()
```

### Text-to-Speech with Playback
```python
from openai import OpenAI
import pygame
import io
import tempfile

client = OpenAI()

class TextToSpeechPlayer:
    def __init__(self):
        pygame.mixer.init()

    def speak(self, text, voice="alloy", model="tts-1"):
        """Generate and play speech"""
        try:
            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=text
            )

            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                tmp_file.write(response.content)
                tmp_file_path = tmp_file.name

            # Play audio
            pygame.mixer.music.load(tmp_file_path)
            pygame.mixer.music.play()

            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)

            # Cleanup
            os.unlink(tmp_file_path)

        except Exception as e:
            print(f"Error playing speech: {e}")

    def speak_with_voice_options(self, text):
        """Demonstrate different voices"""
        voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

        for voice in voices:
            print(f"Speaking with voice: {voice}")
            self.speak(f"Hello, I am speaking with the {voice} voice.", voice=voice)
            input("Press Enter for next voice...")

# Usage
if __name__ == "__main__":
    tts_player = TextToSpeechPlayer()

    # Basic usage
    tts_player.speak("Hello, this is a test of text-to-speech!")

    # Voice demonstration
    tts_player.speak_with_voice_options("Voice demonstration")
```

## Advanced Use Cases

### Podcast Generation
```python
from openai import OpenAI
from pathlib import Path
import json

client = OpenAI()

class PodcastGenerator:
    def __init__(self):
        self.voices = {
            "host": "nova",
            "guest": "onyx",
            "narrator": "alloy"
        }

    def generate_episode(self, script_data):
        """Generate podcast episode from script"""
        audio_segments = []

        for segment in script_data["segments"]:
            speaker = segment["speaker"]
            text = segment["text"]
            voice = self.voices.get(speaker, "alloy")

            print(f"Generating audio for {speaker}: {text[:50]}...")

            response = client.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                input=text,
                speed=1.0
            )

            # Save segment
            segment_file = f"segment_{len(audio_segments):03d}_{speaker}.mp3"
            with open(segment_file, "wb") as f:
                f.write(response.content)

            audio_segments.append({
                "file": segment_file,
                "speaker": speaker,
                "text": text
            })

        return audio_segments

# Example script
script = {
    "title": "AI Technology Podcast",
    "segments": [
        {
            "speaker": "narrator",
            "text": "Welcome to Tech Talk, where we explore the latest in artificial intelligence."
        },
        {
            "speaker": "host",
            "text": "I'm your host Sarah, and today we're discussing the future of AI assistants."
        },
        {
            "speaker": "guest",
            "text": "Thanks for having me, Sarah. I'm excited to share our latest research."
        },
        {
            "speaker": "host",
            "text": "Let's start with the basics. What makes modern AI assistants so powerful?"
        }
    ]
}

# Generate podcast
generator = PodcastGenerator()
segments = generator.generate_episode(script)
print(f"Generated {len(segments)} audio segments")
```

### Multilingual Transcription Service
```python
from openai import OpenAI
import os
from pathlib import Path

client = OpenAI()

class MultilingualTranscriber:
    def __init__(self):
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese'
        }

    def process_audio_file(self, file_path, language=None, translate_to_english=False):
        """Process audio file with transcription and optional translation"""
        results = {}

        try:
            with open(file_path, "rb") as audio_file:
                # Transcription
                transcript_params = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "response_format": "verbose_json"
                }

                if language:
                    transcript_params["language"] = language

                transcript = client.audio.transcriptions.create(**transcript_params)

                results["transcription"] = {
                    "text": transcript.text,
                    "language": transcript.language,
                    "duration": transcript.duration,
                    "segments": transcript.segments
                }

                # Translation to English if requested
                if translate_to_english and transcript.language != "english":
                    audio_file.seek(0)  # Reset file pointer
                    translation = client.audio.translations.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json"
                    )

                    results["translation"] = {
                        "text": translation.text,
                        "duration": translation.duration
                    }

        except Exception as e:
            results["error"] = str(e)

        return results

    def batch_process(self, directory_path, output_dir="transcriptions"):
        """Process all audio files in a directory"""
        audio_extensions = {'.mp3', '.mp4', '.wav', '.m4a', '.flac', '.webm'}
        directory = Path(directory_path)
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        for file_path in directory.iterdir():
            if file_path.suffix.lower() in audio_extensions:
                print(f"Processing: {file_path.name}")

                results = self.process_audio_file(
                    str(file_path),
                    translate_to_english=True
                )

                # Save results
                output_file = output_path / f"{file_path.stem}_results.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)

                print(f"Results saved to: {output_file}")

# Usage
transcriber = MultilingualTranscriber()

# Single file processing
results = transcriber.process_audio_file(
    "french_interview.mp3",
    language="fr",
    translate_to_english=True
)

print("Transcription:", results.get("transcription", {}).get("text"))
print("Translation:", results.get("translation", {}).get("text"))
```

## Error Handling

### Common Errors and Solutions

```python
from openai import OpenAI
import openai

client = OpenAI()

def safe_transcribe(audio_file_path, **kwargs):
    """Transcribe audio with comprehensive error handling"""
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                **kwargs
            )
            return {"success": True, "text": transcript.text}

    except openai.BadRequestError as e:
        if "file size" in str(e).lower():
            return {"success": False, "error": "File too large (max 25MB)"}
        elif "format" in str(e).lower():
            return {"success": False, "error": "Unsupported audio format"}
        else:
            return {"success": False, "error": f"Bad request: {e}"}

    except openai.AuthenticationError:
        return {"success": False, "error": "Invalid API key"}

    except openai.RateLimitError:
        return {"success": False, "error": "Rate limit exceeded"}

    except FileNotFoundError:
        return {"success": False, "error": "Audio file not found"}

    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}

def safe_generate_speech(text, **kwargs):
    """Generate speech with error handling"""
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
            **kwargs
        )
        return {"success": True, "audio_data": response.content}

    except openai.BadRequestError as e:
        if "input" in str(e).lower():
            return {"success": False, "error": "Text too long (max 4096 characters)"}
        else:
            return {"success": False, "error": f"Bad request: {e}"}

    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}

# Usage examples
result = safe_transcribe("audio.mp3")
if result["success"]:
    print(f"Transcription: {result['text']}")
else:
    print(f"Error: {result['error']}")

speech_result = safe_generate_speech("Hello world!")
if speech_result["success"]:
    with open("output.mp3", "wb") as f:
        f.write(speech_result["audio_data"])
else:
    print(f"Error: {speech_result['error']}")
```

## Best Practices

### Audio Quality Optimization
- Use high-quality source audio (16kHz or higher)
- Minimize background noise
- Ensure clear speech without distortion
- Use appropriate microphones for recording

### Cost Optimization
- Use `tts-1` for real-time applications
- Use `tts-1-hd` only when quality is critical
- Batch process multiple files when possible
- Cache generated audio for repeated use

### Performance Tips
- Preprocess audio files to optimal formats
- Use streaming for large files
- Implement proper error handling and retries
- Monitor API usage and quotas

### Security Considerations
- Validate audio file contents before processing
- Implement rate limiting on your end
- Don't log sensitive audio content
- Use secure file storage for audio data

---

*This documentation covers the complete Audio API including Whisper transcription, translation, and TTS speech generation. Use these APIs to build powerful voice-enabled applications.*
