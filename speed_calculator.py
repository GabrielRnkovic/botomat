#!/usr/bin/env python3
import time
import logging
import json
import os
from datetime import datetime

logger = logging.getLogger("SpeedCalculator")

class SpeedCalculator:
    def __init__(self, distance_meters=10.0, speed_limit_kmh=50.0):
        """Initialize speed calculator
        
        Args:
            distance_meters: Distance between the two cameras in meters
            speed_limit_kmh: Speed limit in km/h
        """
        self.distance_meters = distance_meters
        self.speed_limit_kmh = speed_limit_kmh
        self.pending_detections = {}  # Store first camera detections
        self.completed_detections = []  # Store completed speed measurements
        self.detection_timeout = 6.0  # Timeout for matching detections (seconds) - reduced for closer cameras
        
        # Create violations directory if it doesn't exist
        os.makedirs("violations", exist_ok=True)
        
        # Load existing violations if available
        self.violations_file = "violations.json"
        self.violations = []
        self.load_violations()
        
        logger.info(f"Speed calculator initialized with distance: {distance_meters}m, limit: {speed_limit_kmh}km/h")
    
    def load_violations(self):
        """Load existing violations from file"""
        if os.path.exists(self.violations_file):
            try:
                with open(self.violations_file, 'r') as f:
                    self.violations = json.load(f)
                logger.info(f"Loaded {len(self.violations)} existing violations")
            except Exception as e:
                logger.error(f"Error loading violations: {str(e)}")
    
    def save_violations(self):
        """Save violations to file"""
        try:
            with open(self.violations_file, 'w') as f:
                json.dump(self.violations, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving violations: {str(e)}")
    
    def process_detection(self, camera_id, plate_text, timestamp=None, image_path=None):
        """Process a license plate detection from one of the cameras
        
        Args:
            camera_id: ID of the camera (1 or 2)
            plate_text: Detected license plate text
            timestamp: Detection timestamp (defaults to current time)
            image_path: Path to the saved image (optional)
            
        Returns:
            dict or None: Speed measurement if available, None otherwise
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Normalize plate text to improve matching (remove spaces, convert to uppercase)
        plate_text = plate_text.strip().upper().replace(" ", "")
        
        # Log all detections for debugging
        logger.info(f"Detection from camera {camera_id}: plate={plate_text}, time={timestamp}")
        
        # Clean up expired detections
        self._cleanup_expired_detections()
        
        # Get other camera ID
        other_camera_id = 2 if camera_id == 1 else 1
        
        # Check if we have a matching detection from the other camera
        if plate_text in self.pending_detections:
            pending = self.pending_detections[plate_text]
            
            # Check if the detection is from the other camera
            if pending["camera_id"] == other_camera_id:
                # Calculate time difference and speed
                time_diff = abs(timestamp - pending["timestamp"])
                
                # For very close cameras (0.5m), even 0.1 seconds could be a valid measurement
                # but still cap at detection_timeout to avoid matching unrelated vehicles
                if 0.1 <= time_diff <= self.detection_timeout:
                    speed_ms = self.distance_meters / time_diff if time_diff > 0 else 0
                    speed_kmh = speed_ms * 3.6  # Convert m/s to km/h
                    
                    # Create speed measurement record
                    measurement = {
                        "plate": plate_text,
                        "camera1_time": pending["timestamp"] if pending["camera_id"] == 1 else timestamp,
                        "camera2_time": pending["timestamp"] if pending["camera_id"] == 2 else timestamp,
                        "time_diff_seconds": time_diff,
                        "speed_ms": speed_ms,
                        "speed_kmh": speed_kmh,
                        "distance_meters": self.distance_meters,
                        "camera1_image": pending["image_path"] if pending["camera_id"] == 1 else image_path,
                        "camera2_image": pending["image_path"] if pending["camera_id"] == 2 else image_path,
                        "measurement_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "over_speed_limit": speed_kmh > self.speed_limit_kmh
                    }
                    
                    # Add to completed detections
                    self.completed_detections.append(measurement)
                    
                    # Check if speed exceeds limit
                    if speed_kmh > self.speed_limit_kmh:
                        self._create_violation(measurement)
                    
                    # Remove from pending
                    del self.pending_detections[plate_text]
                    
                    logger.info(f"Speed measurement: Plate={plate_text}, Speed={speed_kmh:.2f} km/h")
                    return measurement
            
            # If same camera, update the detection
            elif pending["camera_id"] == camera_id:
                # Update with the most recent detection
                self.pending_detections[plate_text] = {
                    "camera_id": camera_id,
                    "timestamp": timestamp,
                    "image_path": image_path
                }
                return None
        
        # First detection of this plate, add to pending
        self.pending_detections[plate_text] = {
            "camera_id": camera_id,
            "timestamp": timestamp,
            "image_path": image_path
        }
        
        return None
    
    def _cleanup_expired_detections(self):
        """Clean up expired detections based on timeout"""
        current_time = time.time()
        expired_plates = []
        
        for plate, data in self.pending_detections.items():
            if current_time - data["timestamp"] > self.detection_timeout:
                expired_plates.append(plate)
        
        for plate in expired_plates:
            logger.debug(f"Removing expired detection for plate {plate}")
            del self.pending_detections[plate]
    
    def _create_violation(self, measurement):
        """Create a speed violation record
        
        Args:
            measurement: Speed measurement dictionary
        """
        violation = {
            "id": len(self.violations) + 1,
            "plate": measurement["plate"],
            "speed_kmh": measurement["speed_kmh"],
            "speed_limit_kmh": self.speed_limit_kmh,
            "timestamp": measurement["measurement_time"],
            "location": "Test Location",
            "camera1_image": measurement["camera1_image"],
            "camera2_image": measurement["camera2_image"],
            "time_diff_seconds": measurement["time_diff_seconds"],
            "fine_amount": self._calculate_fine(measurement["speed_kmh"])
        }
        
        self.violations.append(violation)
        self.save_violations()
        
        logger.warning(f"Speed violation: Plate={violation['plate']}, Speed={violation['speed_kmh']:.2f} km/h, Fine=${violation['fine_amount']}")
        
        return violation
    
    def _calculate_fine(self, speed_kmh):
        """Calculate fine amount based on speed
        
        Args:
            speed_kmh: Measured speed in km/h
            
        Returns:
            Fine amount (currency)
        """
        # Example fine calculation (adjust as needed)
        excess_speed = speed_kmh - self.speed_limit_kmh
        
        if excess_speed <= 10:
            return 100  # Small excess
        elif excess_speed <= 20:
            return 200  # Medium excess
        elif excess_speed <= 30:
            return 400  # Large excess
        else:
            return 600  # Extreme excess
    
    def get_recent_measurements(self, count=10):
        """Get recent speed measurements
        
        Args:
            count: Number of measurements to return
            
        Returns:
            List of speed measurements
        """
        return self.completed_detections[-count:]
    
    def get_violations(self, count=None):
        """Get speed violations
        
        Args:
            count: Number of violations to return (None for all)
            
        Returns:
            List of violations
        """
        if count is None:
            return self.violations
        else:
            return self.violations[-count:]
    
    def get_statistics(self):
        """Get speed measurement statistics
        
        Returns:
            Dictionary with statistics
        """
        total_measurements = len(self.completed_detections)
        total_violations = len(self.violations)
        
        if total_measurements == 0:
            return {
                "total_measurements": 0,
                "total_violations": 0,
                "violation_percentage": 0,
                "average_speed": 0,
                "max_speed": 0
            }
        
        # Calculate statistics
        speeds = [m["speed_kmh"] for m in self.completed_detections]
        avg_speed = sum(speeds) / len(speeds)
        max_speed = max(speeds) if speeds else 0
        violation_percentage = (total_violations / total_measurements) * 100 if total_measurements > 0 else 0
        
        return {
            "total_measurements": total_measurements,
            "total_violations": total_violations,
            "violation_percentage": violation_percentage,
            "average_speed": avg_speed,
            "max_speed": max_speed
        }
    
    def _create_test_detection(self):
        """Create a test detection with simulated data for demonstration
        
        Returns:
            dict: Speed measurement dictionary
        """
        # Disabled for real-world testing
        return None
        
        # Original test detection code commented out
        """
        current_time = time.time()
        
        # Create random test data
        plates = ["ABC123", "XYZ789", "DEF456", "GHI789"]
        plate_idx = int(current_time) % len(plates)
        test_plate = plates[plate_idx]
        
        # Create a simulated detection with excessive speed
        test_speed = 70.0  # km/h - well above normal limit
        
        # Create measurement record
        measurement = {
            "plate": test_plate,
            "camera1_time": current_time - 1.0,
            "camera2_time": current_time,
            "time_diff_seconds": 1.0,
            "speed_ms": test_speed / 3.6,
            "speed_kmh": test_speed,
            "distance_meters": self.distance_meters,
            "camera1_image": None,
            "camera2_image": None,
            "measurement_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "over_speed_limit": test_speed > self.speed_limit_kmh
        }
        
        # Save as violation if over speed limit
        if test_speed > self.speed_limit_kmh:
            violation = self._create_violation(measurement)
            logger.warning(f"TEST VIOLATION: Plate={test_plate}, Speed={test_speed:.2f} km/h (limit: {self.speed_limit_kmh})")
        
        return measurement
        """

# Sample usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create speed calculator
    calculator = SpeedCalculator(distance_meters=10.0, speed_limit_kmh=50.0)
    
    # Simulate some detections
    # First camera detection
    result1 = calculator.process_detection(
        camera_id=1,
        plate_text="ABC123",
        timestamp=time.time(),
        image_path="simulated_camera1.jpg"
    )
    
    # Wait a bit (simulating car movement)
    time.sleep(0.5)  # 0.5 seconds = 36 km/h if 5 meters apart
    
    # Second camera detection
    result2 = calculator.process_detection(
        camera_id=2,
        plate_text="ABC123",
        timestamp=time.time(),
        image_path="simulated_camera2.jpg"
    )
    
    if result2:
        print(f"Speed measurement: {result2['plate']} traveled at {result2['speed_kmh']:.2f} km/h")
        
        if result2["over_speed_limit"]:
            print(f"VIOLATION: Exceeded speed limit of {calculator.speed_limit_kmh} km/h")
    
    # Simulate a faster car
    # First camera detection
    result1 = calculator.process_detection(
        camera_id=1,
        plate_text="XYZ789",
        timestamp=time.time(),
        image_path="simulated_camera1_2.jpg"
    )
    
    # Wait less (simulating faster car)
    time.sleep(0.2)  # 0.2 seconds = 90 km/h if 5 meters apart
    
    # Second camera detection
    result2 = calculator.process_detection(
        camera_id=2,
        plate_text="XYZ789",
        timestamp=time.time(),
        image_path="simulated_camera2_2.jpg"
    )
    
    if result2:
        print(f"Speed measurement: {result2['plate']} traveled at {result2['speed_kmh']:.2f} km/h")
        
        if result2["over_speed_limit"]:
            print(f"VIOLATION: Exceeded speed limit of {calculator.speed_limit_kmh} km/h")
    
    # Print statistics
    print("\nStatistics:")
    stats = calculator.get_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}") 