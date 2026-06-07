## ContentFlow Demo Script (~4 minutes)

### 0:00 - 0:20 | Setup
- Show terminal: `docker compose up --build`
- Show both services starting (api + ui)
- Say: "One command, two services, no config beyond the API key"

### 0:20 - 1:10 | Normal case (live URL)
- Open localhost:3000
- Paste a real Single Grain blog URL
- Client name: "Single Grain"
- Brand voice: "Data-driven, direct, results-focused"
- Hit Run Agent
- Show spinner, show posts appearing
- Click copy on LinkedIn post
- Point out: char count badge, confidence badge, run metadata (provider: groq, model: llama-3.3-70b)

### 1:10 - 1:50 | Messy case
- Paste the messy fixture URL
- Hit Run Agent
- Show red Escalated banner
- Show INSUFFICIENT_CONTENT flag with detail
- Say: "42 words detected. Agent stops here instead of generating garbage output."

### 1:50 - 2:40 | Failure case
- Paste the failure fixture URL (or describe the content)
- Hit Run Agent
- Show escalated/review status
- Show UNVERIFIED_CLAIMS_DETECTED and SENSITIVE_TOPICS_DETECTED flags
- Say: "This runs in Python code in validate.py — not by the model. The model cannot argue its way past it."

### 2:40 - 3:10 | Model swap
- Open .env in editor
- Change LLM_PROVIDER=groq to LLM_PROVIDER=anthropic
- `docker compose restart api`
- Re-run same URL
- Show identical output structure, different provider badge in UI
- Say: "One line change. No code touched."

### 3:10 - 3:40 | Code walkthrough (curveball prep)
- Open agent/graph.py — show the LangGraph compile with interrupt_before
- Open agent/validate.py — show the Python regex checks
- Open agent/llm.py — show the factory function
- Say: "Human-in-the-loop is a real checkpoint, not a comment."

### 3:40 - 4:00 | Run logs
- Show Recent Runs table in UI
- Open contentflow.db briefly in DB viewer or run:
  `sqlite3 contentflow.db "SELECT run_id, status, llm_provider, duration_seconds FROM runlog ORDER BY created_at DESC LIMIT 5;"`
- Say: "Every run logged. Reviewable."

Record this with Loom. Upload and add the link to your README under a "Demo" section at the top.
