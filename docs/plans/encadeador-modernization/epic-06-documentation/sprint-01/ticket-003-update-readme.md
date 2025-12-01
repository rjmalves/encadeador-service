# [DOCS-003] Update README

> **Epic**: [Epic 06: Documentation](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 2  
> **Priority**: P0

## Context

### Background

The README is the entry point for developers and operators. It needs to reflect the v2.0 architecture with Docker deployment and S3 integration.

### Relation to Epic

First document users see; must accurately represent v2.0.

### Current State

README may be outdated or missing v2.0 features.

## Specification

### File to Update

**Path**: `README.md`

### README Content

```markdown
# Encadeador Service

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Service for chaining DECOMP and NEWAVE cases. Part of the HPC simulation services.

## Overview

The encadeador-service chains variables (VARM, etc.) from source case(s) to a destination case, enabling iterative simulation workflows. It works alongside the [flexibilizador-service](https://github.com/your-org/flexibilizador-service).

### Features

- **S3 Integration**: Read artifacts from and write results to S3
- **Docker Deployment**: Containerized with health checks
- **Structured Errors**: Machine-readable error responses
- **Legacy Support**: Backward compatible with filesystem mode

## Quick Start

### Prerequisites

- Docker and Docker Compose
- AWS credentials (for S3 mode)

### Start with Docker Compose

```bash
# Clone repository
git clone https://github.com/your-org/encadeador-service.git
cd encadeador-service

# Configure environment
cp .env.example .env
vim .env  # Set AWS credentials and buckets

# Start service
docker compose up -d

# Verify
curl http://localhost:8001/health
```

### Start for Development

```bash
# Start with LocalStack (S3 mock)
docker compose -f docker-compose.dev.yml up -d

# Service available at http://localhost:8001
# LocalStack S3 at http://localhost:4566
```

## API Usage

### Chain Variables

```bash
curl -X POST http://localhost:8001/chain \
  -H "Content-Type: application/json" \
  -d '{
    "sources": [{
      "program": "DECOMP",
      "bucket": "decomp-bucket",
      "execution_hash": "source123"
    }],
    "destination": {
      "program": "DECOMP",
      "bucket": "decomp-bucket",
      "execution_hash": "dest456"
    },
    "variable": "VARM"
  }'
```

### Response

```json
{
  "result": [...],
  "output_key": "ingest/dest456_encadeado.zip",
  "output_bucket": "decomp-bucket"
}
```

### Health Check

```bash
curl http://localhost:8001/health
# {"status":"healthy","version":"2.0.0","timestamp":"..."}

curl http://localhost:8001/health/ready
# {"ready":true,"checks":{"temp_dir":true,"s3":true}}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region | us-east-1 |
| `DEFAULT_DECOMP_BUCKET` | DECOMP bucket | decomp-bucket |
| `DEFAULT_NEWAVE_BUCKET` | NEWAVE bucket | newave-bucket |
| `S3_ENDPOINT_URL` | Custom S3 endpoint | - |
| `LOG_LEVEL` | Logging level | INFO |

See [.env.example](.env.example) for all variables.

## Documentation

- [Deployment Guide](docs/DEPLOYMENT.md) - Docker and systemd deployment
- [Migration Guide](docs/MIGRATION.md) - Migrating from v1.x to v2.0
- [API Documentation](http://localhost:8001/docs) - OpenAPI/Swagger (when running)

## Development

### Setup

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run locally
uv run uvicorn app.app:app --reload --port 8001
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific tests
uv run pytest tests/unit/
```

### Linting

```bash
# Check code
uv run ruff check .

# Format code
uv run ruff format .

# Type check
uv run mypy app/
```

## Project Structure

```
encadeador-service/
├── app/
│   ├── adapters/       # Repository implementations
│   ├── internal/       # Settings, exceptions
│   ├── models/         # Pydantic models
│   ├── routers/        # API endpoints
│   ├── services/       # Business logic
│   └── utils/          # Utilities
├── tests/
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
├── deploy/             # Deployment files
├── docs/               # Documentation
├── Dockerfile          # Container definition
├── docker-compose.yml  # Production compose
└── pyproject.toml      # Project configuration
```

## Related Services

- [flexibilizador-service](https://github.com/your-org/flexibilizador-service) - Flexibilization service
- Both services will be unified in a future release

## License

[MIT License](LICENSE)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## Support

- File issues at [GitHub Issues](https://github.com/your-org/encadeador-service/issues)
- Check [Deployment Guide](docs/DEPLOYMENT.md) for troubleshooting
```

## Acceptance Criteria

- [x] README updated with v2.0 content
- [x] Quick start instructions work
- [x] API examples accurate
- [x] Configuration documented
- [x] Links to other docs
- [x] Development instructions
- [x] Project structure documented

## Implementation Guide

### Step 1: Backup existing README

```bash
cp README.md README.md.bak
```

### Step 2: Update README.md

Replace with content above, customizing:
- Repository URLs
- Organization name
- Any project-specific details

### Step 3: Test examples

Run the quick start and API examples to verify accuracy.

### Step 4: Verify links

Ensure all internal links work.

## Files to Read Before Starting

- Current `README.md`
- `docs/MIGRATION.md`
- `docs/DEPLOYMENT.md`
- `/home/rogerio/git/flexibilizador-service/README.md` - Reference

## Definition of Done

- [x] README updated
- [x] All sections complete
- [x] Examples tested
- [x] Links verified
- [x] Changes committed

## Blocked By

- [DOCS-001](./ticket-001-create-migration-guide.md) - Migration guide ✅
- [DOCS-002](./ticket-002-create-deployment-guide.md) - Deployment guide ✅

## Blocks

- None (final documentation task)
