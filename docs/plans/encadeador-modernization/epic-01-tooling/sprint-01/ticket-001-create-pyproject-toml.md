# [TOOL-001] Create pyproject.toml

> **Epic**: [Epic 01: Tooling Modernization](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 2  
> **Priority**: P0 (Blocker)

## Context

### Background

The encadeador-service currently uses legacy `requirements.txt` and `dev-requirements.txt` files for dependency management. Modern Python projects use `pyproject.toml` (PEP 517/518/621) which provides:
- Single source of truth for project metadata and dependencies
- Tool configuration in one file (ruff, mypy, pytest, coverage)
- Compatibility with modern package managers like `uv`

### Relation to Epic

This is the foundational ticket for Epic 01. All subsequent tooling tickets depend on this file existing.

### Current State

```
encadeador-service/
├── requirements.txt         # Production deps (9 packages)
├── dev-requirements.txt     # Dev deps (unknown)
└── (no pyproject.toml)
```

## Specification

### File to Create

**Path**: `pyproject.toml` (repository root)

### Content

```toml
[project]
name = "encadeador-service"
version = "2.0.0"
description = "Chaining service for DECOMP/NEWAVE model variables"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
authors = [
    { name = "Rogerio Alves" }
]
keywords = ["decomp", "newave", "chaining", "hpc", "energy"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Framework :: FastAPI",
    "Topic :: Scientific/Engineering",
]

dependencies = [
    "python-dotenv>=1.0.0",
    "fastapi[standard]>=0.115.0",
    "pyarrow>=14.0.0",
    "requests>=2.31.0",
    "aiohttp>=3.9.0",
    "inewave>=0.0.80",
    "idecomp>=0.0.64",
    "pandas>=2.0.0",
    "boto3>=1.34.0",
    "botocore>=1.34.0",
]

[project.optional-dependencies]
dev = [
    "mypy>=1.8.0",
    "ruff>=0.4.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "moto[s3]>=5.0.0",
    "httpx>=0.27.0",
    "boto3-stubs[essential]>=1.34.0",
]

[project.urls]
Homepage = "https://github.com/rjmalves/encadeador-service"
Documentation = "https://github.com/rjmalves/encadeador-service#readme"
Repository = "https://github.com/rjmalves/encadeador-service"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]
```

### Dependency Mapping

| From requirements.txt | To pyproject.toml | Notes |
|----------------------|-------------------|-------|
| `python-dotenv` | `python-dotenv>=1.0.0` | Environment loading |
| `fastapi[all]` | `fastapi[standard]>=0.115.0` | Changed from `all` to `standard` |
| `pyarrow` | `pyarrow>=14.0.0` | Data serialization |
| `requests` | `requests>=2.31.0` | HTTP client |
| `aiohttp` | `aiohttp>=3.9.0` | Async HTTP |
| `inewave` | `inewave>=0.0.80` | NEWAVE file parsing |
| `idecomp` | `idecomp>=0.0.64` | DECOMP file parsing |
| `pandas` | `pandas>=2.0.0` | Data manipulation |
| `pybase62` | (REMOVED) | Legacy URI encoding |
| (NEW) | `boto3>=1.34.0` | AWS S3 SDK |
| (NEW) | `botocore>=1.34.0` | AWS core |

### Files to Delete (after verification)

- `requirements.txt`
- `dev-requirements.txt`

## Acceptance Criteria

- [ ] `pyproject.toml` exists at repository root
- [ ] All production dependencies from `requirements.txt` are present (except pybase62)
- [ ] `boto3` and `botocore` added for future S3 work
- [ ] Dev dependencies include: mypy, ruff, pytest, pytest-asyncio, pytest-cov, moto, httpx
- [ ] `uv sync` succeeds without errors
- [ ] Application imports work: `python -c "from app.app import make_app; print('OK')"`

## Implementation Guide

### Step 1: Create pyproject.toml

Create the file with content above.

### Step 2: Verify with uv

```bash
cd /home/rogerio/git/encadeador-service

# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync --all-extras

# Verify imports work
uv run python -c "from app.app import make_app; print('OK')"
```

### Step 3: Run existing tests

```bash
uv run pytest tests/ -v
```

### Step 4: Delete old files (only after tests pass)

```bash
rm requirements.txt dev-requirements.txt
```

## Files to Read Before Starting

- `requirements.txt` - Current production dependencies
- `dev-requirements.txt` - Current dev dependencies (if exists)
- `/home/rogerio/git/flexibilizador-service/pyproject.toml` - Reference implementation

## Testing Requirements

### Verification Tests

```bash
# 1. Dependencies install correctly
uv sync --all-extras

# 2. Application can start
uv run python -c "from app.app import make_app; print(make_app())"

# 3. Existing tests pass
uv run pytest tests/ -v

# 4. Key imports work
uv run python -c "import boto3; import fastapi; import pandas; print('All imports OK')"
```

## Definition of Done

- [ ] `pyproject.toml` created with correct content
- [ ] `uv sync --all-extras` succeeds
- [ ] All existing tests pass
- [ ] Application starts correctly
- [ ] Old requirements files deleted
- [ ] Changes committed to git

## Blocked By

None (first ticket)

## Blocks

- [TOOL-002](./ticket-002-configure-ruff-mypy.md) - Needs pyproject.toml for tool config
- [TOOL-003](./ticket-003-setup-pytest-coverage.md) - Needs pyproject.toml for pytest config
- [TOOL-004](./ticket-004-create-uv-lock.md) - Needs pyproject.toml to generate lock
