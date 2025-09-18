# Authentication

> **Source**: https://platform.openai.com/docs/api-reference/authentication
> **Last Updated**: September 17, 2025

## Overview

The OpenAI API uses API keys for authentication. Visit your [API Keys page](https://platform.openai.com/account/api-keys) to retrieve the API key you'll use in your requests.

**Remember that your API key is a secret!** Do not share it with others or expose it in any client-side code (browsers, apps). Production requests must be routed through your own backend server where your API key can be securely loaded from an environment variable or key management service.

## API Key Types

### User API Keys
- Associated with your personal OpenAI account
- Used for development and personal projects
- Have the same permissions as your account

### Service Account API Keys
- Associated with a service account within an organization
- Used for production applications
- Can have restricted permissions
- Recommended for team and production use

## Authentication Methods

### Bearer Token Authentication

All API requests should include your API key in an Authorization header:

```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Setting API Keys

#### Environment Variables (Recommended)

**Linux/macOS:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=your-api-key-here
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

#### Using .env Files

Create a `.env` file in your project root:
```env
OPENAI_API_KEY=your-api-key-here
```

**Python with python-dotenv:**
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
```

**Node.js with dotenv:**
```javascript
require('dotenv').config();
const apiKey = process.env.OPENAI_API_KEY;
```

## Client Library Setup

### Python

#### Automatic Environment Variable Loading
```python
from openai import OpenAI

# API key is automatically read from OPENAI_API_KEY environment variable
client = OpenAI()
```

#### Manual API Key Setting
```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key-here"
)
```

#### Using Custom Base URL
```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key-here",
    base_url="https://your-proxy-server.com/v1"
)
```

### Node.js

#### Automatic Environment Variable Loading
```javascript
import OpenAI from 'openai';

// API key is automatically read from OPENAI_API_KEY environment variable
const openai = new OpenAI();
```

#### Manual API Key Setting
```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: 'your-api-key-here',
});
```

#### Using Custom Configuration
```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  organization: 'your-org-id',
  project: 'your-project-id',
});
```

### cURL Examples

#### Basic Request
```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
```

#### With Organization Header
```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "OpenAI-Organization: org-your-org-id" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
```

## Organization and Project IDs

### Organization Header
For users who belong to multiple organizations, you can pass a header to specify which organization is used for an API request:

```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "OpenAI-Organization: org-your-org-id"
```

### Project Header
You can also specify which project within an organization to use:

```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "OpenAI-Organization: org-your-org-id" \
  -H "OpenAI-Project: proj-your-project-id"
```

## Security Best Practices

### API Key Management

#### Do Not Expose Keys
- **Never** include API keys in client-side code
- **Never** commit API keys to version control
- **Never** share API keys in public forums or documentation

#### Use Environment Variables
```python
# Good ✅
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Bad ❌
from openai import OpenAI

client = OpenAI(api_key="sk-proj-abc123...")
```

#### Secure Storage Options
- Environment variables
- Secret management services (AWS Secrets Manager, Azure Key Vault, etc.)
- Encrypted configuration files
- Container secrets (Kubernetes secrets, Docker secrets)

### Production Security

#### Backend Proxy Pattern
Create a backend API that handles OpenAI requests:

```python
# Backend service
from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/api/chat', methods=['POST'])
def chat():
    # Validate request, check authentication, etc.
    user_message = request.json.get('message')

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_message}]
    )

    return jsonify({"response": response.choices[0].message.content})
```

#### Rate Limiting and Monitoring
```python
from functools import wraps
import time

def rate_limit(calls_per_minute=60):
    def decorator(func):
        last_called = [0.0]

        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = 60.0 / calls_per_minute - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

@rate_limit(calls_per_minute=30)
def make_openai_request():
    # Your OpenAI API call here
    pass
```

### Input Validation and Sanitization

```python
import re
from openai import OpenAI

def sanitize_input(user_input):
    # Remove potential injection attempts
    cleaned = re.sub(r'[^\w\s\-.,!?]', '', user_input)
    # Limit length
    return cleaned[:1000]

def safe_chat_completion(user_input):
    client = OpenAI()

    # Sanitize input
    safe_input = sanitize_input(user_input)

    # Add safety instructions
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Do not generate harmful content."},
        {"role": "user", "content": safe_input}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        # Log error securely (without exposing API key)
        print(f"API request failed: {type(e).__name__}")
        return "Sorry, I couldn't process your request."
```

## Error Handling

### Authentication Errors

#### Invalid API Key
```json
{
  "error": {
    "message": "Incorrect API key provided: sk-proj-abc*****. You can find your API key at https://platform.openai.com/account/api-keys.",
    "type": "invalid_request_error",
    "param": null,
    "code": "invalid_api_key"
  }
}
```

#### Missing API Key
```json
{
  "error": {
    "message": "You didn't provide an API key. You need to provide your API key in an Authorization header using Bearer auth (i.e. Authorization: Bearer YOUR_KEY).",
    "type": "invalid_request_error",
    "param": null,
    "code": null
  }
}
```

### Python Error Handling
```python
import openai

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello!"}]
    )
except openai.AuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Handle invalid API key
except openai.PermissionDeniedError as e:
    print(f"Permission denied: {e}")
    # Handle insufficient permissions
except openai.RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Handle rate limiting
except Exception as e:
    print(f"Unexpected error: {e}")
```

## API Key Rotation

### Best Practices for Key Rotation

1. **Regular Rotation**: Rotate API keys regularly (monthly or quarterly)
2. **Zero-Downtime Rotation**: Use multiple keys during transition periods
3. **Automated Rotation**: Use secret management services for automatic rotation
4. **Monitoring**: Monitor API key usage and detect anomalies

### Implementation Example

```python
import os
from openai import OpenAI

class RotatingAPIKeyClient:
    def __init__(self):
        self.primary_key = os.getenv("OPENAI_API_KEY_PRIMARY")
        self.backup_key = os.getenv("OPENAI_API_KEY_BACKUP")
        self.current_client = OpenAI(api_key=self.primary_key)

    def make_request(self, **kwargs):
        try:
            return self.current_client.chat.completions.create(**kwargs)
        except openai.AuthenticationError:
            # Switch to backup key
            self.current_client = OpenAI(api_key=self.backup_key)
            return self.current_client.chat.completions.create(**kwargs)
```

## Compliance and Auditing

### Logging API Key Usage

```python
import logging
import hashlib
from openai import OpenAI

# Set up secure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuditedOpenAIClient:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        # Hash the API key for logging (never log the actual key)
        self.key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:8]

    def chat_completion(self, **kwargs):
        logger.info(f"API request initiated with key hash: {self.key_hash}")

        try:
            response = self.client.chat.completions.create(**kwargs)
            logger.info(f"API request successful, tokens used: {response.usage.total_tokens}")
            return response
        except Exception as e:
            logger.error(f"API request failed: {type(e).__name__}")
            raise
```

### GDPR and Privacy Compliance

- Use the `user` parameter to identify users for data deletion requests
- Implement data retention policies
- Provide clear privacy notices about AI processing
- Allow users to opt-out of AI processing

---

*This documentation covers authentication and security best practices for the OpenAI API. Always follow security best practices and keep your API keys secure.*
