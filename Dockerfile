ARG SERVICE_NAME
ARG USE_CONFIG_FROM_ROOT=false

# ---------------- Builder Stage ----------------
FROM python:3.11-slim AS builder

# Environment for reproducible, quiet Python
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps for installs and diagnostics
RUN apt-get update && apt-get install -y --no-install-recommends \
      git \
      curl \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast, reproducible installs
RUN pip install uv

WORKDIR /build

# Use Docker layer caching for dependencies
COPY uv.lock pyproject.toml ./

# Create and populate a local virtual environment
RUN uv sync

# Copy the application source
COPY . .

# Handle config from root conditionally
RUN if [ "$USE_CONFIG_FROM_ROOT" = "true" ] && [ -f config.json ]; then \
        echo "✓ Config mode: Using config.json from repo root"; \
    elif [ "$USE_CONFIG_FROM_ROOT" = "true" ]; then \
        echo "⚠ USE_CONFIG_FROM_ROOT=true but no config.json found in repo root" && exit 1; \
    else \
        echo "Standard mode - application will use built-in defaults or runtime config"; \
    fi

# ---------------- Runtime Stage ----------------
FROM python:3.11-slim AS runtime

ARG SERVICE_NAME

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Minimal runtime tools
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
    && rm -rf /var/lib/apt/lists/*

# Create home ubuntu service hydra
RUN mkdir -p /home/ubuntu/1mg/$SERVICE_NAME/logs

# switch to code folder
WORKDIR /home/ubuntu/1mg/$SERVICE_NAME

# Copy and install requirements
ENV VIRTUAL_ENV="/home/ubuntu/1mg/$SERVICE_NAME/.venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Bring app and virtualenv from builder
COPY --from=builder /build /home/ubuntu/1mg/$SERVICE_NAME
