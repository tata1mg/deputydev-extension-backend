# Contributing to DeputyDev Backend

Thanks for your interest in improving DeputyDev Backend! This guide explains the project layout, local development workflows, code style, and how to submit changes.

If you’re new to this codebase, start with the README and in-code docstrings. Any previously separate docs pages are no longer required.


## Project layout (quick tour)

- app/ — Application source
  - backend_common/ — Shared domain code and infrastructure
    - service_clients/ — External APIs & SDK wrappers (GitHub/GitLab/Bitbucket, Jira, AWS, OpenAI, Gemini, SQS, API Gateway, etc.)
    - repository/ — Database access layer (Tortoise ORM wrappers, repositories, DB utilities)
    - constants/ — Shared enums, error codes, and constants
    - utils/ — Cross-cutting helpers (auth, error handling, formatting, redis wrapper, execution helpers)
  - main/ — HTTP routes and services
    - blueprints/ — Sanic blueprints, endpoints and feature services (deputy_dev, one_dev)
  - listeners.py — Sanic lifecycle listeners
  - service.py — App bootstrap and entrypoint
  - migrate.py — Migration utilities (if used)
- config_template.json, config.json — Application configuration (see README)
- deputydev.toml — DeputyDev agent configuration
- pyproject.toml — Project metadata, dependencies, Python version
- ruff.toml — Lint/format rules
- .pre-commit-config.yaml — Hooks (Ruff, uv-lock)
- uv.lock — Dependency lockfile
- README.md — Overview, prerequisites, and local setup
- CODE_OF_CONDUCT.md — Community standards

Note: This backend depends on deputydev-core (pinned in pyproject.toml). Follow core interfaces and update pins in coordination with maintainers when needed.


## Prerequisites and local setup

To avoid duplication, prerequisites (Python version, uv) and setup steps live in README.md. Follow the README for installing dependencies, enabling pre-commit, and running local checks.

Key versions (from pyproject.toml):
- Python: >= 3.11, < 3.12
- Package manager: uv (uv.lock is authoritative)


## Install and build

See README.md for the authoritative setup and build instructions (uv sync, pre-commit install, Ruff commands). This document focuses on contribution workflows and standards.


## Code style and quality

