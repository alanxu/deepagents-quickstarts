"""Research Agent - Standalone script for LangGraph deployment.

This module creates a deep research agent with custom tools and prompts
for conducting web research with strategic thinking and context management.
"""

import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_google_genai import ChatGoogleGenerativeAI
from deepagents import create_deep_agent

from research_agent.prompts import (
    RESEARCHER_INSTRUCTIONS,
    RESEARCH_WORKFLOW_INSTRUCTIONS,
    SUBAGENT_DELEGATION_INSTRUCTIONS,
)
from research_agent.tools import tavily_search, think_tool

# Limits
max_concurrent_research_units = 3
max_researcher_iterations = 3

# Get current date
current_date = datetime.now().strftime("%Y-%m-%d")

# Combine orchestrator instructions (RESEARCHER_INSTRUCTIONS only for sub-agents)
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
    "name": "research-agent",
    "description": "Delegate research to the sub-agent researcher. Only give this researcher one topic at a time.",
    "system_prompt": RESEARCHER_INSTRUCTIONS.format(date=current_date),
    "tools": [tavily_search, think_tool],
}

# Model Gemini 3
# model = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0.0)

# === Dynamic Model Configuration based on MODEL_PROVIDER ===
model_provider = os.getenv("MODEL_PROVIDER", "openrouter").lower()

if model_provider == "ollama":
    # Ollama (Local/Free)
    from langchain_ollama import ChatOllama

    model = ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.0,
    )
    print(f"✓ Using Ollama model: {os.getenv('OLLAMA_MODEL', 'llama3.2')}")

elif model_provider == "anthropic":
    # Anthropic Claude (Paid)
    model = init_chat_model(
        model=f"anthropic:{os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-5-20250929')}",
        temperature=0.0,
    )
    print(f"✓ Using Anthropic model: {os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-5-20250929')}")

else:  # Default to openrouter
    # OpenRouter (Free or Paid models)
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


# Create the agent
agent = create_deep_agent(
    model=model,
    tools=[tavily_search, think_tool],
    system_prompt=INSTRUCTIONS,
    subagents=[research_sub_agent],
)
