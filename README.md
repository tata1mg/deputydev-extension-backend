# DeputyDev Backend

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

---

## Overview

**DeputyDev Backend** is a service that provides the backend functionality for DeputyDev. It integrates with various developer tools and AI services to offer intelligent assistance and automation.

## Features

- **AI-Powered Assistance:** Leverages Large Language Models (LLMs) like OpenAI GPT and Google Gemini through Langchain for intelligent code analysis, generation, and more.
- **SCM Integration:** Connects with popular Source Code Management platforms:
  - GitHub
  - GitLab
  - Bitbucket
- **Issue Tracker Integration:** Seamlessly works with Jira for issue and project tracking.
- **Real-time Communication:** Potentially supports real-time features via WebSockets.
- **Database:** Uses PostgreSQL with the pgvector extension for vector similarity searches (likely for RAG capabilities).
- **Containerized:** Dockerfile provided for easy containerization and deployment.

## Tech Stack

- **Programming Language:** Python (>=3.11)
- **Framework:** Sanic
- **AI/ML:** OpenAI API, Google Generative AI API, Anthropic API
- **Database:** PostgreSQL, pgvector
- **SCM Clients:** Custom clients for GitHub, GitLab, Bitbucket
- **Issue Tracker Clients:** Custom client for Jira
- **Messaging/Queueing:** Azure Service Bus, AioKafka (potentially)
- **Cloud Services:** AWS (Bedrock, SQS, API Gateway)
- **Containerization:** Docker
- **Package Management:** [`uv`](https://github.com/astral-sh/uv) (via `uv.lock`)
- **Linting/Formatting:** Ruff, Flake8, Pylint
- **Testing:** Pytest

## Project Structure

```
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
```

---

## Setup and Installation

### Local Development Setup

1. **Prerequisites:**
    - Python >= 3.11, < 3.12
    - [`uv`](https://github.com/astral-sh/uv): `pip install uv`
    - Git
    - Access to a PostgreSQL server
    - *(Optional)* `dbmate` for database migrations — install from [here](https://github.com/amacneil/dbmate/releases)

2. **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd deputydev-backend
    ```

3. **Install dependencies:**

    It is highly recommended to use a virtual environment:

    ```bash
    uv venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    uv sync
    ```

4. **Configure Environment Variables:**

    - Copy `config_template.json` to `config.json`.
    - Populate `config.json` with credentials/configs:
      - PostgreSQL DB details
      - SCM API tokens (GitHub, GitLab, Bitbucket)
      - Jira API token and URL
      - AI service keys (OpenAI, Google Gemini, etc.)
      - Azure Service Bus connection string
      - AWS credentials (for Bedrock, SQS, API Gateway)
    - Refer to `config_template.json` and `settings.toml` for required keys.

5. **Database Setup:**

    - Ensure PostgreSQL is running.
    - If using `dbmate`:

        ```bash
        # Ensure DATABASE_URL is set
        dbmate up
        ```

    - If not using `dbmate`, follow ORM-based or manual setup instructions.

---

### Docker Setup

1. **Prerequisites:**
    - Docker installed and running.

2. **Build the Docker image:**

    ```bash
    docker build \
      --build-arg SERVICE_NAME="deputydev" \
      -t deputydev-backend .
    ```

    > The `ARG cloud` in the Dockerfile might affect base images used for different environments.

3. **Run the Docker container:**

    Mount the `config.json` so changes don't require a rebuild:

    ```bash
    docker run -d \
      -p <host_port>:<container_port> \
      -v "$(pwd)/config.json:/home/ubuntu/1mg/deputydev/config.json" \
      --name deputydev-backend-container \
      deputydev-backend
    ```

    Replace `<host_port>` and `<container_port>` (e.g., `8000:8000`). Make sure the path and `SERVICE_NAME` match what's expected by the app.

---

## Running the Application

### Locally

```bash
uv venv --python 3.11
source .venv/bin/activate
uv sync
python -m app.service
```

## Local checks

- pre-commit install
- pre-commit run --all-files
- ruff format .
- ruff check .

## Contributing

Please read CONTRIBUTING.md for contribution guidelines (project layout, code style, workflows, and PR process).

## Code of Conduct

By participating, you agree to follow our Code of Conduct (CODE_OF_CONDUCT.md).
