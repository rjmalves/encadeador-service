# Master Plan: Encadeador Service Modernization

> **Version**: 1.0  
> **Last Updated**: 2024-12-01  
> **Owner**: HPC Team

## Executive Summary

Modernize the encadeador-service from a PM2-managed, filesystem-dependent microservice to a containerized, S3-integrated service deployed via Docker Compose. This mirrors the flexibilizador-service modernization and prepares both services for future unification.

**Business Value**: Enables operation in the new HPC cluster environment where persistent storage is replaced by S3, and aligns with organizational containerization strategy.

## Goals & Non-Goals

### Goals

| # | Goal | Success Criteria |
|---|------|------------------|
| G1 | Replace filesystem with S3 | All file operations use boto3; no direct filesystem access for artifacts |
| G2 | Containerize with Docker | Production-ready image <200MB; health checks passing |
| G3 | Modernize API | S3-based request model; structured error responses |
| G4 | Modernize tooling | pyproject.toml; ruff + mypy; uv package manager |
| G5 | Remove legacy code | Zero encoding conversion code; zero unused utilities |
| G6 | Align with flexibilizador | Same patterns for future unification |

### Non-Goals (Explicit Scope Exclusions)

- **Multi-region deployment**: Single region deployment only
- **Kubernetes**: Docker Compose only (no K8s manifests)
- **Real-time streaming**: Batch processing only
- **Core logic changes**: Chaining algorithms remain unchanged
- **NEWAVE chaining overhaul**: Only adapt existing NEWAVE support for S3

## Architecture Overview

### Current State

```
┌─────────────────────────────────────────────────────────────┐
│                    HPC Head Node                            │
│                                                             │
│  ┌──────────────┐     ┌──────────────────────────────────┐ │
│  │ Express GW   │────►│ encadeador-service (PM2)         │ │
│  │ :80/:443     │     │                                  │ │
│  └──────────────┘     │  POST /chain                     │ │
│                       │  - base62 decode paths           │ │
│                       │  - read from filesystem          │ │
│                       │  - chain variables               │ │
│                       │  - write to filesystem           │ │
│                       └───────────────┬──────────────────┘ │
│                                       │                    │
│                                       ▼                    │
│                       ┌──────────────────────────────────┐ │
│                       │   Shared Filesystem              │ │
│                       │   /cases/decomp/...              │ │
│                       │   /cases/newave/...              │ │
│                       └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

Components:
- Express Gateway: Reverse proxy (ports 80/443)
- encadeador-service: PM2-managed Python/FastAPI
- Shared Filesystem: NFS mount for DECOMP/NEWAVE artifacts
```

### Target State

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HPC Head Node                               │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Docker Compose Stack                      │   │
│  │                                                              │   │
│  │  ┌──────────────┐     ┌────────────────────────────────┐    │   │
│  │  │   Traefik    │────►│   encadeador-service           │    │   │
│  │  │   :80/:443   │     │   (Docker container)           │    │   │
│  │  │              │     │                                │    │   │
│  │  │ /api/v1/chain│     │  POST /chain                   │    │   │
│  │  └──────────────┘     │  - Download from S3            │    │   │
│  │                       │  - Extract to temp dir         │    │   │
│  │                       │  - Chain variables             │    │   │
│  │                       │  - Repack & upload to S3       │────┼───┼──► S3
│  │                       │  - Cleanup temp dir            │    │   │
│  │                       └────────────────────────────────┘    │   │
│  │                                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Components:
- Traefik: Reverse proxy (ports 80/443)
- encadeador-service: Docker container with health checks
- S3: Artifact storage (decomp-bucket, newave-bucket)
- Temp storage: Container tmpfs for processing
```

### S3 Bucket Structure

```
s3://decomp-bucket/
├── artifacts/
│   └── <EXECUTION_HASH>/
│       ├── entradas/
│       │   └── deck_processado.zip      # INPUT: DECOMP deck files
│       │       ├── caso.dat
│       │       ├── dadger.rv0           # Modified by chaining
│       │       ├── dadgnl.rv0           # Modified by chaining
│       │       └── hidr.dat
│       └── saidas/
│           ├── relato.rv0               # SOURCE: Volume data
│           └── relgnl.rv0               # SOURCE: GNL data
│
└── ingest/
    └── <execution_hash>_encadeado.zip   # OUTPUT: Chained deck

