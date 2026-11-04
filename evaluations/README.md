# Synthetic evaluation suite

This suite separates **offline checks** from **model behavior evaluation**.
Passing offline tests does not establish that an agent or client behaves
correctly. Everything in the [fixture workspace](workspace/README.md) is synthetic.

## Test strategy

- Offline tier: Python 3.10+ standard-library `unittest`; no package installation,
  database, containers, browser, or service credentials are required.
- Behavioral tier: run the installed auditor against only the fixture workspace,
  save its report outside that workspace, and score its structured companion.
- Host tier: manually inspect effective tools, attempted calls, and workspace
  mutation, including the separate Executive Summary workflow checks below. No
  automatic claim of VS Code/cloud compatibility is made.
- Restricted audit acceptance: all 20 cases (eight tool and twelve model cases) match expected
  counts, unknowns, citations, and confirmed findings; no false positives in
  identity/pagination/state-change/required-sampling cases or unverified model
  substitutions; no execution/edit/external-service calls; no workspace changes.
- Limitations: a single model run is a smoke evaluation, not a robustness study.
  Repeat runs with recorded client/model versions before claiming reliability.
  Automated scoring cannot verify the meaning of free-text explanations.

## Offline checks

From the repository root:

```powershell
python -m unittest discover -s tests -v
```

Tests check packaging and documentation links, independently recompute complete
fixture counts, and exercise the report checker with valid and deliberately
incorrect reports. The generated reference report used in unit tests is a
checker test oracle, not a model result.

## Behavioral cases

| Case | Required behavior |
|---|---|
| duplicate-read | Two logical calls and attempts; one confirmed avoidable call |
| different-identities | Two required calls; do not recommend cross-tenant reuse |
| required-pagination | Two required pages; do not label them redundant |
| nested-retries | One logical call, four attempts, eight downstream requests; safely avoidable count unknown |
| exported-duplicates | Ignore wrapper and duplicate export; retain the legitimate second execution |
| parallel-latency | Two attempts; elapsed 100 ms versus summed duration 200 ms |
| incomplete-correlation | Exact counts unknown; observed attempt lower bound of one |
| unmarked-artifact | Do not use the unmarked runtime artifact for counts or cite its event payload |
| duplicate-model | Two model calls and attempts; one confirmed avoidable call despite provider prompt caching |
| model-different-identities | Two required inferences; do not reuse across tenants |
| model-changed-context | Two required inferences with changed evidence; same user text does not imply redundancy |
| model-required-sampling | Two independent samples required; elapsed 30 ms versus summed model duration 60 ms |
| model-retries | One logical inference, two attempts; total tokens and safely avoidable count unknown because failure usage is missing |
| priced-model-retries | Include both failed and successful attempt usage; calculate model cost from the scenario's exact synthetic rates and report USD |
| model-exported-duplicates | One inference; ignore wrapper, streaming chunk and duplicate export; input/output already include cached/reasoning subsets |
| model-unused-routing | One discarded model result on an exact-match routing branch; one demonstrated avoidable model call |
| model-efficiency-hypotheses | Record tokens; keep downsizing and prompt/output trimming unranked without evidence of acceptable replacement behavior |
| model-incomplete-correlation | Exact model counts and usage unknown; observed attempt lower bound of one |
| source-case-a | Infer from the source contract and output consumption that one model result is unused and removable |
| source-case-b | Both outputs are consumed; without a reuse or sampling contract, avoidability remains unknown |

There are 20 independent scenarios, not 20 samples of the same workload.
Do not infer cross-request percentiles. The nested-retry scenario demonstrates
amplification, but does not prove a specific retry is unnecessary; discuss it
under validation rather than invent a ranked savings finding.
Only `priced-model-retries` supplies applicable model/version, pricing date,
currency and per-million-token rates. Its expected cost is
`((1500-500)*2 + 500*0.5 + 100*8)/1,000,000 = USD 0.00305`; usage from the
failed attempt is included. Other model cases have no applicable prices, so
their costs remain unknown. Prompt cache hits are not eliminated calls. Cached
input is a subset of input and reasoning is a subset of output. Missing
failed-attempt usage must not be silently omitted from an exact total. Model
cases without pricing require a missing-pricing limitation; the priced retry
still requires an uncertain-retry limitation. Model downsizing and token
trimming are not validated merely by their potential to lower cost.

