#!/usr/bin/env python3
"""
DNSCrypt Configuration Module

This module handles the installation and configuration of DNSCrypt-proxy
for encrypted DNS resolution. DNSCrypt provides an additional layer of
security by encrypting DNS queries.
"""

import os
import subprocess
import logging
import json
import urllib.request
import tarfile
import shutil
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DNSCryptConfigurator:
    """
    Handles DNSCrypt-proxy installation and configuration for encrypted DNS.
    
    This class manages downloading, installing, and configuring DNSCrypt-proxy
    to provide encrypted DNS resolution with various privacy-focused resolvers.
    """
    
    def __init__(self, install_dir: str = "/opt/dnscrypt-proxy"):
        """
        Initialize the DNSCrypt configurator.
        
        Args:
            install_dir (str): Directory where DNSCrypt-proxy will be installed
        """
        self.install_dir = Path(install_dir)
        self.config_dir = self.install_dir / "config"
        self.binary_path = self.install_dir / "dnscrypt-proxy"
        self.config_file = self.config_dir / "dnscrypt-proxy.toml"
        self.service_file = Path("/etc/systemd/system/dnscrypt-proxy.service")
        
        # DNSCrypt-proxy download URL (GitHub releases)
        self.download_base_url = "https://github.com/DNSCrypt/dnscrypt-proxy/releases/latest/download"
        self.archive_name = "dnscrypt-proxy-linux_x86_64.tar.gz"
        
        # Default secure resolvers
        self.default_resolvers = [
            "cloudflare",
            "cloudflare-ipv6",
            "quad9-dnscrypt-ip4-nofilter-pri",
            "adguard-dns-doh",
        ]
    
    def check_dependencies(self) -> bool:
        """
        Check if required system dependencies are available.
        
        Returns:
            bool: True if all dependencies are available, False otherwise
        """
        logger.info("Checking DNSCrypt dependencies...")
        
        required_commands = ["wget", "tar", "systemctl"]
        missing_commands = []
        
        for cmd in required_commands:
            if not shutil.which(cmd):
                missing_commands.append(cmd)
        
        if missing_commands:
            logger.error(f"Missing required commands: {', '.join(missing_commands)}")
            return False
        
        logger.info("All DNSCrypt dependencies are available")
        return True
    
    def download_dnscrypt(self) -> bool:
        """
        Download DNSCrypt-proxy binary package.
        
        Returns:
            bool: True if download successful, False otherwise
        """
        logger.info("Downloading DNSCrypt-proxy...")
        
        try:
            download_url = f"{self.download_base_url}/{self.archive_name}"
            download_path = Path("/tmp") / self.archive_name
            
            # Download the archive
            urllib.request.urlretrieve(download_url, download_path)
            
            logger.info(f"Downloaded DNSCrypt-proxy to {download_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download DNSCrypt-proxy: {e}")
            return False
    
    def extract_and_install(self) -> bool:
        """
        Extract DNSCrypt-proxy and install to target directory.
        
        Returns:
            bool: True if installation successful, False otherwise
        """
        logger.info("Extracting and installing DNSCrypt-proxy...")
        
        try:
            download_path = Path("/tmp") / self.archive_name
            extract_dir = Path("/tmp/dnscrypt-extract")
            
            # Create extraction directory
            extract_dir.mkdir(exist_ok=True)
            
            # Extract the archive
            with tarfile.open(download_path, "r:gz") as tar:
                tar.extractall(extract_dir)
            
            # Find the extracted directory
            extracted_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
            if not extracted_dirs:
                logger.error("No directory found in extracted archive")
                return False
            
            source_dir = extracted_dirs[0]
            
            # Create install directory
            self.install_dir.mkdir(parents=True, exist_ok=True)
            self.config_dir.mkdir(exist_ok=True)
            
            # Copy binary
            binary_source = source_dir / "dnscrypt-proxy"
            if binary_source.exists():
                shutil.copy2(binary_source, self.binary_path)
                os.chmod(self.binary_path, 0o755)
                logger.info(f"Installed DNSCrypt-proxy binary to {self.binary_path}")
            else:
                logger.error("DNSCrypt-proxy binary not found in archive")
                return False
            
            # Copy example configuration if available
            config_source = source_dir / "example-dnscrypt-proxy.toml"
            if config_source.exists():
                shutil.copy2(config_source, self.config_dir / "example-dnscrypt-proxy.toml")
                logger.info("Copied example configuration")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to extract and install DNSCrypt-proxy: {e}")
            return False
    
    def create_configuration(self, 
                           listen_addresses: List[str] = None,
                           resolvers: List[str] = None,
                           enable_logging: bool = True) -> bool:
        """
        Create DNSCrypt-proxy configuration file.
        
        Args:
            listen_addresses (List[str]): Addresses to listen on
            resolvers (List[str]): List of resolver names to use
            enable_logging (bool): Whether to enable logging
            
        Returns:
            bool: True if configuration created successfully, False otherwise
        """
        logger.info("Creating DNSCrypt-proxy configuration...")
        
        try:
            if listen_addresses is None:
                listen_addresses = ["127.0.0.1:53", "[::1]:53"]
            
            if resolvers is None:
                resolvers = self.default_resolvers
            
            # Create configuration content
            config_content = f"""##############################################
#                                          #
#        DNSCrypt-proxy configuration      #
#                                          #
##############################################

##################################
#         Global settings        #
##################################

# List of servers to use
server_names = {json.dumps(resolvers)}

# List of local addresses and ports to listen to
listen_addresses = {json.dumps(listen_addresses)}

# Maximum number of simultaneous client connections to accept
max_clients = 250

# Require servers (from remote sources) to satisfy specific properties
ipv4_servers = true
ipv6_servers = true
dnscrypt_servers = true
doh_servers = true
odoh_servers = false

# Require servers defined by remote sources to satisfy specific properties
require_dnssec = true
require_nolog = true
require_nofilter = true

# Server must support DNS security extensions (DNSSEC)
force_tcp = false

# HTTP/HTTPS proxy
# proxy = "socks5://127.0.0.1:9050"

# How long a DNS query will wait for a response, in milliseconds
timeout = 5000

# Keepalive for HTTP (HTTPS, HTTP/2) queries, in seconds
keepalive = 30

# Response for blocked queries
blocked_query_response = 'refused'

# Load-balancing strategy: 'p2' (default), 'ph', 'first' or 'random'
lb_strategy = 'p2'

# Set to `true` to constantly try to estimate the latency of all the resolvers
# and adjust the load-balancing parameters accordingly, or to `false` to disable.
lb_estimator = true

##################################
#            Logging             #
##################################

# Log level (0-6, default: 2 - 0 is very verbose, 6 only contains fatal errors)
log_level = {"2" if enable_logging else "6"}

# log file for the application
log_file = '{self.config_dir / "dnscrypt-proxy.log"}' if enable_logging else ''

# Use the system logger (syslog on Unix, Event Log on Windows)
use_syslog = false

##################################
#        Filters & Blocking      #
##################################

# Immediately respond to IPv6-related queries with an empty response
block_ipv6 = false

# Immediately respond to A and AAAA queries for host names without a domain name
block_unqualified = true

# Immediately respond to queries for local zones instead of leaking them to
# upstream resolvers (always causing errors or timeouts).
block_undelegated = true

##################################
#           DNS cache            #
##################################

# Enable a DNS cache to reduce latency and outgoing traffic
cache = true

# Cache size
cache_size = 4096

# Minimum TTL for cached entries
cache_min_ttl = 2400

# Maximum TTL for cached entries
cache_max_ttl = 86400

# Minimum TTL for negatively cached entries
cache_neg_min_ttl = 60

# Maximum TTL for negatively cached entries
cache_neg_max_ttl = 600

##################################
#        Local DoH server        #
##################################

# Parameters for a local DoH server
# By default, queries are sent to upstream servers in a non-encrypted way.
# The recommended way to enable encryption is to use DoH or DNSCrypt.

[local_doh]

# Comma-separated list of local addresses to listen to
listen_addresses = []

# Local path (if blank, a built-in page will be used)
path = "/dns-query"

# TLS certificate and key file for the local DoH server
cert_file = ""
cert_key_file = ""

##################################
#       Anonymized DNS          #
##################################

# Routes are indirect ways to reach DNSCrypt servers.
# A route maps a server name ("server_name") to one or more relays that will be
# used to connect to that server.

# [anonymized_dns]

# Skip resolvers incompatible with anonymization instead of using them directly
# skip_incompatible = false

##################################
#            Sources             #
##################################

# Remote lists of available servers
# Multiple sources can be used simultaneously, but every source
# requires a dedicated cache file.

[sources]

  # An example of a remote source from https://github.com/DNSCrypt/dnscrypt-resolvers

  [sources.'public-resolvers']
  urls = ['https://raw.githubusercontent.com/DNSCrypt/dnscrypt-resolvers/master/v3/public-resolvers.md', 'https://download.dnscrypt.info/resolvers-list/v3/public-resolvers.md']
  cache_file = '{self.config_dir / "public-resolvers.md"}'
  minisign_key = 'RWQf6LRCGA9i53mlYecO4IzT51TGPpvWucNSCh1CBM0QTaLn73Y7GFO3'
  refresh_delay = 72
  prefix = ''

  [sources.'relays']
  urls = ['https://raw.githubusercontent.com/DNSCrypt/dnscrypt-resolvers/master/v3/relays.md', 'https://download.dnscrypt.info/resolvers-list/v3/relays.md']
  cache_file = '{self.config_dir / "relays.md"}'
  minisign_key = 'RWQf6LRCGA9i53mlYecO4IzT51TGPpvWucNSCh1CBM0QTaLn73Y7GFO3'
  refresh_delay = 72
  prefix = ''

##################################
#        Broken resolvers        #
##################################

# Resolvers can sometimes become misconfigured and either refuse to answer
# queries or always return incorrect responses.
# This mechanism allows reporting servers as temporarily broken.

[broken_implementations]

# List of servers to avoid, with the reason they were broken
# fragments_blocked = ['cisco', 'cisco-ipv6', 'cisco-familyshield', 'cisco-familyshield-ipv6', 'cleanbrowsing-adult', 'cleanbrowsing-adult-ipv6', 'cleanbrowsing-family', 'cleanbrowsing-family-ipv6', 'cleanbrowsing-security', 'cleanbrowsing-security-ipv6']
"""
            
            # Write configuration file
            with open(self.config_file, 'w') as f:
                f.write(config_content)
            
            logger.info(f"DNSCrypt-proxy configuration created at {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create DNSCrypt configuration: {e}")
            return False
    
    def create_systemd_service(self) -> bool:
        """
        Create systemd service file for DNSCrypt-proxy.
        
        Returns:
            bool: True if service created successfully, False otherwise
        """
        logger.info("Creating DNSCrypt-proxy systemd service...")
        
        try:
            service_content = f"""[Unit]
Description=DNSCrypt-proxy client
Documentation=https://github.com/DNSCrypt/dnscrypt-proxy/wiki
After=network.target
Before=nss-lookup.target
Wants=nss-lookup.target

[Service]
Type=simple
ExecStart={self.binary_path} -config {self.config_file}
Restart=always
RestartSec=5
User=nobody
Group=nogroup

# Security settings
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectHome=true
ProtectSystem=strict
ReadWritePaths={self.config_dir}

[Install]
WantedBy=multi-user.target
"""
            
            # Write service file
            with open(self.service_file, 'w') as f:
                f.write(service_content)
            
            # Reload systemd and enable service
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "enable", "dnscrypt-proxy"], check=True)
            
            logger.info("DNSCrypt-proxy systemd service created and enabled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create systemd service: {e}")
            return False
    
    def start_dnscrypt_service(self) -> bool:
        """
        Start the DNSCrypt-proxy service.
        
        Returns:
            bool: True if service started successfully, False otherwise
        """
        logger.info("Starting DNSCrypt-proxy service...")
        
        try:
            # Start the service
            subprocess.run(["systemctl", "start", "dnscrypt-proxy"], check=True)
            
            # Wait a moment for service to initialize
            time.sleep(3)
            
            # Check if service is running
            result = subprocess.run(
                ["systemctl", "is-active", "dnscrypt-proxy"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and "active" in result.stdout:
                logger.info("DNSCrypt-proxy service started successfully")
                return True
            else:
                logger.error("DNSCrypt-proxy service failed to start")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start DNSCrypt-proxy service: {e}")
            return False
    
    def stop_dnscrypt_service(self) -> bool:
        """
        Stop the DNSCrypt-proxy service.
        
        Returns:
            bool: True if service stopped successfully, False otherwise
        """
        logger.info("Stopping DNSCrypt-proxy service...")
        
        try:
            subprocess.run(["systemctl", "stop", "dnscrypt-proxy"], check=True)
            logger.info("DNSCrypt-proxy service stopped")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop DNSCrypt-proxy service: {e}")
            return False
    
    def test_dnscrypt_resolution(self) -> bool:
        """
        Test DNS resolution through DNSCrypt-proxy.
        
        Returns:
            bool: True if DNS resolution works, False otherwise
        """
        logger.info("Testing DNSCrypt DNS resolution...")
        
        test_domains = ["example.com", "cloudflare.com", "google.com"]
        
        for domain in test_domains:
            try:
                # Test DNS resolution using dig with specific server
                result = subprocess.run(
                    ["dig", "+short", f"@127.0.0.1", domain, "A"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    logger.info(f"DNSCrypt resolution test passed for {domain}")
                else:
                    logger.error(f"DNSCrypt resolution test failed for {domain}")
                    return False
                    
            except subprocess.TimeoutExpired:
                logger.error(f"DNSCrypt resolution test timed out for {domain}")
                return False
            except Exception as e:
                logger.error(f"DNSCrypt resolution test error for {domain}: {e}")
                return False
        
        logger.info("All DNSCrypt resolution tests passed")
        return True
    
    def get_service_status(self) -> Dict[str, str]:
        """
        Get DNSCrypt-proxy service status information.
        
        Returns:
            Dict[str, str]: Service status information
        """
        status_info = {
            'active': 'unknown',
            'enabled': 'unknown',
            'uptime': 'unknown'
        }
        
        try:
            # Check if service is active
            result = subprocess.run(
                ["systemctl", "is-active", "dnscrypt-proxy"],
                capture_output=True,
                text=True
            )
            status_info['active'] = result.stdout.strip()
            
            # Check if service is enabled
            result = subprocess.run(
                ["systemctl", "is-enabled", "dnscrypt-proxy"],
                capture_output=True,
                text=True
            )
            status_info['enabled'] = result.stdout.strip()
            
            # Get service status with uptime
            result = subprocess.run(
                ["systemctl", "status", "dnscrypt-proxy", "--no-pager"],
                capture_output=True,
                text=True
            )
            
            # Extract uptime information
            for line in result.stdout.split('\n'):
                if 'Active:' in line:
                    status_info['uptime'] = line.strip()
                    break
            
        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
        
        return status_info
    
    def install_and_configure(self, 
                            resolvers: Optional[List[str]] = None,
                            enable_logging: bool = True) -> bool:
        """
        Complete installation and configuration of DNSCrypt-proxy.
        
        Args:
            resolvers (Optional[List[str]]): List of resolver names to use
            enable_logging (bool): Whether to enable logging
            
        Returns:
            bool: True if installation successful, False otherwise
        """
        logger.info("Starting DNSCrypt-proxy installation and configuration...")
        
        # Check if already installed and working
        if (self.binary_path.exists() and 
            self.config_file.exists() and 
            self.test_dnscrypt_resolution()):
            logger.info("DNSCrypt-proxy is already installed and working")
            return True
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Download DNSCrypt-proxy
        if not self.download_dnscrypt():
            return False
        
        # Extract and install
        if not self.extract_and_install():
            return False
        
        # Create configuration
        if not self.create_configuration(resolvers=resolvers, enable_logging=enable_logging):
            return False
        
        # Create systemd service
        if not self.create_systemd_service():
            return False
        
        # Start service
        if not self.start_dnscrypt_service():
            return False
        
        # Test DNS resolution
        if not self.test_dnscrypt_resolution():
            logger.error("DNSCrypt DNS resolution test failed")
            return False
        
        logger.info("DNSCrypt-proxy installation and configuration completed successfully")
        return True


def enable_dnscrypt(resolvers: Optional[List[str]] = None,
                   enable_logging: bool = True,
                   install_dir: str = "/opt/dnscrypt-proxy") -> Tuple[bool, Optional[str]]:
    """
    Main function to enable DNSCrypt-proxy for encrypted DNS.
    
    Args:
        resolvers (Optional[List[str]]): List of resolver names to use
        enable_logging (bool): Whether to enable logging
        install_dir (str): Directory where DNSCrypt-proxy will be installed
        
    Returns:
        Tuple[bool, Optional[str]]: (success_status, error_message)
    """
    try:
        configurator = DNSCryptConfigurator(install_dir)
        success = configurator.install_and_configure(resolvers, enable_logging)
        
        if success:
            return True, None
        else:
            return False, "DNSCrypt-proxy installation/configuration failed - check logs for details"
            
    except Exception as e:
        error_msg = f"Unexpected error during DNSCrypt setup: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def get_dnscrypt_status(install_dir: str = "/opt/dnscrypt-proxy") -> Dict[str, str]:
    """
    Get DNSCrypt-proxy service status.
    
    Args:
        install_dir (str): Directory where DNSCrypt-proxy is installed
        
    Returns:
        Dict[str, str]: Service status information
    """
    configurator = DNSCryptConfigurator(install_dir)
    return configurator.get_service_status()


if __name__ == "__main__":
    """
    Direct execution for testing the DNSCrypt configurator.
    """
    print("Installing and configuring DNSCrypt-proxy...")
    success, error = enable_dnscrypt()
    if success:
        print("DNSCrypt-proxy installed and configured successfully!")
        
        # Show status
        status = get_dnscrypt_status()
        print(f"Service status: {status}")
    else:
        print(f"DNSCrypt setup failed: {error}")
