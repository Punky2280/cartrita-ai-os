# Assistants API

> **Source**: https://platform.openai.com/docs/api-reference/assistants
> **Last Updated**: September 17, 2025

## Overview

The Assistants API allows you to build AI assistants within your own applications. An Assistant has instructions and can leverage models, tools, and knowledge to respond to user queries. The Assistants API currently supports three types of tools: Code Interpreter, Retrieval, and Function calling.

## Assistant Object

Represents an assistant that can call the model and use tools.

### Assistant Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | The identifier, which can be referenced in API endpoints. |
| `object` | string | The object type, which is always `assistant`. |
| `created_at` | integer | The Unix timestamp (in seconds) for when the assistant was created. |
| `name` | string | The name of the assistant. The maximum length is 256 characters. |
| `description` | string | The description of the assistant. The maximum length is 512 characters. |
| `model` | string | ID of the model to use. |
| `instructions` | string | The system instructions that the assistant uses. |
| `tools` | array | A list of tool enabled on the assistant. |
| `file_ids` | array | A list of file IDs attached to this assistant. |
| `metadata` | object | Set of 16 key-value pairs that can be attached to an object. |

## Create Assistant

Create an assistant with a model and instructions.

### HTTP Request
```
POST https://api.openai.com/v1/assistants
```

### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | ID of the model to use. |
| `name` | string | No | The name of the assistant. |
| `description` | string | No | The description of the assistant. |
| `instructions` | string | No | The system instructions that the assistant uses. |
| `tools` | array | No | A list of tool enabled on the assistant. |
| `file_ids` | array | No | A list of file IDs attached to this assistant. |
| `metadata` | object | No | Set of 16 key-value pairs. |

### Example Request

#### Basic Assistant Creation
```python
from openai import OpenAI

client = OpenAI()

assistant = client.beta.assistants.create(
    name="Math Tutor",
    instructions="You are a personal math tutor. When asked a question, write and run Python code to answer the question.",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4"
)

print(assistant)
```

#### Assistant with Multiple Tools
```python
from openai import OpenAI

client = OpenAI()

assistant = client.beta.assistants.create(
    name="Data Analyst",
    instructions="You are a data analyst assistant. Help users analyze data and create visualizations.",
    tools=[
        {"type": "code_interpreter"},
        {"type": "retrieval"},
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather information for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ],
    model="gpt-4"
)

print(f"Created assistant: {assistant.id}")
```

#### cURL Example
```bash
curl "https://api.openai.com/v1/assistants" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "OpenAI-Beta: assistants=v1" \
  -d '{
    "instructions": "You are a personal math tutor. When asked a question, write and run Python code to answer the question.",
    "name": "Math Tutor",
    "tools": [{"type": "code_interpreter"}],
    "model": "gpt-4"
  }'
```

## List Assistants

Returns a list of assistants.

### HTTP Request
```
GET https://api.openai.com/v1/assistants
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | A limit on the number of objects to be returned. |
| `order` | string | Sort order by the created_at timestamp of the objects. |
| `after` | string | A cursor for use in pagination. |
| `before` | string | A cursor for use in pagination. |

### Example Request

```python
from openai import OpenAI

client = OpenAI()

assistants = client.beta.assistants.list(
    order="desc",
    limit=20
)

print(f"Found {len(assistants.data)} assistants:")
for assistant in assistants.data:
    print(f"- {assistant.name}: {assistant.id}")
```

## Retrieve Assistant

Retrieves an assistant.

### HTTP Request
```
GET https://api.openai.com/v1/assistants/{assistant_id}
```

### Example Request

```python
from openai import OpenAI

client = OpenAI()

assistant = client.beta.assistants.retrieve("asst_abc123")

print(f"Assistant: {assistant.name}")
print(f"Instructions: {assistant.instructions}")
print(f"Tools: {[tool.type for tool in assistant.tools]}")
```

## Modify Assistant

Modifies an assistant.

### HTTP Request
```
POST https://api.openai.com/v1/assistants/{assistant_id}
```

### Example Request

```python
from openai import OpenAI

client = OpenAI()

assistant = client.beta.assistants.update(
    "asst_abc123",
    instructions="You are an advanced math tutor. Solve problems step by step and explain your reasoning.",
    name="Advanced Math Tutor",
    tools=[
        {"type": "code_interpreter"},
        {"type": "retrieval"}
    ]
)

print(f"Updated assistant: {assistant.name}")
```

## Delete Assistant

Delete an assistant.

### HTTP Request
```
DELETE https://api.openai.com/v1/assistants/{assistant_id}
```

### Example Request

```python
from openai import OpenAI

client = OpenAI()

