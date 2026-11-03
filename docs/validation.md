# Candidate validation

## Scope and provenance

- Methodology: 0.2.0, uncommitted candidate based on initial commit `9f12582`.
- Environment: Windows; GitHub Copilot CLI
  `1.0.102-0.unstable.r40029025960.g5a14a15`.
- Model: `gpt-6.1-sol`, recorded in host message events; not forced by the runner.
- Inputs: synthetic fixture workspace only; no enterprise source or real traces.
- Coverage: one successful smoke evaluation of the final candidate, not a
  multi-run reliability study or certification of other clients.

## Results

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

## Failures found and addressed

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

The tool list constrains model calls; it is not an OS sandbox or a complete
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
