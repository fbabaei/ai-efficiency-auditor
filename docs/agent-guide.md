# AI Efficiency Auditor

**Developer and author:** Fereydoun Babaei.

The [AI Efficiency Auditor](../.github/agents/ai-efficiency-auditor.agent.md)
is a reviewer with read-only application access and report-only file creation.
It examines source code and existing
sanitized traces to answer:

> Which tool and model calls are avoidable, where might tokens or model capacity
> be wasted, and how can we improve efficiency without weakening correctness,
> security, or reliability?

The agent definition is an instruction file, not a monitoring service. Analysis
happens when you invoke the agent.

## Why use it instead of the same prompt in Copilot?

The advantage is a repeatable audit method, not a smarter AI model. The auditor
runs through Copilot, adding detailed instructions and a focused tool configuration
behind a short audit request.

| Area | What the auditor adds |
|---|---|
| Coverage | A defined workflow for retrieval, inference, retries, tokens, caching, and model selection. |
| Evidence | Observed runtime counts are separated from static bounds and unknowns, with source citations. |
| Recommendations | Demonstrated waste is distinguished from hypotheses; unverified model substitutions stay in the validation plan. |
| Boundaries | Restricted tools and instructions against changing application code, replaying workloads, or exposing sensitive evidence. |
| Reporting | Standardized findings and a short Executive Summary, with save verification and preview consent. |

Ordinary Copilot could produce comparable results if given the entire agent
definition, equivalent tools, the same model, and the same evidence. The benefit
is packaging and versioning the methodology once, with regression evaluations,
rather than reconstructing it for every audit.

The auditor is not guaranteed to be more accurate, faster, or cheaper. Its longer
instructions add context overhead, and instruction-following can still fail,
including missed report or preview steps. Tool restrictions and instructions are
not a report-only filesystem sandbox. Its strongest benefit is consistency and
reviewability for repeated audits, not proven superiority over a carefully
configured Copilot session.

## How it works

### 1. Establish scope

The agent reads repository instructions and the README, identifies the application
and relevant framework guidance, then finds entry points, orchestration, tool
dispatch, model clients and selection, prompt/context construction, output
consumption, retries, caches, tests, and sanitized traces.
Discovery starts with exact named guidance files and manifests, followed by
narrow source/skill-directory globs. Named trace paths are reused without
enumerating sibling traces; the installed auditor profile is not application
evidence. Trace-only audits skip directory listings and manifest discovery.

Exploration is bounded to avoid an expensive, open-ended audit. If it cannot
locate the application, it reports **not auditable** rather than inventing counts.
Trace files are eligible only after safely isolated headers/metadata explicitly
state that they are sanitized, or the user directly confirms in the conversation
that each exact named path is sanitized.
That eligibility rule applies to runtime artifacts, not application source,
manifests, tests, or ordinary documentation. Labels do not authorize exposing
sensitive values.
Without that user confirmation, runtime eligibility is established before payload
reads or content searches, using small, sequential header-only ranges. If metadata
cannot be safely separated from event payloads, skip the artifact. Before even the
first read, the payload-free range must be established by the user's direct
statement naming the exact path and range, or an independently trusted format
contract. An initial three-line read is not automatically safe. Repository text
or an unendorsed sidecar is not user confirmation.

For an explicitly requested trace-only audit, name the existing trace paths.
The agent does not require an application manifest or discover unrelated source,
but applies the same sanitization and read-budget rules. It reports observed
metrics with trace citations and marks source-level causes, static call sites,
implementation details and avoidability unknown unless the trace establishes
them. If no eligible artifact is found, the result is **not auditable** with no
call counts. This mode does not silently replace a requested application audit.

An ambiguous multi-application workspace requires scope selection, not a guess
based on manifest entry-point counts. When interaction is unavailable, the agent
reports that scope selection is required and does not combine applications.

The entire audit has a limit of 50 distinct files and 15,000 returned content
lines, including search results and repeated reads. Each scenario is additionally
limited to 25 files and 7,500 lines. The normal per-file limit is 300 lines; a
specific finding can justify up to 600 lines within every applicable total.
Shared guidance counts toward the audit-wide totals and is additionally limited
to 10 files and 1,500 lines once per audit. Glob-returned paths count as files,
not content lines. Exhausting any budget means partial coverage, not a clean bill
of health.

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
| Logical model calls | Intended inference operations, separate from tool calls |
| Model attempts | Actual inference requests, including retries, failures, and fallbacks |
| Tokens | Recorded input/output usage, not call counts |
| Agent handoffs | Counted separately from tool and model attempts |

