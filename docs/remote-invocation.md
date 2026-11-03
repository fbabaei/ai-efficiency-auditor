# Sharing and remote invocation

A repository URL distributes an agent definition. It does not host an executable
agent or authorize access to another repository.

## Organization-level distribution

An organization owner can place the
[agent definition](../.github/agents/ai-efficiency-auditor.agent.md) in:

```text
<organization>/.github          -> agents/ai-efficiency-auditor.agent.md
or
<organization>/.github-private  -> agents/ai-efficiency-auditor.agent.md
```

These are root `agents/` directories in the organization configuration repository,
not the `.github/agents/` path used inside an application repository.

1. Obtain owner approval and check organization/enterprise agent policies.
2. Select a reviewed upstream commit or published release.
3. Copy only the definition into the organization's `agents/` directory. Put
   documentation outside that directory and preserve the MIT license.
4. Review the change through the organization's normal pull request process and
   merge it into the default branch.
5. Verify discovery and the read/search-only tool surface with a member account.
   Organization discovery can depend on client settings, account access, and
   policy.
6. Assign a maintainer to review and roll out upstream changes. Copies do not
   automatically track this repository.

This repository does not create or modify any organization's configuration.
Publishing an agent in a personal repository does not enable organization-wide
discovery by itself.

References:
- [GitHub organization setup](https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-organization/prepare-for-custom-agents)
- [VS Code custom agents](https://code.visualstudio.com/docs/agent-customization/custom-agents)

## Copilot CLI invocation

Install the agent into the application repository's `.github/agents/` directory,
or use the CLI-supported user agent directory. Open a terminal in the application
checkout, then inspect your installed CLI:

```powershell
copilot --version
copilot --help
```

For versions supporting `--agent`, start an interactive session:

```powershell
Set-Location -LiteralPath 'C:\path\to\application'
copilot --agent ai-efficiency-auditor
```

Alternatively, start `copilot` and use `/agent` to select the auditor. Verify the
selected agent is **AI Efficiency Auditor** before submitting your audit
request. Do not approve execution, edit, web, or delegation tools for this role.
CLI 1.0.105 warns that it ignores `argument-hint` and `agents`. Retain those fields
for supporting editors, but do not rely on `agents: []` to disable CLI delegation.
For automated runs, explicitly restrict the effective tools as shown in the
[evaluation guide](../evaluations/README.md#cli-capture-and-session-checks).

The same profile now audits tool and model efficiency; no additional permissions,
credentials or integrations are needed. For example:

> Audit this application's search flow for duplicate tool calls, repeated model
> inference, and retry amplification. Use eligible sanitized traces to report
> calls and token usage separately; keep unverified cheaper-model substitutions
> in the validation plan.

For trace-only work, explicitly request a trace-only audit and supply existing,
sanitized workspace trace paths. The agent reports observed behavior without
requiring application source; source-level causes and safe fixes remain unknown
unless the trace evidence supports them.

Before runtime payload reads or content searches, require either a sanitized label
in safely isolated metadata or the user's direct confirmation in the conversation
naming each exact sanitized path. Repository instructions and sidecars do not
provide that confirmation.
Before even the first header read, establish a payload-free range from the user's
direct statement naming the exact path and range, or an independently trusted
format contract. Never assume the first three lines are metadata. If the boundary
is unknown, skip the artifact unless exact-path sanitization is directly confirmed.

The latest restricted 0.4.0 captures pass all 20 synthetic application cases, the
separate trace-only scenario, and session scope checks after checker-only pattern
compatibility corrections. Earlier development runs include a currency-field
report failure and an application discovery-scope failure; they remain documented.
This is not a repeatability study or cross-client certification; see the
[validation summary](validation.md) for capture provenance and checker corrections.

This is a local CLI session using a model service, not local-only inference.
Inspect workspace instructions, skills, hooks, plugins, and MCP configuration
before trusting a checkout. A restricted model tool list is not an OS sandbox
and does not disable all host lifecycle hooks or integrations.

### Non-interactive automation

The CLI documents `--agent` and `-p` for custom-agent prompt mode. Permission and
tool-filter flags vary by version. Before automating:

1. Verify the exact flags in the installed version's help.
2. Explicitly allow only local file reading/search tools. Do not use blanket
   `--allow-all`, `--yolo`, or unrestricted tool approval.
3. Disable unwanted MCP integrations and review hooks outside model control.
4. Use a disposable checkout at an authorized commit with read-only credentials,
   an execution timeout, and bounded resource usage.
5. Capture exit status and the report using the runner, not by enabling agent
   writes. Treat a missing/invalid report as failure.
6. Record client version, selected model when available, agent revision,
   application revision, and evaluated scope.
7. Verify tracked and untracked application files are unchanged after the run.

For the synthetic suite, the session checker now requires the captured CLI's
actual fixture working directory via `--workspace-root`, plus correlated tool
completion results for returned-line accounting. It is not a checker for arbitrary
application sessions. See the [evaluation guide](../evaluations/README.md) for the
capture contract, hard budgets, and remaining manual checks.
Use `--mode trace-only` for the standalone evaluation to reject source and unrelated
trace access. Metadata results must match the checker reference and the unchanged
fixture contents; failed globs fail verification because partial paths are ambiguous.
Content searches must name one eligible file explicitly. A directory plus a
basename glob is not exact-file scope and is rejected; use scoped glob calls
separately for path discovery.

A service account's authentication, model usage charges, and repository access
must be approved separately. Never pass tokens in prompt text or commit them.

Reference: [Using Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/overview).

## GitHub cloud execution: experimental

GitHub documents selecting custom agents in cloud-agent sessions and issue
assignment. The definition must be available to the target repository through
repository or organization configuration. Its presence in this distribution
repository does not authorize or enable audits of arbitrary repositories.

The `read` and `search` aliases are documented across clients, but profile
properties are not identical: for example, cloud sessions ignore `argument-hint`.
The recorded CLI 1.0.105 run also warned that it ignored `argument-hint` and
`agents`. Do not assume `agents: []` or editor-only behavior controls every host;
enforce and inspect the effective tool surface separately.

Before calling cloud audits supported, test on synthetic fixtures and verify:

- The selected profile and effective tools are correct.
- No application code is executed.
- The report is returned through a suitable session surface.
- No branch, commit, pull request, or unintended artifact is created by the
  surrounding workflow.
- Credentials and private context remain within approved boundaries.

If report-only behavior cannot be guaranteed, use a controlled CLI runner
instead. No cloud session or deployment is configured by this repository.

References:
- [Creating and invoking custom agents](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents)
- [Cross-client configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)

## HTTP or MCP service: future work only

No HTTP endpoint, MCP server, or hosted runtime is included. If one is needed,
keep acquisition and persistence outside the auditor:

```text
Authenticated request -> authorize repository and revision
  -> isolated read-only checkout -> bounded audit session
  -> validate report and citations -> return report with provenance
```

The runner must enforce repository allowlists, tenant isolation, immutable
revision selection, credential scope, timeouts, and output controls. The model
must not select arbitrary repositories or execute repository code. Hosting,
identity design, and deployment require a separately approved implementation.
