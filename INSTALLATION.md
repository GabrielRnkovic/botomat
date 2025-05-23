# Speed Camera System Installation Guide

This guide will help you set up the Speed Camera System that uses two iPhones to measure vehicle speed and detect license plates.

## System Requirements

- macOS computer (tested on macOS 10.15+)
- Two iPhones with iOS 14.0+
- USB cables to connect iPhones to Mac
- Python 3.8+ installed on the Mac
- Internet connection (for initial setup)

## Step 1: Install Python Dependencies

1. Open Terminal on your Mac
2. Navigate to the project directory:
   ```
   cd /path/to/speed-camera-system
   ```
3. Install required Python packages:
   ```
   pip install -r requirements.txt
   ```

## Step 2: Install the iPhone App

You need to install the SpeedCameraApp on both iPhones:

### Option 1: Using Xcode (Recommended for Development)

1. Open Xcode on your Mac
2. Create a new iOS project and replace the content with `SpeedCameraApp.swift`
3. Connect each iPhone to your Mac and deploy the app

### Option 2: Using TestFlight (For Distribution)

1. Contact the developer for a TestFlight invitation
2. Follow the TestFlight instructions to install the app

## Step 3: Position the Cameras

1. Set up a stable mount for both iPhones, exactly 5 meters apart
2. Ensure both iPhones have a clear view of the road
3. Keep both iPhones at approximately the same height

## Step 4: Configure the System

1. On the Mac, edit the `config.py` file to set the correct configuration values
2. To customize settings, create a `local_config.py` file that will override the defaults

## Step 5: Connect and Configure the iPhones

1. Connect both iPhones to your Mac via USB
2. Launch the SpeedCameraApp on both iPhones
3. In the app settings on each iPhone:
   - Enter your Mac's IP address
   - Enter port 5001
   - Set Camera ID: 0 for the first iPhone, 1 for the second iPhone

## Step 6: Launch the System

1. Open Terminal on your Mac
2. Navigate to the project directory
3. Run the launcher script:
   ```
   ./launch.py
   ```
4. The web interface should automatically open in your browser

## Step 7: Use the System

1. The web interface shows the camera feeds and detected violations
2. All detections are stored in the `detections` directory
3. All violations are stored in the `violations.json` file

## Troubleshooting

### Camera Connection Issues

- Ensure both iPhones are connected to the Mac
- Check USB cables for damage
- Restart the iPhone apps
- Try restarting the system

### License Plate Recognition Issues

- Adjust the camera positions for better view of license plates
- Check if the lighting conditions are adequate
- Update the `PLATE_CONFIDENCE_THRESHOLD` in `config.py`

### Speed Calculation Issues

- Verify the exact distance between the cameras
- Ensure the cameras are properly synchronized
- Check the timestamp accuracy in the logs

## Testing Mode

If you don't have two iPhones available, you can run the system in test mode:

```
./launch.py --test-mode
```

This will use test videos or your webcam instead of iPhones.

## Additional Information

- All logs are stored in the project directory
- For development documentation, see the project README
- For API documentation, see the API.md file 