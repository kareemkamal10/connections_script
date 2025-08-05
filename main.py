#!/usr/bin/env python3
import subprocess
import requests
import time
import argparse
import random
import os
import sys
import logging
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constants
VPN_GATE_CSV_URL = "https://www.vpngate.net/api/iphone/"
DNS_RESOLV_CONF = "/etc/resolv.conf"
DNSCRYPT_PROXY_TOML = "/etc/dnscrypt-proxy/dnscrypt-proxy.toml"

def get_current_ip():
    """Get the current public IP address"""
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=10)
        return response.json()["ip"]
    except Exception as e:
        logging.error(f"Error getting IP: {e}")
        return "Unknown"

def get_location(ip):
    """Get location information for an IP"""
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=10)
        data = response.json()
        return f"{data.get('city', 'Unknown')}, {data.get('country_name', 'Unknown')}"
    except Exception as e:
        logging.error(f"Error getting location: {e}")
        return "Unknown"

def get_dns_servers():
    """Get current DNS servers from resolv.conf"""
    dns_servers = []
    try:
        with open(DNS_RESOLV_CONF, 'r') as f:
            for line in f:
                if line.startswith('nameserver'):
                    dns_servers.append(line.split()[1])
    except Exception as e:
        logging.error(f"Error reading DNS configuration: {e}")
    
    return dns_servers

