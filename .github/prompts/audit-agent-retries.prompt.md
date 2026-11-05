---
description: "Audit AI agent retry amplification, loops, and handoffs for avoidable tool and model work."
agent: "AI Efficiency Auditor"
---

Audit this workspace's AI agent orchestration and failure-recovery flow using AI Efficiency Auditor methodology 0.4.0.

Keep application code, configuration, and existing evidence read-only. Do not execute commands or workloads, replay requests, invoke other agents, call external services, or modify the application. The only write exception is creating new Markdown detailed audit and Executive Summary files under reports/.

Identify the relevant agent entry points, orchestration loops, handoffs, tool dispatch, model clients, retry wrappers, and provider settings. If multiple applications are equally plausible, ask which to audit; do not combine their counts. If no relevant application or flow can be located, report that it is not auditable instead of substituting evaluation fixtures.

Focus on:
- Retry amplification across orchestration, tools, SDKs, and providers.
- Repeating an entire workflow when only one failed step needs recovery.
- Reissuing completed retrieval or inference after a timeout, handoff, or validation failure.
- Agent loops with missing termination conditions, ineffective progress checks, or unused outputs.
- Handoffs that reload the same context or repeat inference without a demonstrated dependency.
- Token growth from repeated context, tool responses, and retained failure history.

Use existing runtime traces only when their sanitization is safely established under the methodology's eligibility rules. This prompt does not confirm that any trace is sanitized. Do not inspect event payloads to establish sanitization. If safe eligibility cannot be established, skip the artifact and identify the missing evidence.

Separate observed behavior, statically demonstrated behavior, control/instrumentation gaps, and unverified optimization hypotheses. Historical reports are secondary evidence; verify that an issue is still present before presenting it as current.

For each demonstrated finding, cite the affected function or configuration and precise file-and-line ranges. Cite each retry layer and repeated call site separately. Explain why the work is avoidable, considering authorization, freshness, dependencies, output consumption, cancellation, failure recovery, and side effects. Do not treat identical arguments, repeated tool names, or a missing cap as proof of wasted work.

Keep logical tool calls, execution attempts, downstream requests, logical model calls, model attempts, and tokens separate. For static retry bounds, state whether settings count retries or total attempts and whether nested layers actually execute together. Do not multiply unrelated, mutually exclusive, or unknown retry limits.

Build separate baseline/candidate call budgets for applicable scenarios: normal success, one transient tool failure, one transient model failure, timeout after a possible side effect, and exhausted retries. Mark unsupported scenarios N/A and unknown values unknown; never invent measurements or savings.

Rank only demonstrated optimizations by confidence, supported impact, risk, and effort. Keep unverified model substitutions, lower reasoning effort, quality-dependent context reductions, and speculative architectural changes in the validation plan.

Preserve necessary retries, authorization checks, evidence validation, freshness guarantees, and failure notifications. Any proposed reuse must preserve identity and trust boundaries. For side-effecting calls, account for idempotency and uncertain completion before recommending a retry or deduplication strategy.

Save the complete detailed six-section audit as reports/<application>-audit-detailed-report.md and a new Executive Summary as reports/<application>-audit-executive-summary.md. Never overwrite existing files; use the first unused numeric suffix for each occupied path. Include safeguards and a matched baseline/candidate validation plan covering output quality, recovery success, side-effect correctness, call units, tokens, and latency. Recommend experiments; do not run them. If evidence is insufficient, identify the smallest sanitized export needed to resolve the highest-value uncertainty.

Read both saved files back, verify all six sections and evidence citations in the detailed report, and check the Executive Summary's 60-line and 600-word limits (these limits do not apply to the detailed report). Link the verified detailed report from the summary and provide links to both files. Disclose save or verification failures and return any unsaved report in Chat. After successful summary verification, ask: "Open the Executive Summary in Markdown preview?" Open only that new summary after an explicit Yes; otherwise do not open preview.
