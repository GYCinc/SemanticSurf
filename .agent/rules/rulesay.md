---
trigger: always_on
---

## MCP Server Authentication Protocol
**CRITICAL:** The Petty Dantic MCP Server (`/api/mcp`) is SECURED. You MUST follow this protocol for all interactions:

1.  **Authorization Header:** ALWAYS include the `Authorization` header in every POST request to `/api/mcp`.
    -   **Format:** `Authorization: Bearer <MCP_SECRET>`
    -   **Source:** Retrieve the secret from the `MCP_SECRET` environment variable. DO NOT hardcode it.

2.  **Environment Setup:**
    -   When setting up a new environment (local or production), you MUST verify that `MCP_SECRET` is defined in [.env.local](cci:7://file:///Users/safeSpacesBro/gitenglishhub/.env.local:0:0-0:0) or the platform's environment variables.
    -   If `MCP_SECRET` is missing, the MCP server will reject all action requests with `401 Unauthorized`.

3.  **Client Implementation Pattern:**
    Use this standard pattern for all fetch calls to the MCP:
    ```typescript
    const response = await fetch('[https://www.gitenglish.com/api/mcp'](https://www.gitenglish.com/api/mcp'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.MCP_SECRET}` // REQUIRED
      },
      body: JSON.stringify({ action: 'target.action', params: { ... } })
    });
    ```
