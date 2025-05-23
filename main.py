#!/usr/bin/env python3
import os
import time
import cv2
import numpy as np
import easyocr
import threading
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("speed_camera.log"), logging.StreamHandler()]
)
logger = logging.getLogger("SpeedCamera")

# Constants
PHONE_DISTANCE_METERS = 5.0  # Distance between the two iPhones in meters
SPEED_LIMIT_KMH = 60.0  # Speed limit in km/h
FINE_AMOUNT = 100  # Fine amount in currency

# Initialize license plate reader
reader = easyocr.Reader(['en'])

class iPhoneCamera:
    def __init__(self, device_id, name):
        self.device_id = device_id
        self.name = name
        self.last_detection_time = None
        self.last_plate = None
        self.connected = False
        self.video_feed = None
    
    def connect(self):
        """Connect to the iPhone camera"""
        try:
            # In a real implementation, this would use USB or network connection
            # For demonstration, we'll simulate with local webcam or video file
            if os.path.exists(f"test_feed_{self.name}.mp4"):
                self.video_feed = cv2.VideoCapture(f"test_feed_{self.name}.mp4")
            else:
                # Try to connect to a webcam for testing
                self.video_feed = cv2.VideoCapture(self.device_id)
            
            if self.video_feed.isOpened():
                self.connected = True
                logger.info(f"Connected to {self.name} camera")
                return True
            else:
                logger.error(f"Failed to connect to {self.name} camera")
                return False
        except Exception as e:
            logger.error(f"Error connecting to {self.name} camera: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from the iPhone camera"""
        if self.video_feed:
            self.video_feed.release()
        self.connected = False
        logger.info(f"Disconnected from {self.name} camera")
    
    def get_frame(self):
        """Get a frame from the camera"""
        if not self.connected or not self.video_feed:
            return None
        
        ret, frame = self.video_feed.read()
        if not ret:
            return None
        
        return frame

class SpeedCamera:
    def __init__(self):
        self.camera1 = iPhoneCamera(0, "iPhone1")
        self.camera2 = iPhoneCamera(1, "iPhone2")
        self.running = False
        self.violations = []
        
    def start(self):
        """Start the speed camera system"""
        if self.camera1.connect() and self.camera2.connect():
            self.running = True
            logger.info("Speed camera system started")
            # Start processing in separate threads
            threading.Thread(target=self.process_camera, args=(self.camera1,), daemon=True).start()
            threading.Thread(target=self.process_camera, args=(self.camera2,), daemon=True).start()
            threading.Thread(target=self.match_detections, daemon=True).start()
            return True
        else:
            logger.error("Failed to start speed camera system")
            return False
    
    def stop(self):
        """Stop the speed camera system"""
        self.running = False
        self.camera1.disconnect()
        self.camera2.disconnect()
        logger.info("Speed camera system stopped")
    
    def detect_license_plate(self, frame):
        """Detect license plate in frame using EasyOCR"""
        if frame is None:
            return None
        
        # Convert to grayscale for better OCR
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Resize image for faster processing
        height, width = gray.shape
        gray = cv2.resize(gray, (width // 2, height // 2))
        
        # Apply image processing to enhance license plate visibility
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # Detect text in the image
        results = reader.readtext(gray)
        
        # Filter and return the most likely license plate
        if results:
            # Look for patterns similar to license plates (adjust for your country)
            for (bbox, text, prob) in results:
                # Remove spaces and convert to uppercase
                plate_text = text.replace(" ", "").upper()
                # Simple heuristic: license plates often have 5-8 characters
                if 5 <= len(plate_text) <= 8 and prob > 0.5:
                    return plate_text
        
        return None
    
    def process_camera(self, camera):
        """Process frames from a camera to detect vehicles and license plates"""
        while self.running:
            frame = camera.get_frame()
            if frame is not None:
                # Detect license plate
                plate = self.detect_license_plate(frame)
                if plate:
                    # Record detection with timestamp
                    camera.last_detection_time = time.time()
                    camera.last_plate = plate
                    logger.info(f"Camera {camera.name} detected plate: {plate}")
                    
                    # Save the frame with the detection
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    cv2.imwrite(f"detections/{camera.name}_{timestamp}_{plate}.jpg", frame)
            
            # Sleep to reduce CPU usage
            time.sleep(0.01)
    
    def match_detections(self):
        """Match detections between cameras to calculate speed"""
        while self.running:
            # Check if both cameras have detections
            if (self.camera1.last_detection_time and self.camera2.last_detection_time and
                self.camera1.last_plate and self.camera2.last_plate):
                
                # Check if license plates match (allowing for minor OCR errors)
                similarity = self.plate_similarity(self.camera1.last_plate, self.camera2.last_plate)
                
                if similarity > 0.8:  # 80% similarity threshold
                    # Calculate time difference
                    time_diff = abs(self.camera1.last_detection_time - self.camera2.last_detection_time)
                    
                    # Calculate speed in km/h
                    if time_diff > 0:
                        speed_ms = PHONE_DISTANCE_METERS / time_diff
                        speed_kmh = speed_ms * 3.6  # Convert m/s to km/h
                        
                        # Format the plate text for display
                        plate = self.camera1.last_plate if len(self.camera1.last_plate) >= len(self.camera2.last_plate) else self.camera2.last_plate
                        
                        # Log the detection
                        logger.info(f"Vehicle detected: Plate={plate}, Speed={speed_kmh:.2f} km/h")
                        
                        # Check if speed exceeds limit
                        if speed_kmh > SPEED_LIMIT_KMH:
                            violation = {
                                "plate": plate,
                                "speed": speed_kmh,
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "fine_amount": FINE_AMOUNT,
                                "location": "Test Location",
                                "id": len(self.violations) + 1
                            }
                            
                            self.violations.append(violation)
                            logger.warning(f"Speed violation: {violation}")
                            
                            # Save violation to JSON file
                            self.save_violations()
                    
                    # Reset the detection data
                    self.camera1.last_detection_time = None
                    self.camera1.last_plate = None
                    self.camera2.last_detection_time = None
                    self.camera2.last_plate = None
            
            # Sleep to reduce CPU usage
            time.sleep(0.1)
    
    def plate_similarity(self, plate1, plate2):
        """Calculate similarity between two license plates (0.0 to 1.0)"""
        # Simple implementation using string distance
        plate1 = plate1.upper().replace(" ", "")
        plate2 = plate2.upper().replace(" ", "")
        
        # Levenshtein distance
        distance = 0
        for i in range(min(len(plate1), len(plate2))):
            if plate1[i] != plate2[i]:
                distance += 1
        
        max_len = max(len(plate1), len(plate2))
        distance += abs(len(plate1) - len(plate2))
        
        return 1.0 - (distance / max_len) if max_len > 0 else 0.0
    
    def save_violations(self):
        """Save violations to a JSON file"""
        try:
            with open('violations.json', 'w') as f:
                json.dump(self.violations, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving violations: {str(e)}")

# Create Flask web app
app = Flask(__name__)
speed_camera = SpeedCamera()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/violations')
def get_violations():
    """API endpoint to get violations"""
    return jsonify(speed_camera.violations)

@app.route('/api/status')
def get_status():
    """API endpoint to get system status"""
    return jsonify({
        "running": speed_camera.running,
        "camera1_connected": speed_camera.camera1.connected,
        "camera2_connected": speed_camera.camera2.connected,
        "violation_count": len(speed_camera.violations)
    })

if __name__ == "__main__":
    # Create detection directory if it doesn't exist
    os.makedirs("detections", exist_ok=True)
    
    # Start the speed camera system
    if speed_camera.start():
        # Start Flask web app in a separate thread
        threading.Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 5000}, daemon=True).start()
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            # Stop the system when Ctrl+C is pressed
            speed_camera.stop()
            print("System stopped")
    else:
        print("Failed to start the system") 