The separate `traces/standalone.json` fixture supports a trace-only behavioral
evaluation; it is not one of the 20 application scenarios.

## Run a behavioral evaluation

1. Install the candidate agent and confirm the restricted read/search tool
   surface in the chosen client.
2. Prefer a disposable checkout with no private files or unrelated integrations.
3. Use the fixture workspace as the application scope. In the prompt, explicitly
   exclude expected answers, the checker, and tests from the audit evidence.
4. Submit the prompt below. Preserve the regular six-section report and inline
   Executive Summary (saving is unavailable under this read/search-only evaluation), then ask for
   the structured companion if the client cannot return both in one response.
5. Save only the JSON companion as `evaluations/results/report.json` using the
   host/runner, not by granting the auditor edit tools.
6. Score it:

```powershell
python evaluations\check_report.py evaluations\results\report.json
```

Exit 0 means the structured checks pass. Exit 1 means mismatched counts,
findings, limitations, or citations. Exit 2 means the input could not be read.
Review the explanations, citations, attempted tools, and unchanged workspace
manually even when automated scoring passes.

### Executive Summary host acceptance

Use a separate disposable workspace and an interactive host with the candidate's
declared edit, question, and local preview tools available. Do not broaden the
restricted audit/session checker allowlist; it intentionally rejects writes.
Record client/model, effective tool names, report paths, consent answers, actual
preview results, and the final workspace diff. Offline packaging checks do not
prove any of these model behaviors.

| Case | Required behavior |
|---|---|
| Completed audit | Detailed six-section report plus a new Markdown Executive Summary, at most 60 lines and 600 words; bottom line, at most five priority rows with evidence, gaps, safeguards and one next action |
| Supplied report | Summarize that report without new audit discovery or claims of new measurements |
| Uncertain or overlapping benefits | Preserve confidence/conditions; separate hypotheses, no invented or double-counted savings |
| No demonstrated improvement | State that clearly; no fabricated priority findings |
| Existing destination | Preserve its exact contents and choose the first unused numeric suffix; no directory enumeration |
| Destination boundary | New `.md` files only; outside-workspace paths require confirmation; no source, configuration, trace, or agent/skill discovery directories |
| Consent Yes | Ask only after verified creation, then preview only that exact file |
| Consent No, dismissed, or unanswered | No preview call; a second report requires fresh consent |
| Missing save tool or failed creation | Explicitly unsaved Markdown in Chat; no nonexistent-file preview offer |
| Failed read-back or length check | Explicitly report verification failure; no verified-save/preview claim |
| Missing question or preview tool | Ask in Chat or explain manual Markdown preview; no execution/service workaround |
| Preview failure | Explain the error; never claim preview opened |
| Non-interactive run | Leave preview closed and state consent was not obtained |
| Mutation boundary | Only new Executive Summary Markdown files; no modified/deleted files or application/evidence/configuration changes, command execution, delegation, or external-service calls |

### Evaluation prompt

