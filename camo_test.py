#!/usr/bin/env python3
import cv2
import time
import os

# List of camera indices to test for Camo
# Camo often uses indices like 1, 2, or 4
CAMO_TEST_INDICES = [1, 2, 3, 4, 5, 6]

def test_camera(index):
    """Test if a camera index works and save a frame"""
    print(f"Testing camera index {index}...")
    
    try:
        # Open the camera
        cap = cv2.VideoCapture(index)
        
        if not cap.isOpened():
            print(f"  - Camera index {index}: Failed to open")
            return False
        
        # Read a frame
        ret, frame = cap.read()
        if not ret or frame is None:
            print(f"  - Camera index {index}: Opened but couldn't read frame")
            cap.release()
            return False
        
        # Get camera info
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"  - Camera index {index}: SUCCESS")
        print(f"    Resolution: {width}x{height}, FPS: {fps}")
        
        # Create a directory to save test frames
        os.makedirs("camo_test", exist_ok=True)
        
        # Save the frame
        test_file = f"camo_test/camera_{index}.jpg"
        cv2.imwrite(test_file, frame)
        print(f"    Saved test frame to {test_file}")
        
        # Release the camera
        cap.release()
        return True
    
    except Exception as e:
        print(f"  - Camera index {index}: Error: {str(e)}")
        return False

def main():
    # Print header
    print("\nCAMO VIRTUAL CAMERA TEST")
    print("=======================\n")
    print("This script will test potential camera indices that might be used by Camo.\n")
    
    # Test the camera indices
    working_cameras = []
    
    # First test the built-in camera (index 0)
    print("Testing built-in camera (index 0)...")
    built_in_works = test_camera(0)
    if built_in_works:
        working_cameras.append(0)
        print("Built-in camera works!\n")
    else:
        print("Built-in camera not working.\n")
    
    # Test potential Camo indices
    print("Testing potential Camo camera indices...")
    for index in CAMO_TEST_INDICES:
        if test_camera(index):
            working_cameras.append(index)
    
    # Print summary
    print("\nTEST RESULTS")
    print("===========")
    
    if len(working_cameras) <= 1 and 0 in working_cameras:
        print("Only the built-in camera was detected. Camo camera was NOT found.")
        print("\nPossible reasons:")
        print("1. Camo is not running")
        print("2. The iPhone is not connected")
        print("3. Camo virtual camera is not enabled")
        print("\nRecommended actions:")
        print("1. Make sure Camo Studio is running")
        print("2. Connect your iPhone and open the Camo app")
        print("3. In Camo Studio, check that 'Use as Webcam' is enabled")
    elif len(working_cameras) > 1:
        camo_indices = [idx for idx in working_cameras if idx != 0]
        print(f"SUCCESS! Found {len(camo_indices)} potential Camo camera(s) at indices: {camo_indices}")
        print("\nUse these indices in your web_server.py script.")
        print(f"For example, try camera index {camo_indices[0]} for Camera 2.")
    else:
        print("No working cameras detected at all. Check your camera permissions.")
    
    print("\nCheck the 'camo_test' directory to see test frames from each camera.")
    print("This can help you visually identify which index corresponds to Camo.")

if __name__ == "__main__":
    main() 