# [DOCS-001] Create Migration Guide

> **Epic**: [Epic 06: Documentation](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 3  
> **Priority**: P0

## Context

### Background

The migration guide helps API consumers and operators transition from v1.x (filesystem-based) to v2.0 (S3-based). It documents API changes, environment changes, and provides a rollback plan.

### Relation to Epic

Critical documentation for adoption of v2.0.

### Current State

No migration documentation exists.

## Specification

### File to Create

**Path**: `docs/MIGRATION.md`

### Migration Guide Content

```markdown
# Migration Guide: v1.x to v2.0

This guide covers migrating the encadeador-service from v1.x (filesystem-based) to v2.0 (S3-based).

## Overview of Changes

### What's New in v2.0

1. **S3 Integration**: Artifacts are read from and written to S3 buckets
2. **Docker Deployment**: Containerized deployment replaces PM2
3. **Health Endpoints**: Container-ready health checks
4. **Structured Errors**: Machine-readable error responses
5. **Updated API**: New request format with bucket/execution_hash

### What's Removed

1. **Base62 ID encoding** (deprecated, still supported)
2. **Direct filesystem access** (optional, for legacy compatibility)
3. **PM2 process management** (replaced by Docker/systemd)

## API Changes

### Request Format

#### v1.x Format (Deprecated)

```json
{
  "sources": [
    {"id": "2cA3xY...", "program": "DECOMP"}
  ],
  "destination": {
    "id": "4dB5zW...",
    "program": "DECOMP"
  },
  "variable": "VARM"
}
```

#### v2.0 Format (Recommended)

```json
{
  "sources": [
    {
      "program": "DECOMP",
      "bucket": "decomp-bucket",
      "execution_hash": "abc123def456"
    }
  ],
  "destination": {
    "program": "DECOMP",
    "bucket": "decomp-bucket",
    "execution_hash": "xyz789ghi012"
  },
  "variable": "VARM"
}
```

### Response Format

#### v1.x Response

```json
{
  "result": [...]
}
```

#### v2.0 Response

```json
{
  "result": [...],
  "output_key": "ingest/xyz789ghi012_encadeado.zip",
  "output_bucket": "decomp-bucket"
}
```

### Error Response Format

#### v1.x Errors

```json
{
  "detail": "Error message as string"
}
```

#### v2.0 Errors

```json
{
  "error": {
    "error_code": "ARTIFACT_NOT_FOUND",
    "message": "Human readable message",
    "details": {"bucket": "...", "key": "..."}
  },
  "request_id": "req-abc123"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `ARTIFACT_NOT_FOUND` | 404 | S3 object not found |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `PARSE_ERROR` | 422 | File parsing failed |
| `S3_ERROR` | 500 | S3 operation failed |
| `CHAINING_ERROR` | 500 | Chaining processing failed |
| `INTERNAL_ERROR` | 500 | Unexpected error |

## Environment Changes

### New Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `AWS_REGION` | AWS region | us-east-1 |
| `S3_ENDPOINT_URL` | Custom S3 endpoint | (empty) |
| `DEFAULT_DECOMP_BUCKET` | DECOMP bucket | decomp-bucket |
| `DEFAULT_NEWAVE_BUCKET` | NEWAVE bucket | newave-bucket |
| `DECOMP_SOURCE` | Source mode (S3/FS) | S3 |
| `NEWAVE_SOURCE` | Source mode (S3/FS) | S3 |
| `TEMP_DIR` | Temp directory | /tmp/encadeador |

### Deprecated Environment Variables

| Variable | Replacement |
|----------|-------------|
| `APP_BASEDIR` | Use S3 buckets instead |
| `URI_PATTERN` | Use bucket+execution_hash |

## S3 Artifact Structure

### Expected S3 Layout

```
{bucket}/
├── artifacts/
│   └── {execution_hash}/
│       ├── entradas/
│       │   └── deck_processado.zip
│       └── saidas/
│           ├── relato.{ext}
│           └── relgnl.{ext}
└── ingest/
    └── {execution_hash}_encadeado.zip
```

### Artifact Requirements

- **Source artifacts**: Must have output files (relato, relgnl) in `saidas/`
- **Destination artifacts**: Must have `deck_processado.zip` in `entradas/`
- **Output**: Written to `ingest/` prefix

## Migration Steps

### Step 1: Update Environment

Add new environment variables while keeping legacy ones for transition:

```bash
# New variables
AWS_REGION=us-east-1
DEFAULT_DECOMP_BUCKET=decomp-bucket
DEFAULT_NEWAVE_BUCKET=newave-bucket

# Transition: Support both modes
DECOMP_SOURCE=S3  # or FS for legacy
NEWAVE_SOURCE=S3  # or FS for legacy
```

### Step 2: Prepare S3 Buckets

Create buckets and upload artifacts in expected structure.

### Step 3: Update API Clients

Update clients to use new request format:

```python
# Before
request = {
    "sources": [{"id": "2cA3xY...", "program": "DECOMP"}],
    "destination": {"id": "4dB5zW...", "program": "DECOMP"},
    "variable": "VARM"
}

# After
request = {
    "sources": [{
        "program": "DECOMP",
        "bucket": "decomp-bucket",
        "execution_hash": "abc123"
    }],
    "destination": {
        "program": "DECOMP",
        "bucket": "decomp-bucket",
        "execution_hash": "def456"
    },
    "variable": "VARM"
}
```

### Step 4: Update Error Handling

Update clients to handle new error format:

```python
response = requests.post(url, json=request)
if not response.ok:
    error = response.json()
    error_code = error.get("error", {}).get("error_code")
    if error_code == "ARTIFACT_NOT_FOUND":
        # Handle missing artifact
        pass
```

### Step 5: Deploy v2.0

Deploy using Docker Compose or systemd service.

### Step 6: Monitor

- Check health endpoints: `/health`, `/health/ready`
- Monitor logs for errors
- Verify S3 connectivity

## Rollback Plan

If migration fails, rollback to v1.x:

1. Stop v2.0 container
2. Restore v1.x deployment with PM2
3. Revert client changes to use base62 IDs
4. Set `DECOMP_SOURCE=FS` and `NEWAVE_SOURCE=FS`

## Compatibility Mode

v2.0 supports legacy mode for gradual migration:

```bash
# Use filesystem mode
DECOMP_SOURCE=FS
NEWAVE_SOURCE=FS
URI_PATTERN=BASE62
```

Clients can continue using base62 IDs until fully migrated.

## Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| 1 | 1 week | Deploy v2.0 with legacy mode |
| 2 | 2 weeks | Migrate clients to new format |
| 3 | 1 week | Disable legacy mode |

## Support

For migration assistance:
- Check logs: `journalctl -u encadeador -f`
- Health check: `curl http://localhost:8001/health/ready`
- File issues at [repository URL]
```

## Acceptance Criteria

- [x] Migration guide created at `docs/MIGRATION.md`
- [x] API changes documented
- [x] Environment changes documented
- [x] S3 artifact structure documented
- [x] Step-by-step migration process
- [x] Rollback plan included
- [x] Compatibility mode explained

## Implementation Guide

### Step 1: Create docs directory

```bash
mkdir -p docs
```

### Step 2: Create MIGRATION.md

Create the file with content above.

### Step 3: Review for accuracy

- Verify API changes match implementation
- Verify environment variables match Settings
- Test example requests

## Files to Read Before Starting

- `app/models/chainingcase.py` - New request format
- `app/models/errors.py` - Error response format
- `app/internal/settings.py` - Environment variables
- `/home/rogerio/git/flexibilizador-service/docs/MIGRATION.md` - Reference

## Definition of Done

- [x] Migration guide created
- [x] All sections complete
- [x] Examples accurate
- [x] Rollback plan included
- [x] Changes committed

## Blocked By

- [API-001](../../epic-04-api-modernization/sprint-01/ticket-001-update-models.md) - Final API format ✅
- [DOCKER-001](../../epic-05-docker/sprint-01/ticket-001-create-dockerfile.md) - Deployment method ✅

## Blocks

- [DOCS-003](./ticket-003-update-readme.md) - README references migration guide
