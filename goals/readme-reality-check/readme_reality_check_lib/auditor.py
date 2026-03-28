from __future__ import annotations

import shlex
from pathlib import Path

from .models import AuditReport, Finding, Instruction
from .readme_parser import parse_instructions
from .scanners import scan_repository

YARN_RESERVED = {
    "add",
    "bin",
    "cache",
    "config",
    "create",
    "dlx",
    "exec",
    "help",
    "info",
    "init",
    "install",
    "link",
    "node",
    "npm",
    "pack",
    "publish",
    "remove",
    "run",
    "set",
    "stage",
    "test",
    "unlink",
    "up",
    "upgrade",
    "version",
    "why",
}
COMMON_GENERATED_PATHS = {
    ".env",
    ".venv",
    ".venv/bin/activate",
    "venv",
    "venv/bin/activate",
    "node_modules",
    "dist",
    "build",
}


def audit_repository(target: str | Path) -> AuditReport:
    root = Path(target).expanduser().resolve()
    facts = scan_repository(root)
    doc_paths = [root / path for path in facts.doc_files]
    instructions = parse_instructions(root, doc_paths)
    findings = _audit_instructions(instructions, facts)

    if not facts.doc_files:
        findings.append(
            Finding(
                kind="missing_file",
                severity="warning",
                message="No README/setup documentation files were found to audit.",
                reference="README.md",
            )
        )

    for devcontainer in facts.devcontainers:
        for reference in sorted(devcontainer.referenced_files):
            if not facts.has_file(reference):
                findings.append(
                    Finding(
                        kind="missing_file",
                        severity="warning",
                        message=f"Devcontainer references missing file: {reference}",
                        source_path=devcontainer.path,
                        reference=reference,
                    )
                )

    return AuditReport(
        target=str(root),
        instructions=instructions,
        findings=_dedupe_findings(findings),
        facts=facts,
    )


def _audit_instructions(instructions: list[Instruction], facts) -> list[Finding]:
    findings: list[Finding] = []
    for instruction in instructions:
        for raw_command in instruction.commands:
            command = raw_command.strip()
            findings.extend(_check_command(command, instruction, facts))
    return findings


def _check_command(command: str, instruction: Instruction, facts) -> list[Finding]:
    findings: list[Finding] = []
    try:
        tokens = shlex.split(command, comments=False, posix=True)
    except ValueError:
        tokens = command.split()

    if not tokens:
        return findings

    head = tokens[0]

    if head in {"npm", "pnpm", "bun"}:
        findings.extend(_check_node_package_command(tokens, command, instruction, facts))
    elif head == "yarn":
        findings.extend(_check_yarn_command(tokens, command, instruction, facts))
    elif head == "make":
        findings.extend(_check_make_command(tokens, command, instruction, facts))
    elif head in {"docker", "docker-compose"}:
        findings.extend(_check_docker_command(tokens, command, instruction, facts))
    elif head == "cd" and len(tokens) > 1 and not facts.has_directory(tokens[1]):
        findings.append(_missing_file_finding("missing_directory", f"Referenced directory does not exist: {tokens[1]}", tokens[1], command, instruction))
    elif head in {"bash", "sh", "source"} and len(tokens) > 1:
        findings.extend(_check_file_references(tokens[1:2], command, instruction, facts))
    elif head in {"python", "python3"}:
        findings.extend(_check_python_command(tokens[1:], command, instruction, facts))
    elif head in {"cp", "cat"}:
        findings.extend(_check_file_references(tokens[1:2], command, instruction, facts))
    elif head.startswith("./"):
        findings.extend(_check_file_references([head], command, instruction, facts))

    if "-f" in tokens:
        index = tokens.index("-f")
        if index + 1 < len(tokens):
            findings.extend(_check_file_references([tokens[index + 1]], command, instruction, facts))

    if "--file" in tokens:
        index = tokens.index("--file")
        if index + 1 < len(tokens):
            findings.extend(_check_file_references([tokens[index + 1]], command, instruction, facts))

    return findings


def _check_node_package_command(tokens: list[str], command: str, instruction: Instruction, facts) -> list[Finding]:
    findings: list[Finding] = []
    if "run" in tokens:
        index = tokens.index("run")
        if index + 1 < len(tokens):
            script = tokens[index + 1]
            if script not in facts.scripts:
                findings.append(
                    Finding(
                        kind="missing_script",
                        severity="error",
                        message=f"Referenced package script is missing: {script}",
                        source_path=instruction.source_path,
                        line=instruction.line_start,
                        command=command,
                        reference=script,
                    )
                )
    elif len(tokens) > 1 and tokens[1] in {"install", "ci"} and not facts.package_manifests:
        findings.append(
            Finding(
                kind="unsupported_command",
                severity="warning",
                message="Package manager command is documented but no package.json was found.",
                source_path=instruction.source_path,
                line=instruction.line_start,
                command=command,
            )
        )
    return findings


