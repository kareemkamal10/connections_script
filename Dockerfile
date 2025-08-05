FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install necessary packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    openvpn \
    iproute2 \
    dnsutils \
    systemctl \
    curl \
    net-tools \
    dnscrypt-proxy \
    iputils-ping \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Copy the script into the container
COPY . /app
WORKDIR /app

# Make the script executable
RUN chmod +x /app/main.py

# Run the script
ENTRYPOINT ["python3", "main.py"]