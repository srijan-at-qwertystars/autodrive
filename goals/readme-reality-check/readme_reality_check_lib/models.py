from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Instruction:
    source_path: str
    line_start: int
    line_end: int
    text: str
    commands: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Finding:
    kind: str
    severity: str
    message: str
    source_path: str | None = None
    line: int | None = None
    command: str | None = None
    reference: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return {key: value for key, value in payload.items() if value not in (None, {}, [])}


@dataclass(slots=True)
class PackageJsonInfo:
    path: str
    scripts: set[str] = field(default_factory=set)

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "scripts": sorted(self.scripts)}


@dataclass(slots=True)
class DevcontainerInfo:
    path: str
    referenced_files: set[str] = field(default_factory=set)

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "referenced_files": sorted(self.referenced_files)}


@dataclass(slots=True)
class RepositoryFacts:
    root_path: str
    files: set[str] = field(default_factory=set)
    directories: set[str] = field(default_factory=set)
    package_manifests: list[PackageJsonInfo] = field(default_factory=list)
    make_targets: set[str] = field(default_factory=set)
    dockerfiles: set[str] = field(default_factory=set)
    compose_files: set[str] = field(default_factory=set)
    devcontainers: list[DevcontainerInfo] = field(default_factory=list)
    doc_files: list[str] = field(default_factory=list)

    def has_file(self, path: str) -> bool:
        candidate = path.strip().strip('"').strip("'")
        if not candidate:
            return False
        normalized = candidate.removeprefix("./")
        return normalized in self.files

    def has_directory(self, path: str) -> bool:
        candidate = path.strip().strip('"').strip("'")
        if not candidate:
            return False
        normalized = candidate.rstrip("/").removeprefix("./")
        return normalized in self.directories

    @property
    def scripts(self) -> set[str]:
        names: set[str] = set()
        for manifest in self.package_manifests:
            names.update(manifest.scripts)
        return names

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_path": self.root_path,
            "doc_files": sorted(self.doc_files),
            "package_manifests": [item.to_dict() for item in self.package_manifests],
            "make_targets": sorted(self.make_targets),
            "dockerfiles": sorted(self.dockerfiles),
            "compose_files": sorted(self.compose_files),
            "devcontainers": [item.to_dict() for item in self.devcontainers],
        }


@dataclass(slots=True)
class AuditReport:
    target: str
    instructions: list[Instruction]
    findings: list[Finding]
    facts: RepositoryFacts

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "instruction_count": len(self.instructions),
            "instructions": [item.to_dict() for item in self.instructions],
            "finding_count": len(self.findings),
            "findings": [item.to_dict() for item in self.findings],
            "facts": self.facts.to_dict(),
        }
