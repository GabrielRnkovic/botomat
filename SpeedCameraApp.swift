import UIKit
import AVFoundation
import Network

class SpeedCameraViewController: UIViewController {
    
    // MARK: - Outlets
    private var previewView = UIView()
    private var statusLabel = UILabel()
    private var connectionStatusLabel = UILabel()
    private var cameraIdLabel = UILabel()
    private var overlayView = UIView()
    
    // MARK: - Properties
    private var captureSession: AVCaptureSession?
    private var videoPreviewLayer: AVCaptureVideoPreviewLayer?
    private var videoOutput = AVCaptureVideoDataOutput()
    private var connection: NWConnection?
    private var hostName: String = "192.168.1.1"  // Default Mac IP address, will be updated from settings
    private var port: UInt16 = 5001  // Default port
    private var cameraId: Int = 0  // 0 for first camera, 1 for second camera
    private var isConnected = false
    private var frameCount = 0
    
    // MARK: - View Lifecycle
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupCamera()
        
        // Load settings
        if let savedHost = UserDefaults.standard.string(forKey: "hostName") {
            hostName = savedHost
        }
        port = UInt16(UserDefaults.standard.integer(forKey: "port"))
        if port == 0 {
            port = 5001  // Default if not set
        }
        cameraId = UserDefaults.standard.integer(forKey: "cameraId")
        
        // Update UI with loaded settings
        cameraIdLabel.text = "Camera ID: \(cameraId + 1)"
        
