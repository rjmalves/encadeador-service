# Epic 03: S3 Integration

> **Epic Owner**: TBD  
> **Duration**: 1 week  
> **Status**: ✅ Complete

## Summary

Add S3 integration layer to replace filesystem operations. This enables the service to run in the new HPC environment where persistent storage is replaced by S3 buckets.

## Business Value

- Enables operation in new HPC cluster
- Aligns with flexibilizador-service architecture
- Better artifact lifecycle management
- Prepares for service unification

## Scope

### Included

- Create `S3Repository` for S3 operations
- Create zip utilities for artifact packaging
- Create temp directory manager
- Create exception hierarchy
- Update Settings with S3 configuration
- Create S3-aware UnitOfWork classes
- Write comprehensive tests with moto

### Excluded

- Modifying API contract (Epic 04)
- Modifying router logic (Epic 04)
- Creating Docker configuration (Epic 05)

## Dependencies

| Type | Dependency | Description |
|------|------------|-------------|
| **Requires** | Epic 01 (Tooling) | pytest, moto for testing |
| **Requires** | Epic 02 (Legacy) | Clean codebase |
| **Enables** | Epic 04 (API) | S3 infrastructure for new API |

## Acceptance Criteria

- [x] `app/adapters/s3_repository.py` created with download/upload operations
- [x] `app/utils/zip_utils.py` created with extract/create operations
- [x] `app/utils/temp_manager.py` created with lifecycle management
- [x] `app/internal/exceptions.py` created with exception hierarchy
- [x] Settings updated with S3 configuration (region, buckets, etc.)
- [x] S3DecompUnitOfWork and S3NewaveUnitOfWork created
- [x] All S3 operations tested with moto
- [x] Test coverage ≥80% for new code

## Sprint Breakdown

### Sprint 01: Core Infrastructure (3 days) ✅

| Ticket ID | Title | Points | Priority |
|-----------|-------|--------|----------|
| [S3-001](./sprint-01/ticket-001-create-s3-repository.md) | Create S3Repository | 3 | P0 |
| [S3-002](./sprint-01/ticket-002-create-zip-utils.md) | Create zip utilities | 2 | P0 |
| [S3-003](./sprint-01/ticket-003-create-temp-manager.md) | Create temp directory manager | 2 | P0 |
| [S3-004](./sprint-01/ticket-004-create-exceptions.md) | Create exception hierarchy | 1 | P0 |

**Sprint 01 Total**: 8 points

### Sprint 02: Integration (2 days) ✅

| Ticket ID | Title | Points | Priority |
|-----------|-------|--------|----------|
| [S3-005](./sprint-02/ticket-005-update-settings-s3.md) | Update Settings with S3 config | 2 | P0 |
| [S3-006](./sprint-02/ticket-006-create-s3-unitofwork.md) | Create S3UnitOfWork classes | 5 | P0 |
| [S3-007](./sprint-02/ticket-007-s3-repository-tests.md) | Write S3Repository tests | 3 | P0 |

**Sprint 02 Total**: 10 points

## Technical Approach

### File Sources

Copy from flexibilizador-service with minimal modifications:

| Source | Changes Needed |
|--------|---------------|
| `app/adapters/s3_repository.py` | None |
| `app/utils/zip_utils.py` | None |
| `app/utils/temp_manager.py` | None |
| `app/internal/exceptions.py` | Rename base class to `EncadeadorError` |

### New Code

| File | Purpose |
|------|---------|
| `app/services/s3_unitofwork.py` | S3-aware unit of work implementations |
| `tests/unit/test_s3_repository.py` | S3Repository tests with moto |
| `tests/unit/test_zip_utils.py` | Zip utility tests |

### S3 Operations Required

| Operation | Method | Purpose |
|-----------|--------|---------|
| Download file | `download_file(bucket, key)` | Get single artifact |
| Upload file | `upload_file(bucket, key, data)` | Put processed result |
| Check exists | `file_exists(bucket, key)` | Validate artifacts |
| List prefix | `list_objects(bucket, prefix)` | Enumerate artifacts |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| S3 latency | Parallel downloads; local temp storage |
| Large files | Streaming for zip operations |
| Test isolation | moto for all S3 tests |
| Credential management | IAM roles; no hardcoded secrets |

## Files to Reference

| File | Purpose |
|------|---------|
| `/home/rogerio/git/flexibilizador-service/app/adapters/s3_repository.py` | Reference implementation |
| `/home/rogerio/git/flexibilizador-service/app/utils/zip_utils.py` | Reference implementation |
| `/home/rogerio/git/flexibilizador-service/app/utils/temp_manager.py` | Reference implementation |
| `/home/rogerio/git/flexibilizador-service/tests/unit/test_s3_repository.py` | Test patterns |

## Estimated Effort

**Total**: 18 story points / 1 week
**Confidence**: High (copying proven code from flexibilizador)