def test_dns_speed():
    """Test DNS resolution speed"""
    start = time.time()
    try:
        subprocess.run(["dig", "google.com", "+short"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        end = time.time()
        return f"{(end - start)*1000:.2f}ms"
    except Exception as e:
        logging.error(f"Error testing DNS speed: {e}")
        return "Failed to test"

def check_vpn_status():
    """Check if VPN is connected"""
    try:
        result = subprocess.run(["ip", "link", "show", "tun0"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        if result.returncode == 0:
            return "Connected"
        else:
            return "Not connected or not available"
    except Exception as e:
        logging.error(f"Error checking VPN status: {e}")
        return "Error checking status"

def check_dnscrypt_status():
    """Check DNSCrypt service status"""
    service_status = "Not running"
    autostart_status = "Not enabled"
    
    try:
        # Check if service is running
        result = subprocess.run(["systemctl", "is-active", "dnscrypt-proxy"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        if result.returncode == 0:
            service_status = "Running"
        
        # Check if autostart is enabled
        result = subprocess.run(["systemctl", "is-enabled", "dnscrypt-proxy"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        if result.returncode == 0:
            autostart_status = "Enabled"
    except Exception as e:
        logging.error(f"Error checking DNSCrypt status: {e}")
    
    return service_status, autostart_status

def test_dns_leak():
    """Test for DNS leaks"""
    try:
        # Simple check - see if we're using dnscrypt-proxy local port
        dns_servers = get_dns_servers()
        if "127.0.0.1" in dns_servers or "::1" in dns_servers:
            return True
        return False
    except Exception as e:
        logging.error(f"Error testing DNS leak: {e}")
        return False

def test_ip_change(original_ip):
    """Test if IP has changed after VPN connection"""
    current_ip = get_current_ip()
    return current_ip != original_ip and current_ip != "Unknown"

def test_dns_resolution():
    """Test if DNS resolution works"""
    try:
        result = subprocess.run(["dig", "google.com", "+short"], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
        return result.returncode == 0 and len(result.stdout) > 0
    except Exception as e:
        logging.error(f"Error testing DNS resolution: {e}")
        return False

def test_encrypted_dns():
    """Test if we're using encrypted DNS"""
    try:
        # Check if DNSCrypt is running and we're using localhost as DNS
        service_status, _ = check_dnscrypt_status()
        dns_servers = get_dns_servers()
        return service_status == "Running" and ("127.0.0.1" in dns_servers or "::1" in dns_servers)
    except Exception as e:
        logging.error(f"Error testing encrypted DNS: {e}")
        return False

def test_internet():
    """Test general internet connectivity"""
    try:
        response = requests.get("https://www.google.com", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Error testing internet: {e}")
        return False

def setup_vpngate():
    """Connect to VPNGate VPN"""
    logging.info("Setting up VPN connection through VPNGate...")
    
    try:
        # Download VPNGate server list
        response = requests.get(VPN_GATE_CSV_URL, timeout=15)
        csv_data = response.text.split('\n')
        
        # Skip header and empty lines
        server_list = [line for line in csv_data if line and not line.startswith('*')]
        
        if not server_list:
            logging.error("Failed to get VPNGate server list")
            return False
        
        # Filter for OpenVPN servers and sort by score
        openvpn_servers = []
        for server in server_list:
            parts = server.split(',')
            if len(parts) >= 15 and parts[6]:  # Check if OpenVPN config exists
                score = int(parts[2]) if parts[2].isdigit() else 0
                country = parts[5]
                openvpn_config = parts[14]
                openvpn_servers.append((score, country, openvpn_config))
        
        # Sort by score (highest first)
        openvpn_servers.sort(reverse=True)
        
        # Take the top 5 servers and pick one randomly for load balancing
        top_servers = openvpn_servers[:5]
        if not top_servers:
            logging.error("No suitable VPN servers found")
            return False
            
        chosen = random.choice(top_servers)
        logging.info(f"Selected VPN server in {chosen[1]}")
        
        # Save OpenVPN config to file
        with open("/tmp/vpngate.ovpn", "w") as f:
            import base64
            ovpn_config = base64.b64decode(chosen[2]).decode('utf-8')
            f.write(ovpn_config)
        
        # Kill any existing OpenVPN processes
        subprocess.run(["pkill", "-9", "openvpn"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)
        
        # Start OpenVPN as a background process
        process = subprocess.Popen(["openvpn", "--config", "/tmp/vpngate.ovpn"], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE)
        
        # Wait for connection to establish
        logging.info("Waiting for VPN connection to establish...")
        for _ in range(30):  # Wait up to 30 seconds
            if check_vpn_status() == "Connected":
                logging.info("VPN connected successfully")
                return True
            time.sleep(1)
        
        logging.error("VPN connection timed out")
        return False
    
    except Exception as e:
        logging.error(f"Error setting up VPN: {e}")
        return False

def setup_dnscrypt():
    """Set up DNSCrypt-proxy"""
    logging.info("Setting up DNSCrypt-proxy...")
    
    try:
        # Install dnscrypt-proxy if not installed
        if not os.path.exists("/usr/sbin/dnscrypt-proxy"):
            logging.info("Installing DNSCrypt-proxy...")
            subprocess.run(["apt-get", "update"], check=True)
            subprocess.run(["apt-get", "install", "-y", "dnscrypt-proxy"], check=True)
        
        # Create a new configuration file
        with open(DNSCRYPT_PROXY_TOML, "w") as f:
            f.write("""
# DNSCrypt-proxy configuration
listen_addresses = ['127.0.0.1:53', '[::1]:53']
server_names = ['cloudflare', 'google']
require_dnssec = true
require_nolog = true
require_nofilter = true
ipv4_servers = true
ipv6_servers = false
block_unqualified = true
block_undelegated = true
reject_ttl = 600
bootstrap_resolvers = ['9.9.9.9:53', '1.1.1.1:53']
netprobe_timeout = 60
cache = true
cache_size = 4096
cache_min_ttl = 2400
cache_max_ttl = 86400
cache_neg_min_ttl = 60
cache_neg_max_ttl = 600
            """)

        # Stop existing service if running
        subprocess.run(["systemctl", "stop", "dnscrypt-proxy"], 
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Start service
        subprocess.run(["systemctl", "start", "dnscrypt-proxy"], check=True)
        
        # Enable autostart
        subprocess.run(["systemctl", "enable", "dnscrypt-proxy"], check=True)
        
        # Update resolv.conf to use DNSCrypt
        with open(DNS_RESOLV_CONF, "w") as f:
            f.write("nameserver 127.0.0.1\n")
            f.write("options edns0\n")
        
        # Check if service is running
        time.sleep(2)  # Give it time to start
        service_status, _ = check_dnscrypt_status()
        if service_status == "Running":
            logging.info("DNSCrypt-proxy configured and running")
            return True
        else:
            logging.error("DNSCrypt-proxy failed to start")
            return False
            
    except Exception as e:
        logging.error(f"Error setting up DNSCrypt: {e}")
        return False

def status_report():
    """Print current connection status"""
    original_ip = get_current_ip()
    location = get_location(original_ip)
    dns_servers = get_dns_servers()
    dns_speed = test_dns_speed()
    vpn_status = check_vpn_status()
    dnscrypt_service, dnscrypt_autostart = check_dnscrypt_status()
    
    # Tests
    dns_leak_test = test_dns_leak()
    ip_change_test = test_ip_change(original_ip)
    dns_resolution_test = test_dns_resolution()
    encrypted_dns_test = test_encrypted_dns()
    internet_test = test_internet()
    
    # Print the report
    print("\n============================================================")
    print("📊 CURRENT CONNECTION STATUS")
    print("============================================================")
    print(f"🌐 Current IP: {original_ip}")
    print(f"📍 Location: {location}")
    print("")
    print(f"🛡️  DNS Configuration:")
    print(f"   DNS Servers: {', '.join(dns_servers)}")
    logging.info(f"Current DNS servers: {dns_servers}")
    print(f"   DNS Speed: {dns_speed}")
    print("")
    print(f"🔗 VPN Status:")
    print(f"   Status: {vpn_status}")
    print("")
    print(f"🔐 DNSCrypt Status:")
    print(f"   Service: {dnscrypt_service}")
    print(f"   Autostart: {dnscrypt_autostart}")
    print("")
    print(f"🧪 Quick Tests:")
    print(f"   {'✅' if dns_leak_test else '❌'} DNS Leak Protection")
    print(f"   {'✅' if ip_change_test else '❌'} IP Change Verification")
    print(f"   {'✅' if dns_resolution_test else '❌'} DNS Resolution")
    print(f"   {'✅' if encrypted_dns_test else '❌'} Encrypted DNS")
    print(f"   {'✅' if internet_test else '❌'} Internet Connectivity")
    print("============================================================")

def main():
    parser = argparse.ArgumentParser(description="Secure Connection Script")
    parser.add_argument("--status-only", action="store_true", help="Only show status without making changes")
    args = parser.parse_args()
    
    # Just report status if requested
    if args.status_only:
        status_report()
        return
    
    # Otherwise, proceed with the full setup
    print("🚀 Starting secure connection setup...")
    
    # 1. Setup VPN
    if setup_vpngate():
        print("✅ VPN setup completed")
    else:
        print("❌ VPN setup failed")
    
    # 2. Setup DNSCrypt
    if setup_dnscrypt():
        print("✅ DNSCrypt setup completed")
    else:
        print("❌ DNSCrypt setup failed")
    
    # 3. Final status report
    print("\n🔍 Final connection status:")
    status_report()

if __name__ == "__main__":
    # Check if running in Docker with appropriate permissions
    if os.geteuid() != 0:
        print("⚠️ This script requires root privileges to run properly.")
        sys.exit(1)
    
    # Check if in test mode
    if os.environ.get("TEST_MODE", "").lower() == "true":
        print("🧪 Running in test mode - showing status only")
        status_report()
        sys.exit(0)
    
    main()