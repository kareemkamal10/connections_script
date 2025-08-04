# Dockerfile for Secure Anonymous Connection Script
FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    wget \
    curl \
    build-essential \
    gcc \
    make \
    tar \
    dnsutils \
    net-tools \
    iputils-ping \
    sudo \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy requirements first for better Docker caching
COPY requirements.txt .

# Install Python dependencies (optional)
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x main.py

# Create necessary directories
RUN mkdir -p /opt/softether \
    && mkdir -p /opt/dnscrypt-proxy \
    && mkdir -p /var/log

# Set up logging
RUN touch /var/log/secure_connection.log

# Create a non-root user for safer operation (when not requiring root privileges)
RUN useradd -m -s /bin/bash appuser \
    && usermod -aG sudo appuser

# Expose common ports (optional, for monitoring)
EXPOSE 53/udp 53/tcp

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

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
