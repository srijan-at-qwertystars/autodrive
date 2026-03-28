from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .models import DevcontainerInfo, PackageJsonInfo, RepositoryFacts
from .readme_parser import find_documentation_files

MAKE_TARGET_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_.-]*):(?:\s|$)")
IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
}


def scan_repository(root: Path) -> RepositoryFacts:
    files: set[str] = set()
    directories: set[str] = set()
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in IGNORED_DIRECTORIES)
        current_path = Path(current_root)
        if current_path != root:
            directories.add(str(current_path.relative_to(root)))
        for filename in filenames:
            file_path = current_path / filename
            files.add(str(file_path.relative_to(root)))

    facts = RepositoryFacts(
        root_path=str(root),
        files=files,
        directories=directories,
    )
    facts.doc_files = [str(path.relative_to(root)) for path in find_documentation_files(root)]
    facts.package_manifests = _scan_package_json(root)
    facts.make_targets = _scan_makefiles(root)
    facts.dockerfiles = _scan_dockerfiles(root, files)
    facts.compose_files = _scan_compose_files(files)
    facts.devcontainers = _scan_devcontainers(root, files)
    return facts


def _scan_package_json(root: Path) -> list[PackageJsonInfo]:
    manifests: list[PackageJsonInfo] = []
    for path in sorted(root / relative for relative in _iter_paths(root, "package.json")):
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        scripts = data.get("scripts")
        if isinstance(scripts, dict):
            script_names = {str(name) for name in scripts.keys()}
        else:
            script_names = set()
        manifests.append(PackageJsonInfo(path=str(path.relative_to(root)), scripts=script_names))
    return manifests


def _scan_makefiles(root: Path) -> set[str]:
    targets: set[str] = set()
    for name in ("Makefile", "makefile", "GNUmakefile"):
        path = root / name
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in lines:
            if line.startswith(("\t", "#", ".")):
                continue
            match = MAKE_TARGET_RE.match(line)
            if match:
                targets.add(match.group(1))
    return targets


def _scan_dockerfiles(root: Path, files: set[str]) -> set[str]:
    dockerfiles = {path for path in files if Path(path).name.lower().startswith("dockerfile")}
    return dockerfiles


def _scan_compose_files(files: set[str]) -> set[str]:
    compose_names = {
        "docker-compose.yml",
        "docker-compose.yaml",
        "compose.yml",
        "compose.yaml",
    }
    return {path for path in files if Path(path).name in compose_names}


def _scan_devcontainers(root: Path, files: set[str]) -> list[DevcontainerInfo]:
    devcontainers: list[DevcontainerInfo] = []
    for path in sorted(files):
        if not path.startswith(".devcontainer/") or not path.endswith(".json"):
            continue
        full_path = root / path
        try:
            data = json.loads(full_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            data = {}
        referenced = set(_extract_devcontainer_references(data))
        devcontainers.append(DevcontainerInfo(path=path, referenced_files=referenced))
    return devcontainers


def _iter_paths(root: Path, filename: str) -> list[Path]:
    matches: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in IGNORED_DIRECTORIES)
        if filename in filenames:
            matches.append(Path(current_root).relative_to(root) / filename)
    return matches


def _extract_devcontainer_references(data: object) -> list[str]:
    references: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            lowered = key.lower()
            if lowered in {"dockerfile", "dockercomposefile", "composefile"}:
                if isinstance(value, str):
                    references.append(_normalize_devcontainer_reference(value))
                elif isinstance(value, list):
                    references.extend(_normalize_devcontainer_reference(item) for item in value if isinstance(item, str))
            else:
                references.extend(_extract_devcontainer_references(value))
    elif isinstance(data, list):
        for item in data:
            references.extend(_extract_devcontainer_references(item))
    return references


def _normalize_devcontainer_reference(value: str) -> str:
    candidate = value.strip().removeprefix("./")
    if candidate.startswith(".devcontainer/"):
        return candidate
    return f".devcontainer/{candidate}"
