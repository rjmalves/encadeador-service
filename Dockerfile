# ============================================================================
# Stage 1: Builder
# Install uv and dependencies in a clean environment
# ============================================================================
FROM python:3.12-slim AS builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock README.md ./

# Create virtual environment and install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source
COPY app/ ./app/
COPY main.py ./

# Install the project itself
RUN uv sync --frozen --no-dev


# ============================================================================
# Stage 2: Production
# Minimal runtime image with only necessary components
# ============================================================================
FROM python:3.12-slim AS production

# Labels for container identification
LABEL org.opencontainers.image.title="encadeador-service"
LABEL org.opencontainers.image.description="Service for chaining DECOMP/NEWAVE cases"
LABEL org.opencontainers.image.version="2.0.0"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app/app ./app
COPY --from=builder /app/main.py ./

# Create temp directory for processing
RUN mkdir -p /tmp/encadeador && chown appuser:appgroup /tmp/encadeador

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000
ENV HOST=0.0.0.0
ENV TEMP_DIR=/tmp/encadeador

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
