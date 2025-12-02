# Encadeador Service

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Service for chaining DECOMP and NEWAVE case results. Part of the HPC simulation services.

## Overview

The encadeador-service chains variables (VARM, TVIAGEM, GNL) from source case(s) to a destination case, enabling iterative simulation workflows. It works alongside the [flexibilizador-service](https://github.com/rjmalves/flexibilizador-service).

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
git clone https://github.com/rjmalves/encadeador-service
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
curl -X POST http://localhost:8001/chain/ \
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
  "result": [
    {"id": "TUCURUI", "value": 45.5},
    {"id": "SOBRADINHO", "value": 32.1}
  ],
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
| `DECOMP_SOURCE` | Source mode (S3 or FS) | S3 |
| `NEWAVE_SOURCE` | Source mode (S3 or FS) | S3 |

See [.env.example](.env.example) for all variables.

## Documentation

- [Deployment Guide](docs/DEPLOYMENT.md) - Docker and systemd deployment
- [Migration Guide](docs/MIGRATION.md) - Migrating from v1.x to v2.0
- [API Documentation](http://localhost:8001/docs) - OpenAPI/Swagger (when running)
- [CHANGELOG](CHANGELOG.md) - Version history

## Development

### Setup

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run locally
uv run uvicorn main:app --reload --port 8001
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
│   ├── services/       # Business logic (UnitOfWork)
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

## Chained Variables

The following variables can be chained between model executions:

| Variable | Source | Destination | Description |
| -------- | ------ | ----------- | ----------- |
| `VARM` | DECOMP | DECOMP, NEWAVE | Reservoir volumes |
| `TVIAGEM` | DECOMP | DECOMP | Water travel times |
| `GNL` | DECOMP | DECOMP | GNL dispatch |
| `ENA` | (deprecated) | - | Energy inflow forecast |

### VARM (Reservoir Volumes)

Chains initial reservoir volumes from source to destination case. Supports DECOMP → DECOMP and DECOMP → NEWAVE chaining. Handles special cases like Serra da Mesa and Ilha Solteira equivalent representations.

### TVIAGEM (Water Travel Time)

Chains water travel times for Três Marias (156) and Queimado (162) plants. Only supported for DECOMP → DECOMP.

### GNL (GNL Dispatch)

Chains GNL thermal plant dispatch schedules. Only supported for DECOMP → DECOMP.

## Related Services

- [flexibilizador-service](https://github.com/rjmalves/flexibilizador-service) - Flexibilization service
- Both services will be unified in a future release

## License

[MIT License](LICENSE)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## Support

- File issues at [GitHub Issues](https://github.com/rjmalves/encadeador-service/issues)
- Check [Deployment Guide](docs/DEPLOYMENT.md) for troubleshooting