# OpenAI API Quickstart Guide

> **Source**: https://platform.openai.com/docs/quickstart
> **Last Updated**: September 17, 2025

## Overview

This quickstart guide will help you get up and running with the OpenAI API in just a few minutes. You'll learn how to set up your environment, make your first API call, and explore common use cases.

## Step 1: Account Setup

### Create an OpenAI Account
1. Visit [platform.openai.com](https://platform.openai.com)
2. Sign up for a new account or sign in with an existing one
3. Complete the verification process

### Get Your API Key
1. Navigate to the API Keys section in your dashboard
2. Click "Create new secret key"
3. Copy your API key and store it securely
4. **Important**: Never share your API key or include it in client-side code

## Step 2: Environment Setup

### Python Installation

#### Install the OpenAI Python Library
```bash
pip install openai
```

#### Set Your API Key (Recommended Method)

**Option 1: Environment Variable**
```bash
# macOS/Linux
export OPENAI_API_KEY="your-api-key-here"

# Windows (Command Prompt)
set OPENAI_API_KEY=your-api-key-here

# Windows (PowerShell)
$env:OPENAI_API_KEY="your-api-key-here"
```

**Option 2: .env File**
Create a `.env` file in your project directory:
```env
OPENAI_API_KEY=your-api-key-here
```

Then load it in your Python code:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Node.js Installation

#### Install the OpenAI Node.js Library
```bash
npm install openai
```

#### Set Your API Key
```javascript
// Using environment variables
process.env.OPENAI_API_KEY = "your-api-key-here";
```

## Step 3: Make Your First API Call

### Python Example

#### Basic Chat Completion
```python
from openai import OpenAI

# Initialize the client
client = OpenAI()
# API key is automatically read from environment variable

# Make a chat completion request
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

# Print the response
print(response.choices[0].message.content)
```

#### Streaming Response
```python
from openai import OpenAI

client = OpenAI()

stream = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Write a short poem about programming"}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

### Node.js Example

#### Basic Chat Completion
```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

async function main() {
  const completion = await openai.chat.completions.create({
    messages: [
      { role: "system", content: "You are a helpful assistant." },
      { role: "user", content: "What is the capital of France?" }
    ],
    model: "gpt-3.5-turbo",
  });

  console.log(completion.choices[0].message.content);
}

main();
```

#### Streaming Response
```javascript
import OpenAI from 'openai';

const openai = new OpenAI();

async function main() {
  const stream = await openai.chat.completions.create({
    model: 'gpt-3.5-turbo',
    messages: [
      { role: 'user', content: 'Write a short poem about programming' }
    ],
    stream: true,
  });

  for await (const chunk of stream) {
    process.stdout.write(chunk.choices[0]?.delta?.content || '');
  }
}

main();
```

## Step 4: Explore Common Use Cases

### Text Generation
```python
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Write a product description for wireless headphones"}
    ],
    max_tokens=150,
    temperature=0.7
)
```

### Code Generation
```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Write a Python function to calculate fibonacci numbers"}
    ]
)
```

### Function Calling
```python
functions = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["location"]
        }
    }
]

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "What's the weather like in Tokyo?"}
    ],
    functions=functions,
    function_call="auto"
)
```

### Image Generation with DALL-E
```python
response = client.images.generate(
    model="dall-e-3",
    prompt="A futuristic city skyline at sunset",
    size="1024x1024",
    quality="standard",
    n=1,
)

image_url = response.data[0].url
```

### Speech-to-Text with Whisper
```python
audio_file = open("speech.mp3", "rb")
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file
)
print(transcript.text)
```

### Text-to-Speech
```python
response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Hello! This is a text-to-speech conversion."
)

response.stream_to_file("output.mp3")
```

## Step 5: Error Handling

### Robust Error Handling
```python
from openai import OpenAI
import openai

client = OpenAI()

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Hello!"}
        ]
    )
    print(response.choices[0].message.content)

except openai.RateLimitError as e:
    print(f"Rate limit exceeded: {e}")

except openai.APIError as e:
    print(f"API error: {e}")

except openai.AuthenticationError as e:
    print(f"Authentication error: {e}")

except Exception as e:
    print(f"Unexpected error: {e}")
```

## Step 6: Best Practices

### API Key Security
- Never hardcode API keys in your source code
- Use environment variables or secure key management systems
- Rotate API keys regularly
- Monitor API usage for unusual activity

### Cost Management
- Set usage limits in your OpenAI dashboard
- Monitor token consumption
- Use appropriate models (GPT-3.5 for simple tasks, GPT-4 for complex ones)
- Implement caching for repeated queries

### Performance Optimization
- Use streaming for real-time applications
- Implement connection pooling for high-volume applications
- Cache responses when appropriate
- Use async/await for concurrent requests

### Prompt Engineering
- Be specific and clear in your prompts
- Provide examples when needed
- Use system messages to set context
- Experiment with temperature and max_tokens parameters

## Next Steps

### Explore Advanced Features
1. **Function Calling**: Integrate tools and external APIs
2. **Fine-tuning**: Create custom models for your specific use case
3. **Embeddings**: Build semantic search and recommendation systems
4. **Assistants API**: Create sophisticated AI assistants

### Learn More
- [API Reference Documentation](https://platform.openai.com/docs/api-reference)
- [Guides and Tutorials](https://platform.openai.com/docs/guides)
- [Examples Repository](https://github.com/openai/openai-quickstart-python)
- [Community Forum](https://community.openai.com)

### Production Considerations
- Implement monitoring and logging
- Set up alerts for API failures
- Design for scalability
- Plan for disaster recovery

## Troubleshooting

### Common Issues

**Authentication Error**
- Verify your API key is correct
- Ensure the API key is properly set in environment variables
- Check that your account has sufficient credits

**Rate Limit Error**
- Implement exponential backoff retry logic
- Consider upgrading your account tier
- Optimize your requests to reduce frequency

**Model Not Found**
- Verify the model name is correct
- Check if you have access to the requested model
- Use `client.models.list()` to see available models

### Getting Help
- Check the [OpenAI Status Page](https://status.openai.com)
- Review the [Documentation](https://platform.openai.com/docs)
- Ask questions in the [Community Forum](https://community.openai.com)
- Contact [OpenAI Support](https://help.openai.com)

---

*This quickstart guide provides the essential steps to begin using the OpenAI API. For more detailed information, refer to the complete API documentation.*
