# Evidence Log

## Section 1: Evidence Table

| Claim | Proof Tier | Source Label | Evidence |
|---|---|---|---|
| Pipeline correctly escalates insufficient content | Tier 3 | [Observed] | tests/test_messy.py passes · output_messy.json in fixtures |
| Twitter post enforced under 270 chars in code | Tier 3 | [Observed] | validate.py regex + tests/test_normal.py assertion |
| Validator catches first-person voice in Python, not AI | Tier 3 | [Observed] | tests/fixtures/bad_output_log.md + validate.py source |
| Sensitive content triggers escalation or review | Tier 3 | [Observed] | tests/test_failure.py passes · output_failure.json |
| LangGraph interrupt_before pauses for human review | Tier 3 | [Observed] | graph.py compile call · LangGraph checkpoint docs |
| Pipeline runs with Groq, OpenAI, Anthropic, Gemini, Ollama without code changes | Tier 3 | [Observed] | agent/llm.py factory · LLM_PROVIDER env var |
| Pipeline runs correctly on 5 real Single Grain blog posts with observed outputs | Tier 4 | [Observed] | BATCH_TEST_RESULTS.md — measured from real URLs, real model, real outputs logged |
| Full pipeline completes in under 15 seconds | Tier 2 | [Estimated] | asyncio.gather for concurrent platform generation · Groq p50 latency ~2s per call |
| Runs with single docker compose up --build | Tier 3 | [Observed] | Dockerfile + docker-compose.yml verified locally |
| [Assumed] 45 minutes saved per blog post at agencies | Tier 0 | [Assumed] | Brief states "45 minutes per post" — taken from challenge brief directly |
| [Benchmarked] Groq llama-3.3-70b free tier: 14,400 req/day | Tier 2 | [Benchmarked] | console.groq.com pricing page |

## Section 2: AI Usage Disclosure

Tools used:
- Claude (claude.ai): architecture planning, prompt drafting, code scaffolding across 23 prompts
- Groq API (llama-3.3-70b-versatile): runtime LLM for content extraction and post generation

What I decided personally:
- Model-agnostic design with Groq as default — not suggested by AI, motivated by the brief's explicit mention of multiple LLM options
- Validator runs hard checks in Python code, not by AI — deliberate judgment that some rules should not be delegatable to an LLM
- LangGraph over custom state machine — matches production agent patterns, makes human-in-the-loop real and inspectable, not just a comment
- Three-tier routing (approve/review/escalate) instead of binary pass/fail — reflects real agency workflow

What I checked manually:
- Routing logic handles all three test cases correctly
- Char limit enforcement actually counts characters, not tokens
- Bad output example is realistic and fix is verifiable
- Docker compose starts cleanly with only GROQ_API_KEY set

Known weak spots:
- JS-rendered pages will under-perform (mitigated by word count gate)
- Groq rate limits could slow batch runs ([Benchmarked] 6,000 tokens/min on free tier)
- Instagram hashtag relevance depends on extraction quality — low confidence extractions produce generic hashtags
