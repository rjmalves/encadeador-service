# Epic 01: Tooling Modernization

> **Epic Owner**: TBD  
> **Duration**: 1 day  
> **Status**: ✅ Complete

## Summary

Migrate the project from legacy Python tooling (`requirements.txt`, no linting) to modern development practices matching flexibilizador-service. This establishes the foundation for all subsequent work.

## Business Value

- Faster dependency installation (uv is 10-100x faster than pip)
- Consistent code quality through automated linting
- Type safety through mypy checking
- Aligned with flexibilizador-service for future unification

## Scope

### Included

- Create `pyproject.toml` with all dependencies
- Configure ruff for linting and formatting
- Configure mypy for type checking
- Setup pytest with coverage reporting
- Generate `uv.lock` for reproducible builds
- Remove legacy `requirements.txt` files

### Excluded

- Fixing all existing type errors (address in later epics)
- Adding new tests (separate epic)
- Modifying application code

## Dependencies

| Type | Dependency | Description |
|------|------------|-------------|
| **Requires** | None | First epic in sequence |
| **Enables** | Epic 02 (Legacy Cleanup) | Tooling needed for validation |
| **Enables** | Epic 03 (S3 Integration) | Dev dependencies for testing |

## Acceptance Criteria

- [x] `pyproject.toml` created with production and dev dependencies
- [x] `uv.lock` generated successfully
- [x] `ruff check app/` runs without configuration errors
- [x] `ruff format app/` formats code consistently
- [x] `mypy app/` runs (errors expected but command works)
- [x] `pytest` runs (existing tests have pre-existing issues with FastAPI version compatibility)
- [x] `requirements.txt` and `dev-requirements.txt` deleted
- [x] `.dockerignore` created for build optimization

## Sprint Breakdown

### Sprint 01 (1 day)

| Ticket ID | Title | Points | Priority |
|-----------|-------|--------|----------|
| [TOOL-001](./sprint-01/ticket-001-create-pyproject-toml.md) | Create pyproject.toml | 2 | P0 |
| [TOOL-002](./sprint-01/ticket-002-configure-ruff-mypy.md) | Configure ruff and mypy | 1 | P0 |
| [TOOL-003](./sprint-01/ticket-003-setup-pytest-coverage.md) | Setup pytest with coverage | 1 | P1 |
| [TOOL-004](./sprint-01/ticket-004-create-uv-lock.md) | Create uv.lock and verify | 1 | P0 |

**Sprint Total**: 5 points

## Technical Approach

1. **Reference Implementation**: Copy `pyproject.toml` structure from flexibilizador-service
2. **Dependency Analysis**: Extract dependencies from existing `requirements.txt`
3. **Tool Configuration**: Use same ruff/mypy settings as flexibilizador-service
4. **Validation**: Ensure all existing tests pass after migration

## Files to Reference

| File | Purpose |
|------|---------|
| `/home/rogerio/git/flexibilizador-service/pyproject.toml` | Reference configuration |
| `requirements.txt` | Current production dependencies |
| `dev-requirements.txt` | Current dev dependencies |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Missing dependencies | Compare with working flexibilizador config |
| Test failures after migration | Run tests before deleting old files |
| Version conflicts | Use same versions as flexibilizador where possible |

## Estimated Effort

**Total**: 5 story points / 1 day
**Confidence**: High (straightforward migration with reference implementation)
