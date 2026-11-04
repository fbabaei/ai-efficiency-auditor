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
    r"(?<![\w./-])src/pipeline\.py:(\d+)(?:-(\d+))?(?![\w-])"
)
SUPPLIED_LOCATION = re.compile(r"(?<![\w./-])src/worker\.py:42-44(?![\w-])")
ANY_LOCATION = re.compile(r"\b[\w./-]+\.\w+:\d+")


def _priority_rows(summary: str) -> tuple[list[list[str]], list[str]]:
    tables = []
    errors = []
    current: list[list[str]] | None = None
    for line in summary.splitlines():
        if not line.strip().startswith("|"):
            current = None
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
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


def _has_both_sites(text: str) -> bool:
    covered = set()
    for match in SOURCE_LOCATION.finditer(text.replace("\\", "/")):
        start = int(match[1])
        stop = int(match[2] or match[1])
        if start > stop or start < 10 or stop > 11:
            return False
        covered.update(range(start, stop + 1))
    return covered == {10, 11} and "audit_fixture" in text


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
            if not all(record in text for record in ("standalone-1", "standalone-2")):
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
            location = rows[0][2]
            if case == "supplied-locations":
                if (
                    not SUPPLIED_LOCATION.search(location.replace("\\", "/"))
                    or "fetch_context" not in location
                    or "From supplied report; not reverified" not in location
                ):
                    errors.append("Code location must preserve the supplied location and provenance")
            elif location != "Not provided in supplied report":
                errors.append("Code location must explicitly state the supplied report has no location")
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