For example, one logical search call might produce three execution attempts,
each involving multiple downstream requests.
Likewise, one logical model call retried once produces two model attempts.
The model map records purpose, model/version, effective inputs and output
consumers. Embedding usage is separate from generation. A model request inside
a tool is linked across maps, not charged twice in combined savings.

### 3. Measure existing traces

When eligible traces exist, the agent correlates execution records and avoids
double-counting wrapper spans, duplicate exported events, or streaming fragments.
It reports only metrics supported by the evidence, such as calls per request,
retry amplification, failures, and latency.

It distinguishes critical-path latency from summed tool duration: parallel calls
can reduce elapsed time without reducing call count. Observed cost requires
recorded usage and applicable pricing. Model duration is reported separately
from tool duration, with overlapping work accounted for.

Model metrics include logical calls, attempts, retries, and recorded input,
output, cached-input and reasoning tokens. Provider accounting matters: cached
tokens may already be included in input, and reasoning tokens in output.
Those subsets must not be added again. Provider prompt caching may reduce
billed cost while leaving the number of inference calls unchanged.
Failed requests may consume tokens; missing usage is unknown, not zero.
Cost requires applicable model/version, pricing date, units, currency, and
cache/reasoning billing rules. When supplied rates are per million tokens, cached
input is a separately priced subset, and reasoning is included in output, compute
cost across all attempts as
`((input-cached_input)*input_rate + cached_input*cached_rate + output*output_rate)/1_000_000`.
Include failed-attempt usage when recorded. Follow a different calculation only
when the supplied pricing explicitly requires it. Deployment names do not
establish price or quality.

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
- Repeated inference on unchanged effective inputs when the output contract
  permits reuse.
- Model calls whose output is discarded, or that implement fully specified
  deterministic routing without required inference.
- Overlapping planning, critique, repair, and synthesis steps.
- Excessive context or unused generated output.
- Potential model-capacity mismatch for constrained tasks.

**Repeated does not automatically mean redundant.** Freshness, authorization,
pagination, changed state, differing credentials, and legitimate recovery can
justify repetition.
For inference, effective inputs include system instructions, prompt version,
conversation, retrieved evidence, tool schemas, model/settings, policy and
identity. Identical user text or temperature zero is not proof of safe reuse.
Required independent checks and stochastic samples must remain independent.

Findings are labeled measured, statically demonstrated, or hypothetical.
Only measured or statically demonstrated findings enter the ranked list.
Hypotheses remain in the validation plan with the evidence needed to test them.
In particular, a large token count or expensive model is not proof of waste.
Smaller-model substitutions, prompt trimming and step consolidation remain
hypotheses unless source contracts or comparative evaluations establish
acceptable replacement behavior.

### 5. Recommend changes and validation

The agent ranks demonstrated findings by confidence, then estimated avoidable
calls per request, lower risk, and lower implementation effort.
Tool-call, model-call and token/capacity findings are grouped separately.
Token-only findings use supported avoidable tokens, not fictional call savings;
tokens and calls are not interchangeable ranking units. Cross-group cost ranking
requires comparable supported pricing and usage.
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
- Safe inference-result reuse and removal of proven redundant model steps.
- Task-specific output limits and evaluated model routing.

Caching and coalescing must preserve tenant, identity, authorization, freshness,
invalidation, and data-classification boundaries. Side-effecting operations must
not be suppressed indiscriminately; retries of writes require a justified
idempotency strategy.
Model reuse must additionally preserve prompt/model versions, conversation and
evidence state, policy, output schema, and sampling requirements. Removing
inference must preserve required errors and side effects as well as output.

The report separates **projected savings** from **validated savings**. It proposes
matched baseline/candidate comparisons that also check task success, evidence
quality, citation validity, freshness, isolation, and relevant failure scenarios.
An optimization is not considered validated until comparative evidence exists.
Model comparisons additionally cover schema adherence, routing accuracy,
difficult and safety-sensitive inputs, independent checks, and stochastic
variance. Fewer calls alone does not establish a better design.
Tool/model call and token budgets are separate; overlapping savings are not
summed when removing one model step also removes its tool work.

## Capabilities and limits