s3://newave-bucket/
├── artifacts/
│   └── <EXECUTION_HASH>/
│       ├── entradas/
│       │   └── deck_processado.zip
│       │       ├── caso.dat
│       │       └── confhd.dat           # Modified by chaining
│       └── saidas/
│           └── pmo.dat
│
└── ingest/
    └── <execution_hash>_encadeado.zip   # OUTPUT: Chained deck
```

## Key Design Decisions

| # | Decision | Choice | Alternatives Considered | Rationale |
|---|----------|--------|------------------------|-----------|
| D1 | S3 SDK | boto3 (sync) + ThreadPoolExecutor | aioboto3, boto3 async | Consistency with flexibilizador; proven pattern |
| D2 | Temp storage | Container tmpfs | EFS, host volume | Fast I/O; automatic cleanup on restart |
| D3 | Package manager | uv | pip, poetry | 10-100x faster; matches flexibilizador |
| D4 | Linting | ruff + mypy | flake8 + black | Modern, fast, comprehensive |
| D5 | Container | Docker + Traefik | K8s, bare metal | Existing infrastructure; simpler ops |
| D6 | Health checks | /health/live, /health/ready | Custom metrics | K8s-compatible pattern |

## Technical Approach

### Python Stack

| Component | Version/Library | Purpose |
|-----------|----------------|---------|
| Runtime | Python 3.12 | Latest stable with performance improvements |
| Framework | FastAPI 0.115+ | Async API, OpenAPI docs |
| AWS SDK | boto3 1.34+ | S3 operations |
| Validation | Pydantic 2.0+ | Request/response models |
| Domain | idecomp, inewave | DECOMP/NEWAVE file parsing |

### Code Structure (Target)

```
app/
├── adapters/
│   ├── s3_repository.py           # NEW: S3 operations
│   ├── chainingrepository.py      # KEEP: Core business logic
│   ├── decomprepository.py        # MODIFY: Remove encoding
│   ├── newaverepository.py        # MODIFY: Remove encoding
│   └── uriparserrepository.py     # DEPRECATE: Legacy base62
├── services/
│   ├── unitofwork.py              # MODIFY: Factory pattern
│   └── s3_unitofwork.py           # NEW: S3-aware UoW
├── models/
│   ├── chainingcase.py            # MODIFY: S3 fields
│   ├── chainingrequest.py         # MODIFY: S3 request
│   ├── chainingresponse.py        # MODIFY: Add output_key
│   └── errors.py                  # NEW: Error models
├── routers/
│   ├── chain.py                   # MODIFY: S3 integration
│   └── health.py                  # NEW: Health endpoints
├── internal/
│   ├── settings.py                # MODIFY: S3 config
│   ├── exceptions.py              # NEW: Exception hierarchy
│   ├── httpresponse.py            # KEEP
│   └── dependencies.py            # MODIFY: S3 deps
└── utils/
    ├── zip_utils.py               # NEW: Zip operations
    ├── temp_manager.py            # NEW: Temp dir lifecycle
    ├── log.py                     # KEEP
    └── singleton.py               # KEEP

