# [DOCKER-004] Update .env.example

> **Epic**: [Epic 05: Docker & Deployment](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 1  
> **Priority**: P1

## Context

### Background

The `.env.example` file documents all environment variables used by the application. With S3 integration and Docker deployment, new variables need to be documented.

### Relation to Epic

Ensures developers and operators know all configuration options.

### Current State

May have outdated or incomplete environment variables.

## Specification

### File to Update/Create

**Path**: `.env.example`

### Complete Environment Variables

```bash
# =============================================================================
# Encadeador Service Configuration
# =============================================================================
# Copy this file to .env and customize for your environment
# 
# For Docker: docker-compose.yml reads from .env automatically
# For systemd: Copy values to /etc/encadeador/environment
# =============================================================================

# -----------------------------------------------------------------------------
# Application Settings
# -----------------------------------------------------------------------------

# Application version (used in logging and health responses)
APP_VERSION=2.0.0

# Server host and port
HOST=0.0.0.0
PORT=8000

# Root path for reverse proxy (e.g., /encadeador)
ROOT_PATH=/

# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Cluster ID (for multi-instance deployments)
CLUSTER_ID=0

# -----------------------------------------------------------------------------
# AWS Configuration
# -----------------------------------------------------------------------------

# AWS region for S3 operations
AWS_REGION=us-east-1

# Custom S3 endpoint (for LocalStack/MinIO development)
# Leave empty for production AWS S3
S3_ENDPOINT_URL=

# AWS credentials (prefer IAM roles in production)
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=

# -----------------------------------------------------------------------------
# S3 Bucket Configuration
# -----------------------------------------------------------------------------

# Default bucket for DECOMP artifacts
DEFAULT_DECOMP_BUCKET=decomp-bucket

# Default bucket for NEWAVE artifacts
DEFAULT_NEWAVE_BUCKET=newave-bucket

# S3 path prefixes
S3_ARTIFACTS_PREFIX=artifacts
S3_INGEST_PREFIX=ingest

# -----------------------------------------------------------------------------
# Data Source Configuration
# -----------------------------------------------------------------------------

# Source mode for DECOMP: S3 or FS (filesystem)
DECOMP_SOURCE=S3

# Source mode for NEWAVE: S3 or FS (filesystem)
NEWAVE_SOURCE=S3

# URI parsing pattern (for legacy mode): BASE62 or PLAIN
URI_PATTERN=BASE62

# -----------------------------------------------------------------------------
# Processing Configuration
# -----------------------------------------------------------------------------

# Temporary directory for file processing
TEMP_DIR=/tmp/encadeador

# Maximum age of temp directories before cleanup (hours)
MAX_TEMP_DIR_AGE_HOURS=24

# Zip compression level (0-9, higher = smaller files but slower)
ZIP_COMPRESSION_LEVEL=6

# -----------------------------------------------------------------------------
# Legacy Settings (for filesystem mode)
# -----------------------------------------------------------------------------

# Base directory for filesystem operations
# APP_BASEDIR=/path/to/data

# Install directory for binaries
# APP_INSTALLDIR=/usr/local/bin
```

### Environment Variable Reference

| Variable | Purpose | Default | Required |
|----------|---------|---------|----------|
| `APP_VERSION` | Version identifier | 2.0.0 | No |
| `HOST` | Server bind address | 0.0.0.0 | No |
| `PORT` | Server port | 8000 | No |
| `ROOT_PATH` | API root path | / | No |
| `LOG_LEVEL` | Logging verbosity | INFO | No |
| `AWS_REGION` | AWS region | us-east-1 | For S3 |
| `S3_ENDPOINT_URL` | Custom S3 endpoint | (empty) | For dev |
| `DEFAULT_DECOMP_BUCKET` | DECOMP bucket | decomp-bucket | For S3 |
| `DEFAULT_NEWAVE_BUCKET` | NEWAVE bucket | newave-bucket | For S3 |
| `DECOMP_SOURCE` | DECOMP mode | S3 | No |
| `NEWAVE_SOURCE` | NEWAVE mode | S3 | No |
| `TEMP_DIR` | Temp directory | /tmp/encadeador | No |
| `MAX_TEMP_DIR_AGE_HOURS` | Temp cleanup age | 24 | No |
| `ZIP_COMPRESSION_LEVEL` | Compression level | 6 | No |

### Configuration Modes

#### Production (AWS S3)

```bash
AWS_REGION=us-east-1
DEFAULT_DECOMP_BUCKET=prod-decomp-bucket
DEFAULT_NEWAVE_BUCKET=prod-newave-bucket
DECOMP_SOURCE=S3
NEWAVE_SOURCE=S3
LOG_LEVEL=INFO
```

#### Development (LocalStack)

```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
S3_ENDPOINT_URL=http://localhost:4566
DEFAULT_DECOMP_BUCKET=decomp-bucket
DEFAULT_NEWAVE_BUCKET=newave-bucket
DECOMP_SOURCE=S3
NEWAVE_SOURCE=S3
LOG_LEVEL=DEBUG
```

#### Legacy (Filesystem)

```bash
DECOMP_SOURCE=FS
NEWAVE_SOURCE=FS
APP_BASEDIR=/path/to/data
URI_PATTERN=BASE62
LOG_LEVEL=INFO
```

## Acceptance Criteria

- [x] `.env.example` created/updated with all variables
- [x] Variables grouped by category
- [x] Comments explain each variable
- [x] Default values documented
- [x] Configuration modes documented
- [x] No actual secrets in file

## Implementation Guide

### Step 1: Create/Update .env.example

Replace or update `.env.example` with the content above.

### Step 2: Verify all variables used

Search codebase for `os.getenv` and `Settings.` to ensure all variables documented:

```bash
grep -r "os.getenv" app/
grep -r "Settings\." app/
```

### Step 3: Test with example values

```bash
cp .env.example .env
# Start service to verify defaults work
docker compose -f docker-compose.dev.yml up
```

## Files to Read Before Starting

- `app/internal/settings.py` - Settings class
- `docker-compose.yml` - Production compose
- `docker-compose.dev.yml` - Dev compose
- `deploy/environment.template` - systemd environment

## Definition of Done

- [x] .env.example complete and accurate
- [x] All variables from Settings documented
- [x] Comments for each variable
- [x] Example configurations documented
- [x] No secrets in file
- [x] Changes committed

## Blocked By

- [S3-005](../../epic-03-s3-integration/sprint-02/ticket-005-update-settings-s3.md) - S3 settings

## Blocks

- [DOCS-002](../../epic-06-documentation/sprint-01/ticket-002-create-deployment-guide.md) - Deployment guide
