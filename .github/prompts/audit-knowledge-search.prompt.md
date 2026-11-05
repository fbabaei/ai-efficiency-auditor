---
description: "Audit a knowledge-search request flow for unnecessary tool and model calls using AI Efficiency Auditor methodology 0.4.0."
agent: "AI Efficiency Auditor"
---

Audit this workspace’s knowledge-search request flow using AI Efficiency Auditor methodology 0.4.0.

Keep application code, configuration, and existing evidence read-only. Do not execute workloads, call external services, or modify the application.

Trace the current flow from incoming request through routing, skill/reference loading, context reads, RAG retrieval, validation, answer synthesis, and reporting-related inference. Verify the relevant entry points instead of assuming every search uses Q&A.

Focus on:
- Duplicate retrieval and repeated reads within a request.
- Repeated inference, unnecessary handoffs, and unused outputs.
- Retry amplification across orchestration, tools, SDKs, and providers.
- Repeated context, retrieval payload size, token usage, and prompt caching.
- Model selection and reasoning effort.

Use existing runtime traces only when their sanitization is safely established. I am not confirming that any particular trace is sanitized. Otherwise, use source evidence and report conditional bounds—not observed counts.

Treat historical performance reports as secondary evidence. Check whether their recommendations are already implemented before repeating them as current findings.

Clearly separate:
1. Observed behavior.
2. Statically demonstrated behavior.
3. Control and instrumentation gaps.
4. Unverified optimization hypotheses.

For every demonstrated finding, cite the affected function/configuration and precise file-and-line ranges. Explain why the work is avoidable, considering authorization, freshness, dependencies, failure recovery, and output consumption.

Keep logical tool calls, execution attempts, downstream requests, model calls, and tokens separate. Rank demonstrated optimizations by confidence, supported impact, risk, and effort. Do not invent savings or treat repeated calls as automatically redundant.

Keep smaller-model substitutions, lower reasoning effort, and quality-dependent context reductions in the validation plan unless comparative evidence supports them.

Deliver the detailed six-section audit and save a new Executive Summary under reports/. Include scenario-specific baseline/candidate call budgets, safeguards, and a matched validation plan. If evidence is insufficient, identify the smallest sanitized export needed to resolve the highest-value uncertainty.
