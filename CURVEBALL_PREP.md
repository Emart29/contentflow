## Likely Curveballs and My Responses

### "Add a 4th platform - YouTube community post"

How I'd do it in under 10 minutes:
1. Add "youtube" to the platform Literal in models/input.py
2. Add YouTube rules to prompts/generate.md:
   max 5000 chars, conversational, question or poll hook, no hashtags
3. Add "youtube" to the UI checkboxes
4. No other changes needed - generate.py loops over platforms dynamically

Exact lines to change:
- models/input.py: add `"youtube"` to the `platforms` Literal in `RunConfig`
- models/output.py: add `"youtube"` to the `platform` Literal in `SocialPost`
- api/main.py: add `"youtube"` to the `RunRequest.platforms` Literal
- prompts/generate.md: add a YouTube platform rules section
- ui/index.html: add one checkbox and a `youtube` entry in `limits` and `platformLabels`

### "What if the blog post is in a language other than English?"

Current behavior: pipeline runs, extraction may work (LLM handles multilingual), posts generated in same language as input.

Gap: char limits still apply but may not be appropriate for all languages.

Fix I'd add: detect language in extract node, flag non-English as LOW_CONFIDENCE, route to review.

### "What if Single Grain wants to schedule the posts, not just generate them?"

Current: outputs JSON, stops at approved.

Extension: add a "schedule" node after publish.

Integrations: Buffer API, Hootsuite API, or LinkedIn/Twitter direct APIs.

Time to add: 2-3 hours for one platform integration.

What stays human: final schedule time approval.

### "Show me a run that failed and how you debugged it"

Point to bad_output_log.md - first-person detection, how validate.py caught it, how prompt was fixed.

Also show: contentflow.db logs - every run has flags_detail JSON column showing exactly what fired.

### "How would this scale to 50 clients, 20 posts/week each?"

Current: synchronous, one run at a time.

Bottleneck: Groq free tier 14,400 req/day [Benchmarked].

Fix: upgrade to Groq paid tier or add OpenAI as fallback, add a job queue (Redis + Celery or LangGraph's built-in async), run platform generation already uses asyncio.gather.

Numbers: [Estimated] 50 clients x 20 posts x 3 platforms = 3,000 LLM calls/week. Groq paid handles that easily.

### "What's the weakest part of your agent?"

Honest answer: extraction quality on short or poorly structured blog posts. If key_ideas are weak, all three posts are weak. The confidence scoring helps route these to review but doesn't fix them.

Better fix: add a content quality pre-check before extraction - score readability and structure, reject below a threshold.

### "Why LangGraph over a simple Python pipeline?"

Three real reasons:
1. interrupt_before is real - the graph physically pauses for human review, state is persisted in SQLite, resumable
2. State management - every node receives and returns the full state, no hidden globals
3. Observability - LangGraph Studio can visualize runs, checkpoints are inspectable

Honest tradeoff: adds complexity and a dependency. For a prototype, a simple async pipeline would work. LangGraph earns its weight when you need reliable human-in-the-loop and run persistence.