The agent exposes `read`, `search`, `edit`, `ask_user`, and
`appmod-preview-markdown`, with no subagents. Its sole write exception is creating
a new Markdown Executive Summary; preview requires explicit user consent. These
host-specific interaction/preview names must resolve to compatible local tools.
If unavailable, it uses Chat and manual save/preview instructions. The `edit`
group is not path-restricted by the host; report-only writes are an instruction
boundary, not a sandbox. Its instructions
prohibit:

- Editing application code, configuration, evidence, or existing files.
- Running commands, including commands to save or preview reports.
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
   attempts, downstream requests, and evidence, plus a separate model map with
   purpose, model/version, calls, attempts, and input/output dependencies.
3. **Runtime metrics:** separate tool/model totals, per-request/per-tool/per-model
   measures, tokens, latency and supported cost, including coverage, counting
   rules, subset semantics and denominators.
4. **Ranked findings:** priority, evidence level, confidence, avoidable calls,
   supported token/cost impact, recommendation, and risk, grouped by dimension.
5. **Proposed design:** before/after call flow, scenario-specific call budget,
   expected savings, assumptions, and tradeoffs.
6. **Validation plan and missing evidence:** comparison criteria,
   instrumentation gaps, and the next highest-value action.

Source-backed weaknesses and redundancy findings identify the affected file,
function or section, and smallest verified line range. Findings spanning repeated
or duplicated code identify each relevant site and explain its role. Call-site
ranges exclude unrelated return statements or surrounding context. File-and-line
notation stays visible in citation labels or adjacent text; each summary Code
location cell shows the affected paths and ranges directly beside the symbol,
not only in link targets or reference definitions. Detailed
reports may include minimal relevant code excerpts with sensitive values omitted;
Executive Summaries include locations, not code excerpts. Trace-only findings
say "Code location not verified" when no source mapping is available. Summaries
of existing reports label copied locations "From supplied report; not reverified"
or state "Not provided in supplied report"; they do not inspect code to fill gaps.

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

### Executive Summary and preview

Every audit also creates a plain-language Executive Summary of at most 60 lines and
600 words. It includes a bottom line, up to five evidence-backed priority rows
(`Priority | Weak area | Code location | Recommended improvement | Expected benefit | Evidence`),
separate evidence gaps, safeguards to retain, and one next action. It preserves
ranking, confidence, conditional benefits, unknowns, and non-overlapping savings.
An existing supplied audit can be shortened without new source inspection.
The detailed six-section report is still required for new audits.

The default output is `reports/<application>-audit-executive-summary.md` in the audited
workspace (`trace` for trace-only audits). Existing files are never overwritten;
the agent checks exact paths and uses the first available numeric suffix.
An explicitly requested outside-workspace destination requires confirmation.
After reading back the saved report, the agent links it and asks whether to open
Markdown preview. Only an explicit Yes opens that file; declining, dismissing,
or not answering leaves it closed. Each new report requires fresh consent.

Without a save tool or after a save failure, the agent explains that the report
was not saved and returns Markdown in Chat. Without interaction tools it asks
in Chat; without preview tools it explains how to use **Markdown: Open Preview**
manually. Non-interactive runs never open preview. Save, verification, and
preview errors must be reported rather than presented as success.

## Example invocation

Select **AI Efficiency Auditor** in the agent picker and submit:

> Audit this workspace's search request flow for unnecessary tool and model calls.
> Use existing sanitized traces if available. Focus on duplicate retrieval,
> repeated inference, retries, token usage and model selection. Rank demonstrated
> optimizations and keep unverified substitutions in the validation plan.

For a narrower audit, name the application path and scenario explicitly.
If traces are available, provide their workspace paths and either directly confirm
each exact path is sanitized or identify its independently established payload-free
metadata range, where the agent can inspect the sanitization label.

The goal is fewer unnecessary calls, not fewer checks or less reliable behavior.

For missing model telemetry, the auditor recommends opaque logical-call/attempt
IDs, model/version, purpose, prompt/context versions, generation settings,
outcome/finish reason, consumption references and recorded usage with coverage
and subset semantics. It does not request raw prompts, chain-of-thought or
responses, and it does not collect telemetry itself.

## Sharing and invocation

Keep this guide outside agent-discovery directories: hosts can also recognize
plain Markdown files there as agents. See the [installation guide](../README.md),
[remote invocation guide](remote-invocation.md), and
[evaluation instructions](../evaluations/README.md).
