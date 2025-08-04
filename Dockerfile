# Dockerfile optimized for GitHub Actions CI environment
FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# CI Environment Detection
ENV CI=true
ENV GITHUB_ACTIONS=true
ENV TEST_MODE=true

# Install system dependencies optimized for CI
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    curl \
    ca-certificates \
    dnsutils \
    net-tools \
    iputils-ping \
    iproute2 \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

# Install minimal build tools for CI
RUN apt-get update && apt-get install -y \
    gcc \
    make \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create mock systemctl for CI environment
RUN echo '#!/bin/bash\n\
case "$1" in\n\
  "is-active")\n\
    case "$2" in\n\
      "dnscrypt-proxy") echo "inactive" ;;\n\
      "systemd-resolved") echo "active" ;;\n\
      *) echo "inactive" ;;\n\
    esac\n\
    exit 0 ;;\n\
  "enable"|"start"|"stop"|"restart")\n\
    echo "systemctl $1 $2 (simulated in CI)"\n\
    exit 0 ;;\n\
  "status")\n\
    echo "● $2.service - Mock service for CI"\n\
    echo "   Active: active (running) since $(date)"\n\
    exit 0 ;;\n\
  *)\n\
    echo "systemctl: $* (mocked for CI environment)"\n\
    exit 0 ;;\n\
esac' > /usr/bin/systemctl && \
    chmod +x /usr/bin/systemctl

# Create mock VPN tools for CI
RUN mkdir -p /opt/softether /opt/dnscrypt-proxy /var/log && \
    echo '#!/bin/bash\necho "VPN simulation: $*"' > /usr/bin/vpncmd && \
    chmod +x /usr/bin/vpncmd && \
    echo '#!/bin/bash\necho "DNSCrypt simulation: $*"' > /usr/bin/dnscrypt-proxy && \
    chmod +x /usr/bin/dnscrypt-proxy

# Create application directory
WORKDIR /app

# Copy requirements first for better Docker caching
COPY requirements.txt .

# Install Python dependencies with CI optimizations
RUN pip3 install --no-cache-dir --disable-pip-version-check \
    $(if [ -f requirements.txt ]; then cat requirements.txt; else echo "requests"; fi)

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x main.py

# Setup user and permissions for CI
RUN useradd -m -s /bin/bash appuser && \
    echo "appuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    touch /var/log/secure_connection.log && \
    chown appuser:appuser /var/log/secure_connection.log && \
    chown -R appuser:appuser /app

# Environment variables for CI
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV CI_MOCK_MODE=1

# Switch to app user
USER appuser

# Default command optimized for CI
CMD ["python3", "main.py", "--status-only", "--verbose"]

# Alternative entry points for different use cases:
# 
# Build the image:
# docker build -t secure-connection .
#
# Run with full privileges (required for VPN and system configuration):
# docker run --privileged --cap-add=NET_ADMIN --cap-add=SYS_ADMIN -it secure-connection
#
# Run with custom options:
# docker run --privileged --cap-add=NET_ADMIN -it secure-connection python3 main.py --dns-provider quad9 --countries US,CA
#
# Run in interactive mode for debugging:
# docker run --privileged --cap-add=NET_ADMIN -it secure-connection /bin/bash
#
# Run with volume mount for persistent logs:
# docker run --privileged --cap-add=NET_ADMIN -v /host/logs:/var/log -it secure-connection
