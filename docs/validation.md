# Candidate validation

## Current candidate: 0.4.0

The smoke captures below predate the latest architecture-review fixes: an
independently established boundary before the first metadata read, reference-bound
metadata validation, explicit trace-only session scope, failed-glob rejection,
mandatory currency-field presence, and exact-file search scope. They do not
validate the updated agent instructions or revised evaluation prompts; no new
host run is claimed.
The updated offline suite passes 59 tests, including adversarial metadata results,
changed fixtures, trace-only scope, failed globs, omitted currency fields, and
directory searches that return nested basename matches.

On 2026-11-03, the uncommitted 0.4.0 candidate was evaluated with GitHub Copilot
CLI 1.0.105 on Windows. The model was `gpt-6.1-sol`, recorded in host tool events,
not forced by the runner. Application and trace-only captures used separate
isolated Copilot configuration directories, synthetic fixture workspaces,
read/search-only model tools, disabled built-in MCPs, and no application code
execution. Session sync and automatic updates were disabled. Agent and fixture
inputs came from the working tree; no commit or release revision is claimed.

| Check | Result | Scope |
|---|---|---|
| Offline unit tests | PASS, 52 tests | Packaging, links, fixture counts, exact categories, root containment, eligibility sequencing, completion correlation and hard-budget boundaries |
| Application behavioral report | PASS on second attempt | All 20 cases, including USD 0.00305 priced retries with failed-attempt usage; captured companion scored without correction |
| Trace-only behavioral report | PASS | Two logical calls/attempts/downstream requests; avoidability unknown, no ranked finding; captured companion scored without correction |
| Session checks | PASS for accepted application and trace-only captures | Application: 9 `view`, 1 `glob`, 1 `rg`; trace-only: 3 `view`, 1 `glob`; explicit actual roots and completed header gates |
| Fixture preservation | PASS | Before/after SHA-256 hashes and inventories matched: 8 application-workspace files, 2 trace-only files, including installed profiles |

Manual report review confirmed scenario-specific counting, source anchors, pricing,
unknowns, and preservation of independent sampling, identity boundaries, required
recovery and pagination. The trace-only workspace contained no application source;
the captured agent inspected only its named trace and attempted guidance discovery.
No execution, editing, delegation or external-service tools were observed.

The first application attempt placed `cost_currency` inside `metrics`, revealing
ambiguous evaluation-prompt wording; that report failed and was not repaired into
a pass. After explicitly specifying a case-level currency field, the second
application attempt passed. These are not repeated trials of an identical prompt.
The host runs also exposed legitimate completion formats for failed reads
(`error.message`), empty glob results, default-root globs and scoped skill-directory
discovery. The checker was corrected and regression-tested against those formats,
then the same unmodified captures were rescored. No additional host run followed
those checker-only compatibility changes.

This is one accepted application smoke evaluation plus one trace-only smoke
evaluation, not a robustness study or cross-client certification. Per-scenario
budget attribution and justification for normal 300-line per-file exceptions
remain manual checks; audit-wide, shared-guidance and 600-line hard ceilings are
checked from captured results. VS Code and cloud behavior remain untested.

## Historical candidate: 0.3.0

On 2026-11-03, the uncommitted 0.3.0 candidate was evaluated with GitHub Copilot
CLI 1.0.105 on Windows. The model was `gpt-6.1-sol`, recorded in host message
events and not forced by the runner. Both runs used isolated synthetic workspaces,
an isolated Copilot configuration directory, restricted read/search tools,
disabled built-in MCPs and no source from a real application. The agent and
fixtures were copied from the uncommitted working tree; no commit or release
revision is claimed.

| Check | Result | Scope |
|---|---|---|
| Offline unit tests | PASS, 37 tests | Packaging, links, fixture counts, structured reports, session checks and trace-only checks |
| Application behavioral report | PASS | All 19 synthetic scenarios passed the companion checker; report reviewed for counting, evidence, uncertainty and proposed changes |
| Trace-only behavioral report | PASS | Two calls counted; avoidability unknown, no ranked finding; companion and report reviewed |
| Session checks | PASS for both | Application run used 10 `view`, 4 `glob` and 1 `rg`; trace-only run used 2 `view` and 1 `glob` |
| Fixture preservation | PASS for both | Before/after file inventories and SHA-256 hashes matched |

