# Long-Term Memory Guide for Deep Agents

## Overview

This guide explains how to implement long-term memory and session resumption in your deep research agent.

## Memory Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Thread ID: "user-123-session-1"                            │
│  ┌────────────────────────────────────────────────┐         │
│  │ Agent State                                     │         │
│  │ - messages: [msg1, msg2, ...]                  │         │
│  │ - files: {"/report.md": {...}}                 │         │
│  │ - todos: [...]                                 │         │
│  └────────────────────────────────────────────────┘         │
│                        ↓                                     │
│              SummarizationMiddleware                        │
│              (auto-compress old messages)                   │
│                        ↓                                     │
│  ┌────────────────────────────────────────────────┐         │
│  │ Checkpointer (Long-term Storage)               │         │
│  │                                                 │         │
│  │ Option 1: InMemorySaver (RAM only)            │         │
│  │ Option 2: PersistentDict (Pickle file)        │         │
│  │ Option 3: PostgresSaver (Database)            │         │
│  └────────────────────────────────────────────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## The Three Layers of Memory

### Layer 1: Short-term Memory (Messages State)
- **What**: Current conversation messages
- **Managed by**: LangGraph state
- **Lifetime**: Current execution
- **Auto-managed by**: `SummarizationMiddleware` (compresses when too long)

### Layer 2: Session Memory (Checkpointer)
- **What**: Saved snapshots of agent state
- **Managed by**: Checkpointer (InMemorySaver, PersistentDict, etc.)
- **Lifetime**: Depends on checkpointer type
- **Use for**: Resume conversations, time-travel, branching

### Layer 3: Long-term Memory (External Storage)
- **What**: Semantic search, knowledge base
- **Managed by**: You (custom implementation)
- **Use for**: Search across all conversations, context retrieval

## Checkpointer Options

### Option 1: InMemorySaver (Session-only)

**When to use**:
- Testing and development
- Single conversation per process
- Don't need to resume after restart

**Pros**:
- Fast (in-memory)
- No setup required
- Built-in

**Cons**:
- Lost when process ends
- Not suitable for production

**Example**:
```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

agent = create_deep_agent(
    model=model,
    checkpointer=checkpointer,
)
```

### Option 2: PersistentDict + InMemorySaver (File-based)

**When to use**:
- Development
- Single-user applications
- Need persistence across restarts
- Simple deployment

**Pros**:
- Persists across restarts
- Simple setup
- Built-in
- Good for prototyping

**Cons**:
- Not suitable for multi-user
- File-based (not scalable)
- Uses pickle (security concerns)

**Example**:
```python
from langgraph.checkpoint.memory import InMemorySaver, PersistentDict
import os

# Create persistent storage
storage = PersistentDict(filename="./checkpoints.db")
writes = PersistentDict(filename="./checkpoints.db.writes")
blobs = PersistentDict(filename="./checkpoints.db.blobs")

# Load existing data
if os.path.exists("./checkpoints.db"):
    storage.load()
if os.path.exists("./checkpoints.db.writes"):
    writes.load()
if os.path.exists("./checkpoints.db.blobs"):
    blobs.load()

# Create checkpointer with persistent storage
checkpointer = InMemorySaver(
    factory=lambda: storage
)

agent = create_deep_agent(
    model=model,
    checkpointer=checkpointer,
)
```

### Option 3: PostgresSaver (Production)

**When to use**:
- Production applications
- Multi-user systems
- Scalability required
- Team collaboration

**Pros**:
- Scalable
- Multi-user support
- Transaction support
- Query capabilities

**Cons**:
- Requires database setup
- More complex
- Additional dependency

**Setup**:
```bash
# Install the package
pip install langgraph-checkpoint-postgres

# Or with uv
uv add langgraph-checkpoint-postgres
```

**Example**:
```python
from langgraph.checkpoint.postgres import PostgresSaver

# PostgreSQL connection string
DB_URI = "postgresql://user:password@localhost:5432/checkpoints"

# Create checkpointer
checkpointer = PostgresSaver.from_conn_string(DB_URI)

# Setup tables (first time only)
checkpointer.setup()

agent = create_deep_agent(
    model=model,
    checkpointer=checkpointer,
)
```

## Thread IDs: The Key to Sessions

**Thread ID** is how you identify and resume conversations:

```python
# Each conversation needs a unique thread ID
config = {"configurable": {"thread_id": "user-123-research-session-1"}}

# Start conversation
agent.invoke(
    {"messages": [("user", "Research quantum computing")]},
    config=config
)

# Resume SAME conversation later (even after restart!)
agent.invoke(
    {"messages": [("user", "Tell me more about qubits")]},
    config=config  # Same thread_id = same conversation
)

# Start NEW conversation
agent.invoke(
    {"messages": [("user", "Research AI trends")]},
    config={"configurable": {"thread_id": "user-123-ai-session-1"}}
)
```

### Thread ID Strategies

**Per-user session**:
```python
thread_id = f"user-{user_id}-{session_id}"
```

**Per-topic**:
```python
thread_id = f"research-{topic}-{timestamp}"
```

**Per-date**:
```python
thread_id = f"{user_id}-{date.today()}"
```

## Common Patterns

### Pattern 1: Resume Previous Conversation

