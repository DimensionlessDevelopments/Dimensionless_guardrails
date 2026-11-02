from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from .detector import CommandContext, detect_repo_ecosystem, discover_lockfiles
from .policy import Policy
from .types import CheckResult, Finding, Severity


PYTHON_MANAGERS = {"pip", "pip3", "poetry", "uv", "pipenv"}
NODE_MANAGERS = {"npm", "yarn", "pnpm", "bun"}


def evaluate_command(command: CommandContext, policy: Policy, root: Path) -> CheckResult:
    result = CheckResult()

    _check_manager_mismatch(command, root, result)
    _check_lockfile_conflicts(root, policy, result)
    _check_untrusted_dependencies(command, policy, result)
    _check_script_safety(command, policy, result)

    return result


def _check_manager_mismatch(command: CommandContext, root: Path, result: CheckResult) -> None:
    tool = command.tool
    if not tool:
        return

    ecosystems = detect_repo_ecosystem(root)
    if "python" in ecosystems and "node" not in ecosystems and tool in NODE_MANAGERS:
        result.findings.append(
            Finding(
                code="manager.mismatch",
                message=f"Detected Python project but command uses Node manager '{tool}'.",
                severity=Severity.BLOCK,
            )
        )
    if "node" in ecosystems and "python" not in ecosystems and tool in PYTHON_MANAGERS:
        result.findings.append(
            Finding(
                code="manager.mismatch",
                message=f"Detected Node project but command uses Python manager '{tool}'.",
                severity=Severity.BLOCK,
            )
        )


def _check_lockfile_conflicts(root: Path, policy: Policy, result: CheckResult) -> None:
    if not policy.enforce_single_lockfile:
        return

    lockfiles = discover_lockfiles(root)

    node_lockfiles = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb"}
    present_node_locks = [name for name in lockfiles if name in node_lockfiles]

    if len(present_node_locks) > 1:
        result.findings.append(
            Finding(
                code="lockfile.conflict",
                message=f"Multiple Node lockfiles detected: {', '.join(sorted(present_node_locks))}",
                severity=Severity.BLOCK,
            )
        )


def _check_untrusted_dependencies(command: CommandContext, policy: Policy, result: CheckResult) -> None:
    if command.tool not in PYTHON_MANAGERS | NODE_MANAGERS:
        return

    dependencies = _extract_dependency_tokens(command.command_parts)
    for dep in dependencies:
        low = dep.lower()

        if "://" in low:
            host = urlparse(low).netloc.lower()
            if host and host not in policy.trusted_hosts:
                result.findings.append(
                    Finding(
                        code="dependency.untrusted_host",
                        message=f"Dependency URL host '{host}' is not trusted.",
                        severity=Severity.BLOCK,
                    )
                )
            continue

        if low.startswith("@"):
            scope = low.split("/", 1)[0]
            if scope not in policy.trusted_scopes:
                result.findings.append(
                    Finding(
                        code="dependency.untrusted_scope",
                        message=f"Dependency scope '{scope}' is not trusted.",
                        severity=Severity.WARN,
                    )
                )
            continue

        pkg = low.split("==", 1)[0].split("@", 1)[0].split("[", 1)[0]
        if policy.trusted_packages and pkg not in policy.trusted_packages:
            result.findings.append(
                Finding(
                    code="dependency.unknown",
                    message=f"Dependency '{pkg}' is not in trusted package allowlist.",
                    severity=Severity.WARN,
                )
            )


def _check_script_safety(command: CommandContext, policy: Policy, result: CheckResult) -> None:
    if not policy.require_ignore_scripts_for_js_installs:
        return
    if command.tool not in NODE_MANAGERS:
        return

    parts = [item.lower() for item in command.command_parts]
    is_install = any(item in {"install", "add", "i"} for item in parts[1:3])
    has_ignore = any(item in {"--ignore-scripts", "--ignore-script"} for item in parts)

    if is_install and not has_ignore:
        result.findings.append(
            Finding(
                code="scripts.enabled",
                message="JS package install does not disable lifecycle scripts. Use --ignore-scripts.",
                severity=Severity.BLOCK,
            )
        )


def _extract_dependency_tokens(parts: list[str]) -> list[str]:
    if len(parts) < 2:
        return []

    tokens: list[str] = []
    for token in parts[1:]:
        if token.startswith("-"):
            continue
        if token in {"install", "add", "i", "remove", "uninstall", "update", "upgrade"}:
            continue
        if token.startswith(".") or token.startswith("/"):
            continue
        tokens.append(token)
    return tokens
