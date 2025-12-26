import asyncio
import os
import json
import logging
import httpx
from mcp.server.fastmcp import FastMCP
from analyzers.schemas import Turn
from analyzers.llm_gateway import generate_analysis

# Initialize FastMCP server
mcp = FastMCP("Semantic Analysis (Polyguru)")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCP-SemanticServer")

@mcp.tool()
async def analyze_transcript(student_name: str, transcript_text: str) -> str:
    """
    Analyzes an ESL tutoring transcript using the Polyguru suite.
    Combines deterministic linguistic rules with LLM reasoning.
    """
    logger.info(f"🧠 MCP Analysis requested for: {student_name}")
    
    # We can either duplicate the logic from semantic_server.py 
    # OR better, just call its local endpoint if it's running.
    # To keep it truly "One Source of Truth", we call the FastAPI app.
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            # We assume semantic_server.py is running on port 8080 as per launch.sh
            response = await client.post(
                "http://localhost:8080/analyze",
                json={
                    "student_name": student_name,
                    "transcript_text": transcript_text,
                    "turns": [] # Minimal for now
                }
            )
            if response.status_code == 200:
                result = response.json()
                # Return the LLM analysis part primarily
                return json.dumps(result.get("llm_analysis", {}), indent=2)
            else:
                return f"Error from Semantic Server: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Failed to connect to Semantic Server: {str(e)}"

@mcp.tool()
async def get_analysis_handoff(student_name: str, transcript_text: str) -> str:
    """
    Retrieves the COMPLETE analysis data handoff for a session.
    Includes raw metrics, lexical stats, chunks, and LLM analysis.
    Returns the full, unfiltered JSON object.
    Use this for data export, debugging, or full-fidelity downstream processing.
    """
    logger.info(f"🤝 Data Handoff requested for: {student_name}")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            # Call the same internal endpoint but request the full payload return
            response = await client.post(
                "http://localhost:8080/analyze",
                json={
                    "student_name": student_name,
                    "transcript_text": transcript_text,
                    "turns": [] # Minimal, assuming raw text is primary for this dump mode
                }
            )
            if response.status_code == 200:
                result = response.json()
                # [High-Fidelity] Return the ENTIRE object
                return json.dumps(result, indent=2)
            else:
                return f"Error from Semantic Server: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Failed to connect to Semantic Server: {str(e)}"

@mcp.tool()
async def get_agent_card() -> str:
    """
    Retrieves the A2A Agent Card for this server.
    Describes capabilities, skills, and interfaces.
    """
    logger.info(f"🆔 Agent Card requested.")
    card_path = os.path.join(os.path.dirname(__file__), "agent_card.json")
    if os.path.exists(card_path):
        with open(card_path, "r") as f:
            return f.read()
    else:
        return json.dumps({"error": "Agent Card not found."})

if __name__ == "__main__":
    mcp.run()
