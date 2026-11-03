# Tool-Call Optimization Auditor

A read-only custom agent for GitHub Copilot in VS Code. Audit AI application
source code and existing sanitized traces to identify avoidable tool calls,
retry amplification, and loops without weakening correctness or security.

The agent recommends changes and validation experiments. It does not edit code,
run commands, call external services, or replay workloads.

## Files

- [Agent definition](.github/agents/tool-call-optimization-auditor.agent.md)
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
5. Select **Tool-Call Optimization Auditor** in the Copilot Chat agent picker.
   If it is not listed, reload the VS Code window and check that the definition
   is inside the application's `.github/agents/` directory.
6. Submit a scoped audit request.

Commit the copied files to your application repository to share the agent with
that repository's contributors. Opening this distribution repository alone
does not give the agent access to a separate application's workspace.

### Example request

> Audit this workspace's search request flow for unnecessary tool calls. Use
> existing sanitized traces if available. Focus on duplicate retrieval and retry
> amplification, distinguish observed counts from static bounds, and rank safe
> optimizations.

Name application paths and scenarios explicitly for a narrower audit. If traces
are available, provide their workspace paths. Their headers or metadata must
state that they are sanitized before the agent can use them for counts.

## What to expect

The report includes evidence coverage, a call map, supported runtime metrics,
ranked findings, a proposed design, and a validation plan.

- Repeated calls are not automatically redundant.
- Static call sites, logical calls, execution attempts, downstream requests,
  model invocations, and agent handoffs are distinguished.
- Only measured or statically demonstrated findings are ranked.
- Projected savings are not presented as validated results.
- Every ranked finding and call-map row requires a source reference.

See the [detailed documentation](docs/agent-guide.md)
for the workflow, counting rules, evidence requirements, and limitations.

## Permissions and dependencies

The definition exposes only `read` and `search` and allows no subagents. Keep
these restrictions when installing or updating it.

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

Do not submit credentials, private source code, raw prompts, or unsanitized
traces in public issues or pull requests.

## Compatibility and validation

| Environment | Status |
|---|---|
| VS Code with Copilot custom-agent support | Primary intended interface; interactive behavior requires a host evaluation |
| Copilot CLI | One restricted synthetic smoke run passed on the recorded development version; see validation summary |
| Organization-level discovery | Documented setup; not provisioned or verified by this repository |
| GitHub Copilot cloud agent | Experimental for report-only audits; lifecycle and artifact behavior must be evaluated |
| HTTP or MCP audit endpoint | Not implemented |

Offline tests check packaging, fixture integrity, and report scoring. They do
not prove model behavior or client compatibility. See the evaluation guide for
behavioral acceptance criteria and recording client/model provenance.
The [validation summary](docs/validation.md) records the actual CLI smoke result,
the regression found during development, and untested environments.

Candidate methodology version: **0.2.0**. No release tag is implied. Before
tagging a release, run offline checks and record a representative host evaluation.
Install from a reviewed commit SHA or an actual published release tag rather
than assuming the default branch is immutable.

## License

[MIT](LICENSE). Include the license when redistributing the agent.
