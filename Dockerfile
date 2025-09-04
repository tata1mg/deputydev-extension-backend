FROM --platform=linux/amd64 python:3.11-slim AS builder

# Environment for reproducible, quiet Python
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps for installs and diagnostics
RUN apt-get update && apt-get install -y --no-install-recommends \
      git \
      curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast, reproducible installs
RUN pip install --no-cache-dir uv

WORKDIR /app

# Use Docker layer caching for dependencies
COPY pyproject.toml uv.lock ./

# Create and populate a local virtual environment under /app/.venv
RUN uv sync --frozen

# Copy the application source
COPY . .

# ---------------- Runtime ----------------
FROM --platform=linux/amd64 python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/app/.venv/bin:$PATH

# Minimal runtime tools
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bring app and virtualenv from builder
COPY --from=builder /app /app

# Expose service port
EXPOSE 8084

# Default command (same startup pattern)
CMD ["python", "-m", "app.service"]
