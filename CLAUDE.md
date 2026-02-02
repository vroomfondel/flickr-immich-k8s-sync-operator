# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

flickr-immich-k8s-sync-operator — a Python operator for syncing photos from Flickr to Immich (self-hosted photo management) on Kubernetes.

- **PyPI name**: `flickr-immich-k8s-sync-operator`
- **Import name**: `flickr_immich_k8s_sync_operator`
- **License**: LGPLv3
- **Version**: `0.0.1` (single-sourced in `flickr_immich_k8s_sync_operator/__init__.py`)
- **GitHub**: `vroomfondel/flickr-immich-k8s-sync-operator`
- **Reference project**: Follows patterns from `mqttstuff` (same author, same toolchain)

## Environment

- **Python**: 3.14 (virtualenv at `.venv/`)
- **IDE**: PyCharm project configuration in `.idea/`
- **Activate venv**: `source .venv/bin/activate`

## Common Commands

```bash
make venv          # Create/update virtualenv, install all deps
make tests         # Run pytest
make lint          # Format with black (line length 120)
make isort         # Sort imports with isort
make tcheck        # Static type checking with mypy
make commit-checks # Run pre-commit hooks on all files
make prepare       # tests + commit-checks
make pypibuild     # Build sdist + wheel with hatch
make pypipush      # Publish to PyPI
make docker        # Build Docker image
```

## Architecture

- **Origin**: Core operator logic extracted from an Ansible-managed ConfigMap (`kubectlstuff_flickr_downloader.yml`, external to this repo)
- **Flat layout**: Package at `flickr_immich_k8s_sync_operator/` (not src-layout)
- **Build backend**: Hatchling — version is single-sourced from `__init__.py` via `[tool.hatch.version]`
- **Entry point**: Console script `flickr-immich-k8s-sync-operator` → `__main__:main()`
- **Logging**: loguru with `configure_logging()` in `__init__.py`; disabled by default, enabled in `__main__.py`
- **Signal handling**: SIGTERM/SIGINT for clean container shutdown via `threading.Event`
- **Dependencies**: `kubernetes` (K8s Python client), `loguru`

### Modules

- **`__init__.py`** — Version, loguru `configure_logging()` helper
- **`config.py`** — Frozen `OperatorConfig` dataclass with `from_env()` classmethod; reads `NAMESPACE`, `JOB_NAMES` (comma-separated, required), `CHECK_INTERVAL`, `RESTART_DELAY` from environment variables
- **`operator.py`** — `build_manifest()` pure function (strips server metadata/labels from a serialised Job dict), `SERVER_MANAGED_LABELS` frozenset, and `JobRestartOperator` class that monitors K8s Jobs and restarts failed ones after a configurable delay
- **`__main__.py`** — Signal setup, loads config, initialises `JobRestartOperator`, runs the main loop

## Code Style

- **Formatter**: black, line length 120
- **Imports**: isort (`profile = "black"`, `line_length = 120` in `pyproject.toml`)
- **Type checking**: mypy with strict settings (`disallow_untyped_defs`, `check_untyped_defs`)
- **Tests**: pytest, test files in `tests/`
- All public functions must have type annotations

## Testing

```bash
make tests         # or: pytest .
```

Tests live in `tests/`. The `pytest.ini` config discovers test files via `python_files=tests/*.py`.

- `test_config.py` — `OperatorConfig.from_env()` (defaults, custom values, validation, frozen enforcement)
- `test_operator.py` — `build_manifest()` (metadata stripping, label removal, input immutability, edge cases)
- `JobRestartOperator` methods are **not yet tested** (require K8s API mocking — follow-up task)

## Docker

Kubernetes deployment manifests (RBAC, Deployment) are documented in `README.md` under "Kubernetes Deployment".

Single-stage build on `python:3.14-slim`. Non-root user. Entry point is the console script.

```bash
make docker        # Builds image tagged with version + latest
```

## CI

- `.github/workflows/checkblack.yml` — black --check on push to main + PRs
- `.github/workflows/mypynpytests.yml` — mypy + pytest on push to main + PRs
