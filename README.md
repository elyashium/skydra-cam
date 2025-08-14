# SkyDra Detection Cam

A real-time, browser-based surveillance system that uses a phone's camera to stream video for live object detection, while displaying sensor data on a Matrix-style monitoring dashboard. This project is designed for drone applications, providing a lightweight yet powerful solution for real-time monitoring.

![SkyDra Detection Cam Screenshot](https://i.imgur.com/YOUR_SCREENSHOT_ID.png)  <!-- Replace with a real screenshot URL -->

---

## ✨ Features

- **Real-time Video Streaming**: Streams video from a phone's camera to a web browser with low latency.
- **Live Object Detection**: Uses the YOLOv8n model to perform real-time human detection directly in the browser via `ONNX.js`.
- **Matrix-style Dashboard**: A sleek, technical, single-page interface with a pitch-black and neon-green theme.
- **Dynamic Sensor Monitoring**: Displays live data from the phone's sensors, including:
  - Accelerometer (X, Y, Z)
  - Gyroscope (X, Y, Z)
  - Magnetometer (X, Y, Z)
  - Light Sensor
  - Proximity Sensor
  - Battery Level
- **Backend Proxy**: A Flask backend that securely fetches and processes sensor data for the frontend.
- **Optimized for CPU**: Uses the lightweight YOLOv8n model, suitable for running on standard CPUs.

---

## 🛠️ Project Structure

```
.
├── app.py                  # Flask backend (serves the web app and sensor data API)
├── export_model.py         # Script to convert the PyTorch model to ONNX format
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html          # The HTML/CSS/JS for the frontend dashboard
├── static/
│   └── yolov8n.onnx        # The ONNX model file (generated)
├── .gitignore              # Specifies files to ignore for Git
└── README.md               # This file
```

---

## 🚀 How to Run Locally

### 1. Prerequisites

- Python 3.8+
- An Android phone with the [IP Webcam](https://play.google.com/store/apps/details?id=com.pas.webcam) app installed.

### 2. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

### 3. Set up the Environment

Create a virtual environment and activate it:

```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

Install all the required Python packages:

```bash
pip install -r requirements.txt
```

### 5. Generate the ONNX Model

The object detection model needs to be converted to the ONNX format for the browser to use it. The `.pt` file will be downloaded automatically by the script.

```bash
python export_model.py
```

This will create the `yolov8n.onnx` file inside a `static/` directory (it will be created if it doesn't exist).

### 6. Configure the Camera

- **Start IP Webcam on your phone**:
  - Open the app and configure your video preferences.
  - Make sure your phone and your computer are on the **same Wi-Fi network**.
  - Tap "Start server". The app will display an IPv4 address (e.g., `http://192.168.1.10:8080`).

- **Update the Camera URL in `app.py`**:
  - Open the `app.py` file.
  - Find the `camera_url` and `camera_base_url` variables.
  - Replace the placeholder IP address with the one from your phone.

  ```python
  # Example:
  camera_url = "http://192.168.1.10:8080/video"
  camera_base_url = "http://192.168.1.10:8080"
  ```

### 7. Run the Application

Start the Flask web server:

```bash
python app.py
```

Open your web browser and navigate to:

**`http://127.0.0.1:5000`**

You should now see the SkyDra Detection Cam dashboard with the live video feed and sensor data.

---


