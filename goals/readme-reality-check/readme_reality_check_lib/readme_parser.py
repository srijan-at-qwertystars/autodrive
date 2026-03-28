from __future__ import annotations

import re
from pathlib import Path

from .models import Instruction

COMMAND_PREFIXES = (
    "npm ",
    "pnpm ",
    "yarn ",
    "bun ",
    "make ",
    "docker ",
    "docker-compose ",
    "python ",
    "python3 ",
    "pip ",
    "pip3 ",
    "uv ",
    "poetry ",
    "cargo ",
    "go ",
    "bash ",
    "sh ",
    "./",
    "source ",
    "cp ",
    "cat ",
    "cd ",
)

RUN_SENTENCE_RE = re.compile(
    r"(?:run|execute|use|start with|install with|invoke)\s+`([^`]+)`",
    re.IGNORECASE,
)
FENCE_START_RE = re.compile(r"^```(?P<lang>[A-Za-z0-9_-]+)?\s*$")
LIST_PREFIX_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")


def find_documentation_files(root: Path) -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()
    patterns = (
        "README*",
        "readme*",
        "INSTALL*",
        "install*",
        "SETUP*",
        "setup*",
        "docs/**/*.md",
    )
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file() and _is_documentation_candidate(path) and path not in seen:
                seen.add(path)
                candidates.append(path)
    return sorted(candidates)


def _is_documentation_candidate(path: Path) -> bool:
    normalized_name = path.name.lower()
    stem = path.stem.lower()
    if stem not in {"readme", "install", "setup"} and "docs/" not in path.as_posix():
        return False

    suffix = path.suffix.lower()
    return suffix in {"", ".md", ".markdown", ".rst", ".txt"}


def parse_instructions(root: Path, doc_paths: list[Path]) -> list[Instruction]:
    instructions: list[Instruction] = []
    for doc_path in doc_paths:
        try:
            text = doc_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = doc_path.read_text(encoding="utf-8", errors="ignore")
        instructions.extend(_parse_document(root, doc_path, text))
    return instructions


def _parse_document(root: Path, doc_path: Path, text: str) -> list[Instruction]:
    instructions: list[Instruction] = []
    lines = text.splitlines()
    in_shell_fence = False
    fence_start_line = 0
    fence_commands: list[str] = []

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        fence_match = FENCE_START_RE.match(stripped)
        if fence_match:
            if in_shell_fence:
                combined = "\n".join(fence_commands).strip()
                if combined:
                    instructions.append(
                        Instruction(
                            source_path=str(doc_path.relative_to(root)),
                            line_start=fence_start_line,
                            line_end=index - 1,
                            text=combined,
                            commands=[command for command in fence_commands if command.strip()],
                        )
                    )
                in_shell_fence = False
                fence_commands = []
                continue

            language = (fence_match.group("lang") or "").lower()
            in_shell_fence = language in {"", "sh", "shell", "bash", "zsh", "console"}
            fence_start_line = index + 1
            fence_commands = []
            continue

        if in_shell_fence:
            if stripped and not stripped.startswith("#"):
                fence_commands.append(stripped)
            continue

        list_candidate = LIST_PREFIX_RE.sub("", line).strip()
        if _looks_like_command(list_candidate):
            instructions.append(
                Instruction(
                    source_path=str(doc_path.relative_to(root)),
                    line_start=index,
                    line_end=index,
                    text=list_candidate,
                    commands=[list_candidate],
                )
            )
            continue

        for match in RUN_SENTENCE_RE.finditer(line):
            candidate = match.group(1).strip()
            if _looks_like_command(candidate):
                instructions.append(
                    Instruction(
                        source_path=str(doc_path.relative_to(root)),
                        line_start=index,
                        line_end=index,
                        text=line.strip(),
                        commands=[candidate],
                    )
                )

    return instructions


def _looks_like_command(candidate: str) -> bool:
    if not candidate or len(candidate) < 3:
        return False
    return candidate.startswith(COMMAND_PREFIXES)
