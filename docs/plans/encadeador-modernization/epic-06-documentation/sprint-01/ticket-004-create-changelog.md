# [DOCS-004] Create CHANGELOG

> **Epic**: [Epic 06: Documentation](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 1  
> **Priority**: P1

## Context

### Background

A CHANGELOG documents all notable changes for each release. It helps users understand what changed between versions and is essential for migration planning.

### Relation to Epic

Provides version history for the v2.0 release.

### Current State

No CHANGELOG exists.

## Specification

### File to Create

**Path**: `CHANGELOG.md`

### CHANGELOG Content

```markdown
# Changelog

All notable changes to the encadeador-service will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2024-12-XX

### Added

- **S3 Integration**: Full support for reading artifacts from and writing results to S3
  - `S3Repository` for S3 operations with proper error handling
  - `S3DecompUnitOfWork` and `S3NewaveUnitOfWork` for S3-aware processing
  - Configurable buckets via environment variables
  - LocalStack support for development
  
- **Docker Deployment**: Containerized deployment
  - Multi-stage Dockerfile with uv package manager
  - docker-compose.yml for production
  - docker-compose.dev.yml with LocalStack for development
  - systemd service files for server deployment
  
- **Health Endpoints**: Container-ready health checks
  - `GET /health` - Overall health status
  - `GET /health/live` - Liveness probe
  - `GET /health/ready` - Readiness probe with dependency checks
  
- **Structured Error Responses**: Machine-readable errors
  - Error codes for programmatic handling
  - Request IDs for tracing
  - Detailed error information

- **New API Format**: Cleaner request/response models
  - `bucket` and `execution_hash` parameters (replacing base62 IDs)
  - `output_key` and `output_bucket` in response
  - OpenAPI documentation with examples

- **Development Tooling**:
  - pyproject.toml with uv for dependency management
  - ruff for linting and formatting
  - mypy for type checking
  - pytest with coverage

- **Documentation**:
  - Migration guide (v1.x to v2.0)
  - Deployment guide
  - Updated README

### Changed

- **Configuration**: Environment variables reorganized
  - New S3-related variables
  - Source mode configuration (S3 or FS)
  - See `.env.example` for complete list

- **Error Handling**: Improved exception hierarchy
  - `EncadeadorException` base class
  - Specific exceptions for S3, parsing, validation, chaining errors
  - Consistent HTTP status codes

### Deprecated

- **Base62 ID Format**: Legacy `id` field in requests
  - Still supported for backward compatibility
  - Use `bucket` + `execution_hash` instead

- **Filesystem Mode**: Direct filesystem access
  - Still available via `DECOMP_SOURCE=FS`
  - S3 mode is recommended

### Removed

- PM2 process management (replaced by Docker/systemd)
- Unused encoding utilities
- Legacy terminal utilities

### Fixed

- Improved error messages for missing artifacts
- Better handling of S3 connection failures
- Temp directory cleanup on process exit

### Security

- Container runs as non-root user
- No hardcoded credentials
- IAM role support for AWS credentials

## [1.x.x] - Previous Releases

Previous versions used filesystem-based storage and PM2 for process management.
See git history for detailed changes.

---

## Migration Notes

### v1.x to v2.0

See [docs/MIGRATION.md](docs/MIGRATION.md) for detailed migration instructions.

Key changes:
1. Update API requests to use `bucket` + `execution_hash`
2. Configure S3 environment variables
3. Deploy via Docker instead of PM2

### Rollback

If issues occur after upgrading:
1. Stop v2.0 container
2. Restore v1.x with PM2
3. Set `DECOMP_SOURCE=FS` and `NEWAVE_SOURCE=FS`

---

[Unreleased]: https://github.com/your-org/encadeador-service/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/your-org/encadeador-service/releases/tag/v2.0.0
```

## Acceptance Criteria

- [x] CHANGELOG.md created
- [x] Follows Keep a Changelog format
- [x] All v2.0 changes documented
- [x] Added, Changed, Deprecated, Removed sections
- [x] Migration notes included
- [x] Links to releases (when created)

## Implementation Guide

### Step 1: Create CHANGELOG.md

Create the file in repository root with content above.

### Step 2: Update date

Replace `2024-12-XX` with actual release date.

### Step 3: Verify completeness

Review all commits since v1.x to ensure nothing missed.

### Step 4: Update links

Update GitHub URLs to actual repository.

## Files to Read Before Starting

- Git history for changes
- `docs/MIGRATION.md` - Migration details
- Keep a Changelog specification

## CHANGELOG Guidelines

### Format

Each version section includes:
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Features to be removed
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security-related changes

### Best Practices

- Write for humans, not machines
- Most recent version at top
- Link version headers to release tags
- Include date for each release

## Definition of Done

- [x] CHANGELOG.md created
- [x] All v2.0 changes documented
- [x] Format follows standard
- [x] Links placeholder added
- [x] Changes committed

## Blocked By

- All implementation tickets (to document what changed) ✅

## Blocks

- None (final documentation task)
