# LangGraph Server Thread ID Guide

## Overview

When running with `langgraph dev`, thread_id is specified differently than direct Python code. This guide shows all the methods.

## Method 1: LangGraph Studio UI (Easiest)

When you run `langgraph dev`, the Studio UI opens automatically.

### Steps:

1. **Start the server**:
```bash
langgraph dev
```

2. **In the Studio UI**: Look for the **thread selector** in the top-right corner

   ```
   ┌─────────────────────────────────────────────┐
   │  Thread: [my-research-thread-001] [▼]      │
   └─────────────────────────────────────────────┘
   ```

3. **Options**:
   - **New thread**: Click dropdown → "New thread" → Enter thread_id
   - **Resume thread**: Click dropdown → Select from list of existing threads
   - **Auto-generated**: Leave blank, Studio creates unique thread_id

### Example Flow:

```
1. Open Studio → "New thread" → Enter: "quantum-research-001"
2. Send message: "Research quantum computing"
3. Close Studio
4. Later: Open Studio → Select "quantum-research-001" from dropdown
5. Send message: "Tell me more" → Conversation continues!
```

## Method 2: HTTP API (For Custom UIs)

The LangGraph server exposes a REST API.

### Endpoint:
```
POST http://localhost:8123/runs/stream
```

### Request Format:

```bash
curl -X POST http://localhost:8123/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "research",
    "thread_id": "my-custom-thread-123",
    "input": {
      "messages": [
        {"role": "user", "content": "Research quantum computing"}
      ]
    },
    "stream_mode": ["updates"]
  }'
```

### Key Parameters:

- `assistant_id`: The graph name (from langgraph.json → "research")
- `thread_id`: Your custom thread identifier
- `input`: The input to the graph

### Resume Example:

```bash
# First session
curl -X POST http://localhost:8123/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "research",
    "thread_id": "quantum-001",
    "input": {
      "messages": [{"role": "user", "content": "What is quantum computing?"}]
    }
  }'

# Later session - SAME thread_id resumes conversation
curl -X POST http://localhost:8123/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "research",
    "thread_id": "quantum-001",
    "input": {
      "messages": [{"role": "user", "content": "Tell me more"}]
    }
  }'
```

## Method 3: LangGraph SDK (Python Client)

Use the official SDK to connect to LangGraph server.

### Install:
```bash
uv add langgraph-sdk
```

### Code Example:

```python
from langgraph_sdk import get_client

# Connect to local server
client = get_client(url="http://localhost:8123")

# Start new conversation
thread_id = "my-research-session-001"

response = client.runs.create(
    assistant_id="research",
    thread_id=thread_id,  # ⭐ Specify thread_id here
    input={
        "messages": [
            {"role": "user", "content": "Research quantum computing"}
        ]
    }
)

print(response)

# Resume conversation later
response = client.runs.create(
    assistant_id="research",
    thread_id=thread_id,  # Same thread_id = resume
    input={
        "messages": [
            {"role": "user", "content": "Tell me more about qubits"}
        ]
    }
)
```

### Check Thread State:

```python
# Get current state of thread
state = client.threads.get_state(thread_id=thread_id)
print(f"Messages: {len(state['values']['messages'])}")
print(f"Files: {state['values'].get('files', {}).keys()}")

# List all threads
threads = client.threads.list()
for thread in threads:
    print(f"Thread: {thread['thread_id']}")
```

### Streaming:

```python
# Stream responses
for chunk in client.runs.stream(
    assistant_id="research",
    thread_id=thread_id,
    input={"messages": [{"role": "user", "content": "Research AI"}]},
    stream_mode="updates"
):
    print(chunk)
```

## Method 4: JavaScript/TypeScript Client

### Install:
```bash
npm install @langchain/langgraph-sdk
```

### Code Example:

```typescript
import { Client } from "@langchain/langgraph-sdk";

// Connect to server
const client = new Client({ apiUrl: "http://localhost:8123" });

// Start conversation
const threadId = "my-research-session-001";

const response = await client.runs.create({
  assistantId: "research",
  threadId: threadId,  // ⭐ Specify thread_id here
  input: {
    messages: [
      { role: "user", content: "Research quantum computing" }
    ]
  }
});

// Resume conversation
const response2 = await client.runs.create({
  assistantId: "research",
  threadId: threadId,  // Same thread_id = resume
  input: {
    messages: [
      { role: "user", content: "Tell me more" }
    ]
  }
});
```

## Method 5: Deep Agents UI