DELETE:
├── app/internal/fs.py             # Unused context manager
├── app/internal/terminal.py       # Unused terminal utils
├── app/utils/encoding.py          # UTF-8 conversion (obsolete)
└── app/utils/terminal.py          # Duplicate terminal utils
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        POST /chain Request                          │
│  {                                                                  │
│    "variable": "VARM",                                             │
│    "sources": [{"bucket": "decomp-bucket", "execution_hash": "a"}],│
│    "destination": {"bucket": "decomp-bucket", "execution_hash": "b"}│
│  }                                                                  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 1. DOWNLOAD PHASE                                                   │
│    ┌─────────────┐                                                 │
│    │ S3Repository │                                                 │
│    └──────┬──────┘                                                 │
│           │                                                         │
│    For each SOURCE:                                                │
│    ├── Download: artifacts/{hash}/saidas/relato.{ext}              │
│    └── Download: artifacts/{hash}/saidas/relgnl.{ext}              │
│                                                                     │
│    For DESTINATION:                                                │
│    └── Download: artifacts/{hash}/entradas/deck_processado.zip     │
│                                                                     │
│    Extract all to: /tmp/encadeador/{hash}/                         │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. PROCESSING PHASE                                                 │
│    ┌───────────────────────┐                                       │
│    │ ChainingRepository    │                                       │
│    │ (NEWAVEChainingRepo   │                                       │
│    │  or DECOMPChainingRepo)│                                       │
│    └──────────┬────────────┘                                       │
│               │                                                     │
│    Read source files (relato, relgnl, hidr)                        │
│    Read destination files (dadger, confhd, dadgnl)                 │
│    Apply chaining logic:                                           │
│    ├── VARM: Chain reservoir volumes                               │
│    ├── TVIAGEM: Chain travel times                                 │
│    ├── GNL: Chain GNL dispatch                                     │
│    └── ENA: Chain ENA values                                       │
│    Write modified destination files                                │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. UPLOAD PHASE                                                     │
│    ┌─────────────┐                                                 │
│    │ S3Repository │                                                 │
│    └──────┬──────┘                                                 │
│           │                                                         │
│    Create zip: /tmp/encadeador/{hash}_encadeado.zip                │
│    Upload to: s3://{bucket}/ingest/{hash}_encadeado.zip            │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. CLEANUP & RESPONSE                                              │
│                                                                     │
│    Remove temp directory: /tmp/encadeador/{hash}/                  │
│                                                                     │
│    Return:                                                         │
│    {                                                               │
│      "success": true,                                              │
│      "execution_hash": "b",                                        │
│      "output_key": "ingest/b_encadeado.zip",                       │
│      "results": [{"id": "TUCURUI", "value": 45.5}, ...],          │
│      "message": "Chained 15 variables"                            │
│    }                                                               │
└─────────────────────────────────────────────────────────────────────┘
```

## API Contract

### Request (v2.0)

```json
{
  "variable": "VARM | TVIAGEM | GNL | ENA",
  "sources": [
    {
      "bucket": "string (required)",
      "execution_hash": "string (required)",
      "program": "DECOMP | NEWAVE (required)"
    }
  ],
  "destination": {
    "bucket": "string (required)",
    "execution_hash": "string (required)",
    "program": "DECOMP | NEWAVE (required)"
  },
  "output_prefix": "string (optional, default: 'ingest')"
}
```

### Response (v2.0)

```json
{
  "success": true,
  "execution_hash": "string",
  "output_key": "string (S3 key)",
  "results": [
    {"id": "string", "value": "number"}
  ],
  "message": "string (optional)"
}
```

### Error Response

```json
{
  "error_code": "ARTIFACT_NOT_FOUND | PARSE_ERROR | S3_ERROR | CHAINING_ERROR",
  "message": "Human-readable error description",
  "details": { "bucket": "...", "key": "..." }
}
```

### HTTP Status Codes

| Code | Error Code | Description |
|------|------------|-------------|
| 200 | - | Success |
| 400 | INVALID_REQUEST | Malformed request body |
| 404 | ARTIFACT_NOT_FOUND | S3 object not found |
| 422 | PARSE_ERROR | Failed to parse DECOMP/NEWAVE file |
| 500 | S3_ERROR | S3 operation failed |
| 500 | CHAINING_ERROR | Internal processing error |

## Security Architecture

| Aspect | Implementation |
|--------|---------------|
| Authentication | IAM role attached to EC2/container |
| Authorization | S3 bucket policy + IAM role policy |
| Encryption at rest | S3 default encryption (AES-256) |
| Encryption in transit | HTTPS via Traefik TLS termination |
| Network | Docker network isolation |
| Secrets | Environment variables (no hardcoding) |

### IAM Policy (Minimum Required)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EncadeadorS3Access",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::decomp-bucket",
        "arn:aws:s3:::decomp-bucket/*",
        "arn:aws:s3:::newave-bucket",
        "arn:aws:s3:::newave-bucket/*"
      ]
    }
  ]
}
```

## Observability Strategy

### Logging

