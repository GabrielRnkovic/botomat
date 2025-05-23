#!/usr/bin/env python3
"""
Configuration settings for the Speed Camera System
"""

# Camera settings
CAMERA_DISTANCE_METERS = 5.0  # Distance between the two cameras in meters
CAMERA_HEIGHT_METERS = 1.2  # Height of cameras from the ground

# Speed settings
SPEED_LIMIT_KMH = 60.0  # Speed limit in km/h
SPEED_TOLERANCE_KMH = 3.0  # Tolerance for speed measurements

# Fine amounts
FINE_AMOUNTS = {
    "minor": 100,  # 1-10 km/h over limit
    "medium": 200,  # 11-20 km/h over limit
    "major": 400,  # 21-30 km/h over limit
    "extreme": 600  # >30 km/h over limit
}

# Network settings
SERVER_HOST = "0.0.0.0"  # Listen on all interfaces
SERVER_PORT = 8080  # Web server port
CAMERA_PORT = 5001  # Camera streaming port

# License plate recognition
PLATE_CONFIDENCE_THRESHOLD = 0.6  # Minimum confidence for license plate detection
OCR_LANGUAGE = "en"  # Language for OCR

# System paths
DETECTIONS_DIR = "detections"  # Directory for detection images
VIOLATIONS_DIR = "violations"  # Directory for violation records

# Logging
LOG_LEVEL = "INFO"  # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# Testing
TEST_MODE = False  # Run in test mode
USE_TEST_VIDEOS = False  # Use test videos instead of real cameras

# Load local settings if available
try:
    from local_config import *
    print("Loaded local configuration overrides")
except ImportError:
    pass 
