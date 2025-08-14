from flask import Flask, Response, render_template
import cv2

app = Flask(__name__)

# The single source of truth for the camera URL
camera_url = "http://10.79.246.247:8080/video"
# The base URL is needed for fetching sensor data on the frontend
camera_base_url = "http://10.79.246.247:8080"


def generate_frames():
    """Video streaming generator function."""
    cap = cv2.VideoCapture(camera_url)
    if not cap.isOpened():
        print(f"Error: Could not open video stream at {camera_url}")
        return

    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()


@app.route('/')
def index():
    """Video streaming home page."""
    # Pass the camera's base URL to the template
    return render_template('index.html', camera_base_url=camera_base_url)


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
