# Deploying the Semantic Server (MiniGuru)

## Protocol: One Per Student
Each student gets a dedicated, isolated "MiniGuru" instance on Railway. This ensures:
1.  **Isolation**: Student data (transcript history if cached) does not leak.
2.  **Scalability**: We clone the "Master Blueprint" service for each new student on-demand.
3.  **Identity**: The `STUDENT_ID` env var binds the instance to the specific student.

## Prerequisites
- Railway CLI (`brew install railway`)
- Railway Account with "Master Blueprint" project created.

## Deployment Steps

### 1. Push Code to Cloud
Ensure your local `AssemblyAIv2` repo is committed.
```bash
git push origin main
```
(Railway triggers builds from GitHub automatically)

### 2. Verify Environment Variables
Each Semantic Server needs:
- `ASSEMBLYAI_API_KEY`: For LLM Gateway (The Guru).
- `STUDENT_ID`: The UUID of the student this instance serves.
- `HUB_API_KEY`: Secrets for talking back to GitEnglishHub (if applicable).
- `EXA_API_KEY` / `FIRECRAWL_API_KEY`: For Agentic Research tools.

To verify variables:
```bash
railway variables --service [service-name]
```

### 3. Spawning a New Student Instance
Use the Railway CLI or Dashboard to duplicate the "SemanticServer-Template" service.

**Naming Convention:** `guru-[student-username]`
*Example:* `guru-leidy`, `guru-ruslan`

**Set the Student ID:**
```bash
railway variables --service guru-leidy --set STUDENT_ID=123-uuid-456
```

## Health Check
To verify an instance is successfully deployed as a MiniGuru:
```bash
curl https://guru-leidy.up.railway.app/health
# Response: {"status":"ok", "service":"Semantic Server", "version":"2.0.0"}
```

## The FastAPI Server
The entrypoint is `semantic_server.py`.
- **Port**: 8080 (Mapped automatically by Railway)
- **Endpoint**: `POST /analyze` interacts with `analyzers.llm_gateway`.
- **Dependencies**: `requirements-server.txt` (Lightweight version, NO local AssemblyAI SDK).
