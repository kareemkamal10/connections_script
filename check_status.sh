#!/bin/bash

# Run the container in status-only mode
docker run --rm --cap-add=NET_ADMIN --device=/dev/net/tun --network=host secure-connection --status-only