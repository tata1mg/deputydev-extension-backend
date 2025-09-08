# DeputyDev Backend - Comprehensive Documentation

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [Architecture](#architecture)
4. [Tech Stack](#tech-stack)
5. [Prerequisites](#prerequisites)
6. [Installation](#installation)
7. [Configuration](#configuration)
8. [Usage](#usage)
9. [API Reference](#api-reference)
10. [Deployment](#deployment)
11. [Development](#development)
12. [Testing](#testing)
13. [Contributing](#contributing)
14. [Code of Conduct](#code-of-conduct)
15. [License](#license)

---

## Project Overview

**DeputyDev Backend** is a sophisticated AI-powered backend service that serves as the core engine for DeputyDev, an intelligent code assistant platform. The system leverages Large Language Models (LLMs) and integrates with multiple developer tools to provide comprehensive assistance for software development tasks.

### Version Information
- **Current Version**: 14.0.2
- **Authors**: Deputy Dev Team (deputydev@1mg.com)
- **Python Version**: 3.11.x (required)

### Core Functionality

The backend provides:
- Intelligent query processing and response generation
- Multi-agent system for specialized task handling
- Real-time streaming responses
- Tool integration for code analysis and manipulation
- Session management and conversation persistence
- Integration with popular SCM platforms and issue trackers

---

## Key Features

### AI-Powered Assistance
- **Multi-Model Support**: Integrates with OpenAI GPT, Google Gemini, Anthropic Claude, and other LLMs
- **Intelligent Query Solving**: Advanced query processing with context-aware responses
- **Streaming Responses**: Real-time response generation with incremental updates
- **Tool Use**: Dynamic tool invocation for code analysis, file operations, and external integrations

### Developer Tool Integration
- **Source Code Management**:
  - GitHub (REST API, GraphQL)
  - GitLab (API integration)
  - Bitbucket (Workspace and repository management)
- **Issue Tracking**: Jira integration for project management
- **Documentation**: Confluence integration for knowledge base access

### Advanced Capabilities
- **Vector Search**: PostgreSQL with pgvector for semantic code search
- **Session Management**: Persistent conversation history and context
- **Agent System**: Dynamic agent selection based on query intent
- **Prompt Engineering**: Sophisticated prompt management and caching
- **Error Handling**: Comprehensive error tracking and recovery

### Infrastructure Features
- **Asynchronous Processing**: Built with async/await patterns using Sanic framework
- **Database Layer**: Tortoise ORM with PostgreSQL and pgvector
- **Caching**: Redis integration for performance optimization
- **Message Queuing**: Azure Service Bus and Kafka support
- **Monitoring**: Elastic APM and Sentry integration

---

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client Apps   │────│  DeputyDev API   │────│  External APIs  │
│  (VS Code, Web) │    │   (Sanic App)    │    │ (GitHub, Jira)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Query Solver  │────│   LLM Handler    │────│   AI Models     │
│   (Core Logic)  │    │  (Prompt Mgmt)   │    │ (GPT, Gemini)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Tool System    │────│   Repositories   │────│   Databases     │
│ (File Ops, SCM) │    │   (Tortoise)     │    │ (PostgreSQL)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Components

#### 1. Query Solver (`app/main/blueprints/one_dev/services/query_solver/`)
- **Purpose**: Main orchestration layer for processing user queries
- **Key Classes**:
  - `QuerySolver`: Core query processing engine
  - `QuerySolverAgent`: Specialized agents for different task types
  - `AgentSelector`: Dynamic agent selection based on query intent

#### 2. LLM Handler (`app/backend_common/services/llm/`)
- **Purpose**: Unified interface for LLM interactions
- **Features**:
  - Multi-model support with automatic fallback
  - Streaming response handling
  - Tool calling and function execution
  - Prompt caching and optimization

#### 3. Service Clients (`app/backend_common/service_clients/`)
- **Purpose**: Integration layer for external services
- **Supported Services**:
  - **SCM**: GitHub, GitLab, Bitbucket clients
  - **AI**: OpenAI, Google Gemini, Anthropic, OpenRouter
  - **Cloud**: AWS (Bedrock, SQS, API Gateway), Azure
  - **Others**: Jira, Confluence, Supabase

#### 4. Repository Layer (`app/backend_common/repository/`)
- **Purpose**: Data access layer using Tortoise ORM
- **Key Repositories**:
  - User and team management
  - Session and conversation storage
  - Message threads and attachments
  - Analytics and error tracking

### Data Flow

1. **Query Reception**: User query received via API endpoints
2. **Preprocessing**: Query analysis and context extraction
3. **Agent Selection**: Dynamic selection of appropriate agent
4. **LLM Processing**: Query sent to LLM with tools and context
5. **Tool Execution**: External tools invoked as needed
6. **Response Generation**: Streaming response construction
7. **Persistence**: Conversation history and metadata storage

---

## Tech Stack

### Core Framework
- **Web Framework**: Sanic 23.12.2 (async Python web framework)
- **ORM**: Tortoise ORM 0.19-0.21 (async ORM for Python)
- **Database**: PostgreSQL with pgvector extension
- **Cache**: Redis 5.0.1

### AI/ML Services
- **OpenAI**: GPT models integration
- **Google Generative AI**: Gemini models
- **Anthropic**: Claude models
- **OpenRouter**: Multi-provider LLM access
- **AWS Bedrock**: Managed AI services

### External Integrations
- **SCM Platforms**: GitHub, GitLab, Bitbucket
- **Issue Tracking**: Jira, Confluence
- **Cloud Services**: AWS, Azure, Supabase
- **Message Queues**: Azure Service Bus, Kafka

### Development Tools
- **Package Management**: uv (fast Python package manager)
- **Linting**: Ruff (fast Python linter)
- **Testing**: pytest
- **Code Quality**: pre-commit hooks

### Infrastructure
- **Containerization**: Docker
- **Monitoring**: Elastic APM, Sentry
- **Logging**: Python JSON Logger, Rich
- **Database Migrations**: dbmate

---

## Prerequisites

### System Requirements
- **Python**: 3.11.x (3.11.0 to 3.11.x, excluding 3.12+)
- **Git**: 2.42.0+ (for SCM operations)
- **PostgreSQL**: 13+ with pgvector extension
- **Redis**: 5.0.1+
- **Docker**: For containerized deployment

### Development Tools
- **uv**: Fast Python package manager
- **pre-commit**: Git hooks for code quality
- **dbmate**: Database migration tool

### External Accounts (for full functionality)
- OpenAI API key
- Google Cloud service account
- GitHub/GitLab/Bitbucket tokens
- Jira API credentials
- AWS/Azure credentials (if using cloud services)

---

## Installation

### Local Development Setup

#### 1. Environment Preparation
```bash
# Clone the repository
git clone <repository_url>
cd deputydev-backend

# Create virtual environment using uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync
```

#### 2. Database Setup
```bash
# Ensure PostgreSQL is running with pgvector extension
# Install dbmate if using migrations
curl -fsSL -o /usr/local/bin/dbmate https://github.com/amacneil/dbmate/releases/latest/download/dbmate-linux-amd64
chmod +x /usr/local/bin/dbmate

# Run migrations (if applicable)
dbmate up
```

#### 3. Configuration
```bash
# Copy configuration template
cp config_template.json config.json

# Edit config.json with your credentials and settings
# Required: Database credentials, API keys, service tokens
```

### Docker Setup

#### Build and Run
```bash
# Build the Docker image
docker build \
  --build-arg SERVICE_NAME="deputydev" \
  -t deputydev-backend .

# Run the container
docker run -d \
  -p 8000:8000 \
  -v "$(pwd)/config.json:/home/ubuntu/1mg/deputydev/config.json" \
  --name deputydev-backend-container \
  deputydev-backend
```

---

## Configuration

### Configuration Files

#### `config.json`
Main configuration file containing:
- **Database Settings**: PostgreSQL connection details
- **API Keys**: OpenAI, Google Gemini, Anthropic credentials
- **Service Tokens**: GitHub, GitLab, Bitbucket, Jira tokens
- **Cloud Credentials**: AWS, Azure service configurations
- **LLM Models**: Model configurations and limits
- **Feature Flags**: Enable/disable various features

#### `settings.toml`
Additional configuration settings:
- Application constants
- Default values
- Environment-specific overrides

#### `deputydev.toml`
Project-specific configuration:
- Custom settings
- Extension configurations

### Key Configuration Sections

#### Database Configuration
```json
{
  "DATABASE": {
    "credentials": {
      "database": "deputy_dev",
      "host": "localhost",
      "port": 5432,
      "username": "postgres",
      "password": "your_password"
    },
    "engine": "tortoise.backends.asyncpg"
  }
}
```

#### LLM Model Configuration
```json
{
  "CHAT_MODELS": [
    {
      "name": "GPT_4_POINT_1_NANO",
      "provider": "OPENAI",
      "display_name": "GPT-4.1 Nano",
      "model_identifier": "gpt-4.1-nano",
      "limits": {
        "input_tokens_limit": 272000,
        "output_tokens_limit": 32768
      }
    }
  ]
}
```

#### SCM Integration
```json
{
  "GITHUB": {
    "TOKEN": "your_github_token",
    "WEBHOOK_SECRET": "webhook_secret"
  },
  "GITLAB": {
    "TOKEN": "your_gitlab_token",
    "URL": "https://gitlab.com"
  }
}
```

---

## Usage

### Starting the Application

#### Local Development
```bash
# Activate virtual environment
source .venv/bin/activate

# Run the application
python -m app.service
```

#### Production
```bash
# Using Docker
docker run -d -p 8000:8000 deputydev-backend

# Or using gunicorn/uvicorn
gunicorn app.service:app -w 4 -k uvicorn.workers.UvicornWorker
```

### API Endpoints

The application exposes RESTful APIs for:
- **Query Processing**: `/end_user/v1/query-solver`
- **Session Management**: `/end_user/v1/sessions`
- **File Operations**: `/end_user/v1/files`
- **Tool Integration**: `/end_user/v1/tools`

### Example Usage

#### Query Processing
```python
import requests

response = requests.post(
    "http://localhost:8000/end_user/v1/query-solver",
    json={
        "query": "Explain this Python function",
        "session_id": "session_123",
        "llm_model": "GPT_4_POINT_1_NANO",
        "focus_items": [...]
    },
    stream=True
)

for chunk in response.iter_content():
    print(chunk.decode())
```

---

## API Reference

### Core Endpoints

#### POST `/end_user/v1/query-solver`
Process user queries with AI assistance.

**Request Body:**
```json
{
  "query": "string",
  "session_id": "integer",
  "llm_model": "string",
  "focus_items": [...],
  "attachments": [...],
  "reasoning": "string",
  "write_mode": "boolean"
}
```

**Response:** Streaming JSON chunks with response data.

#### GET `/end_user/v1/sessions/{session_id}`
Retrieve session information and conversation history.

#### POST `/end_user/v1/tool-response`
Submit tool execution results.

### Authentication
- API key-based authentication
- Session-based authorization
- OAuth integration for external services

---

## Deployment

### Docker Deployment

#### Production Dockerfile Features
- Multi-stage build for optimized image size
- Git installation for SCM operations
- SSH key setup for private repositories
- uv package manager for fast dependency resolution

#### Environment Variables
```bash
SERVICE_NAME=deputydev
SSH_PRIVATE_KEY=...
SSH_PUBLIC_KEY=...
```

### Cloud Deployment

#### AWS Deployment
- ECS/Fargate for container orchestration
- RDS PostgreSQL with pgvector
- ElastiCache Redis
- API Gateway for external access

#### Azure Deployment
- Azure Container Apps
- Azure Database for PostgreSQL
- Azure Cache for Redis

### Scaling Considerations
- Horizontal scaling with load balancer
- Database connection pooling
- Redis clustering for cache
- Message queue partitioning

---

## Development

### Code Quality
```bash
# Install pre-commit hooks
pre-commit install

# Run all checks
pre-commit run --all-files

# Format code
ruff format .

# Lint code
ruff check .
```

### Database Migrations
```bash
# Create new migration
dbmate new migration_name

# Apply migrations
dbmate up

# Rollback
dbmate rollback
```

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

---

## Testing

### Test Structure
```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
└── conftest.py    # Test configuration
```

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_query_solver.py

# With coverage
pytest --cov=app --cov-report=term-missing

# Parallel execution
pytest -n auto
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: External service integration
- **E2E Tests**: Full workflow testing
- **Performance Tests**: Load and stress testing

---

## Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure code quality checks pass
5. Submit pull request

### Code Standards
- **Linting**: Ruff configuration in `ruff.toml`
- **Formatting**: Consistent code style
- **Documentation**: Docstrings for all public functions
- **Testing**: Minimum 80% code coverage

### Commit Guidelines
- Use conventional commit format
- Reference issue numbers
- Keep commits focused and atomic

### Pull Request Process
1. Update documentation
2. Add tests for new features
3. Ensure CI passes
4. Code review approval
5. Squash and merge

---

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

### Key Principles
- Respect all contributors
- Use inclusive language
- Focus on constructive feedback
- Maintain professional communication

---

## License

Copyright © 2024 DeputyDev. All rights reserved.

This project is proprietary software owned by DeputyDev/1mg. Unauthorized use, reproduction, or distribution is prohibited.

---

## Support

### Documentation
- [API Documentation](docs/api.md)
- [Integration Guides](docs/integrations/)
- [Troubleshooting](docs/troubleshooting.md)

### Community
- [GitHub Issues](https://github.com/DeputyDev/deputydev-backend/issues)
- [Internal Wiki](https://wiki.1mg.com/deputydev)

### Contact
- **Email**: deputydev@1mg.com
- **Slack**: #deputydev-backend

---

*This documentation is maintained by the DeputyDev team. Last updated: September 2024*