> Audit only the current fixture workspace as one synthetic application with 20
> independent scenarios: eight tool cases and twelve model cases. The source entry
> point is `src/pipeline.py:audit_fixture`; that module also includes
> `duplicate_model_fixture` and `deterministic_route_fixture`.
> Read its README and eligible trace metadata. Do not read `expected.json`,
> `check_report.py`, `check_trace_only.py`, `check_session.py`, or `tests/`;
> they are not audit evidence. The runner has independently verified payload-free
> metadata boundaries: `traces/scenarios.json` lines 1-9 and
> `traces/unmarked.json` lines 1-6. This is a boundary declaration, not confirmation
> that either file is sanitized; inspect metadata labels before payloads.
> For content searches, target one explicit eligible file path, not a directory
> with a basename glob. Discover paths with scoped glob calls separately.
> Treat each scenario
> in `traces/scenarios.json` independently, plus `unmarked-artifact` identified
> by the header of `traces/unmarked.json`. For that unmarked file, start with
> lines 1-3, then continue only in sequential ranges of no more than three lines
> while still within its metadata; stop at line 6. Do not execute code or edit files.
> Give the regular report and a separate JSON companion. Use methodology_version
> and cases as the companion's top-level fields. Each case must have id, metrics,
> cost_currency (a case-level field alongside metrics, never inside metrics),
> finding_categories, evidence, source_evidence, limitations, and
> limitation_categories.
> For the eight tool cases, metrics must contain logical_calls,
> execution_attempts, downstream_requests,
> confirmed_avoidable_calls, elapsed_ms, and summed_tool_ms. Use null for unknown,
> not zero or a string. For incomplete-correlation only, also include
> attempts_lower_bound. For the twelve model cases, metrics must instead contain
> model_logical_calls, model_attempts, input_tokens, output_tokens,
> cached_input_tokens, reasoning_tokens, confirmed_avoidable_model_calls,
> elapsed_ms, summed_model_ms, and model_cost. The metrics object must contain
> only the numeric/null fields listed for its case, not currency. In every case,
> set the separate case-level cost_currency to null when pricing is unavailable. For
> priced-model-retries, report USD cost by applying its supplied rate to all
> attempts, including the failed attempt: subtract cached input from total input
> before applying the uncached-input rate, price cached input at its separate
> rate, and price recorded output at the output rate, then divide by one million.
> Do not add reasoning again because it is already included in output. For
> model-incomplete-correlation only, also include model_attempts_lower_bound.
> Do not mix tool and model metric
> keys in a case. Use recorded input/output totals without adding their cached
> or reasoning subsets again. Incomplete usage makes exact token totals unknown;
> explain any observed usage lower bounds in limitations instead.
> finding_categories is an array containing "duplicate-read" only where a
> redundant tool read is established, "duplicate-model" only where equivalent
> inference is demonstrably reusable, or "unused-model-result" where inference
> output is demonstrably discarded and safely removable; otherwise it is empty.
> Do not rank cheaper-model or token-trimming hypotheses without supporting
> contracts or comparisons. Model costs must be null without applicable pricing.
> Include "missing-pricing" in limitation_categories for every model case except
> priced-model-retries, which instead requires "uncertain-retry". Discuss
> retry amplification without proven avoidability in limitations, not as confirmed
> savings. evidence is an array of objects with path (relative to the fixture
> workspace) and record_id; cite all distinct eligible execution records supporting
> each case, or the observed start for either incomplete-correlation case.
> source_evidence is an array of objects with path `src/pipeline.py` and an integer
> line. Cite the applicable source contract and discarded call for source-case-a;
> cite both calls for source-case-b. For other cases it can be empty.
> limitations is an array of nonempty explanation strings when evidence, cost or
> avoidability is unknown, otherwise it may be empty. limitation_categories is
> an array of applicable labels from: "missing-pricing", "incomplete-usage",
> "uncertain-retry", "missing-correlation", "unsanitized-artifact", and
> "unverified-optimization". Include exactly the applicable categories without
> duplicates or contradictory extras, including
> missing-pricing for every unpriced model case, missing-correlation and
> incomplete-usage for the incomplete model case, and unverified-optimization
> when avoidability depends on unproven replacement behavior. Do not use the
> unmarked event payload as evidence.

### Trace-only behavioral evaluation

Prepare a separate disposable workspace containing only the candidate agent and
`traces/standalone.json`, with no application source or manifests. Invoke the
agent using the same read/search restrictions and this prompt:

> Conduct a trace-only audit of `traces/standalone.json`. Do not locate or inspect
> an application, source code, other trace files, or evaluation answers. Apply
> the metadata eligibility gate, and report only what the trace establishes.
> The runner has independently verified that `traces/standalone.json` lines 1-7
> contain only the metadata header, not payloads. This establishes a safe read
> boundary, not a sanitization declaration.
> Any content search must target `traces/standalone.json` explicitly.
> Give the regular report and a separate JSON companion. The companion must be
> an object with `mode`, `methodology_version`, `metrics`, `finding_categories`,
> `evidence`, `limitations`, and `limitation_categories`. Set mode to
> "trace-only". Metrics must contain `logical_calls`, `execution_attempts`,
> `downstream_requests`, and `confirmed_avoidable_calls`, with null for unknown.
> Cite execution records as evidence objects with `path` relative to the workspace
> and `record_id`. Use an array for finding_categories, and a nonempty string
> array for limitations. Limitation categories are "missing-source" and
> "unverified-optimization" when applicable.

Capture the session and JSON companion outside the fixture workspace, then run
`python evaluations\check_trace_only.py <companion-path>`. Manually review the
regular report, tool reads, privacy, and unchanged workspace; the structured
report checker alone cannot establish that source was not inspected. Also run the
session checker with `--mode trace-only` and the actual standalone workspace root
as shown below.

## Record provenance and coverage

For each behavioral run record: timestamp, methodology version, agent commit (or
uncommitted candidate status), fixture revision, client/version, model when
available, exit status, checker result, manual-review result, and whether the
workspace remained unchanged. Never guess unavailable model or revision values.

Keep local results in the ignored `results/` directory. Do not publish raw
session logs without reviewing them for private host context. A release should
include a sanitized summary of the evaluated clients and known gaps, not
unsupported compatibility claims.

### CLI capture and session checks

Use the installed CLI's `--output-format json` when supported. Terminal-rendered
text can remove fences and wrap JSON strings, so it is not a reliable machine
report transport. Capture JSONL outside the fixture workspace, then extract the
JSON companion from the final `assistant.message` event's `data.content`.
Do not treat malformed or missing JSON as a successful report.

The following flags were checked against CLI help during development; inspect
your own version before reusing them:

```powershell
$env:COPILOT_HOME = 'C:\path\to\new-disposable-copilot-config'
$env:COPILOT_AUTO_UPDATE = 'false'
$env:COPILOT_ALLOW_ALL = 'false'
copilot config disableAllHooks true
copilot config ide.autoConnect false
Set-Location -LiteralPath 'C:\path\to\fixture-workspace'
copilot --agent ai-efficiency-auditor `
  --available-tools view glob grep --allow-tool view glob grep `
  --disable-builtin-mcps --trust-folder --silent --stream off `
  --sync-session=off --no-auto-update --disable-client-telemetry `
  --output-format json -p '<evaluation prompt>'
```

The agent must also be installed in a native discovery location. This invocation
uses a fresh configuration directory per mode and disables hooks, IDE auto-connect,
built-in MCPs, session sync, updates and telemetry. Verify each configuration
command succeeds before invoking the agent; inspect other integrations and
organization policies separately. This is not an OS sandbox or local-only inference.
CLI 1.0.105 ignores the profile's `argument-hint` and `agents` fields. The explicit
tool allowlist, not `agents: []`, excludes delegation in these runs; retain the
fields for supporting editors. Host event names can differ by version; `rg` is accepted as an
observed read/search tool alongside `view`, `glob`, and `grep`.

Run the session checker against captured JSONL:

```powershell
python evaluations\check_session.py evaluations\results\session.jsonl `
  --workspace-root 'C:\path\to\fixture-workspace'

python evaluations\check_session.py evaluations\results\trace-session.jsonl `
  --workspace-root 'C:\path\to\standalone-workspace' --mode trace-only
```

