# Secure Anonymous Connection Script

A modular Python project that establishes secure and anonymous internet connections using SoftEther VPN (via VPNGate), custom DNS configuration, and optional DNSCrypt for encrypted DNS queries.

## 🚀 Features

- **SoftEther VPN Integration**: Automatically installs and configures SoftEther VPN client
- **VPNGate Connection**: Connects to free VPNGate servers worldwide
- **Secure DNS**: Configures secure DNS providers (Cloudflare, Quad9, Google, etc.)
- **DNSCrypt Support**: Optional encrypted DNS queries using DNSCrypt-proxy
- **Modular Design**: Each component is a separate, testable module
- **Docker Ready**: Designed to run in Linux Docker containers
- **Comprehensive Logging**: Detailed logging for troubleshooting
- **Status Monitoring**: Real-time status display with IP, DNS, and service information
- **Safety Features**: Backup and restore capabilities for system configurations

## 💻 Platform Support

### 🐧 Linux (Recommended)
- **Native Support**: Ubuntu 20.04+, Debian 11+, CentOS 8+
- **Requirements**: Root access, Python 3.6+, internet connectivity

### 🖥️ Windows Users
**This script is designed for Linux, but you can run it on Windows using:**

#### Option 1: WSL (Recommended) 🌟
```powershell
# Install WSL with Ubuntu
wsl --install Ubuntu-22.04

# After restart, open Ubuntu and run:
sudo python3 main.py
```

#### Option 2: Docker Desktop 🐳
```powershell
# Build and run the container
docker build -t secure-connection .
docker run --privileged --cap-add=NET_ADMIN -it secure-connection
```

#### Option 3: Check Environment 🔍
```bash
# Run this first to get detailed setup instructions
python check_environment.py
```

### 🔧 Quick Windows Setup
1. **Download project** to `C:\secure-connection`
2. **Run environment check**: `python check_environment.py`
3. **Follow the displayed instructions** for your preferred method

## 📁 Project Structure

```
connections_script/
├── main.py                     # Main orchestration script
├── requirements.txt            # Python dependencies (optional)
├── README.md                   # This file
└── network/                    # Network security modules
    ├── __init__.py            # Package initialization
    ├── install_softether.py   # SoftEther VPN installation
    ├── connect_vpngate.py     # VPNGate server connection
    ├── configure_dns.py       # Secure DNS configuration
    └── enable_dnscrypt.py     # DNSCrypt encrypted DNS
```

## 🐳 Docker Usage

### Build Docker Image

```dockerfile
FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    curl \
    build-essential \
    systemd \
    dnsutils \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . /app
WORKDIR /app

# Install Python dependencies (optional)
RUN pip3 install -r requirements.txt

# Run the application
CMD ["python3", "main.py"]
```

### Run Container

```bash
# Build the image
docker build -t secure-connection .

# Run with privileges (required for VPN and system configuration)
docker run --privileged --cap-add=NET_ADMIN -it secure-connection

# Run with custom options
docker run --privileged --cap-add=NET_ADMIN -it secure-connection \
    python3 main.py --dns-provider quad9 --countries US,CA,GB
```

## 💻 Local Usage

### Prerequisites

- Linux system (Ubuntu, Debian, CentOS, etc.)
- Root/sudo access
- Internet connectivity
- Python 3.6+

### Basic Usage

```bash
# Make the script executable
chmod +x main.py

# Run with default settings (requires sudo)
sudo python3 main.py

# Run with custom DNS provider
sudo python3 main.py --dns-provider quad9

# Skip DNSCrypt setup
sudo python3 main.py --no-dnscrypt

# Use custom DNS servers
sudo python3 main.py --custom-dns 1.1.1.1,1.0.0.1

# Prefer specific countries for VPN servers
sudo python3 main.py --countries US,CA,GB,DE

# Enable verbose logging
sudo python3 main.py --verbose
```

### Command Line Options

```
usage: main.py [-h] [--dns-provider {cloudflare,cloudflare_family,quad9,opendns,google,adguard}]
               [--custom-dns CUSTOM_DNS] [--no-dnscrypt] [--countries COUNTRIES]
               [--softether-dir SOFTETHER_DIR] [--verbose] [--status-only]

optional arguments:
  -h, --help            show this help message and exit
  --dns-provider        DNS provider to use (default: cloudflare)
  --custom-dns          Custom DNS servers (comma-separated IPs)
  --no-dnscrypt         Skip DNSCrypt setup
  --countries           Preferred VPN server countries (comma-separated codes)
  --softether-dir       SoftEther installation directory
  --verbose             Enable verbose logging
  --status-only         Show current connection status without making changes
```

### 📊 Status Monitoring

```bash
# Check current connection status
sudo python3 main.py --status-only

# This will show:
# • Current IP address and location
# • DNS server configuration and speed
# • VPN connection status
# • DNSCrypt service status
# • Security test results
```

## 🔧 Module Documentation

### 1. SoftEther Installation (`install_softether.py`)

Handles downloading, compiling, and installing SoftEther VPN client.

```python
from network.install_softether import install_softether

# Install SoftEther to default location
success, error = install_softether()

# Install to custom directory
success, error = install_softether("/custom/path")
```

