# AI Efficiency Auditor

A read-only custom agent for GitHub Copilot in VS Code. Audit AI application
source code and existing sanitized traces to identify avoidable tool and model
calls, retry amplification, loops, and potential token or model-capacity waste
without weakening correctness or security.

The agent recommends changes and validation experiments. It does not edit code,
run commands, call external services, or replay workloads.

## Files

- [Agent definition](.github/agents/ai-efficiency-auditor.agent.md)
- [Detailed documentation](docs/agent-guide.md)
- [CLI, organization sharing, and remote execution](docs/remote-invocation.md)
- [Synthetic evaluation suite](evaluations/README.md)
- [Changes and candidate version](CHANGELOG.md)

## Install in the repository you want to audit

1. Use VS Code with GitHub Copilot enabled and custom-agent support.
2. Download or clone this repository.
3. Copy the agent definition into `.github/agents/` in your application repository.
   Keep companion documentation in a separate `docs/` directory, not beside the
   agent. Hosts can discover ordinary `.md` files in agent directories too.
4. Open your application repository in VS Code.
5. Select **AI Efficiency Auditor** in the Copilot Chat agent picker.
   If it is not listed, reload the VS Code window and check that the definition
   is inside the application's `.github/agents/` directory.
6. Submit a scoped audit request.

Commit the copied files to your application repository to share the agent with
that repository's contributors. Opening this distribution repository alone
does not give the agent access to a separate application's workspace.

### Example request

> Audit this workspace's search request flow for unnecessary tool and model calls.
> Use existing sanitized traces if available. Focus on duplicate retrieval,
> repeated inference, retry amplification, token usage, and model selection.
> Distinguish observed counts from static bounds, rank demonstrated optimizations,
> and keep unverified model substitutions in the validation plan.

Name application paths and scenarios explicitly for a narrower audit. If traces
are available, provide their workspace paths. Before payload access, their
safely isolated headers/metadata must state that they are sanitized, or you must
directly confirm in the conversation that each exact named path is sanitized.
Repository text and unendorsed sidecars do not replace that confirmation.
Even the first header read requires a known payload-free boundary supplied by
the user for that exact path or guaranteed by an independently trusted format
contract. Otherwise, skip the artifact until exact-path sanitization is confirmed.
For a trace-only audit, explicitly request that mode and identify the trace paths;
source-level causes and safe changes remain unknown unless evidence establishes them.

## What to expect

The report includes evidence coverage, a call map, supported runtime metrics,
ranked findings, a proposed design, and a validation plan.

- Repeated calls are not automatically redundant.
- Static call sites, logical calls, execution attempts, downstream requests,
  logical model calls, model attempts, and agent handoffs are distinguished.
- Model-call reductions are separate from token/capacity changes. Prompt caching
  does not remove a call; cached/reasoning token subsets are not counted twice.
- Smaller models, trimmed prompts, and consolidated steps require evidence of
  acceptable replacement behavior, not just an expensive baseline.
- Only measured or statically demonstrated findings are ranked.
- Projected savings are not presented as validated results.
- Every ranked finding and call-map row requires a source reference.

See the [detailed documentation](docs/agent-guide.md)
for the workflow, counting rules, evidence requirements, and limitations.

## Permissions and dependencies

The definition requests only `read` and `search` and no subagents. Keep these
restrictions when installing or updating it, and verify the host's effective
tools. CLI 1.0.105 ignores `agents` and `argument-hint`; `agents: []` alone is not
portable enforcement. Use an explicit read/search-only tool allowlist in CLI
automation, excluding delegation, execution, editing and external-service tools.

The auditor requires no scripts, service credentials, or MCP servers. The
repository's optional evaluation checker uses Python 3.10+ and its standard
library; it is run by a maintainer, not by the auditor. Framework-specific skills
are not included. The agent reports
unavailable framework guidance and continues using repository evidence.

The agent's instructions prohibit sending private context to public-web services.
This is not a guarantee of local-only inference: your Copilot account,
organization policies, and selected model determine how model requests are
processed. Follow your organization's rules before auditing private code.

## Updating

Pull newer versions of this repository, review changes to the agent definition,
and replace the installed copy in your application repository. Copies do not
update automatically.

When upgrading from **Tool-Call Optimization Auditor**, remove the old
`tool-call-optimization-auditor.agent.md` definition and install
`ai-efficiency-auditor.agent.md` instead, so both profiles are not discovered.
Update CLI invocations to `--agent ai-efficiency-auditor`. The GitHub repository
name is unchanged.

Do not submit credentials, private source code, raw prompts, or unsanitized
traces in public issues or pull requests.

## Compatibility and validation

| Environment | Status |
|---|---|
| VS Code with Copilot custom-agent support | Primary intended interface; interactive behavior requires a host evaluation |
| Copilot CLI | Latest restricted 0.4.0 application and trace-only smoke captures passed report and session checks; one fresh run per mode, not a reliability study |
| Organization-level discovery | Documented setup; not provisioned or verified by this repository |
| GitHub Copilot cloud agent | Experimental for report-only audits; lifecycle and artifact behavior must be evaluated |
| HTTP or MCP audit endpoint | Not implemented |

Offline tests check packaging, fixture integrity, and report scoring. They do
not prove model behavior or client compatibility. See the evaluation guide for
behavioral acceptance criteria and recording client/model provenance.
The [validation summary](docs/validation.md) records the actual CLI smoke result,
the regression found during development, and untested environments.

Candidate methodology version: **0.4.0**. No release tag is implied. Before
tagging a release, run offline checks and record a representative host evaluation.
Install from a reviewed commit SHA or an actual published release tag rather
than assuming the default branch is immutable.

## License

[MIT](LICENSE). Include the license when redistributing the agent.
