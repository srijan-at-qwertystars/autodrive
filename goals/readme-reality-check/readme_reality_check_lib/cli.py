from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .auditor import audit_repository
from .renderers import render_report


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
        choices=("json", "text", "html"),
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
    rendered = render_report(report, args.format)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + ("\n" if not rendered.endswith("\n") else ""), encoding="utf-8")
    else:
        sys.stdout.write(rendered)
        if not rendered.endswith("\n"):
            sys.stdout.write("\n")
    return 0