**Features:**
- Automatic dependency checking and installation
- Source compilation from GitHub releases
- Systemd service configuration
- Installation verification

### 2. VPNGate Connection (`connect_vpngate.py`)

Manages connection to VPNGate servers with automatic server selection.

```python
from network.connect_vpngate import connect_vpngate

# Connect to best available server
success, error = connect_vpngate()

# Connect with country preference
success, error = connect_vpngate(
    preferred_countries=['US', 'CA', 'GB']
)
```

**Features:**
- VPNGate API integration
- Server quality filtering (score, ping, speed)
- Multiple connection attempts with fallback
- Connection status monitoring

### 3. DNS Configuration (`configure_dns.py`)

Configures secure DNS providers with backup/restore capabilities.

```python
from network.configure_dns import configure_dns, list_dns_providers

# Configure Cloudflare DNS
success, error = configure_dns('cloudflare')

# Use custom DNS servers
success, error = configure_dns(custom_servers=['1.1.1.1', '1.0.0.1'])

# List available providers
providers = list_dns_providers()
```

**Available DNS Providers:**
- `cloudflare`: Cloudflare DNS (1.1.1.1)
- `cloudflare_family`: Cloudflare for Families (1.1.1.3)
- `quad9`: Quad9 DNS (9.9.9.9)
- `opendns`: OpenDNS (208.67.222.222)
- `google`: Google Public DNS (8.8.8.8)
- `adguard`: AdGuard DNS (94.140.14.14)

### 4. DNSCrypt Setup (`enable_dnscrypt.py`)

Installs and configures DNSCrypt-proxy for encrypted DNS queries.

```python
from network.enable_dnscrypt import enable_dnscrypt, get_dnscrypt_status

# Enable DNSCrypt with default resolvers
success, error = enable_dnscrypt()

# Use custom resolvers
success, error = enable_dnscrypt(
    resolvers=['cloudflare', 'quad9-dnscrypt-ip4-nofilter-pri']
)

# Check service status
status = get_dnscrypt_status()
```

**Features:**
- Automatic download and installation
- Secure resolver configuration
- Systemd service management
- DNS resolution testing

## 🔐 Security Features

### VPN Security
- Automatic connection to high-quality VPNGate servers
- Server filtering based on security criteria
- Connection verification and monitoring

### DNS Security
- Multiple secure DNS provider options
- DNS-over-HTTPS (DoH) support via DNSCrypt
- DNS leak prevention
- Configuration backup and restoration

### System Security
- Minimal privilege requirements
- Safe configuration changes with rollback
- Comprehensive logging for audit trails
- Input validation and error handling

## 📋 Logs and Monitoring

### Log Locations
- Main log: `/var/log/secure_connection.log`
- DNSCrypt log: `/opt/dnscrypt-proxy/config/dnscrypt-proxy.log`
- System logs: `journalctl -u vpnclient` and `journalctl -u dnscrypt-proxy`

### Monitoring Commands

```bash
# Check VPN status
systemctl status vpnclient

# Check DNSCrypt status
systemctl status dnscrypt-proxy

# View connection logs
tail -f /var/log/secure_connection.log

# Test DNS resolution
nslookup google.com
dig @127.0.0.1 example.com

# Check current IP
curl https://api.ipify.org
```

## 🛠️ Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Ensure running as root
   sudo python3 main.py
   ```

2. **VPN Connection Fails**
   ```bash
   # Check available servers
   python3 -c "from network.connect_vpngate import VPNGateConnector; print(len(VPNGateConnector().fetch_vpngate_servers()))"
   
   # Try different countries
   sudo python3 main.py --countries JP,KR,SG
   ```

3. **DNS Resolution Issues**
   ```bash
   # Test DNS manually
   nslookup google.com 1.1.1.1
   
   # Reset DNS configuration
   sudo systemctl restart systemd-resolved
   ```

4. **DNSCrypt Not Working**
   ```bash
   # Check service status
   sudo systemctl status dnscrypt-proxy
   
   # View service logs
   sudo journalctl -u dnscrypt-proxy -f
   ```

### Recovery Commands

```bash
# Restore original DNS settings
sudo cp /etc/resolv.conf.backup /etc/resolv.conf

# Stop all services
sudo systemctl stop dnscrypt-proxy
sudo systemctl stop vpnclient

# Remove immutable flag from resolv.conf
sudo chattr -i /etc/resolv.conf
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with proper tests
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## ⚖️ Legal Notice

This software is provided for educational and legitimate privacy purposes only. Users are responsible for:

- Complying with local laws and regulations
- Respecting VPN service terms of use
- Using the software ethically and responsibly
- Understanding that VPN services may have usage policies

The authors are not responsible for any misuse of this software.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Resources

- [SoftEther VPN Project](https://www.softether.org/)
- [VPNGate Service](https://www.vpngate.net/)
- [DNSCrypt-proxy](https://github.com/DNSCrypt/dnscrypt-proxy)
- [Cloudflare DNS](https://1.1.1.1/)
- [Quad9 DNS](https://www.quad9.net/)

---

**⚠️ Important**: This script modifies system network configuration. Always test in a safe environment first and ensure you have a way to restore original settings if needed.