```python
def get_or_create_session(user_id: str) -> str:
    """Get today's session thread ID"""
    from datetime import date
    return f"user-{user_id}-{date.today()}"

# User comes back later
thread_id = get_or_create_session("alice")
config = {"configurable": {"thread_id": thread_id}}

# Automatically resumes from where they left off
result = agent.invoke(
    {"messages": [("user", "Continue research")]},
    config=config
)
```

### Pattern 2: View Conversation History

```python
def show_history(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}

    # Get current state
    state = agent.get_state(config)

    print(f"Messages: {len(state.values.get('messages', []))}")
    print(f"Files created: {list(state.values.get('files', {}).keys())}")

    # List all checkpoints (time-travel points)
    checkpoints = list(checkpointer.list(config))
    print(f"Total checkpoints: {len(checkpoints)}")

    for checkpoint in checkpoints:
        print(f"  - {checkpoint.config['configurable']['checkpoint_id']}")
```

### Pattern 3: Branch Conversations (Time-travel)

```python
# Get conversation history
config = {"configurable": {"thread_id": "research-001"}}
checkpoints = list(checkpointer.list(config))

# Go back to checkpoint 3
old_checkpoint = checkpoints[3]
old_config = old_checkpoint.config

# Continue from that point (creates new branch)
result = agent.invoke(
    {"messages": [("user", "Try a different approach")]},
    config=old_config
)
```

### Pattern 4: Multi-user Application

```python
def handle_user_query(user_id: str, query: str):
    # Each user gets their own thread
    thread_id = f"user-{user_id}-main"
    config = {"configurable": {"thread_id": thread_id}}

    # User's conversation is automatically loaded
    result = agent.invoke(
        {"messages": [("user", query)]},
        config=config
    )
    return result

# Alice's conversation
handle_user_query("alice", "Research quantum computing")

# Bob's conversation (completely separate)
handle_user_query("bob", "Research AI trends")

# Alice continues her conversation
handle_user_query("alice", "Tell me more about qubits")
```

## How Resumption Works

### Without Checkpointer:
```python
# Session 1
agent.invoke({"messages": [("user", "Hello")]})
# Process ends → ALL DATA LOST

# Session 2 (new process)
agent.invoke({"messages": [("user", "Continue")]})
# Agent has NO memory of "Hello"
```

### With Checkpointer:
```python
# Session 1
config = {"configurable": {"thread_id": "conversation-1"}}
agent.invoke({"messages": [("user", "Hello")]}, config=config)
# Checkpoint saved to disk/database

# Process ends, restart later...

# Session 2 (new process)
config = {"configurable": {"thread_id": "conversation-1"}}
agent.invoke({"messages": [("user", "Continue")]}, config=config)
# Agent loads checkpoint → REMEMBERS "Hello"
```

## What Gets Saved in Checkpoints?

Each checkpoint contains:
- ✅ **All messages** (including summarized history)
- ✅ **All files** created by the agent
- ✅ **Todo lists** and planning state
- ✅ **Sub-agent states**
- ✅ **Metadata** (timestamp, etc.)

## Combining with SummarizationMiddleware

**The power combo**:
```python
agent = create_deep_agent(
    model=model,
    checkpointer=checkpointer,  # Long-term persistence
    # SummarizationMiddleware automatically included!
)
```

**What happens**:
1. User has long conversation over multiple sessions
2. **SummarizationMiddleware** compresses old messages automatically
3. **Checkpointer** saves compressed state to disk
4. User returns days later
5. Agent loads checkpoint → has compressed summary + recent messages
6. Conversation continues seamlessly!

## Production Considerations

### 1. Cleanup Old Checkpoints
```python
# Delete old thread
checkpointer.delete_thread("old-thread-id")
```

### 2. Monitor Storage Size
```python
# Check checkpoint count
config = {"configurable": {"thread_id": thread_id}}
checkpoints = list(checkpointer.list(config))
print(f"Checkpoints: {len(checkpoints)}")
```

### 3. Database Connection Pooling (PostgreSQL)
```python
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    conninfo="postgresql://user:pass@localhost:5432/db",
    min_size=2,
    max_size=10,
)

checkpointer = PostgresSaver(pool)
```

### 4. Error Handling
```python
try:
    result = agent.invoke(
        {"messages": [("user", query)]},
        config={"configurable": {"thread_id": thread_id}}
    )
except Exception as e:
    print(f"Error: {e}")
    # Checkpoint is still safe - can retry
```

## Summary Table

| Feature | No Checkpointer | InMemorySaver | PersistentDict | PostgresSaver |
|---------|----------------|---------------|----------------|---------------|
| Persist after restart | ❌ | ❌ | ✅ | ✅ |
| Multi-user | ❌ | ⚠️ | ⚠️ | ✅ |
| Production-ready | ❌ | ❌ | ⚠️ | ✅ |
| Setup complexity | None | Low | Low | Medium |
| Performance | Fast | Fast | Medium | Fast |
| Storage | None | RAM | Disk (pickle) | Database |

## Quick Start

**For development**: Use `agent_with_memory.py` with PersistentDict

**For production**: Install PostgreSQL checkpointer and use PostgresSaver

## See Also

- `agent_with_memory.py` - Complete working example
- LangGraph checkpointer docs: https://langchain-ai.github.io/langgraph/how-tos/persistence/
