from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    BLOCK = "block"
    WARN = "warn"


@dataclass(slots=True)
class Finding:
    code: str
    message: str
    severity: Severity


@dataclass(slots=True)
class CheckResult:
    findings: list[Finding] = field(default_factory=list)

    @property
    def should_block(self) -> bool:
        return any(item.severity == Severity.BLOCK for item in self.findings)
