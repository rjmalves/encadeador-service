# Epic 04: API Modernization

> **Epic Owner**: TBD  
> **Duration**: 1 week  
> **Status**: ✅ Complete

## Summary

Update the API contract to use S3 buckets and execution hashes instead of base62-encoded filesystem paths. Add health endpoints and structured error responses.

## Business Value

- Clearer, more intuitive API
- Better error handling for consumers
- Health endpoints for orchestration
- Aligned with flexibilizador-service

## Scope

### Included

- Update request/response models for S3
- Create structured error models
- Create health endpoints
- Update chain router for S3 integration
- Add exception handlers
- Write API integration tests

### Excluded

- Modifying core chaining algorithms
- Docker configuration (Epic 05)

## Dependencies

| Type | Dependency | Description |
|------|------------|-------------|
| **Requires** | Epic 03 (S3) | S3Repository, S3UnitOfWork |
| **Enables** | Epic 05 (Docker) | Health endpoints for container |

## Sprint Breakdown

### Sprint 01: Models & Health (2-3 days) ✅

| Ticket ID | Title | Points |
|-----------|-------|--------|
| API-001 | Update request/response models | 3 |
| API-002 | Create structured error models | 2 |
| API-003 | Create health endpoints | 2 |

### Sprint 02: Router & Tests (2-3 days) ✅

| Ticket ID | Title | Points |
|-----------|-------|--------|
| API-004 | Update chain router for S3 | 5 |
| API-005 | Add exception handlers | 2 |
| API-006 | Write API integration tests | 3 |

## Acceptance Criteria

- [x] New request model accepts `bucket` + `execution_hash`
- [x] New response model includes `output_key`
- [x] Health endpoints at `/health`, `/health/live`, `/health/ready`
- [x] Structured error responses with error codes
- [x] OpenAPI docs reflect new contract
- [x] Integration tests with mocked S3
- [x] Old base62 parsing deprecated/removed

## Estimated Effort

**Total**: 17 story points / 1 week
