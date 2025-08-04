# PowerShell Script for Testing Docker Container on Windows
# Test-Docker.ps1

Write-Host "🐳 Docker Container Test Script (Windows)" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue

# Function to print colored output
function Write-Status {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if Docker is available
try {
    $dockerVersion = docker --version
    Write-Status "Docker is available: $dockerVersion"
}
catch {
    Write-Error "Docker is not installed or not in PATH"
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
}

# Check if we're in the correct directory
if (-not (Test-Path "Dockerfile")) {
    Write-Error "Dockerfile not found. Please run this script from the project directory."
    exit 1
}

# Build the image
Write-Status "Building Docker image..."
try {
    docker build -t secure-connection .
    Write-Success "Docker image built successfully"
}
catch {
    Write-Error "Failed to build Docker image"
    exit 1
}

# Test basic functionality
Write-Status "Testing basic container functionality..."

Write-Host ""
Write-Host "1. Testing Python version..." -ForegroundColor Yellow
docker run --rm secure-connection python3 --version

Write-Host ""
Write-Host "2. Testing container OS..." -ForegroundColor Yellow
docker run --rm secure-connection cat /etc/os-release | Select-Object -First 3

Write-Host ""
Write-Host "3. Testing network tools..." -ForegroundColor Yellow
docker run --rm secure-connection which ping curl nslookup

Write-Host ""
Write-Host "4. Testing environment check script..." -ForegroundColor Yellow
docker run --rm secure-connection python3 check_environment.py

Write-Host ""
Write-Host "5. Testing status check (safe mode)..." -ForegroundColor Yellow
docker run --rm -e TEST_MODE=true secure-connection python3 main.py --status-only

Write-Host ""
Write-Success "All basic tests completed successfully!"

Write-Host ""
Write-Host "🚀 Available run commands:" -ForegroundColor Blue
Write-Host "=========================" -ForegroundColor Blue

Write-Host ""
Write-Host "• Basic status check (safe):" -ForegroundColor Green
Write-Host "  docker run --rm secure-connection python3 main.py --status-only" -ForegroundColor Gray

Write-Host ""
Write-Host "• Interactive mode:" -ForegroundColor Green
Write-Host "  docker run --rm -it secure-connection /bin/bash" -ForegroundColor Gray

Write-Host ""
Write-Host "• Full setup (requires privileged mode):" -ForegroundColor Green
Write-Host "  docker run --privileged --cap-add=NET_ADMIN --cap-add=SYS_ADMIN -it secure-connection" -ForegroundColor Gray

Write-Host ""
Write-Host "• Custom DNS provider:" -ForegroundColor Green
Write-Host "  docker run --privileged --cap-add=NET_ADMIN -it secure-connection python3 main.py --dns-provider quad9" -ForegroundColor Gray

Write-Host ""
Write-Host "• Skip DNSCrypt:" -ForegroundColor Green
Write-Host "  docker run --privileged --cap-add=NET_ADMIN -it secure-connection python3 main.py --no-dnscrypt" -ForegroundColor Gray

Write-Host ""
Write-Host "• Verbose logging:" -ForegroundColor Green
Write-Host "  docker run --privileged --cap-add=NET_ADMIN -it secure-connection python3 main.py --verbose" -ForegroundColor Gray

Write-Host ""
Write-Warning "Note: Full setup requires privileged Docker mode"
Write-Warning "On Windows, you may need to enable 'Experimental Features' in Docker Desktop"

Write-Host ""
Write-Host "📚 For more information, see README.md" -ForegroundColor Blue

# Prompt user for action
Write-Host ""
$choice = Read-Host "Would you like to run the container interactively now? (y/N)"
if ($choice -eq "y" -or $choice -eq "Y") {
    Write-Status "Starting interactive container..."
    docker run --rm -it secure-connection /bin/bash
}
