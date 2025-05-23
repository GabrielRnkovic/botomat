#!/usr/bin/env python3
import os
import logging
import time
import threading
import cv2
import numpy as np
from flask import Flask, render_template, Response, jsonify, send_from_directory
import json

# Import our modules
from speed_calculator import SpeedCalculator
from plate_recognition import PlateRecognizer
from iphone_connector import iPhoneConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("web_server.log"), logging.StreamHandler()]
)
logger = logging.getLogger("WebServer")

# Create Flask app
app = Flask(__name__)
app.config['DEBUG'] = False

# Initialize components
speed_calculator = SpeedCalculator(distance_meters=5.0, speed_limit_kmh=60.0)
plate_recognizer = PlateRecognizer()
iphone_connector = iPhoneConnector()

# Simulated camera streams for testing
camera_feeds = {
    1: None,  # Will be set to the first iPhone camera
    2: None   # Will be set to the second iPhone camera
}

# System status
system_status = {
    "running": False,
    "camera1_connected": False,
    "camera2_connected": False,
    "violation_count": 0,
    "last_update": time.time()
}

# Initialization lock to prevent race conditions
init_lock = threading.Lock()

def initialize_system():
    """Initialize the speed camera system"""
    global system_status

    with init_lock:
        logger.info("Initializing speed camera system...")
        
        # Close any existing camera feeds first
        for cam_id, cam in camera_feeds.items():
            if cam is not None and cam.isOpened():
                cam.release()
                
        print("\n==================================================")
        print("SPEED CAMERA SYSTEM INITIALIZATION:")
        print("==================================================")
        print("- Camera 1: Built-in webcam")
        print("- Camera 2: iPhone Continuity Camera")
        print("- Distance setting:", speed_calculator.distance_meters, "meters")
        print("- Real license plate detection ONLY (no simulation)")
        print("==================================================\n")
        
        # List available cameras for debugging
        available_cameras = []
        # Try more indices (up to 20) to find all cameras
        for i in range(20):
            try:
                logger.info(f"Testing camera index {i}...")
                test_cam = cv2.VideoCapture(i)
                if test_cam.isOpened():
                    # Get camera info to help identify it
                    width = test_cam.get(cv2.CAP_PROP_FRAME_WIDTH)
                    height = test_cam.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    available_cameras.append(i)
                    logger.info(f"Found camera at index {i} - Resolution: {width}x{height}")
                    # Read a test frame to confirm it works
                    ret, frame = test_cam.read()
                    if ret:
                        logger.info(f"Successfully read frame from camera {i}")
                    else:
                        logger.warning(f"Could not read frame from camera {i}")
                test_cam.release()
            except Exception as e:
                logger.error(f"Error testing camera {i}: {str(e)}")
        
        logger.info(f"Available camera indices: {available_cameras}")
        
        # Set up first camera - built-in webcam (usually index 0)
        camera_feeds[1] = cv2.VideoCapture(0)  # First camera (built-in)
        system_status["camera1_connected"] = camera_feeds[1].isOpened()
        
        if system_status["camera1_connected"]:
            logger.info("Camera 1 connected successfully (built-in webcam)")
            
            # Set camera properties for better quality
            camera_feeds[1].set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            camera_feeds[1].set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            camera_feeds[1].set(cv2.CAP_PROP_FPS, 30)
        else:
            logger.warning("Could not connect to built-in webcam, falling back to test video")
            # Fall back to test video
            test_video1_path = "test_feed_1.mp4"
            if os.path.exists(test_video1_path):
                logger.info(f"Using test video for Camera 1: {test_video1_path}")
                camera_feeds[1] = cv2.VideoCapture(test_video1_path)
                system_status["camera1_connected"] = camera_feeds[1].isOpened()
        
        # Set up second camera - iPhone Continuity Camera
        # Continuity Camera usually appears as the second camera (index 1)
        # But it could also be higher if other virtual cameras are installed
        continuity_camera_index = None
        
        # Find Continuity Camera - typically the second webcam in the system
        # Skip index 0 (built-in camera)
        for idx in available_cameras:
            if idx != 0:  # Skip built-in
                logger.info(f"Trying potential Continuity Camera at index {idx}")
                continuity_camera_index = idx
                break
        
        if continuity_camera_index is not None:
            logger.info(f"Using Continuity Camera at index {continuity_camera_index} for Camera 2")
            camera_feeds[2] = cv2.VideoCapture(continuity_camera_index)
            system_status["camera2_connected"] = camera_feeds[2].isOpened()
            
            if system_status["camera2_connected"]:
                logger.info("Camera 2 connected successfully (iPhone Continuity Camera)")
                
                # Set camera properties for better quality
                camera_feeds[2].set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                camera_feeds[2].set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                camera_feeds[2].set(cv2.CAP_PROP_FPS, 30)
            else:
                logger.warning("Could not connect to Continuity Camera, falling back to test video")
                # Fall back to test video
                test_video2_path = "test_feed_2.mp4"
                if os.path.exists(test_video2_path):
                    logger.info(f"Using test video for Camera 2: {test_video2_path}")
                    camera_feeds[2] = cv2.VideoCapture(test_video2_path)
                    system_status["camera2_connected"] = camera_feeds[2].isOpened()
        else:
            logger.warning("No Continuity Camera found, falling back to test video")
            # Fall back to test video
            test_video2_path = "test_feed_2.mp4"
            if os.path.exists(test_video2_path):
                logger.info(f"Using test video for Camera 2: {test_video2_path}")
                camera_feeds[2] = cv2.VideoCapture(test_video2_path)
                system_status["camera2_connected"] = camera_feeds[2].isOpened()
                
        # Final check to see if we have cameras
        if system_status["camera1_connected"] or system_status["camera2_connected"]:
            system_status["running"] = True
            logger.info("Speed camera system initialized successfully")
            
            # Start processing threads
            if system_status["camera1_connected"]:
                threading.Thread(target=process_camera_feed, args=(1,), daemon=True).start()
            if system_status["camera2_connected"]:
                threading.Thread(target=process_camera_feed, args=(2,), daemon=True).start()
            
            return True
        else:
            logger.error("Failed to initialize system - no cameras available")
            return False

