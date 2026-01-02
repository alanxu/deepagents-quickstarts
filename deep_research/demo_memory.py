#!/usr/bin/env python
"""Simple demo of long-term memory and session resumption."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agent_with_memory import (
    agent,
    run_new_conversation,
    resume_conversation,
    list_conversation_history,
    get_conversation_state,
)

def demo_basic_persistence():
    """Demo 1: Basic persistence - conversation survives restart"""
    print("\n" + "="*80)
    print("DEMO 1: Basic Persistence")
    print("="*80)

    thread_id = "demo-persistence-001"

    # Session 1: Start research
    print("\n📝 Starting research on quantum computing...")
    run_new_conversation(
        query="What is quantum computing? Give me a brief overview.",
        thread_id=thread_id
    )

    print("\n✅ Session 1 complete. Checkpoint saved.")
    print("💡 You can now RESTART this script and the conversation will resume!")

    # Session 2: Continue research (can be after restart)
    print("\n📝 Continuing research...")
    resume_conversation(
        thread_id=thread_id,
        new_query="What are the main applications?"
    )

    print("\n✅ Session 2 complete.")


def demo_multiple_threads():
    """Demo 2: Multiple independent conversations"""
    print("\n" + "="*80)
    print("DEMO 2: Multiple Independent Threads")
    print("="*80)

    # Research on quantum computing
    print("\n📝 Thread 1: Quantum Computing")
    run_new_conversation(
        query="Brief history of quantum computing",
        thread_id="topic-quantum"
    )

    # Research on AI (completely separate)
    print("\n📝 Thread 2: Artificial Intelligence")
    run_new_conversation(
        query="Brief history of artificial intelligence",
        thread_id="topic-ai"
    )

    # Continue quantum thread
    print("\n📝 Back to Thread 1: Quantum Computing")
    resume_conversation(
        thread_id="topic-quantum",
        new_query="Who are the key researchers?"
    )

    print("\n✅ Both threads maintained separately!")


def demo_history_inspection():
    """Demo 3: Inspect conversation history"""
    print("\n" + "="*80)
    print("DEMO 3: History Inspection")
    print("="*80)

    thread_id = "demo-inspection-001"

    # Have a conversation
    run_new_conversation(
        query="Tell me about LangGraph",
        thread_id=thread_id
    )

    resume_conversation(
        thread_id=thread_id,
        new_query="What are its main features?"
    )

    # Inspect the history
    print("\n🔍 Inspecting conversation history...")
    list_conversation_history(thread_id)

    print("\n🔍 Current state:")
    get_conversation_state(thread_id)


def interactive_session():
    """Demo 4: Interactive session"""
    print("\n" + "="*80)
    print("DEMO 4: Interactive Session")
    print("="*80)

    thread_id = input("\nEnter thread ID (or press Enter for 'interactive-001'): ").strip()
    if not thread_id:
        thread_id = "interactive-001"

    print(f"\n💡 Using thread ID: {thread_id}")
    print("💡 Type 'quit' to exit, 'history' to see checkpoints, 'state' to see current state\n")

    first_query = True
    while True:
        query = input("\n🔵 You: ").strip()

        if not query:
            continue

        if query.lower() == 'quit':
            print("\n👋 Goodbye!")
            break

        if query.lower() == 'history':
            list_conversation_history(thread_id)
            continue

        if query.lower() == 'state':
            get_conversation_state(thread_id)
            continue

        try:
            if first_query:
                run_new_conversation(query, thread_id)
                first_query = False
            else:
                resume_conversation(thread_id, query)
        except Exception as e:
            print(f"\n❌ Error: {e}")


def main():
    """Main demo menu"""
    print("\n" + "="*80)
    print("LONG-TERM MEMORY & SESSION RESUMPTION DEMO")
    print("="*80)

    print("\nAvailable demos:")
    print("  1. Basic Persistence (conversation survives restart)")
    print("  2. Multiple Threads (independent conversations)")
    print("  3. History Inspection (view checkpoints)")
    print("  4. Interactive Session (try it yourself)")
    print("  5. Run all demos")
    print("  q. Quit")

    choice = input("\nSelect demo (1-5, q): ").strip()

    if choice == '1':
        demo_basic_persistence()
    elif choice == '2':
        demo_multiple_threads()
    elif choice == '3':
        demo_history_inspection()
    elif choice == '4':
        interactive_session()
    elif choice == '5':
        demo_basic_persistence()
        demo_multiple_threads()
        demo_history_inspection()
    elif choice.lower() == 'q':
        print("\n👋 Goodbye!")
        return
    else:
        print("\n❌ Invalid choice")

    print("\n" + "="*80)
    print("Demo complete!")
    print("="*80)
    print(f"\n💾 Checkpoints saved to: ./research_checkpoints.db")
    print("💡 Run this script again to see persistence in action!")


if __name__ == "__main__":
    main()
