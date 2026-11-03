# Changelog

## 0.4.0 - Unreleased

- Narrow discovery to exact guidance/manifest and named trace paths, with scoped
  source/skill globs instead of broad profile or sibling-trace enumeration.
- Accept scoped root-relative glob equivalents, application-manifest reads and
  validated top-level fixture listings in the session checker. Correlate rejected
  starts with their real completions without granting evidence eligibility.
- Document that CLI ignores `agents` and `argument-hint`; enforce the effective
  read/search-only tool surface separately and isolate evaluation host settings.
- Record 66 passing offline tests and fresh application/trace-only live captures:
  both original reports and session checks pass after checker-only finite-pattern
  compatibility fixes; preserve earlier failed-session evidence and host caveats.
- Require an independently established payload-free boundary before the first
  runtime metadata read; unknown boundaries require exact-path user sanitization
  confirmation instead of a speculative three-line read.
- Bind metadata results to unchanged reference fixtures and complete top-level
  metadata members; reject record-level sanitization markers.
- Add explicit trace-only session scope, reject ambiguous failed glob results,
  and require the currency field even when its value is unknown.
- Require exact-file content search paths; reject directory searches even with
  basename globs that can match unrelated nested files.
- Add an audit-wide exploration cap alongside per-scenario and shared-guidance
  limits; define line counting and the exact-path, user-confirmed sanitization
  exception for artifacts whose metadata cannot be isolated safely.
- Harden session checks against glob and files-only search scope bypasses and
  require sequential metadata reads in ranges of no more than three lines.
- Require exact integer types for integer report metrics.
- Add a priced retry fixture with complete failed-attempt usage and independently
  verified USD cost accounting; require the matching currency in the report.
- Expand the synthetic suite to 20 scenarios (eight tool and twelve model cases).
- Record that the 0.3.0 host smoke evaluation does not validate this candidate.
- Bind session paths to an explicit actual workspace root; handle absolute and
  relative guidance consistently and reject outside-root paths and symlink escapes.
- Require correlated tool results, completed metadata eligibility checks for every
  trace, and result-based audit-wide/shared-guidance/per-file hard-budget checks.
- Reject duplicate or contradictory limitation categories in both companion formats.
- Align sanitization documentation around metadata labels and direct exact-path
  user confirmation; document the checker capture contract and remaining manual
  per-scenario and exception review.
- Record 0.4.0 CLI application and trace-only smoke results, the initial
  currency-field schema failure, and compatibility corrections for native failed
  reads, empty globs and skill discovery without claiming multi-run reliability.

This is a candidate version, not a published Git tag or GitHub release.

## 0.3.0 - Previous candidate

- Extend the existing read-only agent to audit unnecessary model calls alongside
  tool calls without changing its permissions.
- Rename the profile to AI Efficiency Auditor and its definition to
  `ai-efficiency-auditor.agent.md`; update CLI examples and document replacement
  of the old installed definition. The GitHub repository name is unchanged.
- Map inference purpose and dependencies; separate logical model calls, attempts,
  token accounting, prompt caching, latency, and supported pricing.
- Detect demonstrated redundant inference and unused results; keep unverified
  prompt trimming, step consolidation, and model downsizing as hypotheses.
- Group findings by impact dimension and prevent overlapping tool/model savings
  or cached/reasoning token subsets from being counted twice.
- Add nine initial model scenarios alongside the original eight tool scenarios, with
  offline accounting, false-positive, and report-checker regressions.
- Preserve the historical 0.2.0 smoke evidence and record restricted 0.3.0
  application and trace-only CLI smoke evaluations, with their limitations.
- Add explicitly scoped trace-only audits without requiring a source manifest;
  preserve sanitization gates and disclose missing implementation evidence.
- Harden session search-scope checking and require structured limitation categories
  and source citations in the synthetic companion report.
- Add two source-anchored model cases that require reasoning about discarded
  output and ambiguous repeated inference without stating the conclusion in traces.
- Accept Windows and POSIX separators in structured evidence paths after the
  trace-only host evaluation exposed an overly strict checker.

This is a candidate version, not a published Git tag or GitHub release.

## 0.2.0 - Previous candidate

- Move usage documentation out of agent-discovery directories.
- Clarify runtime-artifact sanitization, scope selection, exploration budgets,
  framework guidance, confidence ranking, and citation portability.
- Record methodology version and available audit provenance in reports.
- Add eight synthetic evaluation fixtures, offline checks, and CLI session
  verification; record one passing smoke evaluation and its limitations.
- Require header-only runtime eligibility reads after a behavioral regression
  exposed an unmarked payload read.
- Document organization distribution and CLI invocation separately from hosted
  execution; cloud audit-only behavior remains experimental.
- Add the MIT license.

This is a candidate version, not a published Git tag or GitHub release.

## Initial publication

- Publish the read-only agent and introductory documentation.
