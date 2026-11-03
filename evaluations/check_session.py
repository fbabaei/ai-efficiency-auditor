"""Verify tool scope, trace eligibility, and returned-content budgets in CLI events."""

import argparse
import json
import ntpath
from dataclasses import dataclass, field
from pathlib import Path


TRACE_HEADERS = {
    "traces/scenarios.json": 9,
    "traces/standalone.json": 7,
    "traces/unmarked.json": 6,
}
GUIDANCE_FILES = {"readme.md", "agents.md", ".github/copilot-instructions.md"}
SKILL_DIRECTORIES = (".github/skills/", ".agents/skills/", ".claude/skills/")
FIXTURE_ROOT = Path(__file__).resolve().parent / "workspace"


def _relative_path(root: Path, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("missing or invalid tool path")
    raw = value.replace("\\", "/")
    path = Path(raw)
    if ".." in path.parts or (ntpath.splitdrive(raw)[0] and not path.is_absolute()):
        raise ValueError("ambiguous parent traversal or drive-relative path")
    resolved = (path if path.is_absolute() else root / path).resolve()
    try:
        return resolved.relative_to(root).as_posix().lower()
    except ValueError as error:
        raise ValueError("tool path is outside the chosen workspace root") from error


def _is_guidance(path: str) -> bool:
    return path in GUIDANCE_FILES or (
        path.startswith(SKILL_DIRECTORIES) and path.endswith("/skill.md")
    )


def _is_evidence(path: str, mode: str) -> bool:
    if mode == "trace-only":
        return path == "traces/standalone.json" or _is_guidance(path)
    return path in TRACE_HEADERS or path in {"src/pipeline.py", "pyproject.toml"} or _is_guidance(path)


def _is_literal_discovery(pattern: str, base_path: str, mode: str) -> bool:
    candidates = [pattern]
    if "{" in pattern or "}" in pattern:
        if pattern.count("{") != 1 or pattern.count("}") != 1:
            return False
        prefix, _, rest = pattern.partition("{")
        choices, closing, suffix = rest.partition("}")
        alternatives = choices.split(",")
        if not closing or not 1 <= len(alternatives) <= 16 or not all(alternatives):
            return False
        candidates = [prefix + choice + suffix for choice in alternatives]
    allowed = GUIDANCE_FILES | {
        path for path in TRACE_HEADERS if _is_evidence(path, mode)
    }
    if mode == "application":
        allowed |= {
            "src/pipeline.py", "pyproject.toml", "requirements.txt",
            "setup.py", "setup.cfg", "pipfile", "package.json",
        }
    prefix = "" if base_path == "." else base_path + "/"
    return all(prefix + candidate in allowed for candidate in candidates)


def _verified_header(root: Path, path: str) -> list[str]:
    reference = (FIXTURE_ROOT / path).read_text(encoding="utf-8")
    if (root / path).read_text(encoding="utf-8") != reference:
        raise ValueError("trace fixture differs from the checker reference")
    lines = reference.splitlines()[:TRACE_HEADERS[path]]
    metadata = json.loads("\n".join(lines).rstrip().removesuffix(",") + "\n}")
    if set(metadata) != {"metadata"} or not isinstance(metadata["metadata"], dict):
        raise ValueError("fixture header must contain only a metadata object")
    return lines


@dataclass
class ExplorationBudget:
    files: set[str] = field(default_factory=set)
    guidance_files: set[str] = field(default_factory=set)
    lines: int = 0
    guidance_lines: int = 0
    per_file_lines: dict[str, int] = field(default_factory=dict)

    def record(self, paths: list[str], content_lines: int = 0) -> list[str]:
        self.files.update(paths)
        self.guidance_files.update(path for path in paths if _is_guidance(path))
        self.lines += content_lines
        if content_lines and len(paths) == 1:
            path = paths[0]
            self.per_file_lines[path] = self.per_file_lines.get(path, 0) + content_lines
            if _is_guidance(path):
                self.guidance_lines += content_lines
        errors = []
        if len(self.files) > 50 or self.lines > 15_000:
            errors.append("audit-wide exploration budget exceeded")
        if len(self.guidance_files) > 10 or self.guidance_lines > 1_500:
            errors.append("shared-guidance exploration budget exceeded")
        if any(lines > 600 for lines in self.per_file_lines.values()):
            errors.append("per-file hard limit of 600 returned lines exceeded")
        return errors


@dataclass
class PendingCall:
    tool: str
    paths: list[str]
    header_range: list[int] | None = None


def check_session(
    events: object, *, workspace_root: Path, sanitized_paths: tuple[str, ...] = (),
    mode: str = "application",
) -> list[str]:
    if not isinstance(events, list):
        return ["session must be an array of CLI events"]
    if mode not in {"application", "trace-only"}:
        return ["mode must be application or trace-only"]
    try:
        root = workspace_root.resolve(strict=True)
        if not root.is_dir():
            return ["workspace root must be a directory"]
        eligible = {_relative_path(root, path) for path in sanitized_paths}
    except (OSError, RuntimeError, ValueError) as error:
        return [f"invalid workspace root or sanitization declaration: {error}"]
    if not eligible.issubset(TRACE_HEADERS) or any(
        not _is_evidence(path, mode) for path in eligible
    ):
        return ["sanitization declarations must name exact fixture trace paths"]
    errors = []
    starts = 0
    results = []
    pending: dict[str, PendingCall] = {}
    seen_ids: set[str] = set()
    next_header_line: dict[str, int] = {}
    budget = ExplorationBudget()
    for event in events:
        if not isinstance(event, dict):
            errors.append("invalid event object")
            continue
        event_type = event.get("type")
        if not isinstance(event_type, str):
            errors.append("event type must be a string")
            continue
        if event_type == "result":
            results.append(event)
            if pending:
                errors.append("CLI result arrived before pending tools completed")
            continue
        if event_type not in {"tool.execution_start", "tool.execution_complete"}:
            continue
        if results:
            errors.append("tool event occurred after CLI completion")
        data = event.get("data")
        if not isinstance(data, dict):
            errors.append("tool execution data must be an object")
            continue
        call_id = data.get("toolCallId")
        if not isinstance(call_id, str) or not call_id:
            errors.append("tool event needs a nonempty toolCallId")
            continue
        if event_type == "tool.execution_complete":
            call = pending.pop(call_id, None)
            if call is None:
                errors.append("duplicate or unmatched tool completion")
                continue
            result = data.get("result")
            content = result.get("content") if isinstance(result, dict) else None
            failure = data.get("error")
            if (
                data.get("success") is False
                and content is None
                and isinstance(failure, dict)
            ):
                content = failure.get("message")
            if type(data.get("success")) is not bool or not isinstance(content, str):
                errors.append("tool completion needs success and returned text content")
                continue
            if call.tool == "view" and call.paths == ["."] and mode == "application":
                allowed_entries = {
                    ".github", ".agents", ".claude", "agents.md", "readme.md",
                    "pyproject.toml", "src", "traces",
                }
                returned_paths = []
                if not data["success"]:
                    errors.append("directory listing is not a successful top-level discovery result")
                for line in content.splitlines():
                    if not line.strip():
                        continue
                    try:
                        path = _relative_path(root, line.strip())
                    except (OSError, RuntimeError, ValueError) as error:
                        errors.append(f"invalid directory listing result: {error}")
                        continue
                    if path not in allowed_entries:
                        errors.append("directory listing includes recursive or excluded evidence")
                    elif _is_evidence(path, mode):
                        returned_paths.append(path)
                errors.extend(budget.record(returned_paths))
                errors.extend(budget.record([], len(content.splitlines())))
            elif call.tool == "glob":
                if not data["success"]:
                    errors.extend(budget.record([], len(content.splitlines())))
                    errors.append("failed glob may contain partial paths; file scope and budget cannot be verified")
                    continue
                returned_paths = []
                for line in content.splitlines():
                    if not line.strip() or line.strip() in {
                        "No matches found.", "No files found.", "No files matched the pattern.",
                    }:
                        continue
                    try:
                        path = _relative_path(root, line.strip())
                    except (OSError, RuntimeError, ValueError) as error:
                        errors.append(f"invalid glob result: {error}")
                        continue
                    if not _is_evidence(path, mode):
                        errors.append("glob returned excluded or ineligible evidence")
                    returned_paths.append(path)
                errors.extend(budget.record(returned_paths))
            else:
                errors.extend(budget.record(call.paths, len(content.splitlines())))
            if call.header_range is not None and data["success"]:
                path = call.paths[0]
                try:
                    lines = _verified_header(root, path)
                except (OSError, UnicodeError, ValueError) as error:
                    errors.append(f"cannot verify fixture metadata: {error}")
                    continue
                start, end = call.header_range
                if content.splitlines() != lines[start - 1:end]:
                    errors.append("metadata result does not match the verified fixture line range")
                    continue
                next_header_line[path] = call.header_range[1] + 1
                prefix = "\n".join(lines[:end])
                # Only a complete metadata member in the verified prefix grants eligibility.
                try:
                    observed = json.loads(prefix.rstrip().removesuffix(",") + "\n}}")
                except json.JSONDecodeError:
                    observed = {}
                if observed.get("metadata", {}).get("sanitized") is True:
                    eligible.add(path)
            continue
        starts += 1
        if call_id in seen_ids:
            errors.append("duplicate toolCallId")
            continue
        seen_ids.add(call_id)
        tool = data.get("toolName")
        arguments = data.get("arguments")
        # Correlate rejected starts too, without granting them evidence eligibility.
        pending[call_id] = PendingCall(tool if isinstance(tool, str) else "", [])
        if not isinstance(tool, str) or tool not in {"view", "glob", "grep", "rg"}:
            errors.append(f"unexpected tool: {tool}")
            continue
        if not isinstance(arguments, dict):
            errors.append("tool arguments must be an object")
            continue
        path_input = arguments.get("path" if tool == "view" else "paths")
        if tool == "glob" and "paths" not in arguments:
            path_input = "."
        inputs = path_input if isinstance(path_input, list) else [path_input]
        if not inputs or (tool == "view" and len(inputs) != 1):
            errors.append("tool needs explicit, unambiguous paths")
            continue
        try:
            paths = [_relative_path(root, path) for path in inputs]
        except (OSError, RuntimeError, ValueError) as error:
            errors.append(str(error))
            continue
        if tool == "glob":
            allowed_patterns = {
                ".": {
                    "agents.md", "readme.md", "{agents.md,readme.md}",
                    "{agents.md,readme.md,.github/copilot-instructions.md}",
                    ".github/copilot-instructions.md", "pyproject.toml",
                    "src/*.py", "src/**/*.py", "traces/scenarios.json",
                    "traces/unmarked.json", "traces/standalone.json",
                    "{.github,.agents,.claude}/skills/**/skill.md",
                },
                "traces": {"scenarios.json", "unmarked.json", "standalone.json"},
                "src": {"*.py", "**/*.py"},
            }
            if mode == "trace-only":
                allowed_patterns.pop("src")
                allowed_patterns["."] -= {
                    "pyproject.toml", "src/*.py", "src/**/*.py",
                    "traces/scenarios.json", "traces/unmarked.json",
                }
                allowed_patterns["traces"] = {"standalone.json"}
            for directory in SKILL_DIRECTORIES:
                allowed_patterns[directory.rstrip("/")] = {"**/skill.md", "skill.md"}
                allowed_patterns["."].update({f"{directory}**/skill.md", f"{directory}skill.md"})
            pattern = arguments.get("pattern")
            if not isinstance(pattern, str) or any(
                pattern.replace("\\", "/").lower() not in allowed_patterns.get(path, set())
                and not _is_literal_discovery(pattern.replace("\\", "/").lower(), path, mode)
                for path in paths
            ):
                errors.append("glob scope or pattern can include excluded evidence")
            pending[call_id] = PendingCall(tool, paths)
            continue
        if tool == "view" and paths == ["."] and mode == "application":
            pending[call_id] = PendingCall(tool, paths)
            continue
        if tool in {"rg", "grep"}:
            if len(paths) != 1:
                errors.append("search must target one fixture file for budget attribution")
        if len(paths) != 1 or not _is_evidence(paths[0], mode):
            errors.append("read/search path is outside approved fixture or guidance evidence")
            pending[call_id] = PendingCall(tool, paths)
            continue
        path = paths[0]
        errors.extend(budget.record(paths))
        header_range = None
        if path in TRACE_HEADERS and path not in eligible:
            view_range = arguments.get("view_range")
            if (
                tool != "view"
                or not isinstance(view_range, list)
                or len(view_range) != 2
                or any(type(value) is not int for value in view_range)
                or view_range[0] != next_header_line.get(path, 1)
                or not 0 <= view_range[1] - view_range[0] <= 2
                or view_range[1] > TRACE_HEADERS[path]
                or any(call.paths == paths for call in pending.values())
            ):
                errors.append("trace requires completed sequential metadata reads before payload access")
            else:
                header_range = view_range
        pending[call_id] = PendingCall(tool, paths, header_range)
    if pending:
        errors.append("missing tool completions; returned-content budget cannot be verified")
    if not starts:
        errors.append("no tool execution evidence; cannot verify behavior")
    if (
        len(results) != 1
        or type(results[0].get("exitCode")) is not int
        or results[0]["exitCode"] != 0
    ):
        errors.append("session needs exactly one successful CLI result")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path, help="raw --output-format json event file")
    parser.add_argument(
        "--mode", choices=("application", "trace-only"), default="application",
        help="evaluation scope; trace-only permits only standalone.json and repository guidance",
    )
    parser.add_argument(
        "--workspace-root", type=Path, required=True,
        help="actual fixture directory and CLI working directory for this capture",
    )
    parser.add_argument(
        "--sanitized-trace", action="append", default=[],
        help="exact trace path directly confirmed sanitized by the user; never infer from files",
    )
    args = parser.parse_args()
    try:
        events = [
            json.loads(line)
            for line in args.session.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        ]
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        parser.exit(2, f"Cannot read session: {error}\n")
    errors = check_session(
        events, workspace_root=args.workspace_root,
        sanitized_paths=tuple(args.sanitized_trace),
        mode=args.mode,
    )
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors))
        return 1
    print("PASS: tool scope, trace eligibility and returned-content hard budgets match.")
    print("Per-scenario attribution and 300-line exceptions still require manual review.")
    print("This is an after-the-fact fixture check, not a sandbox or host-hook audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
