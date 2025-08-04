"""
Network Security Module Package

This package provides modular components for establishing secure and anonymous
internet connections using VPN, secure DNS, and encrypted DNS technologies.

Modules:
- install_softether: SoftEther VPN client installation and setup
- connect_vpngate: VPNGate server connection management  
- configure_dns: Secure DNS configuration
- enable_dnscrypt: DNSCrypt setup for encrypted DNS queries
"""

__version__ = "1.0.0"
__author__ = "Secure Connection Script"

# Package exports
from .install_softether import install_softether
from .connect_vpngate import connect_vpngate
from .configure_dns import configure_dns, list_dns_providers
from .enable_dnscrypt import enable_dnscrypt, get_dnscrypt_status

__all__ = [
    'install_softether',
    'connect_vpngate', 
    'configure_dns',
    'list_dns_providers',
    'enable_dnscrypt',
    'get_dnscrypt_status'
]
