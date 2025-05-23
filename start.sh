#!/bin/bash

# Speed Camera System Startup Script

# Navigate to the project directory
cd "$(dirname "$0")"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check for required directories
mkdir -p detections
mkdir -p violations
mkdir -p templates

# Check if requirements are installed
if ! python3 -c "import cv2" &> /dev/null; then
    echo "Installing required packages..."
    python3 -m pip install -r requirements.txt
fi

# Start the system
echo "Starting Speed Camera System..."
python3 launch.py "$@" 