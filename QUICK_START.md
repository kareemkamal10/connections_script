# 🚀 Quick Start Guide

## Docker Testing Commands

### 🐧 Linux/Mac/WSL:
```bash
# Make the test script executable
chmod +x test_docker.sh

# Run the test script
./test_docker.sh
```

### 🖥️ Windows PowerShell:
```powershell
# Run the PowerShell test script
.\Test-Docker.ps1
```

## Manual Docker Commands

### 1. Build the Image:
```bash
docker build -t secure-connection .
```

### 2. Test Commands:

#### Safe Tests (No Privileges Required):
```bash
# Basic status check
docker run --rm secure-connection python3 main.py --status-only

# Environment check
docker run --rm secure-connection python3 check_environment.py

# Interactive shell
docker run --rm -it secure-connection /bin/bash
```

#### Full Setup (Requires Privileges):
```bash
# Default setup
docker run --privileged --cap-add=NET_ADMIN --cap-add=SYS_ADMIN -it secure-connection

# Custom DNS
docker run --privileged --cap-add=NET_ADMIN -it secure-connection \
    python3 main.py --dns-provider quad9

# Skip DNSCrypt
docker run --privileged --cap-add=NET_ADMIN -it secure-connection \
    python3 main.py --no-dnscrypt

# Verbose logging
docker run --privileged --cap-add=NET_ADMIN -it secure-connection \
    python3 main.py --verbose
```

## Troubleshooting

### Common Issues:

1. **"No internet connectivity detected"**
   - This is normal in CI environments
   - Use test mode: `-e TEST_MODE=true`

2. **"Permission denied"**
   - Add privileged flags: `--privileged --cap-add=NET_ADMIN`

3. **"Docker not found"**
   - Install Docker Desktop
   - Ensure Docker is running

### Test Mode:
```bash
# Run in test mode (skips connectivity checks)
docker run --rm -e TEST_MODE=true secure-connection python3 main.py --status-only
```

## Expected Output

### Successful Build:
```
✅ Prerequisites check passed
✅ SoftEther VPN installed successfully
✅ VPN connection established
✅ DNS configured successfully
✅ DNSCrypt configured successfully
🎉 ALL SYSTEMS OPERATIONAL - SECURE CONNECTION ESTABLISHED!
```

### Status Check Output:
```
📊 CURRENT CONNECTION STATUS
🌐 Current IP: xxx.xxx.xxx.xxx
📍 Location: City, Country
🛡️  DNS Configuration: 1.1.1.1, 1.0.0.1
🔐 DNSCrypt Status: Running
🧪 Quick Tests: All passed
```

## Next Steps

1. **Local Testing**: Use the test scripts above
2. **Full Setup**: Run with privileged mode for complete VPN setup
3. **Customization**: Modify DNS providers and country preferences
4. **Production**: Deploy to a Linux server or cloud instance

For more detailed information, see the main [README.md](README.md)
