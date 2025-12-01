# Migration Guide: v1.x to v2.0

This guide covers migrating from the filesystem-based v1.x to the S3-based v2.0 architecture.

## Overview of Changes

### API Changes

| Aspect         | v1.x                           | v2.0                        |
| -------------- | ------------------------------ | --------------------------- |
| **Input**      | Base62-encoded filesystem path | S3 bucket + execution_hash  |
| **Endpoint**   | `POST /chain`                  | `POST /chain/`              |
| **Path Field** | `id` (base62 encoded)          | `bucket` + `execution_hash` |
| **Storage**    | Local filesystem               | AWS S3                      |
| **Output**     | Modified files in place        | Uploaded to S3              |

### Request Format

**v1.x Request:**

```json
{
  "sources": [
    {
      "id": "IgMI7zzpD0irzRysgz7ia2z2KbKEIQEpZ2GpEhUvJGvNxpMlD65iC9oeOQ4",
      "program": "DECOMP"
    }
  ],
  "destination": {
    "id": "IgMI7zzpD0irzRysgz7ia2z2KbKEIQEpZ2GpEhUvJGvNxpMlD65lJjqJqsv",
    "program": "NEWAVE"
  },
  "variable": "VARM"
}
```

**v2.0 Request:**

```json
{
  "sources": [
    {
      "bucket": "decomp-bucket",
      "execution_hash": "abc123def456",
      "program": "DECOMP"
    }
  ],
  "destination": {
    "bucket": "decomp-bucket",
    "execution_hash": "xyz789ghi012",
    "program": "DECOMP"
  },
  "variable": "VARM"
}
```

### Response Format

**v1.x Response:**

```json
{
  "result": [
    {"id": "TUCURUI", "value": 45.5}
  ]
}
```

**v2.0 Response:**

```json
{
  "result": [
    {"id": "TUCURUI", "value": 45.5}
  ],
  "output_key": "ingest/xyz789ghi012_encadeado.zip",
  "output_bucket": "decomp-bucket"
}
```

### Error Response Format

**v1.x Errors:**

```json
{
  "detail": "Error message as string"
}
```

**v2.0 Errors:**

```json
{
  "error": {
    "error_code": "ARTIFACT_NOT_FOUND",
    "message": "Human readable message",
    "details": {"bucket": "decomp-bucket", "key": "artifacts/abc123/..."}
  },
  "request_id": "req-abc123"
}
```

### Error Codes

| Code                  | HTTP Status | Description                   |
| --------------------- | ----------- | ----------------------------- |
| `ARTIFACT_NOT_FOUND`  | 404         | S3 object not found           |
| `VALIDATION_ERROR`    | 422         | Request validation failed     |
| `PARSE_ERROR`         | 422         | File parsing failed           |
| `S3_ERROR`            | 500         | S3 operation failed           |
| `CHAINING_ERROR`      | 500         | Chaining processing failed    |
| `INTERNAL_ERROR`      | 500         | Unexpected error              |

## Migration Steps

### 1. Update Your S3 Bucket Structure

Ensure your S3 bucket follows this structure:

```
s3://decomp-bucket/
├── artifacts/
│   └── <execution_hash>/
│       ├── entradas/
│       │   └── deck_processado.zip
│       │       ├── caso.dat
│       │       ├── dadger.rv0          # Modified by chaining
│       │       ├── dadgnl.rv0          # Modified by chaining
│       │       └── hidr.dat
│       └── saidas/
│           ├── relato.rv0              # Source: Volume data
│           └── relgnl.rv0              # Source: GNL data
└── ingest/
    └── <execution_hash>_encadeado.zip  # Output

s3://newave-bucket/
├── artifacts/
│   └── <execution_hash>/
│       ├── entradas/
│       │   └── deck_processado.zip
│       │       ├── caso.dat
│       │       └── confhd.dat          # Modified by chaining
│       └── saidas/
│           └── pmo.dat
└── ingest/
    └── <execution_hash>_encadeado.zip  # Output
```

### 2. Update API Calls

Replace base62 encoded paths with bucket and execution_hash:

**Python (Before):**