response = client.beta.assistants.delete("asst_abc123")
print(f"Deleted: {response.deleted}")
```

## Tools

The Assistants API supports three types of tools: Code Interpreter, Retrieval, and Function calling.

### Code Interpreter

Code Interpreter allows the assistants to write and run Python code in a sandboxed execution environment.

```python
tools = [{"type": "code_interpreter"}]
```

#### Capabilities
- Write and execute Python code
- Handle file uploads and downloads
- Generate charts and graphs
- Process data and perform calculations

### Retrieval

Retrieval augments the assistant with knowledge from outside its model, such as proprietary product information or documents.

```python
tools = [{"type": "retrieval"}]
```

#### File Requirements
- Supported formats: `.pdf`, `.txt`, `.md`, `.docx`, `.pptx`, `.xlsx`
- Maximum file size: 512 MB
- Maximum files per assistant: 20

### Function Calling

Function calling allows you to describe functions to the assistants and have them intelligently choose to output a JSON object containing arguments to call those functions.

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"]
                    }
                },
                "required": ["location"]
            }
        }
    }
]
```

## Threads

A thread represents a conversation. We recommend creating one thread per user as soon as the user initiates the conversation.

### Thread Object

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | The identifier, which can be referenced in API endpoints. |
| `object` | string | The object type, which is always `thread`. |
| `created_at` | integer | The Unix timestamp for when the thread was created. |
| `metadata` | object | Set of 16 key-value pairs. |

### Create Thread

```python
from openai import OpenAI

client = OpenAI()

thread = client.beta.threads.create()
print(f"Created thread: {thread.id}")
```

### Create Thread with Messages

```python
from openai import OpenAI

client = OpenAI()

thread = client.beta.threads.create(
    messages=[
        {
            "role": "user",
            "content": "Create 3 data visualizations based on the trends in this file.",
            "file_ids": ["file-abc123"]
        }
    ]
)

print(f"Created thread with messages: {thread.id}")
```

## Messages

A message contains text, and optionally any files that you allow the user to upload.

### Message Object

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | The identifier, which can be referenced in API endpoints. |
| `object` | string | The object type, which is always `thread.message`. |
| `created_at` | integer | The Unix timestamp for when the message was created. |
| `thread_id` | string | The thread ID that this message belongs to. |
| `role` | string | The entity that produced the message. One of `user` or `assistant`. |
| `content` | array | The content of the message in array of text and/or images. |
| `file_ids` | array | A list of file IDs that the assistant should use. |
| `metadata` | object | Set of 16 key-value pairs. |

### Create Message

```python
from openai import OpenAI

client = OpenAI()

message = client.beta.threads.messages.create(
    thread_id="thread_abc123",
    role="user",
    content="I need to solve the equation `3x + 11 = 14`. Can you help me?"
)

print(f"Created message: {message.id}")
```

### List Messages

```python
from openai import OpenAI

client = OpenAI()

messages = client.beta.threads.messages.list(
    thread_id="thread_abc123"
)

for message in messages.data:
    print(f"{message.role}: {message.content[0].text.value}")
```

## Runs

A run represents an execution of an assistant on a thread.

### Run Object

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | The identifier, which can be referenced in API endpoints. |
| `object` | string | The object type, which is always `thread.run`. |
| `created_at` | integer | The Unix timestamp for when the run was created. |
| `thread_id` | string | The ID of the thread that was executed on as part of this run. |
| `assistant_id` | string | The ID of the assistant used for execution of this run. |
| `status` | string | The status of the run. |
| `required_action` | object | Details on the action required to continue the run. |
| `last_error` | object | The last error associated with this run. |
| `expires_at` | integer | The Unix timestamp for when the run will expire. |
| `started_at` | integer | The Unix timestamp for when the run was started. |
| `cancelled_at` | integer | The Unix timestamp for when the run was cancelled. |
| `failed_at` | integer | The Unix timestamp for when the run failed. |
| `completed_at` | integer | The Unix timestamp for when the run was completed. |
| `model` | string | The model that the assistant used for this run. |
| `instructions` | string | The instructions that the assistant used for this run. |
| `tools` | array | The list of tools that the assistant used for this run. |
| `file_ids` | array | The list of File IDs the assistant used for this run. |
| `metadata` | object | Set of 16 key-value pairs. |

### Create Run

```python
from openai import OpenAI

client = OpenAI()

run = client.beta.threads.runs.create(
    thread_id="thread_abc123",
    assistant_id="asst_abc123"
)

print(f"Created run: {run.id}")
print(f"Status: {run.status}")
```

### Check Run Status

```python
from openai import OpenAI
import time

client = OpenAI()

def wait_for_run_completion(thread_id, run_id):
    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )

        if run.status == "completed":
            print("Run completed!")
            return run
        elif run.status == "failed":
            print(f"Run failed: {run.last_error}")
            return run
        elif run.status == "requires_action":
            print("Run requires action")
            return run
        else:
            print(f"Run status: {run.status}")
            time.sleep(1)

# Usage
run = wait_for_run_completion("thread_abc123", "run_abc123")
```

### Handle Required Actions

