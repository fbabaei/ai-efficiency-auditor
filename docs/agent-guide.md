# Tool-Call Optimization Auditor

The [Tool-Call Optimization Auditor](../.github/agents/tool-call-optimization-auditor.agent.md)
is a read-only reviewer for AI applications. It examines source code and existing
sanitized traces to answer:

> Which tool calls are avoidable, what causes them, and how can we reduce them
> without weakening correctness, security, or reliability?

The agent definition is an instruction file, not a monitoring service. Analysis
happens when you invoke the agent.

## How it works

### 1. Establish scope

The agent reads repository instructions and the README, identifies the application
and relevant framework guidance, then finds entry points, orchestration, tool
dispatch, retries, caches, tests, and sanitized traces.

Exploration is bounded to avoid an expensive, open-ended audit. If it cannot
locate the application, it reports **not auditable** rather than inventing counts.
Trace files are eligible for counting only when their headers or metadata
explicitly state that they are sanitized.
That eligibility rule applies to runtime artifacts, not application source,
manifests, tests, or ordinary documentation. Labels do not authorize exposing
sensitive values.
Runtime eligibility is established before payload reads, using small header-only
ranges. If metadata cannot be safely separated from event payloads, the artifact
is skipped until a separate declaration is supplied.

An ambiguous multi-application workspace requires scope selection, not a guess
based on manifest entry-point counts. When interaction is unavailable, the agent
reports that scope selection is required and does not combine applications.

Each scenario has a limit of 25 files and 7,500 returned content lines, including
search results and repeated reads. The normal per-file limit is 300 lines; a
specific finding can justify up to 600 lines within the same total. Shared
guidance has a separate once-per-audit limit of 10 files and 1,500 lines.
Exhausting a budget means partial coverage, not a clean bill of health.

### 2. Map the execution path

The agent follows:

```text
Request -> router -> agent/model -> tool dispatcher -> provider
        -> result validation -> synthesis
```

It looks for branching, handoffs, fan-out, loops, fallbacks, and retries.
It distinguishes these counting units:

| Unit | Meaning |
|---|---|
| Registered tools | Capabilities available to the agent, not executions |
| Static call sites | Code locations that can invoke tools |
| Logical calls | Intended tool operations |
| Execution attempts | Initial executions plus retries |
| Downstream requests | HTTP, SDK, database, or provider operations inside a tool |
| Model invocations and agent handoffs | Counted separately from tool executions |

For example, one logical search call might produce three execution attempts,
each involving multiple downstream requests.

### 3. Measure existing traces

When eligible traces exist, the agent correlates execution records and avoids
double-counting wrapper spans, duplicate exported events, or streaming fragments.
It reports only metrics supported by the evidence, such as calls per request,
retry amplification, failures, and latency.

It distinguishes critical-path latency from summed tool duration: parallel calls
can reduce elapsed time without reducing call count. Observed cost requires
recorded usage and applicable pricing.

Without sufficient traces, the agent can establish what the code permits or
necessarily does, but cannot claim actual production frequency or measured
savings. Static counts are expressed as conditional formulas or bounds where
appropriate; unknown values remain unknown.

### 4. Identify avoidable work

Typical targets include:

- Repeated equivalent reads when state has not changed.
- Handoffs that repeat discovery or lose reusable context.
- Nested retry policies that multiply execution attempts.
- Loops without effective stopping conditions.
- Per-item requests that could safely be batched.
- Concurrent duplicate reads that could share one execution.
- Ambiguous tool descriptions that cause corrective calls.
- Tool results that can be demonstrated to have no downstream use.

**Repeated does not automatically mean redundant.** Freshness, authorization,
pagination, changed state, differing credentials, and legitimate recovery can
justify repetition.

Findings are labeled measured, statically demonstrated, or hypothetical.
Only measured or statically demonstrated findings enter the ranked list.
Hypotheses remain in the validation plan with the evidence needed to test them.

