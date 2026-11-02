# Dimensionless-guardrail


> **Status: Research prototype**
>
> This project is intended for safety research, policy experimentation, and integration testing in agentic coding workflows. It is not a complete software supply-chain security system and should not be treated as a standalone production control.

---

## Table of Contents

- [Overview](#overview)
- [Objectives](#objectives)
- [Threat Model and Scope](#threat-model-and-scope)
- [Features](#features)
- [Guardrail Methodology](#guardrail-methodology)
- [Decision Model](#decision-model)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Running Checks](#running-checks)
- [Validation and Testing](#validation-and-testing)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Risk Disclaimer](#risk-disclaimer)
- [Contributing](#contributing)

---

## Overview

Dimensionless-guardrail evaluates package-management commands before execution and applies policy checks that are commonly missed in autonomous agent workflows.

The project addresses practical failure modes seen in LLM-assisted coding sessions, including:

- using a package manager that does not match the repository ecosystem
- introducing conflicting lockfiles in JavaScript/TypeScript projects
- installing dependencies from untrusted hosts or unknown scopes
- allowing lifecycle scripts to execute during JS installs

The current implementation is intentionally lightweight and CLI-first so it can be embedded in wrappers, preflight hooks, or orchestrators that supervise tool-using agents.

### Project goals

- Make package-management safety checks explicit and repeatable.
- Reduce preventable dependency and lockfile mistakes from agent actions.
- Provide machine-readable allow/block decisions for automation.
- Keep policies configurable and repository-local.
- Establish a practical baseline for stronger future controls.

## Objectives

The project supports three related workflows:

| Area | Objective |
|---|---|
| Agent safety | Prevent unsafe package operations before execution. |
| Engineering controls | Provide deterministic policy checks that can be tested and versioned. |
| Platform integration | Offer a simple CLI contract for CI/CD pipelines and coding-agent runtimes. |

This framework reduces operational risk, but it does not replace broader secure-development or dependency-governance practices.

## Threat Model and Scope

pm-guardrail focuses on command-level preflight risk detection for package-manager usage.

### In scope

- command and tool mismatch against detected repository ecosystem
- lockfile conflict detection for Node lockfiles
- allowlist checks for package names, scopes, and dependency URL hosts
- enforcement of script-suppression flags for JS installs

### Out of scope

- full transitive dependency auditing and CVE scoring
- cryptographic package provenance verification
- runtime sandboxing of install processes
- network-level egress policy enforcement
- malware analysis of package contents

## Features

### Repository and command detection

- Parses raw package-manager commands into a normalized context.
- Detects repository ecosystems from local project files.
- Identifies known lockfiles used by multiple ecosystems.

### Policy-driven checks

- Blocks package-manager mismatch for single-ecosystem repositories.
- Blocks multiple Node lockfiles when strict lockfile mode is enabled.
- Blocks dependency URLs from untrusted hosts.
- Warns on unknown package scopes and package names not in allowlist.
- Blocks JS install commands that do not include an ignore-scripts flag.

### Output and integration

- Human-readable findings for interactive workflows.
- JSON output for machine consumption.
- Deterministic exit codes suitable for wrappers and CI gates.

## Guardrail Methodology

The guardrail treats each package-management operation as a policy-evaluation event.

### Evaluation flow

1. Parse command and extract candidate dependency tokens.
2. Detect repository ecosystem and lockfile state from filesystem context.
3. Load policy defaults and repository-local overrides.
4. Execute checks and accumulate findings.
5. Return allow/block decision with structured evidence.

### Decision philosophy

- Use blocking findings for high-risk and high-confidence violations.
- Use warning findings for uncertainty that may require human review.
- Keep policy simple enough to review and maintain per repository.

## Decision Model

Each finding has a code, severity, and message.

| Severity | Meaning |
|---|---|
| `block` | Operation is denied. Exit code is `2`. |
| `warn` | Operation is allowed but flagged for review. |

### Current decision behavior

- Any `block` finding causes an overall block.
- Zero `block` findings results in allow.

## Project Structure

```text
guard/
├── guardrail-policy.toml
├── pyproject.toml
├── README.md
├── src/
│   └── guardrail/
│       ├── __init__.py
│       ├── __main__.py
│       ├── checks.py
│       ├── cli.py
│       ├── detector.py
│       ├── policy.py
│       └── types.py
└── tests/
    └── test_checks.py
```

## Getting Started

### Requirements

- Python 3.10 or newer.
- A virtual environment is recommended.

### Installation

Clone the repository and enter the project directory:

```bash
git clone <repository-url>
cd guard
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install in editable mode:

```bash
pip install -e .
```

## Configuration

By default, pm-guardrail loads `guardrail-policy.toml` from repository root.

Example policy:

```toml
[trusted]
packages = ["requests", "numpy", "lodash", "react"]
scopes = ["@types"]
hosts = ["pypi.org", "registry.npmjs.org"]

[rules]
enforce_single_lockfile = true
require_ignore_scripts_for_js_installs = true
```

### Configuration areas

- trusted package allowlist
- trusted package scopes
- trusted dependency hosts
- lockfile conflict enforcement
- JS install script-execution enforcement

## Running Checks

Evaluate a command with human-readable output:

```bash
pm-guardrail "npm install lodash"
```

Evaluate a command with JSON output:

```bash
pm-guardrail "pip install requests" --json
```

Specify a repository root and policy filename:

```bash
pm-guardrail "npm install react --ignore-scripts" --root . --policy guardrail-policy.toml
```

### Exit codes

- `0`: allowed
- `2`: blocked

## Validation and Testing

Run the unit tests:

```bash
python -m pytest -q
```

Current tests cover:

- manager mismatch blocking behavior
- Node lockfile conflict blocking behavior
- untrusted host blocking behavior
- JS script-enforcement blocking behavior
- unknown dependency warning behavior

## Known Limitations

This is a prototype and has important limitations.

1. **Policy depth:** The current model is allowlist-driven and does not perform deep package reputation analysis.
2. **Dependency graph awareness:** Checks are command-token based and do not analyze full transitive trees.
3. **Ecosystem breadth:** Lockfile conflict logic is strongest for Node lockfiles and can be expanded for multi-tool Python flows.
4. **Script safety semantics:** `--ignore-scripts` handling may differ across package-manager versions and commands.
5. **No network controls:** The tool flags host trust issues but does not enforce outbound network policy.
6. **No runtime isolation:** It evaluates commands; it does not sandbox install execution.
7. **No provenance verification:** Artifact signatures and attestations are not validated.

## Roadmap

### Phase 1 - Baseline hardening

- [ ] Add richer command normalization across npm, pnpm, yarn, bun, pip, uv, and poetry.
- [ ] Expand lockfile policy checks for Python toolchain combinations.
- [ ] Add configurable severity overrides per finding code.
- [ ] Add policy schema validation and clear error reporting.

### Phase 2 - Security depth

- [ ] Add optional integration with vulnerability and advisory feeds.
- [ ] Add policy checks for VCS and local-path dependency sources.
- [ ] Add trusted-publisher and source provenance policy options.
- [ ] Add deterministic policy snapshots for CI reproducibility.

### Phase 3 - Ecosystem integration

- [ ] Provide pre-commit and CI examples.
- [ ] Add wrapper mode that executes only allowed commands.
- [ ] Add audit log output for governance and observability.
- [ ] Publish integration recipes for common coding-agent runtimes.

## Risk Disclaimer

This software is provided for research, educational, and engineering-control purposes. It helps reduce specific classes of package-management mistakes but does not guarantee software supply-chain security.

Safe usage requires layered controls, including dependency review, vulnerability management, provenance checks, least-privilege execution, and environment isolation.

Do not rely solely on this tool when running autonomous code modification or dependency installation workflows.

## Contributing

Contributions that improve safety coverage, policy clarity, deterministic behavior, and integration ergonomics are welcome.

For proposed changes, include:

- the risk or failure mode addressed
- expected policy behavior before and after
- representative commands and repository contexts
- tests for block/warn/allow outcomes
- migration notes for policy compatibility

**Built with ❤️ for quantitative trading research**
# Dimensionless-Guardrail 

---


## Contact
**Made by Dimensionless Developments**
**Head to our website https://quant.dimensionlessdevelopments.com/**
  **↓   ↓   ↓   ↓   ↓   ↓   ↓   ↓   ↓   ↓**
**Email: contactus@dimensionlessdevelopments.com**