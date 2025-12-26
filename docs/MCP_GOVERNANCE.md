# MCP Governance Specification

## 1. Scope Definition
### Global Scope (Remote)
*   **Infrastructure:** Hosted on Railway containers or centralized cloud providers.
*   **Transport:** SSE (Server-Sent Events) or HTTPS.
*   **Registry:** Managed via a central Postman Collection acting as the "Global Tool Catalog."

### Instance-Specific Scope (Local)
*   **Infrastructure:** Local machine processes.
*   **Transport:** Stdio.
*   **Use Case:** File system operations, local device control (AssemblyAI ingest), and per-user environment management (UV-Agent).
*   **Configuration:** Managed via local `claude_desktop_config.json` or equivalent client settings.

## 2. API Versioning Strategy
*   **Protocol Level:** Strict adherence to `@modelcontextprotocol/sdk` semver. Handshake must verify capability compatibility.
*   **Endpoint Level:** Global servers use path-based versioning (e.g., `/v1/tools`, `/v2/tools`).
*   **Tool Level:** Each tool definition in the registry includes a `version` metadata field in its description to allow LLMs to select the appropriate schema.

## 3. Authentication & Authorization Mechanisms
*   **Internal/Local:** Environment-injected shared secrets (`MCP_SECRET`).
*   **Global/Public:**
    *   **Auth:** Bearer Token (JWT) issued via GitEnglishHub OAuth2 flow.
    *   **Authorization:** Capability-based access control (RBAC). Postman environment variables manage the credential lifecycle.
*   **Transport Security:** Mandatory TLS for all non-local stdio traffic.

## 4. Deployment & Management Lifecycle
1.  **Draft:** Implement tool logic in TypeScript/Python.
2.  **Verify:** Import tool definitions into **Postman** for functional testing and schema validation.
3.  **Deploy:** Push to **Railway** for Global scope; distribute as npm package for Instance scope.
4.  **Monitor:** Use **Postman Monitors** to perform periodic health checks on SSE endpoints to ensure tool availability.
5.  **Audit:** Logs are aggregated in the `logs/` directory and synced to the Hub for behavioral analysis.
