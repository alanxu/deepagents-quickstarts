# Thread ID Quick Reference for LangGraph Server

## TL;DR

When using LangGraph server (`langgraph dev`), specify `thread_id` in **every request** to enable session persistence and resumption.

## Quick Start

### 1. Start the server
```bash
langgraph dev
```

### 2. Use thread_id in requests

**Option A: Studio UI**
- Open http://localhost:8123
- Click thread dropdown (top-right)
- Enter custom thread_id or select existing

**Option B: Python SDK**
```python
from langgraph_sdk import get_client

client = get_client(url="http://localhost:8123")

# Specify thread_id here ⭐
client.runs.create(
    assistant_id="research",
    thread_id="my-session-001",  # ⭐
    input={"messages": [{"role": "user", "content": "Hello"}]}
)

# Resume later with same thread_id
client.runs.create(
    assistant_id="research",
    thread_id="my-session-001",  # Same ID = resume
    input={"messages": [{"role": "user", "content": "Continue"}]}
)
```

**Option C: HTTP API**
```bash
curl -X POST http://localhost:8123/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "research",
    "thread_id": "my-session-001",
    "input": {"messages": [{"role": "user", "content": "Hello"}]}
  }'
```

## Key Concepts

| Concept | Explanation |
|---------|-------------|
| **thread_id** | Unique identifier for a conversation thread |
| **Same thread_id** | Resumes existing conversation (loads checkpoints) |
| **Different thread_id** | Starts new independent conversation |
| **Checkpoints** | Automatically saved in `.langgraph_api/` |
| **Persistence** | Survives server restarts |

## Where thread_id is specified

❌ **NOT in `langgraph.json`** (server config)
❌ **NOT in `agent.py`** (agent code)
✅ **In each API request/SDK call** (runtime)

## Examples

### Example 1: User sessions
```python
# User Alice
thread_id = "user-alice-main"
client.runs.create(assistant_id="research", thread_id=thread_id, ...)

# User Bob (separate conversation)
thread_id = "user-bob-main"
client.runs.create(assistant_id="research", thread_id=thread_id, ...)
```

### Example 2: Topic-based
```python
# Quantum research
thread_id = "research-quantum-001"
client.runs.create(assistant_id="research", thread_id=thread_id, ...)

# AI research (separate)
thread_id = "research-ai-001"
client.runs.create(assistant_id="research", thread_id=thread_id, ...)
```

### Example 3: Daily sessions
```python
from datetime import date

# One thread per day
thread_id = f"daily-{date.today()}"
client.runs.create(assistant_id="research", thread_id=thread_id, ...)
```

## Try It

1. **Install SDK**:
   ```bash
   uv add langgraph-sdk
   ```

2. **Start server** (in one terminal):
   ```bash
   langgraph dev
   ```

3. **Run example** (in another terminal):
   ```bash
   uv run python langgraph_client_example.py
   ```

## Inspect Threads

### View thread state
```python
state = client.threads.get_state(thread_id="my-thread")
print(state['values']['messages'])
```

### List all threads
```python
threads = client.threads.list()
for t in threads:
    print(t['thread_id'])
```

### Delete thread
```python
client.threads.delete(thread_id="old-thread")
```

## Common Patterns

```python
from langgraph_sdk import get_client

client = get_client(url="http://localhost:8123")

# Pattern 1: New conversation
response = client.runs.create(
    assistant_id="research",
    thread_id="new-thread-001",
    input={"messages": [{"role": "user", "content": "Hello"}]}
)

# Pattern 2: Resume conversation
response = client.runs.create(
    assistant_id="research",
    thread_id="new-thread-001",  # Same ID
    input={"messages": [{"role": "user", "content": "Continue"}]}
)

# Pattern 3: Stream responses
for chunk in client.runs.stream(
    assistant_id="research",
    thread_id="my-thread",
    input={"messages": [{"role": "user", "content": "Hi"}]},
    stream_mode=["updates"]
):
    print(chunk)
```

## Troubleshooting

### "Cannot connect to server"
→ Make sure `langgraph dev` is running in another terminal

### "Thread not found"
→ Check spelling of thread_id, or create new thread with that ID

### "Checkpoints not persisting"
→ Check `.langgraph_api/` directory exists and has `.pckl` files

## Files

- `LANGGRAPH_SERVER_THREADS.md` - Detailed guide
- `langgraph_client_example.py` - Runnable examples
- `.langgraph_api/` - Where checkpoints are stored

## See Also

- [LangGraph Server Docs](https://langchain-ai.github.io/langgraph/cloud/reference/api/api_ref/)
- [LangGraph SDK](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/)
- `MEMORY_GUIDE.md` - Long-term memory architecture
