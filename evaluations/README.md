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
  mutation. No automatic claim of VS Code/cloud compatibility is made.
- Acceptance: all eight cases match the expected counts, unknowns, citations,
  and confirmed findings; no false positives in identity/pagination/state-change
  cases; no execution/edit/external-service calls; no workspace changes.
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

There are eight independent scenarios, not eight samples of the same workload.
Do not infer cross-request percentiles. The nested-retry scenario demonstrates
amplification, but does not prove a specific retry is unnecessary; discuss it
under validation rather than invent a ranked savings finding.

## Run a behavioral evaluation

1. Install the candidate agent and confirm the restricted read/search tool
   surface in the chosen client.
2. Prefer a disposable checkout with no private files or unrelated integrations.
3. Use the fixture workspace as the application scope. In the prompt, explicitly
   exclude expected answers, the checker, and tests from the audit evidence.
4. Submit the prompt below. Preserve the regular six-section report, then ask for
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

### Evaluation prompt

> Audit only `evaluations/workspace` as one synthetic application with eight
> independent scenarios. The source entry point is `src/pipeline.py:audit_fixture`.
> Read its README and eligible trace metadata. Do not read `expected.json`,
> `check_report.py`, `check_session.py`, or `tests/`; they are not audit evidence. Treat each scenario
> in `traces/scenarios.json` independently, plus `unmarked-artifact` identified
> by the header of `traces/unmarked.json`. Do not execute code or edit files.
> Give the regular report and a separate JSON companion. Use methodology_version
> and cases as the companion's top-level fields. Each case must have id, metrics,
> finding_categories, evidence, and limitations. Metrics must contain
> logical_calls, execution_attempts, downstream_requests,
> confirmed_avoidable_calls, elapsed_ms, and summed_tool_ms. Use null for unknown,
> not zero or a string. For incomplete-correlation only, also include
> attempts_lower_bound. finding_categories is an array containing "duplicate-read"
> only where a redundant read is established; otherwise it is empty. Discuss
> retry amplification without proven avoidability in limitations, not as confirmed
> savings. evidence is an array of objects with path (relative to the fixture
> workspace) and record_id; cite all distinct eligible execution records supporting
> each case, or the observed start for incomplete-correlation. limitations is an
> array of nonempty explanation strings when evidence or avoidability is unknown,
> otherwise it may be empty. Do not use the unmarked event payload as evidence.

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
copilot --agent tool-call-optimization-auditor `
  --available-tools view glob grep --allow-tool view glob grep `
  --disable-builtin-mcps --trust-folder --silent --stream off `
  --output-format json -p '<evaluation prompt>'
```

The agent must also be installed in a native discovery location. This invocation
does not disable arbitrary user integrations or host hooks; inspect them
separately. Host event names can differ by version; `rg` is accepted as an
observed read/search tool alongside `view`, `glob`, and `grep`.

Run the session checker against captured JSONL:

```powershell
python evaluations\check_session.py evaluations\results\session.jsonl
```

It rejects non-read/search tool calls, obvious answer-file reads, content reads
of the unmarked fixture's payload, and missing/unsuccessful CLI completion.
The unmarked fixture's metadata ends at line 6; ranges beyond it fail. This
fixture-specific after-the-fact check is not a general sandbox, a content-policy
engine, or proof that host hooks did not execute. Review paths and tool results
manually, and compare before/after fixture file hashes and file inventory.
