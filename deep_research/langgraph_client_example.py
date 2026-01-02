#!/usr/bin/env python
"""Example: Using LangGraph SDK to interact with server and manage threads.

Prerequisites:
1. Start LangGraph server in another terminal:
   $ langgraph dev

2. Install SDK:
   $ uv add langgraph-sdk

3. Run this script:
   $ uv run python langgraph_client_example.py
"""

from langgraph_sdk import get_client
import time
import sys


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def example_basic_thread():
    """Example 1: Basic thread creation and resumption"""
    print_section("Example 1: Basic Thread Usage")

    client = get_client(url="http://localhost:8123")

    # Start a new conversation with specific thread_id
    thread_id = "example-basic-001"
    print(f"📝 Starting conversation (thread: {thread_id})")

    run = client.runs.create(
        assistant_id="research",
        thread_id=thread_id,
        input={
            "messages": [
                {"role": "user", "content": "What is quantum computing? Give a brief overview."}
            ]
        },
        stream_mode=["updates"]
    )

    # Wait for completion
    run = client.runs.wait(run['run_id'])
    print(f"✅ Run completed: {run['status']}")

    # Resume the conversation
    print(f"\n📝 Resuming conversation (same thread: {thread_id})")

    run = client.runs.create(
        assistant_id="research",
        thread_id=thread_id,  # Same thread_id = resume
        input={
            "messages": [
                {"role": "user", "content": "What are its main applications?"}
            ]
        }
    )

    run = client.runs.wait(run['run_id'])
    print(f"✅ Run completed: {run['status']}")
    print(f"💡 Thread '{thread_id}' now has full conversation history!")


def example_streaming():
    """Example 2: Streaming responses"""
    print_section("Example 2: Streaming Responses")

    client = get_client(url="http://localhost:8123")

    thread_id = "example-streaming-001"
    print(f"📝 Streaming conversation (thread: {thread_id})")

    # Stream the response
    for chunk in client.runs.stream(
        assistant_id="research",
        thread_id=thread_id,
        input={
            "messages": [
                {"role": "user", "content": "Tell me about LangGraph"}
            ]
        },
        stream_mode=["updates"]
    ):
        # Print each update as it arrives
        if chunk.get("data"):
            print(".", end="", flush=True)

    print("\n✅ Streaming complete!")


def example_thread_inspection():
    """Example 3: Inspect thread state"""
    print_section("Example 3: Thread State Inspection")

    client = get_client(url="http://localhost:8123")

    thread_id = "example-inspect-001"

    # Create conversation
    print(f"📝 Creating conversation (thread: {thread_id})")
    run = client.runs.create(
        assistant_id="research",
        thread_id=thread_id,
        input={
            "messages": [
                {"role": "user", "content": "Research artificial intelligence"}
            ]
        }
    )
    client.runs.wait(run['run_id'])

    # Inspect thread state
    print(f"\n🔍 Inspecting thread state...")
    state = client.threads.get_state(thread_id=thread_id)

    print(f"   Messages: {len(state['values']['messages'])}")
    print(f"   Files: {list(state['values'].get('files', {}).keys())}")

    # Print messages
    print(f"\n📜 Message history:")
    for i, msg in enumerate(state['values']['messages'][-5:], 1):  # Last 5 messages
        role = getattr(msg, 'type', 'unknown')
        content = getattr(msg, 'content', str(msg))
        # Truncate long content
        if isinstance(content, str) and len(content) > 100:
            content = content[:100] + "..."
        print(f"   {i}. [{role}]: {content}")


def example_multiple_threads():
    """Example 4: Multiple independent threads"""
    print_section("Example 4: Multiple Independent Threads")

    client = get_client(url="http://localhost:8123")

    threads = [
        ("quantum-topic", "What is quantum computing?"),
        ("ai-topic", "What is artificial intelligence?"),
        ("blockchain-topic", "What is blockchain?"),
    ]

    print("📝 Creating multiple independent conversations...\n")

    for thread_id, query in threads:
        print(f"   Thread '{thread_id}': {query}")

        run = client.runs.create(
            assistant_id="research",
            thread_id=thread_id,
            input={"messages": [{"role": "user", "content": query}]}
        )
        client.runs.wait(run['run_id'])

    print("\n✅ All threads created!")

    # List all threads
    print("\n🔍 Listing all threads:")
    all_threads = client.threads.list()

    for thread in all_threads:
        tid = thread['thread_id']
        print(f"   - {tid}")


