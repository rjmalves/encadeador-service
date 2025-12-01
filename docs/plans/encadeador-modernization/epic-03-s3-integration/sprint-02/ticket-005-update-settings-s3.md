# [S3-005] Update Settings with S3 Configuration

> **Epic**: [Epic 03: S3 Integration](../00-epic-overview.md)  
> **Sprint**: [Sprint 02](./00-sprint-overview.md)  
> **Points**: 2  
> **Priority**: P0  
> **Status**: ✅ Complete

## Context

### Background

The Settings class already has S3 configuration attributes added (from earlier work). This ticket validates the configuration is complete and adds any missing attributes needed for the S3UnitOfWork implementation.

### Relation to Epic

Ensures S3 configuration is complete for all S3 operations.

### Current State

Settings already includes:
- `aws_region`
- `s3_endpoint_url`
- `default_decomp_bucket`
- `default_newave_bucket`
- `temp_dir`
- `zip_compression_level`
- `max_temp_dir_age_hours`

## Specification

### File to Update

**Path**: `app/internal/settings.py`

### Attributes to Verify/Add

```python
class Settings:
    # ... existing settings ...

    # S3 Configuration (verify present)
    aws_region = os.getenv("AWS_REGION", "us-east-1")
    s3_endpoint_url = os.getenv("S3_ENDPOINT_URL", None)
    default_decomp_bucket = os.getenv("DEFAULT_DECOMP_BUCKET", "decomp-bucket")
    default_newave_bucket = os.getenv("DEFAULT_NEWAVE_BUCKET", "newave-bucket")

    # Processing Configuration (verify present)
    temp_dir = os.getenv("TEMP_DIR", "/tmp/encadeador")
    zip_compression_level = int(os.getenv("ZIP_COMPRESSION_LEVEL", "6"))
    max_temp_dir_age_hours = int(os.getenv("MAX_TEMP_DIR_AGE_HOURS", "24"))

    # S3 Path Patterns (NEW - if needed)
    s3_artifacts_prefix = os.getenv("S3_ARTIFACTS_PREFIX", "artifacts")
    s3_ingest_prefix = os.getenv("S3_INGEST_PREFIX", "ingest")
```

### Environment Variables Summary

| Variable | Purpose | Default |
|----------|---------|---------|
| `AWS_REGION` | AWS region for S3 | `us-east-1` |
| `S3_ENDPOINT_URL` | Custom endpoint (LocalStack) | `None` |
| `DEFAULT_DECOMP_BUCKET` | DECOMP artifacts bucket | `decomp-bucket` |
| `DEFAULT_NEWAVE_BUCKET` | NEWAVE artifacts bucket | `newave-bucket` |
| `TEMP_DIR` | Local temp directory | `/tmp/encadeador` |
| `ZIP_COMPRESSION_LEVEL` | Zip compression (0-9) | `6` |
| `MAX_TEMP_DIR_AGE_HOURS` | Temp cleanup age | `24` |
| `S3_ARTIFACTS_PREFIX` | S3 prefix for artifacts | `artifacts` |
| `S3_INGEST_PREFIX` | S3 prefix for outputs | `ingest` |

## Acceptance Criteria

- [ ] All S3-related attributes present in Settings
- [ ] `read_environments()` method updated with all attributes
- [ ] Defaults are sensible for production
- [ ] LocalStack-friendly (endpoint_url support)
- [ ] Type hints added where missing

## Implementation Guide

### Step 1: Verify existing attributes

Review `app/internal/settings.py` and confirm all attributes from specification are present.

### Step 2: Add missing attributes if needed

Add S3 path pattern attributes if not present:

```python
# S3 Path Patterns
s3_artifacts_prefix = os.getenv("S3_ARTIFACTS_PREFIX", "artifacts")
s3_ingest_prefix = os.getenv("S3_INGEST_PREFIX", "ingest")
```

### Step 3: Update read_environments()

Ensure `read_environments()` class method includes all new attributes:

```python
@classmethod
def read_environments(cls):
    # ... existing code ...
    
    # S3 Path Patterns
    cls.s3_artifacts_prefix = os.getenv("S3_ARTIFACTS_PREFIX", "artifacts")
    cls.s3_ingest_prefix = os.getenv("S3_INGEST_PREFIX", "ingest")
```

### Step 4: Validate configuration

Create simple test or run manually:

```python
from app.internal.settings import Settings
Settings.read_environments()
print(f"Region: {Settings.aws_region}")
print(f"DECOMP bucket: {Settings.default_decomp_bucket}")
print(f"Temp dir: {Settings.temp_dir}")
```

## Files to Read Before Starting

- `app/internal/settings.py` - Current Settings implementation
- `/home/rogerio/git/flexibilizador-service/app/internal/settings.py` - Reference

## Testing Requirements

### Manual Verification

- [ ] All attributes accessible via `Settings.attribute_name`
- [ ] Environment variable overrides work
- [ ] `read_environments()` refreshes values

## Definition of Done

- [ ] All S3 attributes present and documented
- [ ] `read_environments()` updated
- [ ] Environment variable names documented
- [ ] Changes committed

## Blocked By

- None (Settings already partially updated)

## Blocks

- [S3-006](./ticket-006-create-s3-unitofwork.md) - UnitOfWork uses Settings
- [S3-007](./ticket-007-s3-repository-tests.md) - Tests may use Settings
