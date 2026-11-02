from __future__ import annotations

import argparse
from pathlib import Path
import json

from .checks import evaluate_command
from .detector import parse_command
from .policy import load_policy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pm-guardrail",
        description="Evaluate package-management commands against safety policies.",
    )
    parser.add_argument("command", help="Raw package-management command to evaluate.")
    parser.add_argument("--root", default=".", help="Repository root to inspect.")
    parser.add_argument("--policy", default="guardrail-policy.toml", help="Policy filename under root.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    policy = load_policy(root, file_name=args.policy)
    context = parse_command(args.command, cwd=root)
    result = evaluate_command(context, policy, root)

    if args.json:
        payload = {
            "allowed": not result.should_block,
            "findings": [
                {
                    "code": item.code,
                    "severity": item.severity.value,
                    "message": item.message,
                }
                for item in result.findings
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        if result.findings:
            print("Findings:")
            for finding in result.findings:
                print(f"- [{finding.severity.value}] {finding.code}: {finding.message}")
        else:
            print("No findings.")
        print(f"Decision: {'BLOCK' if result.should_block else 'ALLOW'}")

    return 2 if result.should_block else 0
