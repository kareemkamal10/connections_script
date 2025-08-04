#!/usr/bin/env python3
"""
Windows Compatibility Check

This script checks if the system is Windows and provides guidance
on how to run the secure connection script properly.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path


def check_windows_environment():
    """Check if running on Windows and provide guidance."""
    
    if platform.system() == 'Windows':
        print("🖥️  Windows Environment Detected")
        print("="*50)
        print("This script is designed for Linux systems (Ubuntu/Debian).")
        print("Here are your options to run it on Windows:\n")
        
        print("1. 🐧 WSL (Windows Subsystem for Linux) - RECOMMENDED")
        print("   • Open PowerShell as Administrator")
        print("   • Run: wsl --install Ubuntu-22.04")
        print("   • Restart your computer")
        print("   • Open Ubuntu from Start Menu")
        print("   • Run: sudo python3 main.py\n")
        
        print("2. 🐳 Docker Desktop")
        print("   • Install Docker Desktop for Windows")
        print("   • Open PowerShell in project directory")
        print("   • Run: docker build -t secure-connection .")
        print("   • Run: docker run --privileged --cap-add=NET_ADMIN -it secure-connection\n")
        
        print("3. 📦 VirtualBox/VMware")
        print("   • Install Ubuntu 22.04 in a virtual machine")
        print("   • Copy the project files to the VM")
        print("   • Run the script inside the VM\n")
        
        print("4. ☁️  Cloud Instance")
        print("   • Use AWS EC2, Google Cloud, or Azure")
        print("   • Create Ubuntu 22.04 instance")
        print("   • Upload and run the script\n")
        
        # Check for WSL
        check_wsl_availability()
        
        # Check for Docker
        check_docker_availability()
        
        return False
    
    return True


def check_wsl_availability():
    """Check if WSL is available and configured."""
    try:
        result = subprocess.run(['wsl', '--list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ WSL is installed and available")
            if 'Ubuntu' in result.stdout:
                print("✅ Ubuntu is installed in WSL")
                print("💡 You can run: wsl -d Ubuntu")
                print("   Then: sudo python3 main.py")
            else:
                print("⚠️  Ubuntu not found in WSL")
                print("💡 Install Ubuntu: wsl --install Ubuntu-22.04")
        else:
            print("❌ WSL not available")
            print("💡 Install WSL: wsl --install")
    except FileNotFoundError:
        print("❌ WSL command not found")
        print("💡 Install WSL from Microsoft Store or run: wsl --install")


def check_docker_availability():
    """Check if Docker is available."""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is available")
            print("💡 You can build and run with Docker:")
            print("   docker build -t secure-connection .")
            print("   docker run --privileged --cap-add=NET_ADMIN -it secure-connection")
        else:
            print("❌ Docker not working properly")
    except FileNotFoundError:
        print("❌ Docker not found")
        print("💡 Install Docker Desktop from docker.com")


def create_wsl_setup_script():
    """Create a setup script for WSL."""
    script_content = """#!/bin/bash
# WSL Setup Script for Secure Connection

echo "🐧 Setting up Ubuntu environment for Secure Connection Script"
echo "============================================================"

# Update system
echo "📦 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install required packages
echo "📦 Installing required packages..."
sudo apt-get install -y python3 python3-pip build-essential wget curl systemd dnsutils net-tools

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo "🐍 Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# Make script executable
chmod +x main.py

echo "✅ Setup completed!"
echo "Now you can run: sudo python3 main.py"
"""
    
    with open('setup_wsl.sh', 'w') as f:
        f.write(script_content)
    
    print("📄 Created setup_wsl.sh for easy WSL setup")
    print("💡 In WSL, run: bash setup_wsl.sh")


def main():
    """Main function to check environment and provide guidance."""
    print("🔒 Secure Connection Environment Check")
    print("="*40)
    
    if check_windows_environment():
        print("✅ Linux environment detected - you can run the script directly!")
        print("💡 Run: sudo python3 main.py")
    else:
        create_wsl_setup_script()
        print("\n" + "="*50)
        print("📚 For more information, see README.md")
        print("🆘 If you need help, check the documentation")


if __name__ == "__main__":
    main()