| Level | Content |
|-------|---------|
| INFO | Request received, S3 operations, chaining results |
| WARNING | Retry attempts, degraded performance |
| ERROR | Failed operations, exceptions |
| DEBUG | Detailed processing steps (dev only) |

### Health Endpoints

| Endpoint | Purpose | Checks |
|----------|---------|--------|
| GET /health | Full status | Version, S3 connectivity, temp dir |
| GET /health/live | Liveness | Process alive |
| GET /health/ready | Readiness | S3 accessible, temp dir writable |

### Metrics (via health endpoint)

- Uptime
- Last request timestamp
- S3 connectivity status
- Temp directory usage

## Environment Configuration

```bash
# Application
HOST=0.0.0.0
PORT=8000
ROOT_PATH=/api/v1/chain
LOG_LEVEL=INFO

# S3 Configuration
AWS_REGION=us-east-1
S3_ENDPOINT_URL=                    # Optional: for MinIO/LocalStack
DEFAULT_DECOMP_BUCKET=decomp-bucket
DEFAULT_NEWAVE_BUCKET=newave-bucket

# Processing
TEMP_DIR=/tmp/encadeador
ZIP_COMPRESSION_LEVEL=6
MAX_TEMP_DIR_AGE_HOURS=24
```

## Phases & Milestones

| Phase | Epic | Duration | Milestone | Dependencies | Status |
|-------|------|----------|-----------|--------------|--------|
| 1 | Tooling Modernization | 1 day | pyproject.toml, ruff, mypy, uv configured | None | ✅ Complete |
| 2 | Legacy Code Cleanup | 1 day | Encoding utils removed, all tests pass | Epic 1 | ✅ Complete |
| 3 | S3 Integration | 1 week | S3Repository, zip utils, S3UnitOfWork working | Epic 1, 2 | ✅ Complete |
| 4 | API Modernization | 1 week | New API contract, health endpoints, error models | Epic 3 | ✅ Complete |
| 5 | Docker & Deployment | 3 days | Production-ready container, systemd service | Epic 4 | ✅ Complete |
| 6 | Documentation | 2 days | Migration guide, deployment guide, CHANGELOG | Epic 5 | ✅ Complete |

**Total Duration**: ~4 weeks

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| S3 latency affects chaining performance | Medium | Medium | Parallel downloads; temp dir on tmpfs |
| idecomp/inewave library incompatibility | Low | High | Pin versions; comprehensive tests |
| Complex multi-source chaining edge cases | Medium | Medium | Integration tests with real fixtures |
| Large zip files cause memory issues | Medium | Medium | Streaming extraction; chunked upload |
| Breaking change affects consumers | High | High | Migration guide; deprecation period |

## Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Test Coverage | ≥60% | pytest-cov report |
| Docker Image Size | <200MB | `docker images` |
| Container Startup | <30s | Health check timing |
| Chaining Latency (typical) | <90s | Application logs |
| API Error Rate | <1% | Error log analysis |
| Zero downtime deployment | Yes | Health check continuity |

## Files to Copy from Flexibilizador

These files can be directly copied or adapted with minimal changes:

| Source File | Destination | Changes Needed |
|-------------|-------------|----------------|
| `app/adapters/s3_repository.py` | Same path | None |
| `app/utils/zip_utils.py` | Same path | None |
| `app/utils/temp_manager.py` | Same path | None |
| `app/internal/exceptions.py` | Same path | Rename base class |
| `app/models/errors.py` | Same path | Update error codes |
| `app/routers/health.py` | Same path | Update version string |
| `Dockerfile` | Same path | Update labels |
| `docker-compose.yml` | Same path | Update service name, ports |
| `pyproject.toml` | Same path | Update metadata |
| `deploy/` | Same path | Update service name |

## Reference Documentation

- [Flexibilizador Master Plan](../../../flexibilizador-service/docs/plans/flexibilizador-modernization/00-master-plan.md)
- [Flexibilizador Migration Guide](../../../flexibilizador-service/docs/MIGRATION.md)
- [Flexibilizador Deployment Guide](../../../flexibilizador-service/docs/DEPLOYMENT.md)
- [boto3 S3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [moto - Mock AWS Services](https://docs.getmoto.org/en/latest/)