        // Connect to server
        connectToServer()
    }
    
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        startCaptureSession()
    }
    
    override func viewDidDisappear(_ animated: Bool) {
        super.viewDidDisappear(animated)
        stopCaptureSession()
    }
    
    // MARK: - UI Setup
    private func setupUI() {
        view.backgroundColor = .black
        
        // Add preview view
        previewView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(previewView)
        NSLayoutConstraint.activate([
            previewView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            previewView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            previewView.topAnchor.constraint(equalTo: view.topAnchor),
            previewView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])
        
        // Add overlay view
        overlayView.translatesAutoresizingMaskIntoConstraints = false
        overlayView.backgroundColor = .clear
        view.addSubview(overlayView)
        NSLayoutConstraint.activate([
            overlayView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            overlayView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            overlayView.topAnchor.constraint(equalTo: view.topAnchor),
            overlayView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])
        
        // Add status label
        statusLabel.translatesAutoresizingMaskIntoConstraints = false
        statusLabel.textColor = .white
        statusLabel.textAlignment = .center
        statusLabel.text = "Initializing..."
        statusLabel.backgroundColor = UIColor.black.withAlphaComponent(0.6)
        view.addSubview(statusLabel)
        NSLayoutConstraint.activate([
            statusLabel.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            statusLabel.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            statusLabel.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor),
            statusLabel.heightAnchor.constraint(equalToConstant: 40)
        ])
        
        // Add connection status label
        connectionStatusLabel.translatesAutoresizingMaskIntoConstraints = false
        connectionStatusLabel.textColor = .white
        connectionStatusLabel.textAlignment = .center
        connectionStatusLabel.text = "Disconnected"
        connectionStatusLabel.backgroundColor = UIColor.red.withAlphaComponent(0.6)
        view.addSubview(connectionStatusLabel)
        NSLayoutConstraint.activate([
            connectionStatusLabel.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            connectionStatusLabel.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            connectionStatusLabel.bottomAnchor.constraint(equalTo: statusLabel.topAnchor, constant: -5),
            connectionStatusLabel.heightAnchor.constraint(equalToConstant: 30)
        ])
        
        // Add camera ID label
        cameraIdLabel.translatesAutoresizingMaskIntoConstraints = false
        cameraIdLabel.textColor = .white
        cameraIdLabel.textAlignment = .center
        cameraIdLabel.text = "Camera ID: \(cameraId + 1)"
        cameraIdLabel.backgroundColor = UIColor.black.withAlphaComponent(0.6)
        view.addSubview(cameraIdLabel)
        NSLayoutConstraint.activate([
            cameraIdLabel.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            cameraIdLabel.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            cameraIdLabel.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            cameraIdLabel.heightAnchor.constraint(equalToConstant: 30)
        ])
        
        // Add settings button
        let settingsButton = UIButton(type: .system)
        settingsButton.translatesAutoresizingMaskIntoConstraints = false
        settingsButton.setTitle("Settings", for: .normal)
        settingsButton.setTitleColor(.white, for: .normal)
        settingsButton.backgroundColor = UIColor.systemBlue.withAlphaComponent(0.7)
        settingsButton.layer.cornerRadius = 5
        settingsButton.addTarget(self, action: #selector(showSettings), for: .touchUpInside)
        view.addSubview(settingsButton)
        NSLayoutConstraint.activate([
            settingsButton.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -20),
            settingsButton.topAnchor.constraint(equalTo: cameraIdLabel.bottomAnchor, constant: 10),
            settingsButton.widthAnchor.constraint(equalToConstant: 80),
            settingsButton.heightAnchor.constraint(equalToConstant: 40)
        ])
        
        // Draw target area for license plates
        drawPlateTargetArea()
    }
    
    private func drawPlateTargetArea() {
        // Create a rectangle with dashed lines to indicate the optimal license plate area
        let targetView = UIView(frame: CGRect(x: 0, y: 0, width: view.bounds.width * 0.8, height: view.bounds.height * 0.2))
        targetView.center = view.center
        targetView.backgroundColor = .clear
        
        let shapeLayer = CAShapeLayer()
        let path = UIBezierPath(rect: targetView.bounds)
        shapeLayer.path = path.cgPath
        shapeLayer.strokeColor = UIColor.green.cgColor
        shapeLayer.fillColor = UIColor.clear.cgColor
        shapeLayer.lineWidth = 2
        shapeLayer.lineDashPattern = [4, 4]
        
        targetView.layer.addSublayer(shapeLayer)
        overlayView.addSubview(targetView)
        
        // Add a label
        let label = UILabel(frame: CGRect(x: 0, y: -30, width: targetView.bounds.width, height: 25))
        label.textAlignment = .center
        label.text = "Position License Plate Here"
        label.textColor = .green
        label.font = UIFont.systemFont(ofSize: 14, weight: .bold)
        targetView.addSubview(label)
    }
    
    // MARK: - Camera Setup
    private func setupCamera() {
        captureSession = AVCaptureSession()
        captureSession?.sessionPreset = .high
        
        guard let backCamera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back) else {
            statusLabel.text = "Unable to access back camera"
            return
        }
        
        do {
            let input = try AVCaptureDeviceInput(device: backCamera)
            if captureSession?.canAddInput(input) == true {
                captureSession?.addInput(input)
            }
            
            videoPreviewLayer = AVCaptureVideoPreviewLayer(session: captureSession!)
            videoPreviewLayer?.videoGravity = .resizeAspectFill
            videoPreviewLayer?.connection?.videoOrientation = .portrait
            videoPreviewLayer?.frame = previewView.bounds
            if let previewLayer = videoPreviewLayer {
                previewView.layer.addSublayer(previewLayer)
            }
            
            // Set up video output
            videoOutput.setSampleBufferDelegate(self, queue: DispatchQueue(label: "videoQueue"))
            if captureSession?.canAddOutput(videoOutput) == true {
                captureSession?.addOutput(videoOutput)
            }
            
            statusLabel.text = "Camera Ready"
        } catch {
            statusLabel.text = "Error setting up camera: \(error.localizedDescription)"
        }
    }
    
    private func startCaptureSession() {
        if captureSession?.isRunning == false {
            DispatchQueue.global(qos: .userInitiated).async { [weak self] in
                self?.captureSession?.startRunning()
            }
        }
    }
    
    private func stopCaptureSession() {
        if captureSession?.isRunning == true {
            captureSession?.stopRunning()
        }
    }
    
    // MARK: - Network Connection
    private func connectToServer() {
        let hostEndpoint = NWEndpoint.Host(hostName)
        let portEndpoint = NWEndpoint.Port(rawValue: port)!
        
        let parameters = NWParameters.tcp
        
        // Create the connection
        connection = NWConnection(host: hostEndpoint, port: portEndpoint, using: parameters)
        
        // Set the state update handler
        connection?.stateUpdateHandler = { [weak self] newState in
            switch newState {
            case .ready:
                self?.isConnected = true
                DispatchQueue.main.async {
                    self?.connectionStatusLabel.text = "Connected to \(self?.hostName ?? "server")"
                    self?.connectionStatusLabel.backgroundColor = UIColor.green.withAlphaComponent(0.6)
                }
            case .waiting(let error):
                self?.isConnected = false
                DispatchQueue.main.async {
                    self?.connectionStatusLabel.text = "Waiting: \(error)"
                    self?.connectionStatusLabel.backgroundColor = UIColor.orange.withAlphaComponent(0.6)
                }
            case .failed(let error):
                self?.isConnected = false
                DispatchQueue.main.async {
                    self?.connectionStatusLabel.text = "Connection failed: \(error)"
                    self?.connectionStatusLabel.backgroundColor = UIColor.red.withAlphaComponent(0.6)
                    
                    // Try to reconnect after a delay
                    DispatchQueue.main.asyncAfter(deadline: .now() + 5) {
                        self?.connectToServer()
                    }
                }
            case .cancelled:
                self?.isConnected = false
                DispatchQueue.main.async {
                    self?.connectionStatusLabel.text = "Disconnected"
                    self?.connectionStatusLabel.backgroundColor = UIColor.red.withAlphaComponent(0.6)
                }
            default:
                break
            }
        }
        
        // Start the connection
        connection?.start(queue: .global())
    }
    
    private func sendFrame(_ imageData: Data) {
        guard isConnected, let connection = connection else { return }
        
        // Create header with metadata (camera ID and timestamp)
        let timestamp = Date().timeIntervalSince1970
        let header = "CAMERA:\(cameraId),TIME:\(timestamp),SIZE:\(imageData.count)\n".data(using: .utf8)!
        
        // Send header
        connection.send(content: header, completion: .contentProcessed { error in
            if let error = error {
                print("Error sending header: \(error)")
            }
        })
        
        // Send image data
        connection.send(content: imageData, completion: .contentProcessed { error in
            if let error = error {
                print("Error sending image data: \(error)")
            }
        })
    }
    
    // MARK: - Settings
    @objc private func showSettings() {
        let alertController = UIAlertController(title: "Camera Settings", message: nil, preferredStyle: .alert)
        
        alertController.addTextField { textField in
            textField.placeholder = "Mac IP Address"
            textField.text = self.hostName
            textField.keyboardType = .decimalPad
        }
        
        alertController.addTextField { textField in
            textField.placeholder = "Port"
            textField.text = "\(self.port)"
            textField.keyboardType = .numberPad
        }
        
        alertController.addTextField { textField in
            textField.placeholder = "Camera ID (0 or 1)"
            textField.text = "\(self.cameraId)"
            textField.keyboardType = .numberPad
        }
        
        let saveAction = UIAlertAction(title: "Save", style: .default) { [weak self] _ in
            guard let self = self else { return }
            
            // Update host IP
            if let hostTextField = alertController.textFields?[0], let host = hostTextField.text, !host.isEmpty {
                self.hostName = host
                UserDefaults.standard.set(host, forKey: "hostName")
            }
            
            // Update port
            if let portTextField = alertController.textFields?[1], let portString = portTextField.text, let port = UInt16(portString) {
                self.port = port
                UserDefaults.standard.set(Int(port), forKey: "port")
            }
            
            // Update camera ID
            if let cameraIdTextField = alertController.textFields?[2], let cameraIdString = cameraIdTextField.text, let cameraId = Int(cameraIdString) {
                if cameraId == 0 || cameraId == 1 {
                    self.cameraId = cameraId
                    UserDefaults.standard.set(cameraId, forKey: "cameraId")
                    self.cameraIdLabel.text = "Camera ID: \(cameraId + 1)"
                }
            }
            
            // Reconnect with new settings
            self.connection?.cancel()
            self.connectToServer()
        }
        
        let cancelAction = UIAlertAction(title: "Cancel", style: .cancel, handler: nil)
        
        alertController.addAction(saveAction)
        alertController.addAction(cancelAction)
        
        present(alertController, animated: true, completion: nil)
    }
}

// MARK: - AVCaptureVideoDataOutputSampleBufferDelegate
extension SpeedCameraViewController: AVCaptureVideoDataOutputSampleBufferDelegate {
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        // Process every 5th frame to reduce CPU usage and network traffic
        frameCount += 1
        if frameCount % 5 != 0 {
            return
        }
        
        guard let imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        
        let ciImage = CIImage(cvPixelBuffer: imageBuffer)
        let context = CIContext()
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else { return }
        
        let uiImage = UIImage(cgImage: cgImage)
        
        // Compress to JPEG with lower quality to reduce size
        guard let imageData = uiImage.jpegData(compressionQuality: 0.5) else { return }
        
        // Send frame to server
        sendFrame(imageData)
        
        // Update status
        DispatchQueue.main.async { [weak self] in
            self?.statusLabel.text = "Streaming: \(imageData.count / 1024) KB"
        }
    }
}

// MARK: - AppDelegate
@UIApplicationMain
class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?
    
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        window = UIWindow(frame: UIScreen.main.bounds)
        window?.rootViewController = SpeedCameraViewController()
        window?.makeKeyAndVisible()
        return true
    }
} 