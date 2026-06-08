# ContentFlow

A LangGraph agent that takes a blog post URL and generates platform-specific social media posts for LinkedIn, Twitter/X, and Instagram — with deterministic validation, human-in-the-loop review, and full routing logic.

Built for the Single Grain Beat Claude Intern 011 challenge.

Built with: LangGraph · Groq (llama-3.3-70b) · FastAPI · Tailwind CSS · Docker

---

## Part 1 — Domain and Background

**Preferred area:** AI engineering and automation — building systems that make repetitive, judgment-heavy workflows reliable enough to run without constant human intervention.

**Why Single Grain:** Single Grain sits at the exact intersection I care about — a content operation that runs at scale and is actively replacing manual steps with AI. The coordinator workflow in this brief (45 minutes per blog post, 4x/week, manual caption writing across three platforms) is the kind of concrete, measurable problem I build for. Not "AI strategy" — actual hours saved, actual posts shipped.

**Notable prior work:** [evalflow](https://github.com/emartai/evalflow) — a pytest-style regression testing framework for LLM prompts. Catches prompt quality regressions before they reach production by running structured assertions against model outputs. Built it because llm-quality-gate ([github.com/emart29/llm-quality-gate](https://github.com/emart29/llm-quality-gate)) showed me that teams were manually spot-checking LLM outputs in staging — the same way they used to manually test software before CI existed. Also built [ragwell](https://github.com/emart29/ragwell), a production RAG pipeline with semantic chunking and multiple retrieval strategies, and [playagent](https://github.com/emartai/playagent), an agent testing framework for catching agent failures before users do.

---

## Part 3 — Personal Automation

The most tedious recurring task I've done is reviewing LLM prompt outputs after model updates — opening 40–50 generated responses one by one, comparing them to expected behavior, and logging which ones regressed. It's pure pattern recognition that doesn't require judgment, just attention, and it took 2–3 hours every time a provider pushed a model version. I automated it by building evalflow: define expected output properties as assertions, run them against a test suite on every model update, get a pass/fail report in under a minute. The part that stays human is deciding what the assertions should be in the first place — that requires knowing what "good" looks like for a specific client and use case, which is judgment the tool can't replace.

---

## Screenshots

**Approved** — clean post, 0 flags, auto-published

![Approved](screenshots/approved.png)

**Review Required** — competitor names detected, routed to human inspection

![Review Required](screenshots/review.png)

**Escalated** — insufficient content (JS-rendered page, 24 words)

![Escalated](screenshots/escalated.png)

**Tests** — 3/3 passing

![Tests](screenshots/tests.png)

---

## How it works

A blog URL enters a 5-node LangGraph pipeline:

1. **Ingest** — fetches the URL, strips nav/footer/scripts, counts words. Under 200 words or 404 → escalates immediately.
2. **Extract** — LLM returns structured JSON: key ideas, audience, tone, CTA, sensitive topics, confidence.
3. **Generate** — one LLM call per platform, run concurrently via `asyncio.gather`. Twitter auto-retries if over 270 chars.
4. **Validate** — Python regex checks for blocked terms, unverified stat phrases, first-person voice. No LLM involved.
5. **Route** — hard failures → escalated. Soft flags → review (LangGraph `interrupt_before` checkpoint). Clean → approved.

---

## Quickstart

```bash
cp .env.example .env
# add GROQ_API_KEY to .env (free at console.groq.com)
docker compose up --build
# open http://localhost:3000
```

Or run locally:

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python run_demo.py
```

---

## Switching LLM providers

Change one line in `.env` — no code changes needed:

```env
LLM_PROVIDER=groq        # default (free)
LLM_PROVIDER=anthropic   # claude-sonnet-4-20250514
LLM_PROVIDER=openai      # gpt-4o
LLM_PROVIDER=gemini      # gemini-2.0-flash
LLM_PROVIDER=ollama      # local, no key needed
```

---

## Evidence

- `tests/fixtures/output_normal.json` — approved run, 3 posts, 0 flags
- `tests/fixtures/output_messy.json` — escalated, INSUFFICIENT_CONTENT
- `tests/fixtures/output_failure.json` — review, sensitive topics flagged
- `BATCH_TEST_RESULTS.md` — 5 real Single Grain URLs, live pipeline execution
- `tests/fixtures/bad_output_log.md` — real failure caught during development + fix documented
