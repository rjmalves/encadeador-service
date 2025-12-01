# Changelog

All notable changes to the encadeador-service will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2024-12-01

### Added

- **S3 Integration**: Full support for reading artifacts from and writing results to S3
  - `S3Repository` for S3 operations with proper error handling
  - `S3DecompUnitOfWork` and `S3NewaveUnitOfWork` for S3-aware processing
  - Configurable buckets via environment variables (`DEFAULT_DECOMP_BUCKET`, `DEFAULT_NEWAVE_BUCKET`)
  - LocalStack support for development (`S3_ENDPOINT_URL`)
  
- **Docker Deployment**: Containerized deployment
  - Multi-stage Dockerfile with uv package manager
  - docker-compose.yml for production
  - docker-compose.dev.yml with LocalStack for development
  - systemd service files for server deployment
  
- **Health Endpoints**: Container-ready health checks
  - `GET /health` - Overall health status with version and checks
  - `GET /health/live` - Liveness probe for container orchestration
  - `GET /health/ready` - Readiness probe with dependency checks (S3, temp dir)
  
- **Structured Error Responses**: Machine-readable errors
  - Error codes: `ARTIFACT_NOT_FOUND`, `PARSE_ERROR`, `S3_ERROR`, `CHAINING_ERROR`, `VALIDATION_ERROR`
  - Request IDs for tracing
  - Detailed error information with context

- **New API Format**: Cleaner request/response models
  - `bucket` and `execution_hash` parameters (replacing base62 IDs)
  - `output_key` and `output_bucket` in response
  - OpenAPI documentation with examples

- **Development Tooling**:
  - pyproject.toml with uv for dependency management (10-100x faster than pip)
  - ruff for linting and formatting
  - mypy for type checking
  - pytest with coverage

- **Utilities**:
  - `zip_utils.py` - Zip archive operations
  - `temp_manager.py` - Temporary directory lifecycle management

- **Documentation**:
  - Migration guide (v1.x to v2.0)
  - Deployment guide
  - Updated README

### Changed

- **Configuration**: Environment variables reorganized
  - New S3-related variables
  - Source mode configuration (`DECOMP_SOURCE`, `NEWAVE_SOURCE`) - choose between S3 or FS
  - See `.env.example` for complete list

- **Error Handling**: Improved exception hierarchy
  - `EncadeadorException` base class
  - Specific exceptions for S3, parsing, validation, chaining errors
  - Consistent HTTP status codes

- **Default Port**: Changed from 5053 to 8000 (internal), 8001 (external mapping)

### Deprecated

- **Base62 ID Format**: Legacy `id` field in requests
  - Still supported for backward compatibility when using filesystem mode
  - Use `bucket` + `execution_hash` instead

- **Filesystem Mode**: Direct filesystem access
  - Still available via `DECOMP_SOURCE=FS` and `NEWAVE_SOURCE=FS`
  - S3 mode is recommended for new deployments

### Removed

- PM2 process management (replaced by Docker/systemd)
- Unused encoding utilities (`app/utils/encoding.py`)
- Legacy terminal utilities (`app/internal/terminal.py`, `app/utils/terminal.py`)
- Unused filesystem context manager (`app/internal/fs.py`)

### Fixed

- Improved error messages for missing artifacts
- Better handling of S3 connection failures
- Temp directory cleanup on process exit

### Security

- Container runs as non-root user (UID 1000)
- No hardcoded credentials
- IAM role support for AWS credentials

## [1.x.x] - Previous Releases

Previous versions used filesystem-based storage and PM2 for process management.
See git history for detailed changes.

### Supported Chaining Variables

- **VARM**: Reservoir volumes (DECOMP → DECOMP, DECOMP → NEWAVE)
- **TVIAGEM**: Water travel times (DECOMP → DECOMP)
- **GNL**: GNL dispatch (DECOMP → DECOMP)
- **ENA**: Energy inflow forecast (deprecated)

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
