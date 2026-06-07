## Bad Output Log - Run #003

**Date**: During development testing
**Provider**: groq (llama-3.3-70b-versatile)
**Input**: Single Grain blog post about AI content strategy
**Platform**: LinkedIn

**What the agent produced**:
"I recently built a content pipeline that reduced our publishing time by 60%. Here's what I learned about using AI in content strategy: [rest of post]"

**Why it's wrong**:
First-person singular voice detected - "I recently built". ContentFlow generates posts on behalf of a brand, not an individual. Single Grain posts speak in brand voice. This post would publish as if a named employee wrote it, not as Single Grain the company.

**Proof tier**: Tier 3 - observed during development, logged here with fix applied.
[Observed] Detected in development run, not production.

**How it was detected**:
Hard-coded regex in validate.py checks for patterns:
- r"^I " (starts with I)
- r"\bI built\b|\bI created\b|\bI think\b|\bI recently\b"
This runs in Python code, not by AI, so it cannot be hallucinated away.

**What happened next**:
EscalationFlag added:
reason="FIRST_PERSON_DETECTED"
stage="validate"
detail="Post starts with first-person singular: 'I recently'"
routing_decision set to "escalated"
Post not delivered.

**How it was fixed**:
Two changes made:
1. prompts/generate.md updated - added explicit rule:
   "Never write in first person singular. You are writing on behalf of a brand. Never start with I or use I built / I created / I think / I recently."
2. generate.py retry logic: if FIRST_PERSON_DETECTED pattern found post-generation, retry once with the rule appended as a reminder before escalating.

**After fix**: Same input produced:
"Most content teams are leaving AI leverage on the table.
Here's what the data shows about AI-powered content strategy in 2025: [rest of post]"
No first-person. Validated clean. Routed to approved.

**Source label**: [Observed] - happened in dev, fix verified by re-running same input.
