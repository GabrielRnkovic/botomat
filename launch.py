#!/usr/bin/env python3
import os
import sys
import time
import logging
import subprocess
import argparse
import platform
import webbrowser
import signal
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("launch.log"), logging.StreamHandler()]
)
logger = logging.getLogger("Launcher")

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        "opencv-python",
        "numpy",
        "easyocr",
        "torch",
        "flask"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.info("Please install them using: pip install -r requirements.txt")
        return False
    
    return True

def check_iphones():
    """Check for connected iPhones"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        try:
            # Use system_profiler to list USB devices
            result = subprocess.run(
                ["system_profiler", "SPUSBDataType"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Count iPhones in the output
            iphone_count = result.stdout.count("iPhone")
            
            if iphone_count >= 2:
                logger.info(f"Found {iphone_count} iPhones connected")
                return True
            else:
                logger.warning(f"Only {iphone_count} iPhone(s) connected. At least 2 are recommended.")
                return False
            
        except Exception as e:
            logger.error(f"Error checking for iPhones: {str(e)}")
            return False
    else:
        logger.warning(f"iPhone detection not supported on {system}. Assuming test mode.")
        return False

def start_server():
    """Start the web server"""
    try:
        # Start the web server in a new process
        server_process = subprocess.Popen(
            [sys.executable, "web_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"Started web server (PID: {server_process.pid})")
        
        # Start a thread to monitor the server output
        def monitor_output():
            for line in server_process.stdout:
                logger.info(f"Server: {line.strip()}")
            for line in server_process.stderr:
                logger.error(f"Server error: {line.strip()}")
                
        threading.Thread(target=monitor_output, daemon=True).start()
        
        # Wait for server to initialize
        time.sleep(2)
        
        # Check if server is running
        if server_process.poll() is not None:
            logger.error("Server failed to start")
            return None
        
        return server_process
    
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        return None

def open_web_interface():
    """Open the web interface in the default browser"""
    try:
        url = "http://localhost:5000"
        logger.info(f"Opening web interface: {url}")
        webbrowser.open(url)
    except Exception as e:
        logger.error(f"Error opening web interface: {str(e)}")

def main():
    """Main function"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Speed Camera System Launcher")
    parser.add_argument("--skip-checks", action="store_true", help="Skip dependency and iPhone checks")
    parser.add_argument("--test-mode", action="store_true", help="Run in test mode (no iPhones required)")
    args = parser.parse_args()
    
    logger.info("Starting Speed Camera System Launcher")
    
    # Create required directories
    os.makedirs("detections", exist_ok=True)
    os.makedirs("violations", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    
    # Check dependencies
    if not args.skip_checks:
        if not check_dependencies():
            if input("Install missing dependencies? (y/n): ").lower() == "y":
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
                    logger.info("Dependencies installed successfully")
                except Exception as e:
                    logger.error(f"Error installing dependencies: {str(e)}")
                    return 1
            else:
                return 1
    
    # Check for connected iPhones
    if not args.test_mode and not args.skip_checks:
        if not check_iphones():
            if input("Continue in test mode? (y/n): ").lower() != "y":
                return 1
    
    # Start the server
    server_process = start_server()
    if not server_process:
        return 1
    
    # Open web interface
    open_web_interface()
    
    try:
        # Keep running until interrupted
        logger.info("System is running. Press Ctrl+C to stop...")
        while True:
            # Check if server is still running
            if server_process.poll() is not None:
                logger.error("Server process stopped unexpectedly")
                break
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Stopping system...")
    
    finally:
        # Stop the server
        if server_process and server_process.poll() is None:
            logger.info(f"Stopping server (PID: {server_process.pid})")
            try:
                # Try to terminate gracefully
                server_process.terminate()
                
                # Wait for process to terminate
                for _ in range(5):
                    if server_process.poll() is not None:
                        break
                    time.sleep(1)
                
                # If process is still running, kill it
                if server_process.poll() is None:
                    server_process.kill()
            except Exception as e:
                logger.error(f"Error stopping server: {str(e)}")
    
    logger.info("System stopped")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 