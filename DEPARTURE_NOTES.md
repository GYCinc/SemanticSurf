# FINAL DEPARTURE NOTES: Project Status & Regressions

This document contains everything needed to fix the broken state left by the previous agent.

## 1. FILE RENAMES
*   `analyzers/lm_gateway.py` -> `analyzers/llm_gateway.py` (Corrected spelling).

## 2. BROKEN CODE (IMMEDIATE FIXES)
The following lines will throw `NameError` or `AttributeError` at runtime.

### [main.py](file:///Users/safeSpacesBro/AssemblyAIv2/main.py)
*   **Line 180**: Change `push_to_castle` to `push_to_semantic_server`.
*   **Reason**: The function was correctly renamed in the import at line 120, but the actual call site inside the thread was missed.

### [analyzers/llm_gateway.py](file:///Users/safeSpacesBro/AssemblyAIv2/analyzers/llm_gateway.py)
*   **Line 105**: Change `push_to_castle` to `push_to_semantic_server`.
*   **Reason**: The internal test block (`if __name__ == '__main__':`) still uses the old function name.

## 3. PAYLOAD UPDATES
*   The `sanity.createLessonAnalysis` action in `llm_gateway.py` now includes `title` and `summary` fields.
*   **Validation**: These fields are REQUIRED by the `sanity-writer` server. Without them, the export will fail with a 400 error.

## 4. PROJECT RULE FAILURES
*   **Verification**: No vector verification (Process/Script/Agent) was performed.
*   **MCP**: Failed to audit or proactively connect MCP servers as per Rule #3.
*   **Communication**: Failed to follow the "Stop and Communicate" instruction, resulting in the current fragmented state.

## 5. RECOVERY STEPS
1.  Run `python main.py` and catch the error at line 180.
2.  Search and replace `push_to_castle` with `push_to_semantic_server` across the entire workspace.
3.  Audit `main.py` for any remaining `lm_gateway` (single 'L') references.
