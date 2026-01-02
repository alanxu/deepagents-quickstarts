#!/bin/bash
# Script to commit and push changes

cd "$(dirname "$0")"

echo "📝 Staging changes..."
git add .

echo "✍️  Committing changes..."
git commit -m "Add long-term memory and session resumption support

- Add debug logging with RawResponseLogger (commented out by default)
- Add step to print final report in research workflow
- Add comprehensive memory and thread ID documentation
- Add agent_with_memory.py with persistent checkpointing
- Add interactive demos (demo_memory.py, langgraph_client_example.py)
- Document three checkpointer options: InMemorySaver, PersistentDict, PostgreSQL
- Explain thread ID usage with LangGraph server (Studio, SDK, HTTP API)
- Include examples for multi-user sessions and conversation resumption"

echo "🚀 Pushing to remote..."
git push

echo "✅ Done!"