```python
from openai import OpenAI
import json

client = OpenAI()

def handle_required_action(thread_id, run_id):
    run = client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run_id
    )

    if run.status == "requires_action":
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        tool_outputs = []

        for tool_call in tool_calls:
            if tool_call.function.name == "get_current_weather":
                # Call your function here
                function_args = json.loads(tool_call.function.arguments)
                weather_data = get_current_weather(function_args["location"])

                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(weather_data)
                })

        # Submit tool outputs
        run = client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )

        return run

    return run

def get_current_weather(location):
    # Your weather API implementation
    return {"temperature": "22°C", "condition": "sunny"}
```

## Complete Assistant Example

Here's a complete example of creating and using an assistant:

```python
from openai import OpenAI
import time
import json

client = OpenAI()

def create_math_tutor():
    """Create a math tutor assistant"""
    assistant = client.beta.assistants.create(
        name="Math Tutor",
        instructions="""You are a personal math tutor. When asked a math question:
        1. Analyze the problem carefully
        2. Show your work step by step
        3. Use code interpreter when helpful for calculations
        4. Explain concepts clearly
        5. Provide practice problems when appropriate""",
        tools=[{"type": "code_interpreter"}],
        model="gpt-4"
    )
    return assistant

def create_conversation_thread():
    """Create a new conversation thread"""
    thread = client.beta.threads.create()
    return thread

def ask_question(thread_id, assistant_id, question):
    """Ask a question and get the response"""
    # Add user message
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=question
    )

    # Create run
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # Wait for completion
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )

        if run_status.status == "completed":
            break
        elif run_status.status == "failed":
            print(f"Run failed: {run_status.last_error}")
            return None

        time.sleep(1)

    # Get messages
    messages = client.beta.threads.messages.list(
        thread_id=thread_id,
        order="asc"
    )

    # Return the latest assistant message
    for message in reversed(messages.data):
        if message.role == "assistant":
            return message.content[0].text.value

    return None

# Example usage
def main():
    # Create assistant
    assistant = create_math_tutor()
    print(f"Created assistant: {assistant.id}")

    # Create thread
    thread = create_conversation_thread()
    print(f"Created thread: {thread.id}")

    # Ask questions
    questions = [
        "Solve the equation 2x + 5 = 15",
        "What is the derivative of x^3 + 2x^2 - 5x + 1?",
        "Calculate the area of a circle with radius 7"
    ]

    for question in questions:
        print(f"\nQ: {question}")
        response = ask_question(thread.id, assistant.id, question)
        print(f"A: {response}")

if __name__ == "__main__":
    main()
```

## File Management for Assistants

### Upload File for Assistant

```python
from openai import OpenAI

client = OpenAI()

# Upload file
file = client.files.create(
    file=open("data.pdf", "rb"),
    purpose="assistants"
)

# Create assistant with file
assistant = client.beta.assistants.create(
    name="Data Analyst",
    instructions="You are a data analyst. Analyze the uploaded file and provide insights.",
    model="gpt-4",
    tools=[{"type": "retrieval"}],
    file_ids=[file.id]
)

print(f"Created assistant with file: {assistant.id}")
```

### Add File to Existing Assistant

```python
from openai import OpenAI

client = OpenAI()

# Upload new file
file = client.files.create(
    file=open("additional_data.xlsx", "rb"),
    purpose="assistants"
)

# Update assistant with new file
assistant = client.beta.assistants.update(
    "asst_abc123",
    file_ids=["file_abc123", file.id]  # Include existing and new files
)

print(f"Updated assistant with new file")
```

## Error Handling

### Common Errors

```python
from openai import OpenAI
import openai

client = OpenAI()

def safe_assistant_operation():
    try:
        assistant = client.beta.assistants.create(
            name="Test Assistant",
            instructions="You are a helpful assistant.",
            model="gpt-4"
        )
        return assistant

    except openai.BadRequestError as e:
        print(f"Bad request: {e}")
    except openai.AuthenticationError as e:
        print(f"Authentication error: {e}")
    except openai.PermissionDeniedError as e:
        print(f"Permission denied: {e}")
    except openai.RateLimitError as e:
        print(f"Rate limit exceeded: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return None
```

## Best Practices

### Assistant Design
- Write clear, specific instructions
- Define the assistant's role and capabilities
- Use appropriate tools for the task
- Test thoroughly with various inputs

### Thread Management
- Create one thread per conversation/user
- Keep threads focused on related topics
- Clean up old threads when no longer needed
- Use metadata for organization

### File Management
- Optimize file formats for retrieval
- Keep file sizes reasonable
- Update file_ids when files change
- Monitor file usage and costs

### Performance Optimization
- Cache assistant and thread IDs
- Batch operations when possible
- Use appropriate models for complexity
- Monitor run statuses efficiently

---

*This documentation covers the complete Assistants API. Use assistants to build sophisticated AI applications with persistent conversations and tool integration.*