def process_camera_feed(camera_id):
    """Process video feed from a camera
    
    Args:
        camera_id: ID of the camera (1 or 2)
    """
    global system_status
    
    logger.info(f"Starting processing for camera {camera_id}")
    
    cam = camera_feeds[camera_id]
    if cam is None or not cam.isOpened():
        logger.error(f"Camera {camera_id} is not available")
        return
    
    frame_count = 0
    last_detection_time = 0
    detection_interval = 1  # seconds between detection attempts (reduced from 3)
    
    while system_status["running"]:
        ret, frame = cam.read()
        
        if not ret:
            # Try to reopen the camera
            logger.warning(f"Lost connection to camera {camera_id}, trying to reconnect...")
            if camera_id == 1:
                system_status["camera1_connected"] = False
            else:
                system_status["camera2_connected"] = False
                
            time.sleep(1)
            
            # For test videos, reopen from beginning
            if os.path.exists(f"test_feed_{camera_id}.mp4"):
                if cam is not None and cam.isOpened():
                    cam.release()
                cam = cv2.VideoCapture(f"test_feed_{camera_id}.mp4")
                camera_feeds[camera_id] = cam
                if camera_id == 1:
                    system_status["camera1_connected"] = cam.isOpened()
                else:
                    system_status["camera2_connected"] = cam.isOpened()
                logger.info(f"Reopened test video for camera {camera_id}")
            continue
        
        # Flip the frame (videos are upside down)
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        
        current_time = time.time()
        
        # Save frames periodically for analysis 
        if frame_count % 30 == 0:  # Increased frequency (was 50)
            # Save a frame every ~3 seconds for debugging
            debug_dir = "debug_frames"
            os.makedirs(debug_dir, exist_ok=True)
            debug_filename = f"{debug_dir}/camera{camera_id}_{int(current_time)}.jpg"
            cv2.imwrite(debug_filename, frame)
            logger.debug(f"Saved debug frame: {debug_filename}")
        
        # Process every 3rd frame to increase detection frequency (was 5th)
        process_this_frame = (frame_count % 3 == 0)
        
        # Check if it's time to attempt a detection
        attempt_detection = (current_time - last_detection_time) > detection_interval
        
        if process_this_frame or attempt_detection:
            # Process frame to detect license plates
            annotated, plate, confidence = plate_recognizer.process_video_frame(frame)
            
            # If we forced a detection, update the last detection time
            if attempt_detection:
                last_detection_time = current_time
            
            if plate and confidence > 0.2:  # Lowered threshold further for more detections
                logger.info(f"Camera {camera_id} detected plate: {plate} ({confidence:.2f})")
                
                # Save the frame
                timestamp = int(time.time())
                image_filename = f"detections/camera{camera_id}_{timestamp}_{plate}.jpg"
                cv2.imwrite(image_filename, frame)
                
                # Process the detection for speed calculation
                measurement = speed_calculator.process_detection(
                    camera_id=camera_id,
                    plate_text=plate,
                    timestamp=time.time(),
                    image_path=image_filename
                )
                
                # Update violation count regardless of result
                system_status["violation_count"] = len(speed_calculator.violations)
                
                if measurement:
                    logger.info(f"Speed measurement: {measurement['speed_kmh']:.1f} km/h")
            else:
                # Only log, don't simulate plates anymore
                logger.debug(f"No plate detected in frame {frame_count} from camera {camera_id} or confidence too low")
        
        frame_count += 1
        
        # Sleep to reduce CPU usage (reduced from 0.01)
        time.sleep(0.005)

