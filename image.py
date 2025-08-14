import cv2
import numpy as np
from ultralytics import YOLO
import torch

# Check if GPU is available
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")

# Load YOLOv8 model (Medium version for balance between speed and accuracy)
model = YOLO('yolov8n.pt').to(device)

# Connect to your mobile camera
url = "http://10.79.246.247:8080/video"  # Update with your IP Webcam URL
cap = cv2.VideoCapture(url)


frame_count = 0
frame_skip = 2  # Process every 2nd frame for performance

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    frame_count += 1
    if frame_count % frame_skip != 0:
        continue

    # Resize frame for faster processing
    frame_resized = cv2.resize(frame, (640, 480))

    # Run YOLOv8 inference on the frame
    results = model(frame_resized, device=device, half=True, stream=True)

    # Process results
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()      # Bounding box coordinates
        confidences = result.boxes.conf.cpu().numpy() # Confidence scores
        class_ids = result.boxes.cls.cpu().numpy().astype(int)  # Class IDs

        for box, confidence, class_id in zip(boxes, confidences, class_ids):
            if confidence < 0.4:  # Confidence threshold
                continue

            # Extract box coordinates
            x1, y1, x2, y2 = map(int, box)

            # Define label and color
            label = model.names[class_id]
            color = (0, 255, 0)

            # Draw bounding box and label
            cv2.rectangle(frame_resized, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame_resized, f"{label} {int(confidence * 100)}%", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Show the frame
    cv2.imshow("YOLOv8 Live Detection", frame_resized)

    # Exit if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
