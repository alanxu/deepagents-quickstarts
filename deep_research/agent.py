"""Research Agent - Standalone script for LangGraph deployment.

This module creates a deep research agent with custom tools and prompts
for conducting web research with strategic thinking and context management.
"""

import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import langchain
import logging

# Enable debug mode to see raw LLM responses
langchain.debug = True

# Configure logging to show more details
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("langchain").setLevel(logging.DEBUG)
logging.getLogger("langgraph").setLevel(logging.DEBUG)

from langchain.chat_models import init_chat_model
from langchain_google_genai import ChatGoogleGenerativeAI
from deepagents import create_deep_agent
from langchain_core.callbacks.base import BaseCallbackHandler

# Custom callback to print raw LLM responses
class RawResponseLogger(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print("\n" + "="*80)
        print("🔵 RAW LLM INPUT:")
        print("="*80)
        for prompt in prompts:
            print(prompt)
        print("="*80 + "\n")

    def on_llm_end(self, response, **kwargs):
        print("\n" + "="*80)
        print("🟢 RAW LLM OUTPUT:")
        print("="*80)
        print(response)
        print("\nGenerations:")
        for gen in response.generations:
            print(gen)
        if hasattr(response, 'llm_output') and response.llm_output:
            print("\nLLM Output metadata:")
            print(response.llm_output)
        print("="*80 + "\n")

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
    "name": "researcher",
    "description": "Delegate research tasks to this researcher sub-agent. Use this for conducting web searches and gathering information. Only give this researcher one specific topic at a time.",
    "system_prompt": RESEARCHER_INSTRUCTIONS.format(date=current_date),
    "tools": [tavily_search, think_tool],
}

# Model Gemini 3
# model = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0.0)

# === Dynamic Model Configuration based on MODEL_PROVIDER ===
model_provider = os.getenv("MODEL_PROVIDER", "openrouter").lower()

# Initialize callback for raw response logging
raw_logger = RawResponseLogger()

if model_provider == "ollama":
    # Ollama (Local/Free)
    from langchain_ollama import ChatOllama

    model = ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.0,
        # callbacks=[raw_logger],
    )
    print(f"✓ Using Ollama model: {os.getenv('OLLAMA_MODEL', 'llama3.2')}")

elif model_provider == "anthropic":
    # Anthropic Claude (Paid)
    model = init_chat_model(
        model=f"anthropic:{os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-5-20250929')}",
        temperature=0.0,
    )
    # Add callbacks after initialization
    # model.callbacks = [raw_logger]
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
    # Add callbacks after initialization
    # model.callbacks = [raw_logger]
    print(f"✓ Using OpenRouter model: {os.getenv('OPENROUTER_MODEL', 'openai/gpt-oss-120b:free')}")


# Create the agent
# OPTION 1: Main agent delegates to subagents (recommended for proper multi-agent workflow)
agent = create_deep_agent(
    model=model,
    tools=[],  # Main agent has no custom tools - only built-in file/planning tools
    system_prompt=INSTRUCTIONS,
    subagents=[research_sub_agent],
)

# OPTION 2: Main agent can use search tools directly (commented out)
# agent = create_deep_agent(
#     model=model,
#     tools=[tavily_search, think_tool],  # Direct access to search tools
#     system_prompt=INSTRUCTIONS,
#     subagents=[research_sub_agent],
# )
