from flask import Flask, Response, render_template, jsonify
import cv2
import requests
import json

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


@app.route('/api/sensors')
def get_sensors():
    """Proxy route to fetch sensor data from the IP camera and return it as JSON."""
    sensors_url = f"{camera_base_url}/sensors.json"
    
    try:
        # Fetch sensor data from the camera
        response = requests.get(sensors_url, timeout=5)
        if response.status_code == 200:
            sensor_data = response.json()
            
            # Process and structure the data for easier frontend consumption
            processed_data = {
                'status': 'success',
                'timestamp': sensor_data.get('timestamp', 'unknown'),
                'gps': {
                    'available': False,
                    'latitude': None,
                    'longitude': None,
                    'status': 'OFFLINE'
                },
                'accelerometer': {
                    'available': False,
                    'x': None,
                    'y': None,
                    'z': None
                },
                'gyroscope': {
                    'available': False,
                    'x': None,
                    'y': None,
                    'z': None
                },
                'magnetometer': {
                    'available': False,
                    'x': None,
                    'y': None,
                    'z': None
                },
                'environment': {
                    'light': None,
                    'proximity': None,
                    'battery': None
                }
            }
            
            # Parse GPS data
            if 'gps' in sensor_data and sensor_data['gps'].get('data'):
                try:
                    gps_values = sensor_data['gps']['data'][0][0]['values']
                    processed_data['gps'] = {
                        'available': True,
                        'latitude': round(gps_values[0], 6),
                        'longitude': round(gps_values[1], 6),
                        'status': 'ONLINE'
                    }
                except (IndexError, KeyError):
                    pass
            
            # Parse Accelerometer data
            if 'accel' in sensor_data and sensor_data['accel'].get('data'):
                try:
                    accel_values = sensor_data['accel']['data'][0][0]['values']
                    processed_data['accelerometer'] = {
                        'available': True,
                        'x': round(accel_values[0], 2),
                        'y': round(accel_values[1], 2),
                        'z': round(accel_values[2], 2)
                    }
                except (IndexError, KeyError):
                    pass
            
            # Parse Gyroscope data
            if 'gyro' in sensor_data and sensor_data['gyro'].get('data'):
                try:
                    gyro_values = sensor_data['gyro']['data'][0][0]['values']
                    processed_data['gyroscope'] = {
                        'available': True,
                        'x': round(gyro_values[0], 3),
                        'y': round(gyro_values[1], 3),
                        'z': round(gyro_values[2], 3)
                    }
                except (IndexError, KeyError):
                    pass
            
            # Parse Magnetometer data
            if 'mag' in sensor_data and sensor_data['mag'].get('data'):
                try:
                    mag_values = sensor_data['mag']['data'][0][0]['values']
                    processed_data['magnetometer'] = {
                        'available': True,
                        'x': round(mag_values[0], 1),
                        'y': round(mag_values[1], 1),
                        'z': round(mag_values[2], 1)
                    }
                except (IndexError, KeyError):
                    pass
            
            # Parse Light sensor
            if 'light' in sensor_data and sensor_data['light'].get('data'):
                try:
                    light_value = sensor_data['light']['data'][0][0]['values'][0]
                    processed_data['environment']['light'] = round(light_value, 1)
                except (IndexError, KeyError):
                    pass
            
            # Parse Proximity sensor
            if 'prox' in sensor_data and sensor_data['prox'].get('data'):
                try:
                    prox_value = sensor_data['prox']['data'][0][0]['values'][0]
                    processed_data['environment']['proximity'] = round(prox_value, 1)
                except (IndexError, KeyError):
                    pass
            
            # Parse Battery temperature
            if 'batTemp' in sensor_data and sensor_data['batTemp'].get('data'):
                try:
                    battery_value = sensor_data['batTemp']['data'][0][0]['values'][0]
                    processed_data['environment']['battery'] = round(battery_value, 1)
                except (IndexError, KeyError):
                    pass
            
            return jsonify(processed_data)
        
        else:
            return jsonify({
                'status': 'error',
                'message': f'Camera returned status code {response.status_code}'
            }), response.status_code
            
    except requests.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to connect to camera: {str(e)}'
        }), 500
    except json.JSONDecodeError as e:
        return jsonify({
            'status': 'error',
            'message': f'Invalid JSON response from camera: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
