from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib


@dataclass(slots=True)
class Policy:
    trusted_packages: set[str] = field(default_factory=set)
    trusted_scopes: set[str] = field(default_factory=set)
    trusted_hosts: set[str] = field(default_factory=lambda: {"pypi.org", "registry.npmjs.org"})
    enforce_single_lockfile: bool = True
    require_ignore_scripts_for_js_installs: bool = True


DEFAULT_POLICY_FILE = "guardrail-policy.toml"


def load_policy(root: Path, file_name: str = DEFAULT_POLICY_FILE) -> Policy:
    policy_path = root / file_name
    if not policy_path.exists():
        return Policy()

    data = tomllib.loads(policy_path.read_text(encoding="utf-8"))
    trusted = data.get("trusted", {})
    rules = data.get("rules", {})

    return Policy(
        trusted_packages=set(_lower_list(trusted.get("packages", []))),
        trusted_scopes=set(_lower_list(trusted.get("scopes", []))),
        trusted_hosts=set(_lower_list(trusted.get("hosts", ["pypi.org", "registry.npmjs.org"]))),
        enforce_single_lockfile=bool(rules.get("enforce_single_lockfile", True)),
        require_ignore_scripts_for_js_installs=bool(rules.get("require_ignore_scripts_for_js_installs", True)),
    )


def _lower_list(values: list[str]) -> list[str]:
    return [item.strip().lower() for item in values if isinstance(item, str) and item.strip()]
