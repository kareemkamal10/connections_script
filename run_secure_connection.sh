#!/bin/bash

# Build the Docker image
docker build -t secure-connection .

# Run the container with necessary privileges
docker run --rm --cap-add=NET_ADMIN --device=/dev/net/tun --sysctl net.ipv6.conf.all.disable_ipv6=0 --network=host -it secure-connection