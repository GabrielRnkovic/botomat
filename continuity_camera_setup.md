# Setting Up Continuity Camera for Speed Camera System

Continuity Camera lets you use your iPhone as a webcam with your Mac. This is a more stable solution than third-party apps like Camo, especially for speed camera applications requiring precise timing.

## Requirements

- Mac running macOS Sequoia
- iPhone 13 Pro Max running iOS 18
- Both devices signed into the same Apple ID
- Both devices have Bluetooth and Wi-Fi enabled
- Both devices are on the same Wi-Fi network

## Step 1: Enable Continuity Camera on Your iPhone

1. On your iPhone, go to **Settings**
2. Tap **General**
3. Tap **AirPlay & Handoff**
4. Make sure **Handoff** and **Continuity Camera** are toggled ON

## Step 2: Position Your iPhone

For the speed camera system to work effectively:
1. Mount your iPhone securely with a clear view of the road
2. Position it approximately 5 meters away from your Mac's built-in camera
3. Both cameras should face the same section of road, from different angles
4. Make sure the iPhone has good lighting for license plate detection

## Step 3: Connect iPhone as Webcam

There are two ways to use Continuity Camera:

### Option A: Automatic Connection (Recommended)
1. Simply place your iPhone near your Mac
2. The iPhone should be detected automatically as a camera option
3. Your Mac will show a notification that your iPhone is available as a camera

### Option B: Manual Connection
1. Open Control Center on your Mac (click the Control Center icon in the menu bar)
2. Click on **Video Effects**
3. Select your iPhone from the camera options

## Step 4: Test Using FaceTime or Photo Booth

Before using the speed camera system:
1. Open FaceTime or Photo Booth on your Mac
2. Click on the video source selector (usually in the app's preferences or settings)
3. Select your iPhone as the camera
4. Verify you can see the iPhone's camera feed

## Step 5: Run the Speed Camera System

Once Continuity Camera is working:
1. Run the speed camera system with the following command:
```
python3 web_server.py
```
2. The system will now use:
   - Your Mac's built-in webcam as Camera 1
   - Your iPhone (via Continuity Camera) as Camera 2
   - 5.0 meters as the distance between cameras

## Troubleshooting

If Continuity Camera isn't detected:

1. **Ensure Devices are Compatible**
   - Verify your iPhone is running iOS 18 or later
   - Verify your Mac is running macOS Sequoia

2. **Check Connectivity**
   - Make sure both devices are on the same Wi-Fi network
   - Make sure Bluetooth is enabled on both devices
   - Sign out and sign back into your Apple ID on both devices

3. **Check System Settings**
   - On Mac: Go to System Settings → General → AirDrop & Handoff
   - Ensure "Allow Handoff between this Mac and your iCloud devices" is enabled

4. **Restart Both Devices**
   - Sometimes a simple restart resolves connection issues

5. **Camera Access**
   - Make sure camera access is enabled for Terminal/Python in:
   - System Settings → Privacy & Security → Camera 