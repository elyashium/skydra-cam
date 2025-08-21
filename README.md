# SkyDra Detection Cam

A real-time, browser-based surveillance system that uses a phone's camera (for now) to stream video for live **YOLOv8 object detection**, while displaying sensor + GPS data on a Matrix-style monitoring dashboard.

This project is designed for **drone applications**, providing a lightweight yet powerful solution for real-time monitoring with CUDA acceleration (GPU) if available.

---

## 📂 Project Structure

```
.
├── server.py               # Flask backend (serves video stream, YOLOv8 inference, and sensor API)
├── requirements.txt        # Python dependencies
├── cudatest.py             # Script to check CUDA/GPU availability
├── templates/
│   └── index.html          # The HTML/CSS/JS for the frontend dashboard
├── .gitignore              # Specifies files to ignore for Git
└── README.md               # This file
```

---

## ⚙️ How to Run Locally

### 1. Prerequisites

* **Python 3.8+**
* **PyTorch with CUDA support (if GPU available)**
* An **Android phone** with these apps:

  * **IP Webcam** → Streams video (recommended 2019-2020 APK from [APKMirror](https://www.apkmirror.com/apk/thyoni-tech/ip-webcam/))
  * **F-Droid** → For installing latest **Termux**
  * **Termux** → To send GPS/location data
  * **Termux\:API** → To let Termux access sensors

---

### 2. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

---

### 3. Set up Python Environment

```bash
# Create venv
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### 4. Install PyTorch with CUDA (GPU Acceleration)

If you have an NVIDIA GPU, uninstall old torch and install the CUDA-enabled version:

```bash
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

Check CUDA availability:

```bash
python cudatest.py
```

You should see:

```
True
NVIDIA GPU NAME
```

If it prints `False` → torch is using CPU only.

---

### 5. Configure Phone Camera (IP Webcam)

1. Connect **phone + computer to the same Wi-Fi**.
2. Open **IP Webcam** → Start Server.
3. Note the IP address (e.g., `http://192.168.1.10:8080`).
4. Edit `server.py` → set your phone’s IP:

   ```python
   CAMERA_URL = "http://192.168.1.10:8080/video"
   ```

---

### 6. Run the Application

Start Flask server:

```bash
python server.py
```

You’ll see:

```
 * Running on http://0.0.0.0:5000/
```

Open browser → **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

✅ You should see the dashboard with:

* Live YOLOv8 video detections
* GPS coordinates
* Sensor data

---

### 7. Send GPS Data from Termux

On your phone (Termux):

```bash
pkg update && pkg upgrade
pkg install termux-api
termux-setup-storage
```

Grant location permission for **Termux\:API**.

Then run loop (replace `<your-laptop-ip>`):

```bash
while true
do
  termux-location -p gps | \
  curl -X POST -H "Content-Type: application/json" \
  -d @- http://<your-laptop-ip>:5000/update_location
  sleep 2
done
```

---

## 📌 Notes

* **CUDA speeds up YOLOv8** → CPU is slower but still works.
* **GPS accuracy depends on environment** (indoor vs outdoor).
* Works best outdoors with a clear sky view.
