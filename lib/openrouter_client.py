import os
from typing import Optional, Iterator, AsyncIterator
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI

load_dotenv()

# Default models for different use cases
MODELS = {
    "fast": "mistralai/mistral-medium-3",       # Fast, good for simple tasks
    "smart": "anthropic/claude-sonnet-4",       # Best quality reasoning
    "code": "deepseek/deepseek-chat-v3-0324:especiale", # Best for code generation
    "cheap": "moonshotai/kimi-k2-instruct",     # Very cheap, thinking model
    "analysis": "google/gemini-3-pro-preview",  # Long context analysis
}

DEFAULT_MODEL = MODELS["smart"]


def _get_client() -> OpenAI:
    """Get configured OpenAI client pointing to OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
    
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def _get_async_client() -> AsyncOpenAI:
    """Get configured AsyncOpenAI client pointing to OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
    return AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


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
    
    client = _get_client()
    response = client.chat.completions.create(
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
    
    client = _get_async_client()
    response = await client.chat.completions.create(
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
    
    client = _get_client()
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True,
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content

