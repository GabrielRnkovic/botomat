# Setting Up Camo Virtual Camera for Speed Camera System

The test detected that while Camo Studio is running, the Camo virtual camera is not available to OpenCV. Here's how to fix this:

## Step 1: Ensure Camo is Set Up Correctly

1. **Make sure Camo Studio is running**
   - Check your menu bar to confirm Camo Studio is active
   - If not, open Camo Studio from your Applications folder

2. **Check iPhone Connection**
   - Connect your iPhone to your Mac using a USB cable (more reliable than wireless)
   - Open the Camo app on your iPhone
   - Make sure your iPhone screen shows the camera view

3. **Enable Virtual Camera in Camo Studio**
   - In Camo Studio, click on the "Use as Webcam" button at the top of the window
   - This activates the Camo virtual camera that other applications can use
   - The button should turn green when enabled

## Step 2: Test Camo with Another Application

To verify Camo is working correctly:
1. Open FaceTime, Photo Booth, or Zoom
2. In the camera selection menu, choose "Camo" or "Reincubate Camo"
3. You should see the feed from your iPhone camera

## Step 3: Special Fixes for macOS

If the camera still doesn't appear in OpenCV:

1. **Restart Camo with Admin Privileges**
   - Quit Camo Studio
   - Open Terminal
   - Run: `sudo open -a "Camo Studio"`
   - Enter your password when prompted

2. **Check Camera Permissions**
   - Go to System Preferences > Security & Privacy > Privacy > Camera
   - Make sure your terminal/Python environment has camera access
   - Add Terminal or your Python IDE to the list if needed

3. **Install Camo Studio Plugin** (if available)
   - Check if Camo offers an SDK or plugin for developer access
   - Follow Camo's documentation to install any necessary components

## Step 4: Run the Detection Test Again

After completing these steps, run the test script again:
```
python3 camo_test.py
```

If Camo is configured correctly, the test should now find the virtual camera!

## Alternative Solution

If you still can't get Camo working with OpenCV, consider these alternatives:

1. **Use a Different Virtual Camera Software**
   - Try OBS Virtual Camera
   - Try ManyCam

2. **Modify the Speed Camera System**
   - Continue using the built-in webcam for Camera 1
   - Use the test video for Camera 2 as a fallback

## Contact Camo Support

If you're still having issues, consider contacting Camo support:
- Website: https://reincubate.com/support/camo/
- Email: support@reincubate.com 