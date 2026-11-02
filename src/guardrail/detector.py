from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex


@dataclass(slots=True)
class CommandContext:
    raw_command: str
    command_parts: list[str]
    cwd: Path

    @property
    def tool(self) -> str:
        return self.command_parts[0].lower() if self.command_parts else ""


def parse_command(raw_command: str, cwd: Path) -> CommandContext:
    parts = shlex.split(raw_command, posix=False)
    return CommandContext(raw_command=raw_command, command_parts=parts, cwd=cwd)


def detect_repo_ecosystem(root: Path) -> set[str]:
    ecosystems: set[str] = set()
    if (root / "requirements.txt").exists() or (root / "pyproject.toml").exists():
        ecosystems.add("python")
    if (root / "package.json").exists():
        ecosystems.add("node")
    if (root / "Gemfile").exists():
        ecosystems.add("ruby")
    return ecosystems


def discover_lockfiles(root: Path) -> list[str]:
    known = [
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "bun.lockb",
        "poetry.lock",
        "Pipfile.lock",
        "uv.lock",
    ]
    return [name for name in known if (root / name).exists()]
