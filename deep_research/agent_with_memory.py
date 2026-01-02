"""Research Agent with Long-term Memory - Persistent session support.

This demonstrates how to add checkpointing for:
1. Session persistence across restarts
2. Resume previous conversations
3. Time-travel through conversation history
"""

import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import InMemorySaver, PersistentDict

from research_agent.prompts import (
    RESEARCHER_INSTRUCTIONS,
    RESEARCH_WORKFLOW_INSTRUCTIONS,
    SUBAGENT_DELEGATION_INSTRUCTIONS,
)
from research_agent.tools import tavily_search, think_tool

# ============================================================================
# CHECKPOINTER OPTIONS
# ============================================================================

def get_memory_checkpointer():
    """Option 1: In-memory checkpointer (session-only)

    - Stores in RAM
    - Fast
    - Lost when process ends
    - Good for: Testing, single-session use
    """
    return InMemorySaver()


def get_persistent_checkpointer(db_path="./checkpoints.db"):
    """Option 2: Persistent checkpointer (survives restarts)

    - Stores to disk using pickle
    - Persists across restarts
    - Good for: Development, single-user apps

    Args:
        db_path: Path to checkpoint file
    """
    # Create storage using PersistentDict
    storage = PersistentDict(filename=db_path)
    writes = PersistentDict(filename=db_path + ".writes")
    blobs = PersistentDict(filename=db_path + ".blobs")

    # Load existing data if file exists
    if os.path.exists(db_path):
        storage.load()
    if os.path.exists(db_path + ".writes"):
        writes.load()
    if os.path.exists(db_path + ".blobs"):
        blobs.load()

    return InMemorySaver(
        factory=lambda: storage if storage else PersistentDict(filename=db_path)
    )


# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

# Limits
max_concurrent_research_units = 3
max_researcher_iterations = 3

# Get current date
current_date = datetime.now().strftime("%Y-%m-%d")

# Combine orchestrator instructions
INSTRUCTIONS = (
    RESEARCH_WORKFLOW_INSTRUCTIONS
    + "\n\n"
    + "=" * 80
    + "\n\n"
    + SUBAGENT_DELEGATION_INSTRUCTIONS.format(
        max_concurrent_research_units=max_concurrent_research_units,
        max_researcher_iterations=max_researcher_iterations,
    )
)

# Create research sub-agent
research_sub_agent = {
    "name": "researcher",
    "description": "Delegate research tasks to this researcher sub-agent. Use this for conducting web searches and gathering information. Only give this researcher one specific topic at a time.",
    "system_prompt": RESEARCHER_INSTRUCTIONS.format(date=current_date),
    "tools": [tavily_search, think_tool],
}

# Model configuration
model_provider = os.getenv("MODEL_PROVIDER", "openrouter").lower()

if model_provider == "ollama":
    from langchain_ollama import ChatOllama
    model = ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.0,
    )
    print(f"✓ Using Ollama model: {os.getenv('OLLAMA_MODEL', 'llama3.2')}")

elif model_provider == "anthropic":
    model = init_chat_model(
        model=f"anthropic:{os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-5-20250929')}",
        temperature=0.0,
    )
    print(f"✓ Using Anthropic model: {os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-5-20250929')}")

else:  # Default to openrouter
    model = init_chat_model(
        model=os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free"),
        model_provider="openai",
        temperature=0.0,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        model_kwargs={
            "extra_headers": {
                "HTTP-Referer": "https://github.com/alanxu/deepagents-quickstarts",
                "X-Title": "Deep Research Agent",
            }
        },
    )
    print(f"✓ Using OpenRouter model: {os.getenv('OPENROUTER_MODEL', 'openai/gpt-oss-120b:free')}")


# ============================================================================
# CREATE AGENT WITH CHECKPOINTER
# ============================================================================

# Choose your checkpointer
# checkpointer = get_memory_checkpointer()  # Session-only
checkpointer = get_persistent_checkpointer("./research_checkpoints.db")  # Persistent

agent = create_deep_agent(
    model=model,
    tools=[],
    system_prompt=INSTRUCTIONS,
    subagents=[research_sub_agent],
    checkpointer=checkpointer,  # ⭐ THIS ENABLES LONG-TERM MEMORY
)

print(f"✓ Agent created with persistent checkpointing")
print(f"✓ Checkpoints saved to: ./research_checkpoints.db")


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def run_new_conversation(query: str, thread_id: str):
    """Start a new conversation with a specific thread ID"""
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n{'='*80}")
    print(f"Starting new conversation (thread: {thread_id})")
    print(f"Query: {query}")
    print(f"{'='*80}\n")

    result = agent.invoke(
        {"messages": [("user", query)]},
        config=config
    )
    return result


def resume_conversation(thread_id: str, new_query: str):
    """Resume an existing conversation by thread ID"""
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n{'='*80}")
    print(f"Resuming conversation (thread: {thread_id})")
    print(f"New query: {new_query}")
    print(f"{'='*80}\n")

    # The agent automatically loads previous messages from checkpointer
    result = agent.invoke(
        {"messages": [("user", new_query)]},
        config=config
    )
    return result


def list_conversation_history(thread_id: str):
    """View all checkpoints for a thread"""
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n{'='*80}")
    print(f"Conversation history (thread: {thread_id})")
    print(f"{'='*80}\n")

    # List all checkpoints
    checkpoints = list(checkpointer.list(config))

    for i, checkpoint in enumerate(checkpoints):
        print(f"Checkpoint {i+1}:")
        print(f"  ID: {checkpoint.config['configurable']['checkpoint_id']}")
        print(f"  Messages: {len(checkpoint.checkpoint.get('channel_values', {}).get('messages', []))}")
        print()

    return checkpoints


def get_conversation_state(thread_id: str):
    """Get current state of a conversation"""
    config = {"configurable": {"thread_id": thread_id}}
    state = agent.get_state(config)

    print(f"\n{'='*80}")
    print(f"Current state (thread: {thread_id})")
    print(f"{'='*80}\n")

    print(f"Messages: {len(state.values.get('messages', []))}")
    print(f"Files: {list(state.values.get('files', {}).keys())}")

    return state


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example 1: Start a new research session
    result1 = run_new_conversation(
        query="Research the history of quantum computing",
        thread_id="research-quantum-001"
    )

    # Example 2: Continue the same research session later
    # (even after restarting the script!)
    result2 = resume_conversation(
        thread_id="research-quantum-001",
        new_query="Now compare quantum computing with classical computing"
    )

    # Example 3: Start a different research session
    result3 = run_new_conversation(
        query="Research the latest trends in AI",
        thread_id="research-ai-001"
    )

    # Example 4: View conversation history
    list_conversation_history("research-quantum-001")

    # Example 5: Check current state
    get_conversation_state("research-quantum-001")
