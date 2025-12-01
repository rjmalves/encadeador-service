# [TOOL-004] Create uv.lock and verify setup

> **Epic**: [Epic 01: Tooling Modernization](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 1  
> **Priority**: P0

## Context

### Background

Generate the `uv.lock` file for reproducible builds and perform final verification of the complete tooling setup. This is the final ticket in Epic 01.

### Relation to Epic

Final verification ticket. Ensures all tooling works together correctly.

### Current State

`pyproject.toml` exists with all configurations. Need to generate lock file and verify.

## Specification

### Files to Create

**Path**: `uv.lock` (auto-generated)

### Additional File: .dockerignore

Create `.dockerignore` to optimize Docker builds:

```
# Git
.git
.gitignore

# Environment
.env
.env.*
!.env.example

# Virtual environments
.venv
venv

# Python cache
__pycache__
*.pyc
*.pyo
*.pyd
.Python

# Testing
.pytest_cache
.coverage
htmlcov
coverage.xml

# Type checking
.mypy_cache

# Linting
.ruff_cache

# IDE
.idea
.vscode
*.swp
*.swo

# Documentation (not needed in container)
docs

# Tests (not needed in container)
tests

# Development files
*.md
!README.md

# Build artifacts
dist
build
*.egg-info
```

## Acceptance Criteria

- [ ] `uv lock` generates `uv.lock` successfully
- [ ] `uv sync --all-extras` installs all dependencies
- [ ] `uv run pytest` passes all tests
- [ ] `uv run ruff check app/` runs
- [ ] `uv run mypy app/` runs
- [ ] `.dockerignore` created
- [ ] Old requirements files deleted and committed

## Implementation Guide

### Step 1: Generate lock file

```bash
cd /home/rogerio/git/encadeador-service

# Generate lock file
uv lock

# Verify it was created
ls -la uv.lock
```

### Step 2: Full sync

```bash
# Install all dependencies (production + dev)
uv sync --all-extras
```

### Step 3: Complete verification

```bash
# Run all verification steps
echo "=== Pytest ==="
uv run pytest tests/ -v

echo "=== Coverage ==="
uv run pytest tests/ --cov=app --cov-report=term-missing

echo "=== Ruff Check ==="
uv run ruff check app/ || true

echo "=== Ruff Format ==="
uv run ruff format app/ --check || true

echo "=== Mypy ==="
uv run mypy app/ || true

echo "=== Import Check ==="
uv run python -c "
from app.app import make_app
from app.internal.settings import Settings
from app.adapters.chainingrepository import factory
print('All imports successful!')
"
```

### Step 4: Create .dockerignore

Create the file with content specified above.

### Step 5: Cleanup old files

```bash
# Remove old requirements files
rm -f requirements.txt dev-requirements.txt

# Verify deletion
ls requirements.txt dev-requirements.txt 2>&1 | grep "No such file"
```

### Step 6: Commit

```bash
git add pyproject.toml uv.lock .dockerignore
git rm requirements.txt dev-requirements.txt 2>/dev/null || true
git commit -m "chore: migrate to pyproject.toml and uv

- Add pyproject.toml with all dependencies
- Configure ruff for linting
- Configure mypy for type checking
- Configure pytest with coverage
- Add .dockerignore for build optimization
- Remove legacy requirements.txt files"
```

## Files to Read Before Starting

- `pyproject.toml` - Complete configuration
- All TOOL-00X tickets - Previous work

## Testing Requirements

### Full Verification Script

```bash
#!/bin/bash
set -e

echo "=== Tooling Migration Verification ==="

cd /home/rogerio/git/encadeador-service

echo "1. Lock file exists"
test -f uv.lock && echo "✓ uv.lock exists"

echo "2. Dependencies sync"
uv sync --all-extras && echo "✓ Dependencies installed"

echo "3. Tests pass"
uv run pytest tests/ -v && echo "✓ Tests pass"

echo "4. Ruff runs"
uv run ruff check app/ > /dev/null 2>&1 || true
echo "✓ Ruff runs (issues may exist)"

echo "5. Mypy runs"
uv run mypy app/ > /dev/null 2>&1 || true
echo "✓ Mypy runs (errors may exist)"

echo "6. Application imports work"
uv run python -c "from app.app import make_app; print('✓ Imports work')"

echo "7. Old files removed"
test ! -f requirements.txt && echo "✓ requirements.txt removed"
test ! -f dev-requirements.txt && echo "✓ dev-requirements.txt removed"

echo "8. .dockerignore exists"
test -f .dockerignore && echo "✓ .dockerignore exists"

echo ""
echo "=== All verifications passed! ==="
```

## Definition of Done

- [ ] `uv.lock` generated and committed
- [ ] `.dockerignore` created and committed
- [ ] All tests pass with uv run pytest
- [ ] Ruff and mypy run without crashes
- [ ] Application imports work
- [ ] Old requirements files deleted
- [ ] All changes committed with descriptive message
- [ ] PR merged to main branch

## Blocked By

- [TOOL-001](./ticket-001-create-pyproject-toml.md)
- [TOOL-002](./ticket-002-configure-ruff-mypy.md)
- [TOOL-003](./ticket-003-setup-pytest-coverage.md)

## Blocks

- [Epic 02: Legacy Code Cleanup](../../epic-02-legacy-cleanup/00-epic-overview.md)
