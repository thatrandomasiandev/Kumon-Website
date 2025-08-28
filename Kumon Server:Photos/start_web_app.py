#!/usr/bin/env python3
"""
Photo Slideshow Web Application Startup Script
Dual interface: TV Display + Admin Upload
"""

import os
import sys
import subprocess
import time
import socket
from pathlib import Path

def get_local_ip():
    """Get local IP address"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def check_python_version():
    """Check if Python 3.6+ is available"""
    if sys.version_info < (3, 6):
        print("❌ Python 3.6 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import flask
        import flask_socketio
        print("✅ All dependencies are installed")
        return True
    except ImportError:
        print("❌ Missing dependencies")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        "static/photos",
        "templates"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def main():
    """Main startup function"""
    print("=" * 70)
    print("📺 Photo Slideshow Web Application")
    print("=" * 70)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\n🔧 Installing dependencies...")
        if not install_dependencies():
            print("\n❌ Failed to install dependencies. Please run manually:")
            print("   pip install -r requirements.txt")
            sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Get local IP
    local_ip = get_local_ip()
    
    print("\n" + "=" * 70)
    print("🚀 Starting Photo Slideshow Web Application...")
    print("=" * 70)
    print(f"🌐 TV Display: http://localhost:5000/")
    print(f"🔧 Admin Panel: http://localhost:5000/admin")
    print(f"📱 Network Access:")
    print(f"   TV Display: http://{local_ip}:5000/")
    print(f"   Admin Panel: http://{local_ip}:5000/admin")
    print("=" * 70)
    print("\n💡 Usage:")
    print("   1. Open Admin Panel in your browser to upload photos")
    print("   2. Open TV Display on your TV to view slideshow")
    print("   3. Photos update in real-time on both interfaces")
    print("   4. Configure slideshow settings in Admin Panel")
    print("=" * 70)
    
    try:
        # Start the Flask application
        print("\n🔄 Starting server...")
        subprocess.run([sys.executable, "app.py"])
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\n💡 Try running manually:")
        print("   python app.py")

if __name__ == "__main__":
    main()
