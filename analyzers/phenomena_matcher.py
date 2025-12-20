import json
import re
import logging
import httpx
import os
import asyncio
from typing import Any
from pathlib import Path

logger = logging.getLogger("ErrorPhenomenonMatcher")

class ErrorPhenomenonMatcher:
    """
    Holy Mirror Matcher.
    Aligned 100% with gitenglishhub/lib/processing/phenomena-matcher.ts.
    Uses tiered detection: local triggerPatterns + remote Sanity cross-referencing.
    """
    _local_patterns: list[dict[str, Any]] | None = None
    _sanity_phenomena: list[dict[str, Any]] | None = None
    _lock: asyncio.Lock = asyncio.Lock()

    api_base: str
    mcp_secret: str | None

    def __init__(self) -> None:
        self.api_base = os.getenv("GITENGLISH_API_BASE", "https://gitenglish.com")
        self.mcp_secret = os.getenv("MCP_SECRET")

    async def initialize(self) -> None:
        """Tiered initialization: Load local JSON + Fetch Sanity context."""
        async with self._lock:
            if self._local_patterns is not None:
                return

            # 1. Load Local Unified Phenomena (The Bedrock)
            # Aligned with Hub path: data/unified_phenomena.json
            local_path = Path(__file__).parent.parent / "data" / "unified_phenomena.json"
            try:
                if local_path.exists():
                    with open(local_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self._local_patterns = []
                        if isinstance(data, list):
                            for p in data:
                                if isinstance(p, dict):
                                    trigger = p.get("triggerPattern")
                                    if isinstance(trigger, str) and len(trigger) > 2:
                                        try:
                                            self._local_patterns.append({
                                                "phenomenon": p,
                                                "regex": re.compile(trigger, re.IGNORECASE)
                                            })
                                        except re.error:
                                            continue
                        logger.info(f"✅ Loaded {len(self._local_patterns)} local trigger patterns.")
            except Exception as e:
                logger.error(f"❌ Local phenomena load failed: {e}")

            # 2. Fetch Sanity Context (Detailed matching)
            if self.mcp_secret:
                try:
                    url = f"{self.api_base}/api/mcp"
                    headers = {"Authorization": self.mcp_secret, "Content-Type": "application/json"}
                    # Action aligned with Hub API capability
                    payload = {"action": "sanity.fetchPhenomena", "studentId": "system", "params": {}}
                    
                    async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
                        response = await client.post(url, headers=headers, json=payload)
                        if response.status_code == 200:
                            res_data = response.json()
                            if isinstance(res_data, dict):
                                self._sanity_phenomena = res_data.get("phenomena", [])
                            if self._sanity_phenomena is not None:
                                logger.info(f"✅ Fetched {len(self._sanity_phenomena)} detailed phenomena from Sanity.")
                except Exception as e:
                    logger.error(f"❌ Sanity context fetch failed: {e}")

    def match(self, text: str) -> list[dict[str, Any]]:
        """Tiered matching logic (Fast Pattern -> Sanity Semantic)."""
        matches: list[dict[str, Any]] = []
        text_lower = text.lower()

        # 1. Fast Trigger Matching
        if self._local_patterns:
            for item in self._local_patterns:
                if item["regex"].search(text_lower):
                    p: dict[str, Any] = item["phenomenon"]
                    # Find semantic enrichment from Sanity if available
                    enriched: dict[str, Any] | None = None
                    if self._sanity_phenomena:
                        enriched = next((s for s in self._sanity_phenomena if s.get("_id") == p.get("phenomenon_id")), None)
                    
                    matches.append({
                        "phenomenon_id": p.get("phenomenon_id"),
                        "item": p.get("itemName"),
                        "internal_category": (enriched.get("publicCategory") if enriched else p.get("publicCategory", "Lexis")) or "Lexis",
                        "explanation": (enriched.get("description") if enriched else p.get("explanation", "")) or "",
                        "match_type": "triggerPattern",
                        "confidence": 0.95 if enriched else 0.7
                    })

        # 2. Semantic Keyword Fallback (if no pattern hits)
        if not matches and self._sanity_phenomena:
            for p_sanity in self._sanity_phenomena:
                keywords = p_sanity.get("keywords", [])
                if isinstance(keywords, list) and any(isinstance(k, str) and k.lower() in text_lower for k in keywords if k):
                    matches.append({
                        "phenomenon_id": p_sanity.get("_id"),
                        "item": p_sanity.get("title"),
                        "internal_category": p_sanity.get("publicCategory"),
                        "explanation": p_sanity.get("description"),
                        "match_type": "keyword",
                        "confidence": 0.8
                    })

        return matches

    def get_stats(self) -> dict[str, int]:
        return {
            "local_patterns": len(self._local_patterns) if self._local_patterns is not None else 0,
            "sanity_context": len(self._sanity_phenomena) if self._sanity_phenomena is not None else 0
        }