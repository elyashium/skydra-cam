from flask import Flask, Response, render_template, jsonify, request
import cv2
import requests
import json

app = Flask(__name__)

# Global variable to store the latest GPS data
gps_data = {"lat": None, "lon": None}

# The single source of truth for the camera URL
camera_url = "http://10.79.246.247:8080/video"
# The base URL is needed for fetching sensor data on the frontend
camera_base_url = "http://10.79.246.247:8080"


@app.route("/update_location", methods=["POST"])
def update_location():
    """Endpoint to receive GPS data from Termux."""
    global gps_data
    data = request.json
    gps_data["lat"] = data.get("latitude")
    gps_data["lon"] = data.get("longitude")
    print(f"Received GPS: Lat={gps_data['lat']}, Lon={gps_data['lon']}") # For debugging
    return jsonify({"status": "ok"})


@app.route('/video_feed')
def video_feed():
    """Video streaming route. This route now directly proxies the camera feed."""
    try:
        # Use stream=True to avoid loading the whole video into memory at once
        req = requests.get(camera_url, stream=True, timeout=10)
        
        # Check if the request was successful
        req.raise_for_status()
        
        # Return a streaming response, passing through the original content-type header
        # which includes the all-important frame boundary definition.
        return Response(req.iter_content(chunk_size=10240),
                        content_type=req.headers['content-type'])

    except requests.exceptions.RequestException as e:
        print(f"Error proxying video stream: {e}")
        # Return a 502 Bad Gateway error to the client
        return "Could not connect to video stream.", 502


@app.route('/api/gps_data')
def gps_data_api():
    """API endpoint to provide the latest GPS data."""
    return jsonify(gps_data)


@app.route('/')
def index():
    """Video streaming home page."""
    # Pass the camera's base URL to the template
    return render_template('index.html', camera_base_url=camera_base_url)


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
            
            # Parse GPS data (check for gps key - might not be available)
            if 'gps' in sensor_data and sensor_data['gps'].get('data'):
                try:
                    gps_values = sensor_data['gps']['data'][0][1]  # [timestamp, [values]]
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
                    accel_values = sensor_data['accel']['data'][0][1]  # [timestamp, [x, y, z]]
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
                    gyro_values = sensor_data['gyro']['data'][0][1]  # [timestamp, [x, y, z]]
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
                    mag_values = sensor_data['mag']['data'][0][1]  # [timestamp, [x, y, z]]
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
                    light_value = sensor_data['light']['data'][0][1][0]  # [timestamp, [value]]
                    processed_data['environment']['light'] = round(light_value, 1)
                except (IndexError, KeyError):
                    pass
            
            # Parse Proximity sensor
            if 'proximity' in sensor_data and sensor_data['proximity'].get('data'):
                try:
                    prox_value = sensor_data['proximity']['data'][0][1][0]  # [timestamp, [value]]
                    processed_data['environment']['proximity'] = round(prox_value, 1)
                except (IndexError, KeyError):
                    pass
            
            # Parse Battery level (percentage)
            if 'battery_level' in sensor_data and sensor_data['battery_level'].get('data'):
                try:
                    battery_value = sensor_data['battery_level']['data'][0][1][0]  # [timestamp, [percentage]]
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
