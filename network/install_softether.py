#!/usr/bin/env python3
"""
SoftEther VPN Client Installer Module

This module handles the installation and setup of SoftEther VPN Client
on a Linux-based Docker container. It downloads, compiles, and configures
the SoftEther VPN client for use with VPNGate servers.
"""

import os
import subprocess
import logging
import tarfile
import urllib.request
import shutil
from pathlib import Path
from typing import Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SoftEtherInstaller:
    """
    Handles the installation and setup of SoftEther VPN Client.
    
    This class manages downloading, compiling, and configuring SoftEther VPN
    client for establishing VPN connections through VPNGate servers.
    """
    
    def __init__(self, install_dir: str = "/opt/softether"):
        """
        Initialize the SoftEther installer.
        
        Args:
            install_dir (str): Directory where SoftEther will be installed
        """
        self.install_dir = Path(install_dir)
        self.download_url = "https://github.com/SoftEtherVPN/SoftEtherVPN_Stable/releases/download/v4.42-9798-beta/softether-vpnclient-v4.42-9798-beta-2023.06.30-linux-x64-64bit.tar.gz"
        self.archive_name = "softether-vpnclient.tar.gz"
        self.binary_path = self.install_dir / "vpnclient"
        
    def check_dependencies(self) -> bool:
        """
        Check if required system dependencies are available.
        
        Returns:
            bool: True if all dependencies are available, False otherwise
        """
        logger.info("Checking system dependencies...")
        
        required_packages = ["gcc", "make", "wget", "tar"]
        missing_packages = []
        
        for package in required_packages:
            if not shutil.which(package):
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing required packages: {', '.join(missing_packages)}")
            logger.info("Please install missing packages using: apt-get update && apt-get install -y " + " ".join(missing_packages))
            return False
        
        logger.info("All system dependencies are available")
        return True
    
    def install_dependencies(self) -> bool:
        """
        Install required system dependencies using apt-get.
        
        Returns:
            bool: True if installation successful, False otherwise
        """
        logger.info("Installing system dependencies...")
        
        try:
            # Update package list
            subprocess.run(["apt-get", "update"], check=True, capture_output=True)
            
            # Install required packages
            packages = ["gcc", "make", "wget", "tar", "build-essential"]
            cmd = ["apt-get", "install", "-y"] + packages
            subprocess.run(cmd, check=True, capture_output=True)
            
            logger.info("System dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def download_softether(self) -> bool:
        """
        Download SoftEther VPN client archive.
        
        Returns:
            bool: True if download successful, False otherwise
        """
        logger.info(f"Downloading SoftEther VPN client from {self.download_url}")
        
        try:
            # Create temporary download directory
            download_path = Path("/tmp") / self.archive_name
            
            # Download the archive
            urllib.request.urlretrieve(self.download_url, download_path)
            
            logger.info(f"Downloaded SoftEther archive to {download_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download SoftEther: {e}")
            return False
    
    def extract_and_compile(self) -> bool:
        """
        Extract SoftEther archive and compile the VPN client.
        
        Returns:
            bool: True if compilation successful, False otherwise
        """
        logger.info("Extracting and compiling SoftEther VPN client...")
        
        try:
            download_path = Path("/tmp") / self.archive_name
            extract_dir = Path("/tmp/softether")
            
            # Create extraction directory
            extract_dir.mkdir(exist_ok=True)
            
            # Extract the archive
            with tarfile.open(download_path, "r:gz") as tar:
                tar.extractall(extract_dir)
            
            # Find the vpnclient directory
            vpnclient_dir = None
            for item in extract_dir.iterdir():
                if item.is_dir() and "vpnclient" in item.name.lower():
                    vpnclient_dir = item
                    break
            
            if not vpnclient_dir:
                logger.error("Could not find vpnclient directory in extracted archive")
                return False
            
            # Compile SoftEther
            logger.info("Compiling SoftEther VPN client...")
            os.chdir(vpnclient_dir)
            
            # Run make
            subprocess.run(["make"], check=True, capture_output=True)
            
            # Create install directory
            self.install_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy compiled binaries
            for binary in ["vpnclient", "vpncmd"]:
                src = vpnclient_dir / binary
                dst = self.install_dir / binary
                if src.exists():
                    shutil.copy2(src, dst)
                    # Make executable
                    os.chmod(dst, 0o755)
            
            logger.info(f"SoftEther VPN client compiled and installed to {self.install_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extract and compile SoftEther: {e}")
            return False
    
    def setup_service(self) -> bool:
        """
        Set up SoftEther VPN client as a service.
        
        Returns:
            bool: True if service setup successful, False otherwise
        """
        logger.info("Setting up SoftEther VPN client service...")
        
        try:
            # Create systemd service file
            service_content = f"""[Unit]
Description=SoftEther VPN Client
After=network.target

[Service]
Type=forking
ExecStart={self.install_dir}/vpnclient start
ExecStop={self.install_dir}/vpnclient stop
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
            
            service_file = Path("/etc/systemd/system/vpnclient.service")
            service_file.write_text(service_content)
            
            # Reload systemd and enable service
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "enable", "vpnclient"], check=True)
            
            logger.info("SoftEther VPN client service configured")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup service: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """
        Verify that SoftEther VPN client is properly installed.
        
        Returns:
            bool: True if installation is valid, False otherwise
        """
        logger.info("Verifying SoftEther installation...")
        
        try:
            # Check if binaries exist and are executable
            if not self.binary_path.exists():
                logger.error(f"VPN client binary not found at {self.binary_path}")
                return False
            
            # Test vpnclient command
            result = subprocess.run(
                [str(self.binary_path), "check"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("SoftEther VPN client installation verified successfully")
                return True
            else:
                logger.error(f"VPN client check failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to verify installation: {e}")
            return False
    
    def install(self) -> bool:
        """
        Complete installation process for SoftEther VPN client.
        
        Returns:
            bool: True if installation successful, False otherwise
        """
        logger.info("Starting SoftEther VPN client installation...")
        
        # Check if already installed
        if self.binary_path.exists() and self.verify_installation():
            logger.info("SoftEther VPN client is already installed and working")
            return True
        
        # Install dependencies
        if not self.check_dependencies():
            if not self.install_dependencies():
                return False
        
        # Download SoftEther
        if not self.download_softether():
            return False
        
        # Extract and compile
        if not self.extract_and_compile():
            return False
        
        # Setup service
        if not self.setup_service():
            return False
        
        # Verify installation
        if not self.verify_installation():
            return False
        
        logger.info("SoftEther VPN client installation completed successfully")
        return True


def install_softether(install_dir: str = "/opt/softether") -> Tuple[bool, Optional[str]]:
    """
    Main function to install SoftEther VPN client.
    
    Args:
        install_dir (str): Directory where SoftEther will be installed
        
    Returns:
        Tuple[bool, Optional[str]]: (success_status, error_message)
    """
    try:
        installer = SoftEtherInstaller(install_dir)
        success = installer.install()
        
        if success:
            return True, None
        else:
            return False, "Installation failed - check logs for details"
            
    except Exception as e:
        error_msg = f"Unexpected error during installation: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


if __name__ == "__main__":
    """
    Direct execution for testing the installer.
    """
    success, error = install_softether()
    if success:
        print("SoftEther VPN client installed successfully!")
    else:
        print(f"Installation failed: {error}")
