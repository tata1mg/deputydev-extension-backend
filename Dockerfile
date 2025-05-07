ARG cloud
FROM --platform=linux/amd64 ${cloud:+"831059512818.dkr.ecr.ap-south-1.amazonaws.com/utility/docker/library/"}python:3.11.9-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Poetry venv in same folder for easy mobility
ENV POETRY_VIRTUALENVS_IN_PROJECT=1

# Args passed in the build command
ARG SSH_PRIVATE_KEY
ARG SSH_PUBLIC_KEY
ARG SERVICE_NAME

RUN apt-get update && \
    apt-get install -y \
        git \
        gcc \
        openssh-server \
        curl

RUN echo "Y" | apt-get install procps

RUN curl -fsSL -o /usr/local/bin/dbmate https://github.com/amacneil/dbmate/releases/latest/download/dbmate-linux-amd64 && chmod +x /usr/local/bin/dbmate
# For Dexter service
# For hr_digitisation service

# Authorize SSH Host
RUN mkdir -p /root/.ssh && \
    chmod 0700 /root/.ssh && \
    ssh-keyscan bitbucket.org >> /root/.ssh/known_hosts && \
    ssh-keyscan github.com >> /root/.ssh/known_hosts

# Add the keys and set permissions
RUN echo "$SSH_PRIVATE_KEY" > /root/.ssh/id_ed25519 && \
    echo "$SSH_PUBLIC_KEY" > /root/.ssh/id_ed25519.pub && \
    chmod 600 /root/.ssh/id_ed25519 && \
    chmod 600 /root/.ssh/id_ed25519.pub


RUN pip install poetry=="1.8.3"
RUN pip install --upgrade pip

COPY poetry.lock pyproject.toml ./
RUN poetry install --only main --no-root -vvv

# Create home ubuntu service hydra
RUN mkdir -p /home/ubuntu/1mg/$SERVICE_NAME/logs

# switch to code folder
WORKDIR /home/ubuntu/1mg/$SERVICE_NAME

# Copy and install requirements
ENV PATH="/.venv/bin:$PATH"
RUN pip install click==8.1.3

# Copy code folder
COPY . .