```python
import base62
import requests

path = "/cases/decomp/run123"
encoded = base62.encodebytes(path.encode())

response = requests.post(
    "http://localhost:5053/chain",
    json={
        "sources": [{"id": encoded, "program": "DECOMP"}],
        "destination": {"id": encoded_dest, "program": "DECOMP"},
        "variable": "VARM"
    }
)
```

**Python (After):**

```python
import requests

response = requests.post(
    "http://localhost:8001/chain/",
    json={
        "sources": [{
            "bucket": "decomp-bucket",
            "execution_hash": "source123",
            "program": "DECOMP"
        }],
        "destination": {
            "bucket": "decomp-bucket",
            "execution_hash": "dest456",
            "program": "DECOMP"
        },
        "variable": "VARM"
    }
)

data = response.json()
if "output_key" in data:
    output_key = data["output_key"]
    output_bucket = data["output_bucket"]
    # Download from s3://{output_bucket}/{output_key}
```

### 3. Update Error Handling

v2.0 uses structured error responses:

```python
response = requests.post(url, json=payload)

if response.status_code == 404:
    error = response.json()
    print(f"Error: {error['error']['error_code']}")
    print(f"Message: {error['error']['message']}")
    print(f"Details: {error['error']['details']}")
elif response.status_code == 422:
    # Validation or parse error
    error = response.json()
    print(f"Validation failed: {error['error']['message']}")
elif response.status_code == 500:
    # Internal or S3 error
    error = response.json()
    print(f"Server error: {error['error']['message']}")
```

### 4. Update Environment Variables

| v1.x Variable         | v2.0 Variable            | Notes                   |
| --------------------- | ------------------------ | ----------------------- |
| `PORT=5053`           | `PORT=8000`              | Default port changed    |
| `ROOT_PATH=/api/v1/chain` | `ROOT_PATH=/api/v1/chain` | Unchanged             |
| -                     | `AWS_REGION=us-east-1`   | New: AWS region         |
| -                     | `S3_ENDPOINT_URL=`       | New: Custom S3 endpoint |
| -                     | `DEFAULT_DECOMP_BUCKET=` | New: Default DECOMP bucket |
| -                     | `DEFAULT_NEWAVE_BUCKET=` | New: Default NEWAVE bucket |
| -                     | `DECOMP_SOURCE=S3`       | New: Source mode (S3 or FS) |
| -                     | `NEWAVE_SOURCE=S3`       | New: Source mode (S3 or FS) |
| `URI_PATTERN=BASE62`  | (removed)                | No longer needed        |

### 5. Update Deployment

**Before (PM2):**

```bash
pm2 start main.py --name encadeador
```

**After (Docker):**

```bash
docker compose up -d
```

**Or with systemd:**

```bash
sudo ./deploy/install.sh
sudo systemctl start encadeador
```

## Rollback Plan

If you need to rollback to v1.x:

1. Stop v2.0 service
2. Restore v1.x codebase
3. Reinstall PM2 process
4. Set environment variables back to v1.x values
5. Verify base62-encoded requests work

## Compatibility Mode

v2.0 still supports filesystem mode for gradual migration:

```bash
# Use filesystem mode
DECOMP_SOURCE=FS
NEWAVE_SOURCE=FS
```

When using filesystem mode, clients can continue using base62-encoded paths until fully migrated to S3.

## Chained Variables

The following variables can be chained between model executions:

| Variable | Source | Destination | Description |
| -------- | ------ | ----------- | ----------- |
| `VARM`   | DECOMP | DECOMP, NEWAVE | Reservoir volumes |
| `TVIAGEM` | DECOMP | DECOMP | Water travel times |
| `GNL`    | DECOMP | DECOMP | GNL dispatch |
| `ENA`    | (deprecated) | - | Energy inflow forecast |

## Health Endpoints

New health endpoints are available:

| Endpoint | Purpose | Response |
| -------- | ------- | -------- |
| `/health` | Full status | `{"status": "healthy", "version": "2.0.0", ...}` |
| `/health/live` | Liveness probe | `{"status": "ok"}` |
| `/health/ready` | Readiness probe | `{"ready": true, "checks": {...}}` |

## Support

For migration assistance, open an issue in the repository or check the [Deployment Guide](DEPLOYMENT.md).
