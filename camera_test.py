#!/usr/bin/env python3
import cv2
import numpy as np
import time
import os

def test_camera(index):
    """Test a camera at the specified index and return details"""
    print(f"\nTesting camera at index {index}...")
    
    try:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            print(f"Camera {index} could not be opened")
            return None
        
        # Get basic camera properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Try to read a frame
        ret, frame = cap.read()
        success = ret and frame is not None
        
        # Create a directory for test frames
        os.makedirs("camera_test", exist_ok=True)
        
        # Save a frame for inspection if successful
        if success:
            frame_file = f"camera_test/camera_{index}_test.jpg"
            cv2.imwrite(frame_file, frame)
            print(f"Saved test frame to {frame_file}")
        
        # Release the camera
        cap.release()
        
        result = {
            "index": index,
            "opened": True,
            "width": width,
            "height": height,
            "fps": fps,
            "frame_read_success": success
        }
        
        print(f"Camera {index} details:")
        print(f"  - Resolution: {width}x{height}")
        print(f"  - FPS: {fps}")
        print(f"  - Successfully read frame: {success}")
        
        return result
    
    except Exception as e:
        print(f"Error testing camera {index}: {str(e)}")
        return None

def find_all_cameras(max_index=20):
    """Test a range of camera indices and return details of available cameras"""
    print(f"Scanning for cameras (indices 0-{max_index-1})...")
    
    available_cameras = []
    
    for i in range(max_index):
        result = test_camera(i)
        if result and result["opened"] and result["frame_read_success"]:
            available_cameras.append(result)
    
    return available_cameras

def main():
    """Main function"""
    print("Camera Detection Tool")
    print("====================")
    print("This tool will scan for available cameras and save test frames.")
    
    # Find all available cameras
    available_cameras = find_all_cameras(max_index=20)
    
    # Print summary
    print("\nCamera Detection Results:")
    print("=========================")
    
    if not available_cameras:
        print("No working cameras detected!")
    else:
        print(f"Found {len(available_cameras)} working cameras:")
        for cam in available_cameras:
            print(f"  - Camera {cam['index']}: {cam['width']}x{cam['height']} @ {cam['fps']} fps")
    
    print("\nCheck the 'camera_test' directory for test frames from each camera.")
    print("Look for the Camo virtual camera in the images.")

if __name__ == "__main__":
    main() 