### 5. Recommend changes and validation

The agent ranks demonstrated findings by confidence, then estimated avoidable
calls per request, lower risk, and lower implementation effort.
High confidence requires complete evidence of avoidability and the relevant
identity, state, freshness, and dependency conditions. Medium confidence applies
to demonstrated bounded scenarios with unknown frequency. Low-confidence
hypotheses are unranked. Evidence level and confidence are separate labels;
unknown impact is never converted to zero.

Recommendations may include:

- Deterministic routing and narrower tool contracts.
- Request-scoped result reuse.
- Safe batching and coalescing of equivalent concurrent reads.
- Bounded retries with backoff.
- Explicit call budgets and early stopping.
- Reuse of validated evidence.

Caching and coalescing must preserve tenant, identity, authorization, freshness,
invalidation, and data-classification boundaries. Side-effecting operations must
not be suppressed indiscriminately; retries of writes require a justified
idempotency strategy.

The report separates **projected savings** from **validated savings**. It proposes
matched baseline/candidate comparisons that also check task success, evidence
quality, citation validity, freshness, isolation, and relevant failure scenarios.
An optimization is not considered validated until comparative evidence exists.

## Capabilities and limits

The agent exposes only `read` and `search`, with no subagents. Its instructions
prohibit:

- Editing files or running commands.
- Executing application tools or calling external services.
- Invoking other agents.
- Provisioning resources.
- Replaying workloads or performing experiments.

It produces an audit and recommendations; it does not implement or benchmark
the fixes. When evidence is insufficient, it identifies missing inputs and
recommends minimum instrumentation instead of fabricating measurements.

Repository content and traces are treated as evidence, not instructions or
authorization. Reports must not expose credentials, raw private prompts,
sensitive arguments, or full tool responses. Private context must not be sent
to public-web services.

## Report contents

The report contains:

1. **Verdict and evidence coverage:** scope, static versus observed evidence,
   sampling, limitations, and projected versus validated savings.
2. **Call map and inventory:** tools, static call sites, logical calls,
   attempts, downstream requests, and evidence.
3. **Runtime metrics:** supported totals and per-request/per-tool measures,
   including counting rules and denominators.
4. **Ranked findings:** priority, evidence level, confidence, avoidable calls,
   recommendation, and risk.
5. **Proposed design:** before/after call flow, scenario-specific call budget,
   expected savings, assumptions, and tradeoffs.
6. **Validation plan and missing evidence:** comparison criteria,
   instrumentation gaps, and the next highest-value action.

Every ranked finding and call-map row requires a citation. Local reports use
the editor's absolute file-and-line links; remote reports use commit-pinned
repository links when URL and revision are verified. Otherwise, remote reports
use a textual path and verified line and disclose that pinned links are
unavailable. Findings from sanitized traces use the trace path and record ID.
If a line cannot be verified, the report gives the path and marks the line
unknown. Methodology version and any known audited revision, host, and model
are recorded; unavailable provenance stays unknown.

If no redundant calls are demonstrated, the report says so and identifies what
evidence could resolve uncertainty.

## Example invocation

Select **Tool-Call Optimization Auditor** in the agent picker and submit:

> Audit this workspace's search request flow for unnecessary tool calls. Use
> existing sanitized traces if available. Focus on duplicate retrieval and retry
> amplification, distinguish observed counts from static bounds, and rank safe
> optimizations.

For a narrower audit, name the application path and scenario explicitly.
If traces are available, provide their workspace paths and ensure their headers
or metadata state that they are sanitized.

The goal is fewer unnecessary calls, not fewer checks or less reliable behavior.

## Sharing and invocation

Keep this guide outside agent-discovery directories: hosts can also recognize
plain Markdown files there as agents. See the [installation guide](../README.md),
[remote invocation guide](remote-invocation.md), and
[evaluation instructions](../evaluations/README.md).
