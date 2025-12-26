"""
LLM Gateway: The Intelligent Research Agent
Direct integration with AssemblyAI LLM Gateway with Tool Calling.
Supports Gemini 3 Flash Preview and Agentic Research (Exa/Firecrawl).
"""

import os
import json
import httpx
import logging
import asyncio
from typing import Any, List, Dict
from collections.abc import Mapping
from .schemas import Turn

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LLMGateway")

# Configuration
AAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
EXA_API_KEY = "758d3439-a850-4818-9f47-485d8b3d5415" # From exa_slam_search.py
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
LLM_GATEWAY_URL = "https://llm-gateway.assemblyai.com/v1/chat/completions"

# --- TOOLS ---

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "exa_search",
            "description": "Search the internet using Exa for high-quality, neural search results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "use_autoprompt": {"type": "boolean", "default": True}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "firecrawl_scrape",
            "description": "Scrape a specific URL and convert it to clean markdown using Firecrawl.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to scrape"}
                },
                "required": ["url"]
            }
        }
    }
]

async def handle_tool_call(name: str, args: Dict[str, Any]) -> str:
    """Execute the requested tool and return the result as a string."""
    logger.info(f"🛠️ Executing Tool: {name} with args: {args}")
    
    if name == "exa_search":
        url = "https://api.exa.ai/search"
        headers = {"x-api-key": EXA_API_KEY, "Content-Type": "application/json"}
        payload = {
            "query": args["query"],
            "useAutoprompt": args.get("use_autoprompt", True),
            "numResults": 5,
            "contents": {"text": True}
        }
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers, json=payload, timeout=30.0)
                return res.text
        except Exception as e:
            return f"Exa Search Error: {str(e)}"

    elif name == "firecrawl_scrape":
        if not FIRECRAWL_API_KEY:
            return "Error: FIRECRAWL_API_KEY missing"
        url = "https://api.firecrawl.dev/v1/scrape"
        headers = {"Authorization": f"Bearer {FIRECRAWL_API_KEY}", "Content-Type": "application/json"}
        payload = {"url": args["url"], "formats": ["markdown"]}
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers, json=payload, timeout=60.0)
                return res.text
        except Exception as e:
            return f"Firecrawl Scrape Error: {str(e)}"
            
    return f"Error: Unknown tool {name}"

async def generate_analysis(
    system_prompt: str,
    user_message: str,
    model: str = "gemini-3-flash-preview", # Definitively supported ID
    temperature: float = 0.2
) -> Mapping[str, object] | None:
    """
    The Oracle: Agentic analysis using AssemblyAI LLM Gateway with research tools.
    """
    if not AAI_API_KEY:
        logger.warning("🚫 ASSEMBLYAI_API_KEY missing.")
        return None

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    headers = {
        "authorization": AAI_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        iterations = 0
        MAX_ITERATIONS = 5
        
        while iterations < MAX_ITERATIONS:
            iterations += 1
            logger.info(f"🦅 Gateway Iteration {iterations} ({model})...")
            
            payload = {
                "model": model,
                "messages": messages,
                "tools": TOOLS,
                "max_tokens": 20000, 
                "temperature": temperature
            }

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(LLM_GATEWAY_URL, json=payload, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"❌ Gateway Error {response.status_code}: {response.text}")
                    return None
                    
                data = response.json()
                choice = data["choices"][0]
                message = choice["message"]
                
                # Add assistant message to history
                messages.append(message)
                
                # Check for tool calls
                tool_calls = message.get("tool_calls")
                if tool_calls:
                    logger.info(f"🧬 Processing {len(tool_calls)} tool calls...")
                    for tool_call in tool_calls:
                        func = tool_call["function"]
                        name = func["name"]
                        args = json.loads(func["arguments"])
                        
                        # Execute tool
                        result = await handle_tool_call(name, args)
                        
                        # Add tool response to history
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": result
                        })
                    continue 
                else:
                    # Final response received
                    content = message.get("content", "")
                    if not content:
                        logger.warning("⚠️ Received empty final content.")
                        return None
                        
                    # Extract JSON
                    clean_content = content.strip()
                    if "```json" in clean_content:
                        clean_content = clean_content.split("```json")[1].split("```")[0].strip()
                    elif "```" in clean_content:
                        clean_content = clean_content.split("```")[1].split("```")[0].strip()
                    
                    try:
                        return json.loads(clean_content)
                    except json.JSONDecodeError:
                        import re
                        match = re.search(r'\{.*\}', clean_content, re.DOTALL)
                        if match:
                            return json.loads(match.group())
                        raise

        logger.warning(f"⚠️ Reached max iterations ({MAX_ITERATIONS}).")
        return None

    except Exception as e:
        logger.error(f"❌ Agentic Loop Failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def push_to_semantic_server(
    student_name: str,
    turns: list[Turn], 
    analysis_context: Mapping[str, object],
    session_id: str | None = None,
    notes: str = ""
) -> Mapping[str, object]:
    """Fallback handler for data push to GitEnglishHub."""
    # Logic remains similar to before, ensures MCP_SECRET is handled
    mcp_secret = os.getenv("MCP_SECRET")
    if not mcp_secret:
        return {"success": False, "error": "MCP_SECRET missing"}
        
    url = f"{os.getenv('GITENGLISH_API_BASE', 'https://gitenglish.com')}/api/mcp"
    serializable_turns = [t.model_dump() for t in turns]
    
    payload = {
        "action": "sanity.createLessonAnalysis",
        "studentId": student_name,
        "params": {
            "studentName": student_name,
            "sessionDate": turns[0].timestamp if turns else None,
            "analysisReport": json.dumps(analysis_context, default=str),
            "teacherNotes": notes,
            "transcriptId": session_id,
            "rawTurns": serializable_turns,
            "detectedPhenomena": analysis_context.get("detected_errors", []) 
        }
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            res = client.post(url, headers={"Authorization": f"Bearer {mcp_secret}"}, json=payload)
            return res.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

run_llm_gateway_query = push_to_semantic_server
