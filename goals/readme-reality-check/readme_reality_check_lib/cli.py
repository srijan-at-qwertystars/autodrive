from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .auditor import audit_repository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readme_reality_check.py",
        description="Audit README and setup docs against local repository surfaces.",
    )
    subparsers = parser.add_subparsers(dest="command")

    audit_parser = subparsers.add_parser("audit", help="Audit a local repository path.")
    audit_parser.add_argument("path", nargs="?", default=".", help="Path to the repository to audit.")
    audit_parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="text",
        help="Output format.",
    )
    audit_parser.add_argument(
        "--output",
        help="Optional file path to write the report to. Defaults to stdout.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "audit":
        parser.print_help()
        return 0

    target = Path(args.path).expanduser()
    if not target.exists():
        parser.error(f"path does not exist: {target}")

    report = audit_repository(target)
    rendered = _render_report(report, args.format)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(rendered + ("\n" if not rendered.endswith("\n") else ""), encoding="utf-8")
    else:
        sys.stdout.write(rendered)
        if not rendered.endswith("\n"):
            sys.stdout.write("\n")
    return 0


def _render_report(report, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(report.to_dict(), indent=2, sort_keys=True)

    lines = [
        f"Target: {report.target}",
        f"Docs scanned: {len(report.facts.doc_files)}",
        f"Instructions parsed: {len(report.instructions)}",
        f"Findings: {len(report.findings)}",
    ]
    for finding in report.findings:
        location = ""
        if finding.source_path:
            location = finding.source_path
            if finding.line:
                location = f"{location}:{finding.line}"
            location = f" [{location}]"
        lines.append(f"- {finding.severity.upper()} {finding.kind}{location}: {finding.message}")
    return "\n".join(lines)
