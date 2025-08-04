#!/usr/bin/env python3
"""
VPNGate Connection Module

This module handles connecting to VPNGate servers using SoftEther VPN client.
It fetches available VPNGate servers, selects the best one based on criteria,
and establishes a VPN connection.
"""

import os
import subprocess
import logging
import csv
import urllib.request
import base64
import time
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VPNGateConnector:
    """
    Handles VPNGate server discovery and connection using SoftEther VPN client.
    
    This class manages fetching VPNGate server lists, selecting optimal servers,
    and establishing VPN connections through SoftEther VPN client.
    """
    
    def __init__(self, softether_dir: str = "/opt/softether"):
        """
        Initialize the VPNGate connector.
        
        Args:
            softether_dir (str): Directory where SoftEther is installed
        """
        self.softether_dir = Path(softether_dir)
        self.vpnclient_path = self.softether_dir / "vpnclient"
        self.vpncmd_path = self.softether_dir / "vpncmd"
        self.vpngate_api_url = "http://www.vpngate.net/api/iphone/"
        self.connection_name = "VPNGate_Connection"
        self.virtual_hub_name = "VPN"
        
    def fetch_vpngate_servers(self) -> List[Dict[str, str]]:
        """
        Fetch available VPNGate servers from the API.
        
        Returns:
            List[Dict[str, str]]: List of server information dictionaries
        """
        logger.info("Fetching VPNGate server list...")
        
        try:
            # Download CSV data from VPNGate API
            response = urllib.request.urlopen(self.vpngate_api_url)
            csv_data = response.read().decode('utf-8')
            
            # Parse CSV data
            servers = []
            csv_reader = csv.reader(csv_data.strip().split('\n'))
            
            # Skip header and comment lines
            for row in csv_reader:
                if row and not row[0].startswith('#') and len(row) > 10:
                    try:
                        server_info = {
                            'hostname': row[0],
                            'ip': row[1],
                            'score': int(row[2]) if row[2].isdigit() else 0,
                            'ping': int(row[3]) if row[3].isdigit() else 9999,
                            'speed': int(row[4]) if row[4].isdigit() else 0,
                            'country_long': row[5],
                            'country_short': row[6],
                            'vpn_sessions': int(row[7]) if row[7].isdigit() else 0,
                            'uptime': int(row[8]) if row[8].isdigit() else 0,
                            'total_users': int(row[9]) if row[9].isdigit() else 0,
                            'total_traffic': int(row[10]) if row[10].isdigit() else 0,
                            'log_type': row[11] if len(row) > 11 else '',
                            'operator': row[12] if len(row) > 12 else '',
                            'message': row[13] if len(row) > 13 else '',
                            'config_data': row[14] if len(row) > 14 else ''
                        }
                        servers.append(server_info)
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Skipping malformed server entry: {e}")
                        continue
            
            logger.info(f"Fetched {len(servers)} VPNGate servers")
            return servers
            
        except Exception as e:
            logger.error(f"Failed to fetch VPNGate servers: {e}")
            return []
    
    def filter_servers(self, servers: List[Dict[str, str]], 
                      min_score: int = 1000000,
                      max_ping: int = 500,
                      min_speed: int = 1000000,
                      preferred_countries: Optional[List[str]] = None) -> List[Dict[str, str]]:
        """
        Filter servers based on quality criteria.
        
        Args:
            servers (List[Dict[str, str]]): List of server information
            min_score (int): Minimum server score
            max_ping (int): Maximum acceptable ping (ms)
            min_speed (int): Minimum speed requirement
            preferred_countries (Optional[List[str]]): List of preferred country codes
            
        Returns:
            List[Dict[str, str]]: Filtered and sorted server list
        """
        logger.info("Filtering VPNGate servers...")
        
        filtered_servers = []
        
        for server in servers:
            # Apply filters
            if (server['score'] >= min_score and
                server['ping'] <= max_ping and
                server['speed'] >= min_speed and
                server['config_data']):  # Must have config data
                
                # Check preferred countries if specified
                if preferred_countries:
                    if server['country_short'].upper() in [c.upper() for c in preferred_countries]:
                        filtered_servers.append(server)
                else:
                    filtered_servers.append(server)
        
        # Sort by score (higher is better), then by ping (lower is better)
        filtered_servers.sort(key=lambda x: (-x['score'], x['ping']))
        
        logger.info(f"Filtered to {len(filtered_servers)} suitable servers")
        return filtered_servers
    
    def create_ovpn_config(self, server: Dict[str, str], output_path: str) -> bool:
        """
        Create OpenVPN configuration file from server data.
        
        Args:
            server (Dict[str, str]): Server information
            output_path (str): Path to save the config file
            
        Returns:
            bool: True if config created successfully, False otherwise
        """
        try:
            # Decode base64 config data
            config_data = base64.b64decode(server['config_data']).decode('utf-8')
            
            # Write config to file
            with open(output_path, 'w') as f:
                f.write(config_data)
            
            logger.info(f"Created OpenVPN config: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create OpenVPN config: {e}")
            return False
    
    def start_vpnclient_service(self) -> bool:
        """
        Start the SoftEther VPN client service.
        
        Returns:
            bool: True if service started successfully, False otherwise
        """
        logger.info("Starting SoftEther VPN client service...")
        
        try:
            # Start the service
            subprocess.run([str(self.vpnclient_path), "start"], check=True, capture_output=True)
            
            # Wait a moment for service to initialize
            time.sleep(3)
            
            logger.info("VPN client service started")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start VPN client service: {e}")
            return False
    
    def create_virtual_adapter(self) -> bool:
        """
        Create a virtual network adapter for the VPN connection.
        
        Returns:
            bool: True if adapter created successfully, False otherwise
        """
        logger.info("Creating virtual network adapter...")
        
        try:
            # Create virtual adapter using vpncmd
            cmd = [
                str(self.vpncmd_path),
                "localhost",
                "/CLIENT",
                "/CMD",
                f"NicCreate {self.connection_name}"
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Virtual adapter '{self.connection_name}' created")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create virtual adapter: {e}")
            return False
    
    def create_vpn_connection(self, server: Dict[str, str]) -> bool:
        """
        Create VPN connection configuration in SoftEther.
        
        Args:
            server (Dict[str, str]): Server information
            
        Returns:
            bool: True if connection created successfully, False otherwise
        """
        logger.info(f"Creating VPN connection to {server['hostname']} ({server['country_short']})...")
        
        try:
            # Extract connection details from OpenVPN config
            config_data = base64.b64decode(server['config_data']).decode('utf-8')
            
            # Parse remote host and port from config
            remote_host = server['ip']
            remote_port = "1194"  # Default OpenVPN port
            
            for line in config_data.split('\n'):
                if line.startswith('remote '):
                    parts = line.split()
                    if len(parts) >= 3:
                        remote_host = parts[1]
                        remote_port = parts[2]
                    break
            
            # Create account using vpncmd
            cmd = [
                str(self.vpncmd_path),
                "localhost",
                "/CLIENT",
                "/CMD",
                f"AccountCreate {self.connection_name}",
                f"/SERVER:{remote_host}:{remote_port}",
                f"/HUB:{self.virtual_hub_name}",
                "/USERNAME:vpn",
                "/NICNAME:" + self.connection_name
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"VPN connection '{self.connection_name}' created")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create VPN connection: {e}")
            return False
    
    def connect_to_vpn(self) -> bool:
        """
        Establish the VPN connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        logger.info("Establishing VPN connection...")
        
        try:
            # Connect using vpncmd
            cmd = [
                str(self.vpncmd_path),
                "localhost",
                "/CLIENT",
                "/CMD",
                f"AccountConnect {self.connection_name}"
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Wait for connection to establish
            time.sleep(5)
            
            # Check connection status
            if self.check_connection_status():
                logger.info("VPN connection established successfully")
                return True
            else:
                logger.error("VPN connection failed to establish")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to connect to VPN: {e}")
            return False
    
    def check_connection_status(self) -> bool:
        """
        Check if VPN connection is active.
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            # Check account status
            cmd = [
                str(self.vpncmd_path),
                "localhost",
                "/CLIENT",
                "/CMD",
                f"AccountStatusGet {self.connection_name}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Look for connection status indicators
            if "Connected" in result.stdout:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check connection status: {e}")
            return False
    
    def disconnect_vpn(self) -> bool:
        """
        Disconnect from the VPN.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        logger.info("Disconnecting from VPN...")
        
        try:
            # Disconnect using vpncmd
            cmd = [
                str(self.vpncmd_path),
                "localhost",
                "/CLIENT",
                "/CMD",
                f"AccountDisconnect {self.connection_name}"
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("VPN disconnected successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to disconnect VPN: {e}")
            return False
    
    def connect_best_server(self, max_attempts: int = 3) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Connect to the best available VPNGate server.
        
        Args:
            max_attempts (int): Maximum number of connection attempts
            
        Returns:
            Tuple[bool, Optional[Dict[str, str]]]: (success_status, connected_server_info)
        """
        logger.info("Connecting to best available VPNGate server...")
        
        # Fetch available servers
        servers = self.fetch_vpngate_servers()
        if not servers:
            return False, None
        
        # Filter servers
        filtered_servers = self.filter_servers(servers)
        if not filtered_servers:
            logger.error("No suitable servers found")
            return False, None
        
        # Start VPN client service
        if not self.start_vpnclient_service():
            return False, None
        
        # Try connecting to servers in order
        for attempt in range(max_attempts):
            # Select a server (try top servers first, then random)
            if attempt < len(filtered_servers):
                server = filtered_servers[attempt]
            else:
                server = random.choice(filtered_servers[:10])  # Random from top 10
            
            logger.info(f"Attempt {attempt + 1}: Trying server {server['hostname']} ({server['country_short']})")
            
            try:
                # Create virtual adapter
                self.create_virtual_adapter()
                
                # Create VPN connection
                if self.create_vpn_connection(server):
                    # Attempt to connect
                    if self.connect_to_vpn():
                        logger.info(f"Successfully connected to {server['hostname']} ({server['country_short']})")
                        return True, server
                
                # If connection failed, clean up and try next server
                self.disconnect_vpn()
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Connection attempt failed: {e}")
                continue
        
        logger.error(f"Failed to connect after {max_attempts} attempts")
        return False, None


def connect_vpngate(softether_dir: str = "/opt/softether", 
                   preferred_countries: Optional[List[str]] = None) -> Tuple[bool, Optional[str], Optional[Dict[str, str]]]:
    """
    Main function to connect to VPNGate servers.
    
    Args:
        softether_dir (str): Directory where SoftEther is installed
        preferred_countries (Optional[List[str]]): List of preferred country codes
        
    Returns:
        Tuple[bool, Optional[str], Optional[Dict[str, str]]]: (success_status, error_message, server_info)
    """
    try:
        connector = VPNGateConnector(softether_dir)
        success, server = connector.connect_best_server()
        
        if success:
            return True, None, server
        else:
            return False, "Failed to connect to any VPNGate server", None
            
    except Exception as e:
        error_msg = f"Unexpected error during VPN connection: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, None


if __name__ == "__main__":
    """
    Direct execution for testing the VPNGate connector.
    """
    success, error = connect_vpngate()
    if success:
        print("Successfully connected to VPNGate!")
    else:
        print(f"Connection failed: {error}")
