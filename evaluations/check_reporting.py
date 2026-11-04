"""Check captured Markdown from the four synthetic code-location reporting cases."""

import argparse
import json
from pathlib import Path
import re


CASES = {"multi-site", "trace-unmapped", "supplied-locations", "supplied-missing"}
HEADER = [
    "Priority", "Weak area", "Code location", "Recommended improvement",
    "Expected benefit", "Evidence",
]
SOURCE_LOCATION = re.compile(
    r"(?<![\w./-])src/pipeline\.py:([0-9]+)(?:-([0-9]+))?(?![\w/:-]|\.[\w./-])"
)
SUPPLIED_LOCATION = re.compile(r"(?<![\w./-])src/worker\.py:42-44(?![\w/:-]|\.[\w./-])")
ANY_LOCATION = re.compile(r"\b[\w./-]+\.\w+:\d+")


def _priority_rows(summary: str) -> tuple[list[list[str]], list[str]]:
    tables = []
    errors = []
    current: list[list[str]] | None = None
    for line in summary.splitlines():
        if not line.strip().startswith("|"):
            current = None
            continue
        content = line.strip()[1:]
        if content.endswith("|"):
            content = content[:-1]
        cells = [cell.strip() for cell in content.split("|")]
        if cells == HEADER:
            current = []
            tables.append(current)
        elif current is not None:
            current.append(cells)
        else:
            errors.append("summary contains table content outside the priority table")
    if len(tables) != 1:
        return [], ["summary must contain exactly one six-column priority table"]
    table = tables[0]
    if not table or len(table[0]) != 6 or any(
        re.fullmatch(r":?-{3,}:?", cell) is None for cell in table[0]
    ):
        return [], ["priority table must have a six-column Markdown separator"]
    rows = table[1:]
    if len(rows) > 5:
        errors.append("summary must contain at most five priority rows")
    if any(len(row) != 6 or any(not cell for cell in row) for row in rows):
        errors.append("priority rows must have six nonempty cells")
        return [], errors
    return rows, errors


def _has_identifier(text: str, identifier: str) -> bool:
    return re.search(r"(?<![\w-])" + re.escape(identifier) + r"(?![\w-])", text) is not None


def _visible_markdown(text: str) -> str:
    """Keep citation text, excluding comments, reference definitions and link targets."""
    text = re.sub(r"<!--[\s\S]*?-->", "", text)
    text = re.sub(r"(?m)^ {0,3}\[[^\]\n]+\]:[^\n]*(?:\n[ \t]+[^\n]+)*", "", text)
    parts = []
    cursor = 0
    while match := re.search(r"`+|\]\(|\]\[[^\]\n]*\]", text[cursor:]):
        start = cursor + match.start()
        stop = cursor + match.end()
        parts.append(text[cursor:start])
        token = match[0]
        if token.startswith("`"):
            closing = re.search(r"(?<!`)" + re.escape(token) + r"(?!`)", text[stop:])
            if closing is not None:
                stop += closing.end()
            parts.append(text[start:stop])
        elif token.startswith("]["):
            parts.append("]")
        else:
            depth = 1
            quoted = ""
            while stop < len(text) and depth:
                char = text[stop]
                if char == "\\":
                    stop += 2
                    continue
                if quoted:
                    if char == quoted:
                        quoted = ""
                elif char == "<":
                    quoted = ">"
                elif char in "\"'" and text[stop - 1].isspace():
                    quoted = char
                elif char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                stop += 1
            parts.append("]" if depth == 0 else text[start:stop])
        cursor = stop
    parts.append(text[cursor:])
    return "".join(parts)


def _has_both_sites(text: str) -> bool:
    text = _visible_markdown(text)
    covered = set()
    for match in SOURCE_LOCATION.finditer(text.replace("\\", "/")):
        start = match[1].lstrip("0") or "0"
        stop = (match[2] or match[1]).lstrip("0") or "0"
        # Compare arbitrary-length decimal lines before converting only the two pinned sites.
        if (len(start), start) > (len(stop), stop):
            return False
        if start not in {"10", "11"} or stop not in {"10", "11"}:
            continue
        covered.update(range(int(start), int(stop) + 1))
    return covered == {10, 11} and _has_identifier(text, "audit_fixture")


def check_reporting(report: object) -> list[str]:
    if not isinstance(report, dict):
        return ["report must be a JSON object"]
    case = report.get("case")
    if not isinstance(case, str) or case not in CASES:
        return ["case must name one of the four reporting cases"]
    detailed = report.get("detailed_report")
    summary = report.get("executive_summary")
    if not isinstance(detailed, str) or not detailed.strip():
        return ["detailed_report must contain the captured Markdown"]
    if not isinstance(summary, str) or not summary.strip():
        return ["executive_summary must contain the captured Markdown"]
    errors = []
    if len(summary.splitlines()) > 60 or len(summary.split()) > 600:
        errors.append("summary exceeds 60 lines or 600 whitespace-delimited words")
    if not re.search(r"(?m)^#{1,6}\s+.*Executive Summary", summary):
        errors.append("summary needs an Executive Summary heading")
    if re.search(r"(?m)^\s*(?:`{3,}|~{3,})", summary):
        errors.append("summary must not contain fenced code excerpts")
    rows, table_errors = _priority_rows(summary)
    errors.extend(table_errors)
    if case == "trace-unmapped":
        if rows:
            errors.append("trace-only avoidability is unknown; no ranked rows are allowed")
        for name, text in (("detailed report", detailed), ("summary", summary)):
            if "Code location not verified" not in text:
                errors.append(f"{name} must mark the unavailable source mapping")
            if ANY_LOCATION.search(text.replace("\\", "/")):
                errors.append(f"{name} must not invent file-and-line locations")
            if not all(_has_identifier(text, record) for record in ("standalone-1", "standalone-2")):
                errors.append(f"{name} must retain both trace record citations")
    else:
        if len(rows) != 1:
            errors.append("this synthetic case requires exactly one supported priority row")
        if case == "multi-site":
            if not _has_both_sites(detailed):
                errors.append("detailed report must identify audit_fixture and both exact read sites")
            if rows and not _has_both_sites(rows[0][2]):
                errors.append("Code location must identify audit_fixture and both exact read sites")
        elif rows:
            location = _visible_markdown(rows[0][2])
            if case == "supplied-locations":
                if (
                    not SUPPLIED_LOCATION.search(location.replace("\\", "/"))
                    or not _has_identifier(location, "fetch_context")
                    or "From supplied report; not reverified" not in location
                ):
                    errors.append("Code location must preserve the supplied location and provenance")
            elif location != "Not provided in supplied report":
                errors.append("Code location must explicitly state the supplied report has no location")
        if case == "supplied-missing" and ANY_LOCATION.search(summary.replace("\\", "/")):
            errors.append("summary must not invent file-and-line locations absent from the supplied report")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="captured reporting-case JSON envelope")
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        parser.exit(2, f"Cannot read report: {error}\n")
    errors = check_reporting(report)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors))
        return 1
    print("PASS: captured reporting case matches location and summary checks.")
    print("Manual review is still required for semantics, tool scope and host behavior.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
