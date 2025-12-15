"""
OpenRouter Client - Unified LLM Gateway

This module provides a type-safe, async-compatible client for OpenRouter,
enabling access to multiple LLM providers through a single API.

Usage:
    from lib.openrouter_client import chat, chat_async, stream_chat

    # Synchronous
    response = chat("What is 2+2?", model="openai/gpt-4o-mini")
    
    # Async
    response = await chat_async("What is 2+2?")
    
    # Streaming
    for chunk in stream_chat("Write a story"):
        print(chunk, end="")

Environment:
    OPENROUTER_API_KEY - Required API key from openrouter.ai/settings/keys
"""

import os
from typing import Optional, Iterator, AsyncIterator
from dotenv import load_dotenv

load_dotenv()

try:
    from openrouter import OpenRouter
except ImportError:
    raise ImportError("openrouter package not installed. Run: pip install openrouter")


# Default models for different use cases
MODELS = {
    "fast": "mistralai/mistral-medium-3",       # Fast, good for simple tasks
    "smart": "anthropic/claude-sonnet-4",       # Best quality reasoning
    "code": "deepseek/deepseek-chat-v3-0324:especiale", # Best for code generation
    "cheap": "moonshotai/kimi-k2-instruct",     # Very cheap, thinking model
    "analysis": "google/gemini-3-pro-preview",  # Long context analysis
}

DEFAULT_MODEL = MODELS["smart"]


def _get_client() -> OpenRouter:
    """Get configured OpenRouter client."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
    return OpenRouter(api_key=api_key)


def chat(
    prompt: str,
    model: Optional[str] = None,
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Send a chat message and get a response.
    
    Args:
        prompt: User message
        model: Model identifier (e.g., "openai/gpt-4o-mini"). Defaults to smart model.
        system: Optional system prompt
        temperature: Creativity (0.0-1.0)
        max_tokens: Max response length
        
    Returns:
        Model's response text
    """
    model = model or DEFAULT_MODEL
    messages = []
    
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    with _get_client() as client:
        response = client.chat.send(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
    return response.choices[0].message.content


async def chat_async(
    prompt: str,
    model: Optional[str] = None,
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Async version of chat.
    
    Args:
        prompt: User message
        model: Model identifier. Defaults to smart model.
        system: Optional system prompt
        temperature: Creativity (0.0-1.0)
        max_tokens: Max response length
        
    Returns:
        Model's response text
    """
    model = model or DEFAULT_MODEL
    messages = []
    
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    async with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client:
        response = await client.chat.send_async(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
    return response.choices[0].message.content


def stream_chat(
    prompt: str,
    model: Optional[str] = None,
    system: Optional[str] = None,
    temperature: float = 0.7,
) -> Iterator[str]:
    """
    Stream a chat response token by token.
    
    Args:
        prompt: User message
        model: Model identifier. Defaults to smart model.
        system: Optional system prompt
        temperature: Creativity (0.0-1.0)
        
    Yields:
        Response text chunks
    """
    model = model or DEFAULT_MODEL
    messages = []
    
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    with _get_client() as client:
        stream = client.chat.send(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        
        for event in stream:
            if event.choices:
                content = event.choices[0].delta.content
                if content:
                    yield content


def analyze_text(
    text: str,
    task: str,
    model: Optional[str] = None,
) -> str:
    """
    Analyze text with a specific task instruction.
    
    Convenience function for common analysis patterns.
    
    Args:
        text: Text to analyze
        task: What to do with the text (e.g., "summarize", "extract errors", "translate to Spanish")
        model: Model to use. Defaults to analysis model.
        
    Returns:
        Analysis result
    """
    model = model or MODELS["analysis"]
    
    prompt = f"""Task: {task}

Text:
{text}

Provide your analysis:"""
    
    return chat(prompt, model=model, temperature=0.3)


# Quick test
if __name__ == "__main__":
    print("Testing OpenRouter client...")
    
    try:
        response = chat(
            "Say 'OpenRouter integration successful!' and nothing else.",
            model=MODELS["fast"]
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure OPENROUTER_API_KEY is set in .env")
