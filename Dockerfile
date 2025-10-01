ARG SERVICE_NAME
ARG SSH_PRIVATE_KEY
ARG SSH_PUBLIC_KEY
ARG USE_CONFIG_FROM_ROOT=false

# ---------------- Builder Stage ----------------
FROM python:3.11-slim AS builder

# Environment for reproducible, quiet Python
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create SSH directory and set up keys
RUN mkdir -p /root/.ssh && \
    echo "$SSH_PRIVATE_KEY" > /root/.ssh/id_ed25519 && \
    echo "$SSH_PUBLIC_KEY" > /root/.ssh/id_ed25519.pub && \
    chmod 600 /root/.ssh/id_ed25519 && \
    chmod 600 /root/.ssh/id_ed25519.pub && \
    chmod 700 /root/.ssh

# System deps for installs and diagnostics
RUN apt-get update && apt-get install -y --no-install-recommends \
      git \
      curl \
      build-essential \
      openssh-server \
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

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
      git \
      curl \
      wget \
    && rm -rf /var/lib/apt/lists/*

# Install dbmate for database migrations
# Automatically detects architecture and downloads the appropriate binary
RUN echo "Installing dbmate for database migrations..." && \
    ARCH=$(uname -m) && \
    echo "Detected architecture: $ARCH" && \
    case $ARCH in \
        x86_64) \
            DBMATE_ARCH="linux-amd64" ;; \
        aarch64|arm64) \
            DBMATE_ARCH="linux-arm64" ;; \
        *) \
            echo "ERROR: Unsupported architecture: $ARCH" && exit 1 ;; \
    esac && \
    echo "Downloading dbmate-${DBMATE_ARCH}..." && \
    wget -q -O /usr/local/bin/dbmate "https://github.com/amacneil/dbmate/releases/latest/download/dbmate-${DBMATE_ARCH}" && \
    chmod +x /usr/local/bin/dbmate && \
    echo "dbmate installation complete:" && \
    dbmate --version

# Create home ubuntu service hydra
RUN mkdir -p /home/ubuntu/1mg/$SERVICE_NAME/logs

# switch to code folder
WORKDIR /home/ubuntu/1mg/$SERVICE_NAME

# Set git configuration for GitPython
ENV GIT_PYTHON_REFRESH=quiet
ENV GIT_PYTHON_GIT_EXECUTABLE="/usr/bin/git"

# Copy and install requirements
ENV VIRTUAL_ENV="/home/ubuntu/1mg/$SERVICE_NAME/.venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Bring app and virtualenv from builder
COPY --from=builder /build /home/ubuntu/1mg/$SERVICE_NAME
