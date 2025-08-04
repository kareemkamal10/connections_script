#!/bin/bash
# Local Docker Test Script
# This script provides easy commands to test the Docker container locally

set -e

echo "🐳 Docker Container Test Script"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

print_status "Docker is available"

# Build the image
print_status "Building Docker image..."
if docker build -t secure-connection .; then
    print_success "Docker image built successfully"
else
    print_error "Failed to build Docker image"
    exit 1
fi

# Test basic functionality
print_status "Testing basic container functionality..."

echo ""
echo "1. Testing Python version..."
docker run --rm secure-connection python3 --version

echo ""
echo "2. Testing container OS..."
docker run --rm secure-connection cat /etc/os-release | head -3

echo ""
echo "3. Testing network tools..."
docker run --rm secure-connection which ping curl nslookup

echo ""
echo "4. Testing environment check script..."
docker run --rm secure-connection python3 check_environment.py

echo ""
echo "5. Testing status check (safe mode)..."
docker run --rm -e TEST_MODE=true secure-connection python3 main.py --status-only

echo ""
print_success "All basic tests completed successfully!"

echo ""
echo "🚀 Available run commands:"
echo "========================="

echo ""
echo "• Basic status check (safe):"
echo "  docker run --rm secure-connection python3 main.py --status-only"

echo ""
echo "• Interactive mode:"
echo "  docker run --rm -it secure-connection /bin/bash"

echo ""
echo "• Full setup (requires privileged mode):"
echo "  docker run --privileged --cap-add=NET_ADMIN --cap-add=SYS_ADMIN -it secure-connection"

echo ""
echo "• Custom DNS provider:"
echo "  docker run --privileged --cap-add=NET_ADMIN -it secure-connection python3 main.py --dns-provider quad9"

echo ""
echo "• Skip DNSCrypt:"
echo "  docker run --privileged --cap-add=NET_ADMIN -it secure-connection python3 main.py --no-dnscrypt"

echo ""
echo "• Verbose logging:"
echo "  docker run --privileged --cap-add=NET_ADMIN -it secure-connection python3 main.py --verbose"

echo ""
print_warning "Note: Full setup requires privileged Docker mode and may not work in all environments"
print_status "For Windows users, consider using WSL or checking system compatibility first"

echo ""
echo "📚 For more information, see README.md"
