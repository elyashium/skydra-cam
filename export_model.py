from ultralytics import YOLO

# Load the YOLOv8n model
model = YOLO('yolov8n.pt')

# Export the model to ONNX format
# opset=12 is a good choice for broad compatibility
model.export(format='onnx', opset=12)

print("Model exported to yolov8n.onnx")
