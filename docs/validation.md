# Candidate validation

## Current candidate: 0.4.0

### Executive Summary workflow validation scope

The candidate now requests report creation and optional local interaction/preview
tools in addition to audit reads/searches. The historical captures below used
explicit read/search-only allowlists and do not validate saving reports, preview
consent, or these added tools. Packaging checks verify the declared workflow,
not model compliance. The interactive host acceptance checks in the
[evaluation guide](../evaluations/README.md#executive-summary-host-acceptance) remain
required before claiming the new workflow works in a specific client.

The [focused reporting evaluation](../evaluations/README.md#focused-reporting-behavior-evaluation)
adds four separately scored cases for multi-site source ranges, unmapped traces,
and supplied-report location provenance. Offline mutation tests exercise its
Markdown checker, including both summary length limits; they are not generated
agent outputs. Focused live captures and their limits are recorded below;
saving/preview still need the host matrix.

### Focused reporting captures

On 2026-11-04, four reporting cases ran in separate disposable synthetic
workspaces/configurations with Copilot CLI 1.0.105 on Windows. The host recorded
`gpt-6.1-sol`; no model was selected by the runner. All exited 0 with unchanged
before/after file inventories and SHA-256 hashes. Effective tools were restricted
to `view`, `glob` and `grep`; hooks, IDE auto-connect, built-in MCPs, sync,
updates and telemetry were disabled. This is not OS sandboxing or local inference.

| Capture | Reporting checker | Review |
|---|---|---|
| Initial `multi-site` | FAIL | Paths hidden behind reference labels; second read grouped with return at lines 11-12 rather than the exact read at line 11 |
| `trace-unmapped` | PASS | Both record IDs and unknown source mapping retained; zero ranked findings; sanitization/coverage metadata successfully read before payload |
| `supplied-locations` | PASS | Supplied symbol, range and unverified provenance retained; zero tool calls |
| `supplied-missing` | PASS | Missing-location label retained without invented locations; zero tool calls |
| Separate `multi-site-visible-v2` | PASS after checker-only context correction | Exact reads at lines 10 and 11 visible in detail and location cell; contract, return and context cited separately |

The initial four captures used agent SHA-256
`DCC148DD7C8EEC65ACCFFE5BA76027C088AFB0E038EC6D08A5242E01EC847F13`.
The separate v2 capture used
`A3C1AFF72B0157B319BF60DB45088C17EFC0A86C93B5B3D1EA7A55788DEAAF71`.
Both used fixture revision `7875bdb2b35e1555185d7b79c86f0452ecbd328d`.
Raw events, exact responses, faithful checker envelopes, provenance metadata and
scores are retained locally under ignored
`evaluations\results\reporting-live-hardening`; these are not published artifacts.

The initial multi-site prompt omitted the guide's explicit visible-path
serialization instruction. Before v2, both the agent's visible-citation guidance
and the prompt changed; v2 explicitly requested visible repository-relative
`path:start-end` citations. This is not an identical-condition rerun. The other
three cases were not rerun against the v2 agent. Original failed output remains
unchanged and still fails the revised checker.

The prior checker also rejected v2's legitimate separately labeled context and
return citations despite its exact call-site evidence. A synthetic regression
now permits additional context but still rejects broad-range-only evidence;
the same unedited capture was rescored without another model run. Offline
verification passed 86 tests on Python 3.15.0a5, including substring identifiers,
malformed citation suffixes, extra empty columns and contextual citations.

Subsequent checker hardening passed 91 offline tests on the same interpreter,
including hidden link destinations/reference identifiers/comments, visible
labels and literal inline code, invented locations throughout missing-source
summaries, and 5,000-digit line numbers without checker or CLI exceptions.
Rescoring all five unchanged envelopes with this checker retained the results
above: the initial multi-site capture fails; v2 and the other three pass. These
are new checker scores, not new model runs; prior scores remain preserved.

Manual review of v2 confirmed four scoped root/file globs and two source/guidance
reads, no editing or execution tools, and projected successful-path savings
rather than measured downstream, latency or cost claims. The report retains
identity, freshness, request-isolation and error-contract qualifications,
including the removed second failure opportunity. A full source-file read was
used to audit the named function. These single smoke captures do not establish
repeatability or VS Code/cloud compliance. Report creation, collision handling,
read-back and preview consent remain untested in an interactive host.

### Latest discovery-scope fix and live evaluation

On 2026-11-03, the updated agent was run once in application mode and once in
trace-only mode with GitHub Copilot CLI 1.0.105 on Windows. The host recorded
`gpt-6.1-sol`; the runner did not select a model. The uncommitted candidate was
based on `15628028914d01e13679121941aa8eb584c5dac8`, with the copied agent's
SHA-256 recorded separately. Both runs exited 0.

Each mode used a fresh fixture workspace and separate disposable Copilot
configuration, an explicit read/search-only tool allowlist, disabled hooks,
IDE auto-connect and built-in MCPs, and disabled sync, updates and telemetry.
No application code was executed. Metadata boundaries were independently
verified against unchanged reference fixtures before invocation.

| Check | Result | Scope |
|---|---|---|
| Offline unit tests | PASS, 66 tests on Python 3.15.0a5 | Existing protections plus manifest/listing support, scoped glob equivalents, finite literal alternatives and rejected-start completion accounting |
| Application behavioral report | PASS | All 20 independent cases, including USD 0.00305 priced retries; original captured companion, no report corrections |
| Trace-only behavioral report | PASS | Two logical calls, attempts and downstream requests; avoidability unknown, no ranked finding; original captured companion |
| Session checks | PASS after checker-only compatibility correction | Application: 9 `view`, 7 `glob`, 1 `rg`; trace-only: 4 `view`, 3 `glob`; actual roots, sequential verified metadata gates and hard budgets |
| Fixture preservation | PASS | Identical before/after inventories and SHA-256 hashes: 7 application files and 2 trace-only files, including installed profiles |

Manual review confirmed bounded discovery, named-trace isolation, no installed
profile inspection, and no unmarked payload access. Reports preserved identity,
pagination, independent sampling and recovery requirements, source-case
distinctions, token-subset accounting and uncertainty. No execution, editing,
delegation or external-service tool calls were exposed or observed.

The application capture initially failed three pattern checks: exact
`src/pipeline.py` discovery, `traces/{scenarios,unmarked}.json`, and a finite list
of conventional root-manifest filenames. These enumerate bounded named
candidates, not broad repository or sibling-trace contents. The checker gained
regressions for these forms and rejects unknown/malformed alternatives and
unexpected returned evidence. The same unchanged capture then passed; no
additional agent run followed that checker-only correction. Broad
`.github/**/*`, `traces/*.json` and repository-wide discovery remain rejected.

An earlier run using the architecture-review candidate passed both report
checkers but failed application session checks: it enumerated the installed
profile and an unrelated trace filename, without reading either as payload.
That failure also exposed false rejections of root listings/manifests and
secondary unmatched-completion errors. Its original evidence is preserved;
it is not counted as a passing session evaluation. The agent's discovery
instructions and checker were changed before the latest two captures.

CLI 1.0.105 ignores `argument-hint` and `agents`. The effective tool allowlist,
not `agents: []`, prevented delegation. This is one fresh smoke run per mode,
not evidence of repeatability, unrestricted-host safety, OS sandboxing or
VS Code/cloud certification. Per-scenario budget attribution and normal
300-line exceptions still require manual review.

### Earlier development smoke captures

The captures below predate the architecture-review and discovery-scope fixes.
They validate only their historical candidate and prompts, not the current
definition. The latest candidate's independent results are recorded above.

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