If you're using the [deep-agents-ui](https://github.com/langchain-ai/deep-agents-ui):

### Setup:
```bash
git clone https://github.com/langchain-ai/deep-agents-ui.git
cd deep-agents-ui
yarn install
yarn dev
```

### In the UI:

1. The UI automatically manages thread_id
2. **New conversation** → Creates new thread_id
3. **Select conversation** from sidebar → Loads that thread_id
4. All thread management is automatic!

## Where Are Threads Stored?

### Local Development (`langgraph dev`):

Checkpoints are stored in `.langgraph_api/`:
```bash
ls -la .langgraph_api/
# .langgraph_checkpoint.1.pckl
# .langgraph_checkpoint.2.pckl
# ...
```

These persist across server restarts!

### Production Deployment:

LangGraph Cloud automatically uses managed checkpointer:
- No configuration needed
- Automatically persisted
- Scalable storage

## Common Patterns

### Pattern 1: User-specific threads

```python
# Generate thread_id per user
thread_id = f"user-{user_id}-{session_id}"

client.runs.create(
    assistant_id="research",
    thread_id=thread_id,
    input={"messages": [{"role": "user", "content": query}]}
)
```

### Pattern 2: Date-based threads

```python
from datetime import date

# One thread per day per user
thread_id = f"user-{user_id}-{date.today()}"
```

### Pattern 3: Topic-based threads

```python
# Separate thread for each research topic
thread_id = f"research-{topic_slug}-{user_id}"
```

## Retrieve Thread History

### Via SDK:

```python
# Get all messages from a thread
state = client.threads.get_state(thread_id="my-thread-001")
messages = state['values']['messages']

for msg in messages:
    print(f"{msg.type}: {msg.content}")
```

### Via HTTP:

```bash
curl http://localhost:8123/threads/my-thread-001/state
```

## Delete Thread

### Via SDK:

```python
client.threads.delete(thread_id="old-thread-001")
```

### Via HTTP:

```bash
curl -X DELETE http://localhost:8123/threads/old-thread-001
```

## Configuration

### Enable Checkpointing in `langgraph.json`:

Your current config:
```json
{
  "dependencies": ["."],
  "graphs": {
    "research": "./agent.py:agent"
  },
  "env": ".env"
}
```

**Checkpointing is automatic!** LangGraph server creates checkpointer by default.

### Custom Checkpointer (Optional):

If you want to use PostgreSQL instead of file-based:

1. **Install**:
```bash
uv add langgraph-checkpoint-postgres
```

2. **Modify `agent.py`**:
```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost:5432/checkpoints"
)

agent = create_deep_agent(
    model=model,
    checkpointer=checkpointer,
)
```

3. **Set environment variable**:
```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/checkpoints
```

## Testing Thread Persistence

### Test Script:

```python
from langgraph_sdk import get_client

client = get_client(url="http://localhost:8123")

# Session 1
print("Starting session 1...")
client.runs.create(
    assistant_id="research",
    thread_id="test-persistence",
    input={"messages": [{"role": "user", "content": "Hello"}]}
)

# Stop server (Ctrl+C), then restart with `langgraph dev`

# Session 2 - after restart
print("Starting session 2 (after restart)...")
response = client.runs.create(
    assistant_id="research",
    thread_id="test-persistence",  # Same thread_id
    input={"messages": [{"role": "user", "content": "Continue"}]}
)

# Agent remembers "Hello" from session 1! ✅
```

## Summary

| Method | When to Use | Thread ID Specified |
|--------|-------------|-------------------|
| **Studio UI** | Development, debugging | Via dropdown in UI |
| **HTTP API** | Custom web apps | In POST body: `thread_id` |
| **Python SDK** | Python apps, scripts | Parameter: `thread_id=` |
| **JavaScript SDK** | Web/Node.js apps | Parameter: `threadId:` |
| **Deep Agents UI** | End-user interface | Automatic management |

## Quick Reference

```python
# Python SDK
from langgraph_sdk import get_client

client = get_client(url="http://localhost:8123")

# Create/resume thread
client.runs.create(
    assistant_id="research",
    thread_id="my-thread",  # ⭐ THIS IS THE KEY
    input={"messages": [{"role": "user", "content": "Hi"}]}
)
```

```bash
# HTTP API
curl -X POST http://localhost:8123/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "research",
    "thread_id": "my-thread",  # ⭐ THIS IS THE KEY
    "input": {"messages": [{"role": "user", "content": "Hi"}]}
  }'
```

The key insight: **thread_id is always part of the request**, not the server config!