The CLI reported that it ignored the `argument-hint` and `agents` profile fields.
No delegation tool was exposed or observed in these runs; this is not proof that
the ignored `agents` field restricts delegation in other hosts. The trace-only
report used Windows path separators, which initially failed the strict checker;
the checker was corrected to accept either separator, regression-tested, and the
same captured report passed. No behavioral run was repeated after that
checker-only change.

These are two single-run synthetic smoke evaluations, not a robustness study.
Offline and structured checks cannot establish correctness of unrestricted
free-text reasoning, privacy handling, host hooks or other clients. The
historical results below refer only to the previous 0.2.0 candidate.

The 0.4.0 candidate adds checker, budget, sanitization and pricing-fixture changes
after these runs. Its separate evaluation is recorded above; the 0.3.0 results
alone must not be presented as validation of 0.4.0.

## Historical smoke evaluation: 0.2.0

### Scope and provenance

- Methodology: 0.2.0, uncommitted candidate based on initial commit `9f12582`.
- Environment: Windows; GitHub Copilot CLI
  `1.0.102-0.unstable.r40029025960.g5a14a15`.
- Model: `gpt-6.1-sol`, recorded in host message events; not forced by the runner.
- Inputs: synthetic fixture workspace only; no enterprise source or real traces.
- Coverage: one successful smoke evaluation of the final candidate, not a
  multi-run reliability study or certification of other clients.

### Results

| Check | Result | Evidence scope |
|---|---|---|
| Offline unit tests | PASS, 22 tests, exit 0 | Packaging, links, fixture counts, report and session checker regressions |
| Actual model report | PASS, all eight cases, exit 0 from report checker | Counts, unknowns, findings, and scenario-bound record citations |
| Session checks | PASS, exit 0 | Observed tools and unmarked-fixture read ranges |
| Fixture preservation | PASS | Before/after file inventory and SHA-256 hashes identical |
| Manual report review | PASS for this smoke run | Correct identity, pagination, state-change, retry, and latency reasoning; savings remain projected |

The final session made 19 observed tool calls: 15 `view`, 2 `glob`, and 2 `rg`.
No execution, editing, external-service, or delegation tool calls were observed.
Two read attempts reported missing optional repository instruction files; they
were disclosed as absent, not treated as source evidence.

The unmarked trace was inspected only through metadata lines 1-6. No event
payload from that artifact was used for counts or citations. The final result
identified one avoidable read only in the duplicate-read case. Nested retries
produced one logical call, four attempts, and eight downstream requests, with
safely avoidable retries left unknown.

### Failures found and addressed

An earlier candidate produced correct numerical results but read past an
unmarked artifact's metadata into its event payload. It was not accepted as a
successful behavioral evaluation. The instructions now require bounded
header-only eligibility reads, and a session-check regression rejects that
earlier tool log even though its report counts pass.

Terminal-rendered CLI output also removed code fences and wrapped JSON strings.
The evaluation now uses raw `--output-format json` events instead of attempting
to score terminal-rendered text. The session checker was tested to distinguish
an explicitly filtered search of the eligible trace from a broad content search
that could include the unmarked artifact.

## Limits and next release gate

The tool list constrains the model's tool access; it is not an OS sandbox or a complete
assessment of client hooks, plugins, or inference data handling. Fixture checks
are after-the-fact assertions, not a general policy-enforcement layer.

VS Code interaction, organization-level discovery, GitHub cloud lifecycle
behavior, and unattended hosted execution were not tested. No HTTP/MCP endpoint
was created, no organization settings were changed, and no cloud resources
were provisioned.

Repeat the synthetic evaluation across representative supported client/model
versions and record variance before publishing reliability claims or promoting
cloud execution out of experimental status. This candidate has no release tag.
Raw session logs remain local because host metadata can contain private context.
