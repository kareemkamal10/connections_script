# Dockerfile for Secure Anonymous Connection Script
FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies in two stages for better caching
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    curl \
    ca-certificates \
    dnsutils \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

# Install build tools only if needed (separate layer for better caching)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    make \
    tar \
    bind9-dnsutils \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy requirements first for better Docker caching
COPY requirements.txt .

# Install Python dependencies (optional)
RUN if [ -f requirements.txt ]; then pip3 install --no-cache-dir -r requirements.txt; fi

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x main.py

# Create necessary directories and setup
RUN mkdir -p /opt/softether /opt/dnscrypt-proxy /var/log && \
    touch /var/log/secure_connection.log && \
    useradd -m -s /bin/bash appuser && \
    usermod -aG sudo appuser

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TEST_MODE=1

# Default command - run the main script
CMD ["python3", "main.py", "--verbose"]

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