Type hints and style
- Type hints are required for function parameters and return types (public and private). Annotate *args/**kwargs as needed.
- Keep modules cohesive and small. Extract helpers to app/backend_common/utils when appropriate.
- Avoid top-level side effects on import; prefer explicit functions/classes.

Ruff (lint and format)
- Format: ruff format .
- Lint: ruff check .
- Config: ruff.toml (line-length 120, import ordering, PEP8 naming, complexity checks, no print statements, prefer pathlib, async best practices, and ANN* type-hint rules)

Pre-commit
- Install: pre-commit install
- Run all hooks: pre-commit run --all-files

Logging and errors
- Use deputydev_core.utils.app_logger.AppLogger for consistent logging.
- Use centralized error handling and exceptions in backend_common (e.g., utils/error_handler.py) or define domain-specific exceptions close to their domains.

Public contracts
- Treat HTTP endpoints, event payloads, and DTOs as public contracts. Avoid breaking changes without coordination.


## Monorepo-like structure and module boundaries

This repository hosts multiple feature areas that share common foundations. Treat it as a monorepo-lite with clear module boundaries:

- backend_common (shared library)
  - Owns shared DTOs, DAOs, repositories, service clients, utilities, constants.
  - Anything reusable across features should live here. Avoid duplicating logic in feature modules.
- one_dev (feature module)
  - Lives under app/main/blueprints/one_dev/ and contains its routes, DTOs, DAOs, services, and helpers.
  - Must not import from deputy_dev internals. If you need functionality, extract it into backend_common.
- deputy_dev (feature module)
  - Lives under app/main/blueprints/deputy_dev/ with its routes, DTOs, DAOs, services, and helpers.
  - Must not import from one_dev internals. Share via backend_common when needed.

Import hygiene
- Allowed imports: feature → backend_common, feature → deputydev_core, backend_common → deputydev_core.
- Disallowed: feature ↔ feature direct imports of internal modules.
- Prefer explicit public interfaces (services, repositories) over deep internal imports.

Data models and repositories
- Shared or platform-agnostic DTOs should be placed in backend_common/models/dto/.
- Feature-specific DTOs stay within their feature module (e.g., app/main/blueprints/one_dev/models/dto/...).
- Keep DAOs/ORM models organized per module. If DB tables are shared, centralize the DAO in backend_common and re-use.

Routing and API surface
- Keep APIs namespaced per feature (e.g., /one-dev/... vs /deputy-dev/...). Follow versioned routes (v1, v2) as seen in the tree.
- Avoid breaking changes across modules; coordinate changes and provide deprecation paths where feasible.

Cross-cutting changes
- Prefer two-step changes for shared contracts:
  1) Introduce new shared APIs in backend_common and adopt them in one module.
  2) Migrate the other module, then remove legacy code after both are switched.
- For large efforts, split into separate PRs per module with a shared tracking issue.

Commit scoping
- Use Conventional Commit scope for clarity, for example:
  - feat(one_dev): add xyz endpoint
  - fix(deputy_dev): correct comment serializer
  - refactor(backend_common): extract jira client retry

Testing guidance
- Keep module tests separated by feature to mirror the monorepo layout (see guidance in Running checks and debugging).

## Working on core functionality

Service clients
- Implement or extend clients under app/backend_common/service_clients/ (oauth, scm, cloud, LLM providers, etc.).
- Reuse shared base clients and helpers from deputydev-core where applicable.
- Keep adapters thin and consistent; centralize auth and retry logic.

HTTP routes and services
- Add endpoints and feature logic under app/main/blueprints/<area>/.
- Keep business logic in services; keep route handlers thin and validated.
- Use ConfigManager from deputydev-core for configuration access.

Repositories and DB
- Follow existing patterns in app/backend_common/repository/.
- Keep DTOs under app/backend_common/models/dto/.
- Keep ORM entities/DAOs under app/backend_common/models/dao/postgres/.
- Prefer repository methods over ad-hoc queries; keep transactions explicit.

Constants and configuration
- Add shared constants under app/backend_common/constants/ with clear namespacing.
- Use deputydev_core.utils.config_manager.ConfigManager for configuration access.
- If you introduce new configuration knobs, update config_template.json and document them in README.md.


## Running checks and debugging

- ruff format .
- ruff check .
- pre-commit run --all-files

If you add a test suite (recommended for non-trivial features):
- Use pytest. Recommended layout to mirror modules:
  - tests/backend_common/
  - tests/one_dev/
  - tests/deputy_dev/
- Add minimal fixtures and keep tests fast and deterministic.
- Prefer unit tests; add targeted integration tests per module when needed.


## Submitting changes

1) Fork-based workflow (default; non-maintainers)
- Non-maintainers cannot create branches on the upstream repository.
- Fork this repository to your GitHub account.
- In your fork, create a branch using the same conventions: feat/…, fix/…, chore/…, docs/…
- Push to your fork and open a Pull Request against the upstream default branch (usually main). If unsure, target main.
- Enable "Allow edits by maintainers" on the PR.

2) Maintainers-only workflow (optional)
- Maintainers may create branches directly in the upstream repository.
- Branch naming: feat/…, fix/…, chore/…, docs/…

3) Ensure quality gates pass
- Local lint/format pass (ruff format, ruff check)
- Pre-commit hooks pass
- Update README.md if you introduce user-visible changes or configuration
- Add tests or usage notes for behavioral changes

4) Commit messages
- Use Conventional Commits with a scope when possible: feat(one_dev): ..., feat(deputy_dev): ..., feat(backend_common): ...
- Common types: feat, fix, chore, docs, refactor, test, perf, build, ci, revert
- Keep messages concise and reference issues when applicable

5) Open a Pull Request
- Describe the motivation, what changed, and how you validated it
- Link related issues
- Avoid bumping the version; maintainers handle releases


## Versioning and release notes

- Project version is defined in pyproject.toml.
- Coordinate version bumps with maintainers; do not change the version in PRs unless asked.


## Security and privacy

- Do not commit secrets or tokens. Use local environment configuration (config.json) and secret stores.
- Be mindful of logs; avoid including sensitive data in logs.


## Code of Conduct

By participating, you agree to abide by our Code of Conduct. See CODE_OF_CONDUCT.md at the repository root.


## Troubleshooting

- Python version errors: Ensure your Python matches the range in pyproject.toml (>=3.11, <3.12).
- Missing tools: Ensure uv, pre-commit, and ruff are installed and available.
- Lockfile updates: If dependencies change, run uv lock (or rely on the uv-lock pre-commit hook) and commit uv.lock.
- Lint issues: Run ruff format . then ruff check . to see remaining violations.


## Questions?

Open an issue or start a discussion in the repository. Thanks again for contributing to DeputyDev Backend!