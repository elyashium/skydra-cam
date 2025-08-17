# SkyDra Detection Cam

A real-time, browser-based surveillance system that uses a phone's camera (for now) to stream video for live object detection, while displaying sensor data on a Matrix-style monitoring dashboard. This project is designed for drone applications, providing a lightweight yet powerful solution for real-time monitoring.


##  Project Structure

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

##  How to Run Locally

### 1. Prerequisites

- Python 3.8+
- An Android phone with the following apps installed:
  - **IP Webcam**: For streaming video. The 2019-2020 version is recommended. You can find it on sites like [APKMirror](https://www.apkmirror.com/apk/thyoni-tech/ip-webcam/ip-webcam-1-14-31-737-aarch64-release/).
  - **F-Droid**: The main Termux app is best installed from the [F-Droid store](https://f-droid.org) to ensure full functionality.
  - **Termux**: For accessing the phone's GPS via command line.
  - **Termux:API**: The plugin for Termux that enables hardware access.

### 2. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

### 3. Set up the Python Environment

Create a virtual environment and activate it:

```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python -m venv venv
source venv/bin/activate
```

Install all the required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Generate the ONNX Model

The object detection model needs to be converted to the ONNX format for the browser to use it. The `.pt` file will be downloaded automatically by the script.

```bash
python export_model.py
```

This will create the `yolov8n.onnx` file inside a `static/` directory (it will be created if it doesn't exist).

### 5. Configure the Phone and App

#### Step 5a: Configure and Start the Video Stream

- **Connect to Wi-Fi**: Make sure your phone and your computer are on the **same Wi-Fi network**.
- **Configure IP Webcam on your phone**:
  - Open the app.
  - Go to **Video Preferences** and enable `Enable GPS on start`.
  - Go to **Optional Permissions** and ensure `Allow GPS` is granted.
  - Enable `Data Logging`.
- **Start the Server**:
  - On the main screen of IP Webcam, tap "Start server".
  - The app will display an IPv4 address (e.g., `http://192.168.1.10:8080`).

#### Step 5b: Update the Camera URL in `app.py`

- Open the `app.py` file on your computer.
- Find the `camera_url` and `camera_base_url` variables.
- Replace the placeholder IP address with the one from your phone.

  ```python
  # Example:
  camera_url = "http://192.168.1.10:8080/video"
  camera_base_url = "http://192.168.1.10:8080"
  ```

### 6. Run the Application

Start the Flask web server on your computer:

```bash
python app.py
```

The terminal should show that the server is running on `http://0.0.0.0:5000/`.

### 7. Start the GPS Data Stream

- **Find your computer's IP address**:
  - On your computer, run `ipconfig` (Windows) or `ifconfig` (macOS/Linux) to find its local IP address (e.g., `192.168.1.15`).

- **On your phone, open the Termux app** and set it up:
  ```bash
  # Update packages and install tools
  pkg update && pkg upgrade
  pkg install termux-api

  # Grant storage permissions
  termux-setup-storage
  ```
- **Allow permissions**: A pop-up might ask for location permissions for Termux:API. Make sure to allow it. If not, go to your phone's Settings -> Apps -> Termux:API and manually grant Location permission.

- **Start the GPS sending script in Termux**: Run the following loop, **replacing `<your-laptop-ip>`** with the computer IP address you just found.
  ```bash
  while true
  do
    termux-location --request once | \
    curl -X POST -H "Content-Type: application/json" \
    -d @- http://<your-laptop-ip>:5000/update_location
    sleep 2
  done
  ```
  You should see your Flask app's terminal printing "Received GPS..." messages.

- **Troubleshooting the GPS Command**:
  - The `termux-location --request once` command is for medium-to-high accuracy and works well indoors. If it fails or returns no data, try one of the following alternatives:
  - **For outdoor use (high accuracy)**:
    ```bash
    termux-location -p gps
    ```
  - **For indoor use (low accuracy)**: This command uses the network/ISP location and can be off by a large margin, but it works without a direct sky view.
    ```bash
    termux-location -p network
    ```

### 8. View the Dashboard

Open your web browser on your computer and navigate to:

**`http://127.0.0.1:5000`**

You should now see the SkyDra Detection Cam dashboard with the live video feed, sensor data, and GPS coordinates.

---

### Notes on Accuracy

- **GPS signal is key**: Location accuracy depends heavily on a clear signal. Indoor readings can sometimes be inaccurate by a significant distance.
- For best results, operate the phone outdoors or near a window.


