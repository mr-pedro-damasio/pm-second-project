FROM mcr.microsoft.com/devcontainers/base:ubuntu

# Add common build tools and certificates.
RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends build-essential curl ca-certificates \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*
