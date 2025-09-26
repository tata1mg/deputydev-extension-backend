# DeputyDev Quick Start Guide

This guide will help you set up the DeputyDev development environment quickly. Follow these steps in order to get everything running locally.

## Prerequisites

Before starting, ensure you have the following installed:
- Git
- Docker and Docker Compose -(https://www.docker.com/get-started/)
- Node.js - (https://nodejs.org/en/download)
- Yarn - (https://yarnpkg.com/getting-started/install)
- VS Code - (https://code.visualstudio.com/Download)

## Step 1: Clone Required Repositories

Clone all the following repositories into the same parent folder:

```bash
git clone https://github.com/tata1mg/deputydev-auth.git
git clone https://github.com/tata1mg/deputydev-extension-backend.git
git clone https://github.com/tata1mg/deputydev-binary.git
git clone https://github.com/tata1mg/deputydev-vscode-extension.git
git clone https://github.com/tata1mg/deputydev-core.git
```

## Step 2: Configure Backend Services

### Create Configuration Files

Run the following command in both `deputydev-auth` and `deputydev-extension-backend` directories:

```bash
cp config_template.json config.json
```

This creates configuration files for both the auth service and backend. The services depend on Redis, LocalStack, and PostgreSQL, which will be set up automatically by Docker Compose. The `config_template.json` already contains the credentials for the local setup. If you need to modify these credentials, edit both the `docker-compose.yml` and `config.json` files accordingly.

### Add API Credentials

In the `deputydev-extension-backend` configuration, you'll need to add your credentials for the following services:

- **AWS S3** - for file storage (By default, a localstack container is already pointed to)
- **AWS Bedrock** - for AI model access (If you want to use Claude models via BedRock)
- **OpenAI API Key** - for reranking functionality and OpenAI models (required)
- **OpenRouter API Key** - for additional AI models
- **Vertex AI Keys** - for Gemini models

**Note:** The current system requires OpenAI for reranking functionality, so this credential is mandatory. Other API keys can be configured based on your model preferences.

### Authentication Setup

By default, `deputydev-auth` runs in fake auth mode for local development. If you prefer to integrate with Supabase, you can configure it, but you'll need to create your own frontend for the sign-in process.

Now, run the backend using the following command in `deputydev-extension-backend` (as it has the docker-compose file)
```
docker compose up --build
```
This should take a while, and will setup your services - deputydev-auth, deputydev-extension-backend and deputydev-binary.

## Step 3: Set Up VS Code Extension

Navigate to the `deputydev-vscode-extension` folder and run:

```bash
yarn install:all
```

### Configure Environment

Copy the environment template and configure it for local development:

```bash
cp .env.example .env
```

Edit the `.env` file to configure it for local development.
```
Uncomment DD_HOST=http://localhost:8084
Uncomment BINARY_DD_HOST=http://deputydev-extension-backend:8084
And toggle USE_LOCAL_BINARY to true
```
### Build the Extension

```bash
yarn build:all
```

Now, run the extension using debug menu in VSCode and selecting Run Extension when opening the folder deputydev-vscode-extension
