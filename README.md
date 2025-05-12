# DeputyDev Backend

# DeputyDev Backend

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
---

## Overview

DeputyDev Backend is a service that provides the backend functionality for DeputyDev. It integrates with various developer tools and AI services to offer intelligent assistance and automation.

## Features

*   **AI-Powered Assistance:** Leverages Large Language Models (LLMs) like OpenAI GPT and Google Gemini through Langchain for intelligent code analysis, generation, and more.
*   **SCM Integration:** Connects with popular Source Code Management platforms:
    *   GitHub
    *   GitLab
    *   Bitbucket
*   **Issue Tracker Integration:** Seamlessly works with Jira for issue and project tracking.
*   **Real-time Communication:** Potentially supports real-time features via websockets.
*   **Database:** Uses PostgreSQL with the pgvector extension for vector similarity searches (likely for RAG capabilities).
*   **Containerized:** Dockerfile provided for easy containerization and deployment.

## Tech Stack

*   **Programming Language:** Python (>=3.11)
*   **Framework:** Sanic, Torpedo (custom framework)
*   **AI/ML:** OpenAI API, Google Generative AI API, Anthropic API
*   **Database:** PostgreSQL, pgvector
*   **SCM Clients:** Custom clients for GitHub, GitLab, Bitbucket
*   **Issue Tracker Clients:** Custom client for Jira
*   **Messaging/Queueing:** Azure Service Bus, AioKafka (potentially)
*   **Cloud Services:** AWS (Bedrock, SQS, API Gateway), Supabase
*   **Containerization:** Docker
*   **Package Management:** `uv` (from `uv.lock`)
*   **Linting/Formatting:** Ruff, Flake8, Pylint
*   **Testing:** Pytest

## Project Structure


/
├── app/                     # Main application code
│   ├── backend_common/      # Common utilities, models, service clients
│   ├── main/                # Main application logic, blueprints
│   ├── listeners.py         # Application event listeners
│   └── service.py           # Main service entry point
├── tests/                   # Tests (assumption, based on conftest.py and pytest.ini)
├── .env                     # Environment variables (example or actual)
├── .flake8                  # Flake8 configuration
├── .gitignore               # Git ignore rules
├── .pre-commit-config.yaml  # Pre-commit hook configurations
├── .pylintrc                # Pylint configuration
├── bitbucket-pipelines.yml  # Bitbucket CI/CD pipeline
├── config.json              # Application configuration
├── config_template.json     # Template for configuration
├── deputydev.toml           # Project-specific TOML configuration
├── Dockerfile               # Docker build instructions
├── main.spec                # PyInstaller spec file (potentially)
├── pytest.ini               # Pytest configuration
├── pyproject.toml           # Project metadata and dependencies (PEP 621)
├── README.md                # This file
└── uv.lock                  # uv lock file


## Setup and Installation

### Local Development Setup

1.  **Prerequisites:**
    *   Python >= 3.11, < 3.12
    *   `uv` (Python package installer, `pip install uv`)
    *   Git
    *   Access to a PostgreSQL server
    *   (Optional) `dbmate` for database migrations (if used, install from [here](https://github.com/amacneil/dbmate/releases))

2.  **Clone the repository:**
    bash
    git clone <repository_url>
    cd deputydev-backend


3.  **Set up SSH Keys:**
    *   Ensure your SSH keys are configured to access private repositories on Bitbucket and GitHub if your dependencies require it (e.g., `cache_wrapper`, `torpedo`, `tortoise_wrapper`, `deputydev-core`).

4.  **Install dependencies:**
    *   It's highly recommended to use a virtual environment.
    bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    uv sync


5.  **Configure Environment Variables:**
    *   Create a `config.json` file in the root of the project by copying `config_template.json`.
    *   Populate `config.json` with the necessary credentials and configurations for:
        *   Database connection (host, port, user, password, database name)
        *   SCM API keys/tokens (GitHub, GitLab, Bitbucket)
        *   Jira API token and URL
        *   AI service API keys (OpenAI, Google Gemini/Vertex AI)
        *   Azure Service Bus connection string
        *   AWS credentials and region (for Bedrock, SQS, API Gateway)
        *   Supabase URL and key
        *   Any other service credentials.
    *   Refer to `config_template.json` and `settings.toml` for potential configuration keys and structure.

6.  **Database Setup:**
    *   Ensure your PostgreSQL server is running.
    *   If `dbmate` is used for migrations (check for a `db/migrations` folder and `dbmate` commands):
        bash
        # Ensure DATABASE_URL is set in your environment or config.json if dbmate uses it
        dbmate up

    *   Otherwise, you might need to run custom scripts or use an ORM's migration tools.

### Docker Setup

1.  **Prerequisites:**
    *   Docker installed and running.

2.  **Build the Docker image:**
    *   You will need to pass `SSH_PRIVATE_KEY` and `SSH_PUBLIC_KEY` as build arguments if your private dependencies are fetched via SSH.
    *   The `SERVICE_NAME` build argument is also required (e.g., `deputydev`).
    bash
    docker build --build-arg SSH_PRIVATE_KEY="$(cat ~/.ssh/id_ed25519)" --build-arg SSH_PUBLIC_KEY="$(cat ~/.ssh/id_ed25519.pub)" --build-arg SERVICE_NAME="deputydev" -t deputydev-backend .

    *   Note: The `cloud` argument in the `Dockerfile` (`ARG cloud`) suggests there might be different base images for cloud deployments. For local Docker setup, it might not be needed or set to a default.

3.  **Run the Docker container:**
    *   You'll need to mount the `config.json` file into the container.
    *   The `Dockerfile` copies `config.json` if it's present at build time, but for local development, mounting allows for easier changes without rebuilding.
    *   The application inside the container needs to be configured to read `config.json` from the expected path (e.g., `/home/ubuntu/1mg/deputydev/config.json` based on the `WORKDIR` and `SERVICE_NAME`).
    bash
    docker run -d -p <host_port>:<container_port> -v "$(pwd)/config.json:/home/ubuntu/1mg/deputydev/config.json" --name deputydev-backend-container deputydev-backend

    *   Replace `<host_port>` and `<container_port>` with appropriate values (e.g., `8000:8000`). Ensure `SERVICE_NAME` in the path `/home/ubuntu/1mg/deputydev/config.json` matches the one used during the build or expected by the application.

## Running the Application

### Locally

bash
source .venv/bin/activate # If you haven't already
python app/service.py

The application should now be running. Check the application logs for the exact host and port.

### With Docker

If you started the container in detached mode (`-d`), you can view logs using:
bash
docker logs deputydev-backend-container

The application will be accessible on the host port you mapped during `docker run`.

