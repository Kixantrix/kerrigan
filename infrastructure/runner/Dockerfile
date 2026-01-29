# Dockerfile for Self-Hosted GitHub Actions Runner with Copilot CLI
#
# This Dockerfile creates a self-hosted GitHub Actions runner with
# GitHub CLI and Copilot CLI pre-installed for SDK Agent workflows.
#
# Build: docker build -t kerrigan-runner -f infrastructure/runner/Dockerfile .
# Run: docker run -d --name kerrigan-runner \
#        -v runner-auth:/home/runner/.config/gh \
#        -v runner-copilot:/home/runner/.copilot \
#        -e RUNNER_TOKEN=<token> \
#        -e RUNNER_NAME=kerrigan-runner \
#        kerrigan-runner

FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Set up runner user
RUN useradd -m -s /bin/bash runner && \
    usermod -aG sudo runner && \
    echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Install base dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    build-essential \
    libssl-dev \
    python3 \
    python3-pip \
    sudo \
    wget \
    unzip \
    gnupg \
    software-properties-common \
    ca-certificates \
    apt-transport-https \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
    dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | \
    tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    apt-get update && \
    apt-get install -y gh && \
    rm -rf /var/lib/apt/lists/*

# Switch to runner user
USER runner
WORKDIR /home/runner

# Install Copilot CLI extension
RUN gh extension install github/gh-copilot

# Download and extract GitHub Actions runner
ARG RUNNER_VERSION=2.311.0
RUN mkdir -p /home/runner/actions-runner && \
    cd /home/runner/actions-runner && \
    curl -o actions-runner-linux-x64.tar.gz -L \
    "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" && \
    tar xzf actions-runner-linux-x64.tar.gz && \
    rm actions-runner-linux-x64.tar.gz

# Copy scripts
COPY --chown=runner:runner scripts/runner /home/runner/scripts

# Create directories for persistent data
RUN mkdir -p /home/runner/.config/gh && \
    mkdir -p /home/runner/.copilot && \
    mkdir -p /home/runner/logs

# Copy entrypoint script
COPY --chown=runner:runner infrastructure/runner/entrypoint.sh /home/runner/entrypoint.sh
RUN chmod +x /home/runner/entrypoint.sh

# Expose volumes for persistent authentication
VOLUME ["/home/runner/.config/gh", "/home/runner/.copilot"]

# Set environment variables
ENV RUNNER_ALLOW_RUNASROOT=0
ENV RUNNER_WORKDIR=/home/runner/actions-runner/_work

ENTRYPOINT ["/home/runner/entrypoint.sh"]