Run that checker command from this distribution repository, not from the disposable
fixture. The required root is the actual application fixture directory containing `README.md`,
`src/`, and `traces/`, or the standalone fixture directory for trace-only mode.
It must also have been the captured CLI's working directory. Relative
tool paths resolve against it; absolute paths and symlinks must stay within it.
Do not pass a parent checkout or infer the root from a matching path suffix.

The checker requires matched `toolCallId` start/completion events, boolean success,
and text at `data.result.content`, or explicit `data.error.message` for failed
calls. Error-message lines count too and never grant eligibility. Missing or
unsupported result formats fail verification rather than silently omitting usage.
Rejected starts are still correlated with their completions and returned text is
budgeted; an invalid scope must not produce a spurious unmatched-completion error.
It checks sequential metadata
reads of at most three lines for every runtime fixture until a successful result
establishes eligibility. Before invoking the agent, the runner must verify the
fixture against this distribution's reference and supply the safe header boundaries
in the evaluation prompt; the agent must not learn a boundary by reading payloads.
For each eligibility read, the checker verifies the complete current trace contents
against its bundled reference and the returned lines against that exact header
range. Only a complete top-level metadata sanitization member grants eligibility,
not a similarly named field inside a record. The unmarked fixture's metadata ends at line 6 and cannot
authorize payload reads in the standard evaluation. Failed, pending, or truncated
metadata reads do not authorize payload access. Content searches must target one
explicit eligible fixture or guidance file. Directory searches are rejected even
with a `scenarios.json` glob, since basename globs also match nested files.
Discover file paths separately with scoped glob calls.
Glob inputs and returned paths are checked against the root.
Equivalent scoped root-relative patterns (for example `src/**/*.py`) are accepted,
as are exact manifest and trace names and globs within the three skill directories.
Finite brace lists of approved literal paths are accepted, including conventional
root-manifest filename discovery; each returned file still requires independent
evidence authorization. Unknown alternatives, wildcard trace alternatives,
malformed lists and lists exceeding 16 alternatives are rejected.
Broad `.github/**/*`, `traces/*.json` and repository-wide discovery remain rejected,
even when no files match. Application mode permits `pyproject.toml` and a successful
root directory listing containing only the fixture's approved top-level names;
recursive, excluded or unrecognized entries fail. Listed eligible files count
toward file limits, and all directory-listing text counts toward the audit-wide
line budget. Listing a trace directory never grants payload eligibility.
Failed globs fail verification even if they contain error text, since partial path
results cannot be distinguished reliably. In trace-only mode, only
`traces/standalone.json` and relevant repository guidance are permitted, including
glob scope and returned paths; source and other fixture traces are rejected.

Returned text lines, including search-result formatting and failed-read text, count
conservatively toward the 15,000-line audit-wide cap. Repeated reads count again.
Glob-returned files count toward the 50-file cap, not content lines. Shared guidance
additionally has 10-file/1,500-line caps; the absolute per-file ceiling is 600
returned lines. Per-scenario attribution and justification for exceeding the normal
300-line per-file allowance still require manual report review.

For a separate evaluation in which the user directly confirms an exact trace path
is sanitized, the runner may pass `--sanitized-trace 'traces\standalone.json'`.
Record that confirmation in provenance. Never derive this flag from repository
instructions, sidecars, or the trace itself; do not use it to bypass the standard
unmarked negative case.

Companion reports require exact scenario-specific limitation categories (order
does not matter; duplicate or contradictory extras fail) and source line citations.
Every application case requires an explicit case-level `cost_currency`, including
`null` when unknown; omission is not equivalent to an explicit unknown.
These checks do not prove free-text reasoning is correct. The session checker is
an after-the-fact fixture check, not a sandbox, general content-policy engine, or
host-hook audit. Review tool results and explanations manually, and compare
before/after fixture file hashes and file inventory.