def _check_yarn_command(tokens: list[str], command: str, instruction: Instruction, facts) -> list[Finding]:
    if len(tokens) <= 1:
        return []
    subcommand = tokens[1]
    if subcommand == "run" and len(tokens) > 2:
        script = tokens[2]
    elif subcommand in YARN_RESERVED:
        script = None
    else:
        script = subcommand

    if script and script not in facts.scripts:
        return [
            Finding(
                kind="missing_script",
                severity="error",
                message=f"Referenced package script is missing: {script}",
                source_path=instruction.source_path,
                line=instruction.line_start,
                command=command,
                reference=script,
            )
        ]

    if subcommand == "install" and not facts.package_manifests:
        return [
            Finding(
                kind="unsupported_command",
                severity="warning",
                message="yarn install is documented but no package.json was found.",
                source_path=instruction.source_path,
                line=instruction.line_start,
                command=command,
            )
        ]
    return []


def _check_make_command(tokens: list[str], command: str, instruction: Instruction, facts) -> list[Finding]:
    if len(tokens) <= 1:
        return []
    target = next((token for token in tokens[1:] if not token.startswith("-")), None)
    if not target:
        return []
    if not facts.make_targets:
        return [
            Finding(
                kind="unsupported_command",
                severity="warning",
                message="make command is documented but no Makefile was found.",
                source_path=instruction.source_path,
                line=instruction.line_start,
                command=command,
            )
        ]
    if target not in facts.make_targets:
        return [
            Finding(
                kind="missing_script",
                severity="error",
                message=f"Referenced make target is missing: {target}",
                source_path=instruction.source_path,
                line=instruction.line_start,
                command=command,
                reference=target,
            )
        ]
    return []


def _check_docker_command(tokens: list[str], command: str, instruction: Instruction, facts) -> list[Finding]:
    findings: list[Finding] = []
    joined = " ".join(tokens[:3])
    if joined.startswith("docker compose") or tokens[0] == "docker-compose":
        if not facts.compose_files:
            findings.append(
                Finding(
                    kind="unsupported_command",
                    severity="warning",
                    message="Compose command is documented but no compose file was found.",
                    source_path=instruction.source_path,
                    line=instruction.line_start,
                    command=command,
                )
            )
    elif len(tokens) > 1 and tokens[1] == "build" and not facts.dockerfiles:
        findings.append(
            Finding(
                kind="unsupported_command",
                severity="warning",
                message="docker build is documented but no Dockerfile was found.",
                source_path=instruction.source_path,
                line=instruction.line_start,
                command=command,
            )
        )

    if any(token.startswith(".devcontainer") for token in tokens) and not facts.devcontainers:
        findings.append(
            Finding(
                kind="unsupported_command",
                severity="warning",
                message="Command references .devcontainer but no devcontainer config was found.",
                source_path=instruction.source_path,
                line=instruction.line_start,
                command=command,
            )
        )
    return findings


def _check_python_command(args: list[str], command: str, instruction: Instruction, facts) -> list[Finding]:
    if not args or args[0].startswith("-"):
        return []
    candidate = args[0]
    if candidate == "-m":
        return []
    return _check_file_references([candidate], command, instruction, facts)


def _check_file_references(candidates: list[str], command: str, instruction: Instruction, facts) -> list[Finding]:
    findings: list[Finding] = []
    for candidate in candidates:
        normalized = candidate.strip().strip('"').strip("'").removeprefix("./").rstrip("/")
        if not normalized or normalized in COMMON_GENERATED_PATHS:
            continue
        if normalized.startswith("-") or "://" in normalized:
            continue
        if normalized in {".", ".."}:
            continue

        looks_like_path = "/" in normalized or "." in Path(normalized).name
        if not looks_like_path:
            continue
        if facts.has_file(normalized) or facts.has_directory(normalized):
            continue

        findings.append(
            _missing_file_finding(
                "missing_file",
                f"Referenced file does not exist: {normalized}",
                normalized,
                command,
                instruction,
            )
        )
    return findings


def _missing_file_finding(kind: str, message: str, reference: str, command: str, instruction: Instruction) -> Finding:
    return Finding(
        kind=kind,
        severity="warning",
        message=message,
        source_path=instruction.source_path,
        line=instruction.line_start,
        command=command,
        reference=reference,
    )


def _dedupe_findings(findings: list[Finding]) -> list[Finding]:
    deduped: list[Finding] = []
    seen: set[tuple[str, str | None, int | None, str | None, str | None]] = set()
    for finding in findings:
        key = (
            finding.kind,
            finding.source_path,
            finding.line,
            finding.command,
            finding.reference,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return deduped