def generate_frames(camera_id):
    """Generate frames for video streaming
    
    Args:
        camera_id: ID of the camera (1 or 2)
    """
    cam = camera_feeds[camera_id]
    if cam is None or not cam.isOpened():
        # Generate an error image
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(img, f"Camera {camera_id} Not Available", (50, 240), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        while True:
            ret, jpeg = cv2.imencode('.jpg', img)
            frame = jpeg.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            time.sleep(1)
    
    while True:
        success, frame = cam.read()
        if not success:
            # Generate an error image
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(img, f"Camera {camera_id} Feed Lost", (50, 240), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Try to reopen the video file
            if os.path.exists(f"test_feed_{camera_id}.mp4"):
                if cam is not None and cam.isOpened():
                    cam.release()
                cam = cv2.VideoCapture(f"test_feed_{camera_id}.mp4")
                camera_feeds[camera_id] = cam
                logger.info(f"Reopened test video for camera {camera_id} in generate_frames")
                # Try to read first frame
                success, frame = cam.read()
                if success:
                    # Flip the frame (videos are upside down)
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                    # Add info text to the frame
                    cv2.putText(frame, f"Camera {camera_id}", (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Add timestamp
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame, timestamp, (10, frame.shape[0] - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                    
                    ret, jpeg = cv2.imencode('.jpg', frame)
                    frame = jpeg.tobytes()
                    yield (b'--frame\r\n'
                          b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
                    continue
            
            ret, jpeg = cv2.imencode('.jpg', img)
        else:
            # Flip the frame (videos are upside down)
            frame = cv2.rotate(frame, cv2.ROTATE_180)
            
            # Add some info text to the frame
            cv2.putText(frame, f"Camera {camera_id}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Add timestamp
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, (10, frame.shape[0] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
            
            ret, jpeg = cv2.imencode('.jpg', frame)
            
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        
        # Limit frame rate to reduce CPU usage
        time.sleep(0.1)

# Routes
@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/video_feed/<int:camera_id>')
def video_feed(camera_id):
    """Video streaming route for a specific camera"""
    return Response(generate_frames(camera_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def api_status():
    """API endpoint to get the system status"""
    # Update the status with current violation count
    system_status["violation_count"] = len(speed_calculator.violations)
    system_status["last_update"] = time.time()
    return jsonify(system_status)

@app.route('/api/violations')
def api_violations():
    """API endpoint to get violations"""
    return jsonify(speed_calculator.violations)

@app.route('/api/statistics')
def api_statistics():
    """API endpoint to get statistics"""
    return jsonify(speed_calculator.get_statistics())

@app.route('/detections/<path:filename>')
def detection_image(filename):
    """Serve detection images"""
    return send_from_directory('detections', filename)

# Main function
if __name__ == "__main__":
    # Create required directories
    os.makedirs("detections", exist_ok=True)
    os.makedirs("violations", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    os.makedirs("debug_frames", exist_ok=True)
    
    # Initialize system
    if initialize_system():
        # Start Flask server
        try:
            logger.info("Starting web server on http://0.0.0.0:8080")
            logger.info(f"Speed calculator using {speed_calculator.distance_meters}m between cameras")
            logger.info(f"Speed limit set to {speed_calculator.speed_limit_kmh}km/h")
            app.run(host='0.0.0.0', port=8080)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            system_status["running"] = False
            
            # Close camera feeds
            for cam_id, cam in camera_feeds.items():
                if cam is not None and cam.isOpened():
                    cam.release()
    else:
        logger.error("Failed to initialize system, exiting") 