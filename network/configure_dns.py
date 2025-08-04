#!/usr/bin/env python3
"""
DNS Configuration Module

This module handles configuring custom DNS servers for secure and private
DNS resolution. It supports setting up various DNS providers like Cloudflare,
Quad9, and others while backing up original DNS settings.
"""

import os
import subprocess
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DNSConfigurator:
    """
    Handles DNS configuration for secure and private DNS resolution.
    
    This class manages configuring system DNS settings, backing up original
    configurations, and restoring them when needed.
    """
    
    def __init__(self):
        """
        Initialize the DNS configurator.
        """
        self.resolv_conf_path = Path("/etc/resolv.conf")
        self.resolv_conf_backup = Path("/etc/resolv.conf.backup")
        self.systemd_resolved_conf = Path("/etc/systemd/resolved.conf")
        self.systemd_resolved_backup = Path("/etc/systemd/resolved.conf.backup")
        
        # Predefined secure DNS servers
        self.dns_providers = {
            'cloudflare': {
                'name': 'Cloudflare DNS',
                'primary': '1.1.1.1',
                'secondary': '1.0.0.1',
                'description': 'Fast and privacy-focused DNS'
            },
            'cloudflare_family': {
                'name': 'Cloudflare for Families',
                'primary': '1.1.1.3',
                'secondary': '1.0.0.3',
                'description': 'Cloudflare DNS with malware and adult content blocking'
            },
            'quad9': {
                'name': 'Quad9 DNS',
                'primary': '9.9.9.9',
                'secondary': '149.112.112.112',
                'description': 'Security-focused DNS with threat blocking'
            },
            'opendns': {
                'name': 'OpenDNS',
                'primary': '208.67.222.222',
                'secondary': '208.67.220.220',
                'description': 'Cisco OpenDNS with security and filtering'
            },
            'google': {
                'name': 'Google Public DNS',
                'primary': '8.8.8.8',
                'secondary': '8.8.4.4',
                'description': 'Google\'s fast public DNS service'
            },
            'adguard': {
                'name': 'AdGuard DNS',
                'primary': '94.140.14.14',
                'secondary': '94.140.15.15',
                'description': 'DNS with ad and tracker blocking'
            }
        }
    
    def backup_current_dns(self) -> bool:
        """
        Backup current DNS configuration files.
        
        Returns:
            bool: True if backup successful, False otherwise
        """
        logger.info("Backing up current DNS configuration...")
        
        try:
            # Backup /etc/resolv.conf if it exists
            if self.resolv_conf_path.exists():
                shutil.copy2(self.resolv_conf_path, self.resolv_conf_backup)
                logger.info(f"Backed up {self.resolv_conf_path} to {self.resolv_conf_backup}")
            
            # Backup systemd-resolved configuration if it exists
            if self.systemd_resolved_conf.exists():
                shutil.copy2(self.systemd_resolved_conf, self.systemd_resolved_backup)
                logger.info(f"Backed up {self.systemd_resolved_conf} to {self.systemd_resolved_backup}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup DNS configuration: {e}")
            return False
    
    def get_current_dns(self) -> List[str]:
        """
        Get currently configured DNS servers.
        
        Returns:
            List[str]: List of current DNS server IP addresses
        """
        dns_servers = []
        
        try:
            # Read from /etc/resolv.conf
            if self.resolv_conf_path.exists():
                with open(self.resolv_conf_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('nameserver '):
                            dns_ip = line.split()[1]
                            dns_servers.append(dns_ip)
            
            logger.info(f"Current DNS servers: {dns_servers}")
            return dns_servers
            
        except Exception as e:
            logger.error(f"Failed to get current DNS configuration: {e}")
            return []
    
    def is_systemd_resolved_active(self) -> bool:
        """
        Check if systemd-resolved is active and managing DNS.
        
        Returns:
            bool: True if systemd-resolved is active, False otherwise
        """
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "systemd-resolved"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and "active" in result.stdout
            
        except Exception as e:
            logger.debug(f"Could not check systemd-resolved status: {e}")
            return False
    
    def configure_systemd_resolved(self, dns_servers: List[str]) -> bool:
        """
        Configure DNS using systemd-resolved.
        
        Args:
            dns_servers (List[str]): List of DNS server IP addresses
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        logger.info("Configuring DNS using systemd-resolved...")
        
        try:
            # Create systemd-resolved configuration
            config_content = f"""[Resolve]
DNS={' '.join(dns_servers)}
FallbackDNS=
Domains=~.
DNSSEC=yes
DNSOverTLS=opportunistic
Cache=yes
"""
            
            # Write configuration
            with open(self.systemd_resolved_conf, 'w') as f:
                f.write(config_content)
            
            # Restart systemd-resolved
            subprocess.run(["systemctl", "restart", "systemd-resolved"], check=True)
            
            # Ensure /etc/resolv.conf points to systemd-resolved
            stub_resolv_content = """# This file is managed by systemd-resolved
nameserver 127.0.0.53
options edns0 trust-ad
search .
"""
            
            with open(self.resolv_conf_path, 'w') as f:
                f.write(stub_resolv_content)
            
            logger.info("systemd-resolved DNS configuration completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure systemd-resolved: {e}")
            return False
    
    def configure_resolv_conf(self, dns_servers: List[str]) -> bool:
        """
        Configure DNS using direct /etc/resolv.conf modification.
        
        Args:
            dns_servers (List[str]): List of DNS server IP addresses
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        logger.info("Configuring DNS using /etc/resolv.conf...")
        
        try:
            # Create new resolv.conf content
            resolv_content = "# Custom DNS configuration\n"
            for dns_server in dns_servers:
                resolv_content += f"nameserver {dns_server}\n"
            
            # Add options for better performance and security
            resolv_content += "options timeout:2\n"
            resolv_content += "options attempts:3\n"
            resolv_content += "options rotate\n"
            resolv_content += "options single-request-reopen\n"
            
            # Write new configuration
            with open(self.resolv_conf_path, 'w') as f:
                f.write(resolv_content)
            
            # Make file immutable to prevent other services from modifying it
            subprocess.run(["chattr", "+i", str(self.resolv_conf_path)], 
                         capture_output=True)
            
            logger.info("Direct resolv.conf DNS configuration completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure resolv.conf: {e}")
            return False
    
    def flush_dns_cache(self) -> bool:
        """
        Flush DNS cache to apply new settings.
        
        Returns:
            bool: True if cache flush successful, False otherwise
        """
        logger.info("Flushing DNS cache...")
        
        try:
            # Try different methods to flush DNS cache
            flush_commands = [
                ["systemctl", "restart", "systemd-resolved"],
                ["systemctl", "reload", "systemd-resolved"],
                ["resolvectl", "flush-caches"],
                ["systemd-resolve", "--flush-caches"]
            ]
            
            for cmd in flush_commands:
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                    logger.info(f"DNS cache flushed using: {' '.join(cmd)}")
                    return True
                except subprocess.CalledProcessError:
                    continue
            
            # If systemd methods fail, try traditional methods
            try:
                subprocess.run(["service", "dnsmasq", "restart"], 
                             check=True, capture_output=True)
                logger.info("DNS cache flushed using dnsmasq")
                return True
            except subprocess.CalledProcessError:
                pass
            
            logger.warning("Could not flush DNS cache - new settings may take time to apply")
            return True  # Don't fail the entire operation for this
            
        except Exception as e:
            logger.error(f"Error while flushing DNS cache: {e}")
            return True  # Don't fail the entire operation for this
    
    def test_dns_resolution(self, test_domains: Optional[List[str]] = None) -> bool:
        """
        Test DNS resolution with configured servers.
        
        Args:
            test_domains (Optional[List[str]]): Domains to test resolution for
            
        Returns:
            bool: True if DNS resolution is working, False otherwise
        """
        if test_domains is None:
            test_domains = ["google.com", "cloudflare.com", "github.com"]
        
        logger.info("Testing DNS resolution...")
        
        for domain in test_domains:
            try:
                # Test DNS resolution using nslookup
                result = subprocess.run(
                    ["nslookup", domain],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and "NXDOMAIN" not in result.stdout:
                    logger.info(f"DNS resolution test passed for {domain}")
                else:
                    logger.error(f"DNS resolution test failed for {domain}")
                    return False
                    
            except subprocess.TimeoutExpired:
                logger.error(f"DNS resolution test timed out for {domain}")
                return False
            except Exception as e:
                logger.error(f"DNS resolution test error for {domain}: {e}")
                return False
        
        logger.info("All DNS resolution tests passed")
        return True
    
    def restore_dns_backup(self) -> bool:
        """
        Restore DNS configuration from backup.
        
        Returns:
            bool: True if restoration successful, False otherwise
        """
        logger.info("Restoring DNS configuration from backup...")
        
        try:
            restored = False
            
            # Remove immutable flag if set
            try:
                subprocess.run(["chattr", "-i", str(self.resolv_conf_path)], 
                             capture_output=True)
            except:
                pass
            
            # Restore /etc/resolv.conf
            if self.resolv_conf_backup.exists():
                shutil.copy2(self.resolv_conf_backup, self.resolv_conf_path)
                logger.info("Restored /etc/resolv.conf from backup")
                restored = True
            
            # Restore systemd-resolved configuration
            if self.systemd_resolved_backup.exists():
                shutil.copy2(self.systemd_resolved_backup, self.systemd_resolved_conf)
                subprocess.run(["systemctl", "restart", "systemd-resolved"], 
                             capture_output=True)
                logger.info("Restored systemd-resolved configuration from backup")
                restored = True
            
            if restored:
                self.flush_dns_cache()
                logger.info("DNS configuration restored successfully")
                return True
            else:
                logger.warning("No DNS backup found to restore")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restore DNS backup: {e}")
            return False
    
    def configure_dns(self, provider: str = 'cloudflare', 
                     custom_servers: Optional[List[str]] = None) -> bool:
        """
        Configure DNS with specified provider or custom servers.
        
        Args:
            provider (str): DNS provider name from predefined list
            custom_servers (Optional[List[str]]): Custom DNS server IP addresses
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        logger.info(f"Configuring DNS with provider: {provider}")
        
        # Backup current configuration
        if not self.backup_current_dns():
            return False
        
        # Determine DNS servers to use
        if custom_servers:
            dns_servers = custom_servers
            logger.info(f"Using custom DNS servers: {dns_servers}")
        elif provider in self.dns_providers:
            dns_config = self.dns_providers[provider]
            dns_servers = [dns_config['primary'], dns_config['secondary']]
            logger.info(f"Using {dns_config['name']}: {dns_servers}")
        else:
            logger.error(f"Unknown DNS provider: {provider}")
            return False
        
        # Configure DNS based on system setup
        if self.is_systemd_resolved_active():
            success = self.configure_systemd_resolved(dns_servers)
        else:
            success = self.configure_resolv_conf(dns_servers)
        
        if not success:
            logger.error("DNS configuration failed")
            return False
        
        # Flush DNS cache
        self.flush_dns_cache()
        
        # Test DNS resolution
        if not self.test_dns_resolution():
            logger.error("DNS resolution test failed, restoring backup")
            self.restore_dns_backup()
            return False
        
        logger.info("DNS configuration completed successfully")
        return True


def configure_dns(provider: str = 'cloudflare', 
                 custom_servers: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
    """
    Main function to configure DNS settings.
    
    Args:
        provider (str): DNS provider name ('cloudflare', 'quad9', 'google', etc.)
        custom_servers (Optional[List[str]]): Custom DNS server IP addresses
        
    Returns:
        Tuple[bool, Optional[str]]: (success_status, error_message)
    """
    try:
        configurator = DNSConfigurator()
        success = configurator.configure_dns(provider, custom_servers)
        
        if success:
            return True, None
        else:
            return False, "DNS configuration failed - check logs for details"
            
    except Exception as e:
        error_msg = f"Unexpected error during DNS configuration: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def list_dns_providers() -> Dict[str, Dict[str, str]]:
    """
    Get list of available DNS providers.
    
    Returns:
        Dict[str, Dict[str, str]]: Dictionary of available DNS providers
    """
    configurator = DNSConfigurator()
    return configurator.dns_providers


if __name__ == "__main__":
    """
    Direct execution for testing the DNS configurator.
    """
    print("Available DNS providers:")
    for key, provider in list_dns_providers().items():
        print(f"  {key}: {provider['name']} - {provider['description']}")
    
    print("\nConfiguring DNS with Cloudflare...")
    success, error = configure_dns('cloudflare')
    if success:
        print("DNS configured successfully!")
    else:
        print(f"DNS configuration failed: {error}")
