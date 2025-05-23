# Speed Camera System

A system that uses two iPhones connected to a Mac to measure vehicle speed and capture license plate information for traffic enforcement.

## Features

- **Dual Camera Speed Detection**: Uses two iPhones positioned 5 meters apart to accurately measure vehicle speed
- **License Plate Recognition**: Employs AI-powered OCR to identify vehicle license plates
- **Automated Violation Detection**: Automatically registers vehicles exceeding the 60 km/h speed limit
- **Fine Generation**: Calculates appropriate fines based on the severity of the speed violation
- **Web Dashboard**: Real-time monitoring interface for system status and violations
- **Data Storage**: Preserves evidence including timestamps, images, and measurement data

## System Architecture

The system consists of the following components:

1. **iPhone Cameras**: Two iPhones running the custom SpeedCameraApp that stream video data to the Mac
2. **Mac Server**: Processes camera feeds, calculates speeds, and hosts the web interface
3. **License Plate Recognition Module**: Detects and reads license plates using EasyOCR
4. **Speed Calculator**: Matches detections between cameras to calculate vehicle speed
5. **Web Interface**: Provides real-time monitoring and access to violation records

## Technologies Used

- **Python 3.8+**: Core backend processing
- **OpenCV**: Computer vision for image processing
- **EasyOCR**: AI-powered optical character recognition
- **PyTorch**: Deep learning for object detection
- **Flask**: Web server framework
- **Swift**: iOS app development

## Installation

For detailed installation instructions, see [INSTALLATION.md](INSTALLATION.md).

Quick start:

```bash
# Clone the repository
git clone https://github.com/yourusername/speed-camera-system.git
cd speed-camera-system

# Install dependencies
pip install -r requirements.txt

# Launch the system
./start.sh
```

## Configuration

The system is configurable through the `config.py` file. Key settings include:

- Camera distance (default: 5 meters)
- Speed limit (default: 60 km/h)
- Fine amounts for different violation levels
- Network ports and server settings

## Usage

1. Position two iPhones 5 meters apart with a clear view of the road
2. Install and launch the SpeedCameraApp on both iPhones
3. Connect the iPhones to your Mac via USB
4. Run the system using `./start.sh`
5. Monitor speed violations through the web interface at http://localhost:5000

## Testing Mode

For development or demonstration purposes, the system can run in test mode without actual iPhones:

```bash
./start.sh --test-mode
```

This mode uses sample videos or your Mac's webcam to simulate the iPhone cameras.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- EasyOCR for license plate recognition
- OpenCV community for computer vision tools
- Flask for the web framework 