def example_thread_cleanup():
    """Example 5: Thread cleanup"""
    print_section("Example 5: Thread Cleanup")

    client = get_client(url="http://localhost:8123")

    # Create a temporary thread
    temp_thread = "temp-thread-to-delete"

    print(f"📝 Creating temporary thread: {temp_thread}")
    run = client.runs.create(
        assistant_id="research",
        thread_id=temp_thread,
        input={"messages": [{"role": "user", "content": "Hello"}]}
    )
    client.runs.wait(run['run_id'])

    # List threads before deletion
    print(f"\n🔍 Threads before deletion:")
    threads_before = [t['thread_id'] for t in client.threads.list()]
    print(f"   Total: {len(threads_before)}")
    if temp_thread in threads_before:
        print(f"   ✓ '{temp_thread}' exists")

    # Delete the thread
    print(f"\n🗑️  Deleting thread: {temp_thread}")
    client.threads.delete(thread_id=temp_thread)

    # List threads after deletion
    print(f"\n🔍 Threads after deletion:")
    threads_after = [t['thread_id'] for t in client.threads.list()]
    print(f"   Total: {len(threads_after)}")
    if temp_thread not in threads_after:
        print(f"   ✓ '{temp_thread}' deleted successfully")


def example_interactive():
    """Example 6: Interactive session"""
    print_section("Example 6: Interactive Session")

    client = get_client(url="http://localhost:8123")

    thread_id = input("Enter thread ID (or press Enter for 'interactive-session'): ").strip()
    if not thread_id:
        thread_id = "interactive-session"

    print(f"\n💡 Using thread: {thread_id}")
    print("💡 Type 'quit' to exit, 'state' to see thread state")
    print("💡 Type 'history' to see message history\n")

    while True:
        query = input("🔵 You: ").strip()

        if not query:
            continue

        if query.lower() == 'quit':
            print("\n👋 Goodbye!")
            break

        if query.lower() == 'state':
            state = client.threads.get_state(thread_id=thread_id)
            print(f"\n📊 Thread State:")
            print(f"   Messages: {len(state['values']['messages'])}")
            print(f"   Files: {list(state['values'].get('files', {}).keys())}\n")
            continue

        if query.lower() == 'history':
            state = client.threads.get_state(thread_id=thread_id)
            print(f"\n📜 Message History:")
            for i, msg in enumerate(state['values']['messages'], 1):
                role = getattr(msg, 'type', 'unknown')
                content = getattr(msg, 'content', str(msg))
                if isinstance(content, str) and len(content) > 80:
                    content = content[:80] + "..."
                print(f"   {i}. [{role}]: {content}")
            print()
            continue

        # Send message
        print("🤖 Agent: ", end="", flush=True)

        try:
            for chunk in client.runs.stream(
                assistant_id="research",
                thread_id=thread_id,
                input={"messages": [{"role": "user", "content": query}]},
                stream_mode=["updates"]
            ):
                print(".", end="", flush=True)

            print("\n")

        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def main():
    """Main demo menu"""
    print("\n" + "="*80)
    print("  LANGGRAPH SERVER SDK EXAMPLES")
    print("="*80)

    # Check if server is running
    try:
        client = get_client(url="http://localhost:8123")
        # Try to list threads to verify connection
        client.threads.list()
        print("\n✅ Connected to LangGraph server at http://localhost:8123")
    except Exception as e:
        print("\n❌ Cannot connect to LangGraph server!")
        print("   Make sure the server is running:")
        print("   $ langgraph dev")
        print(f"\n   Error: {e}")
        sys.exit(1)

    print("\nAvailable examples:")
    print("  1. Basic thread creation and resumption")
    print("  2. Streaming responses")
    print("  3. Thread state inspection")
    print("  4. Multiple independent threads")
    print("  5. Thread cleanup")
    print("  6. Interactive session")
    print("  7. Run all examples (1-5)")
    print("  q. Quit")

    choice = input("\nSelect example (1-7, q): ").strip()

    if choice == '1':
        example_basic_thread()
    elif choice == '2':
        example_streaming()
    elif choice == '3':
        example_thread_inspection()
    elif choice == '4':
        example_multiple_threads()
    elif choice == '5':
        example_thread_cleanup()
    elif choice == '6':
        example_interactive()
    elif choice == '7':
        example_basic_thread()
        example_streaming()
        example_thread_inspection()
        example_multiple_threads()
        example_thread_cleanup()
    elif choice.lower() == 'q':
        print("\n👋 Goodbye!")
        return
    else:
        print("\n❌ Invalid choice")
        return

    print("\n" + "="*80)
    print("  Example complete!")
    print("="*80)
    print("\n💡 Thread data is persisted in .langgraph_api/")
    print("💡 Restart the server and threads will still be there!")


if __name__ == "__main__":
    main()
