from ultralytics import YOLO

# Load trained model
model = YOLO("runs/train/bangladesh_lp_model/weights/best.pt")

def detect_plate(image_path):
    results = model(image_path)
    boxes = results[0].boxes.xyxy
    confidences = results[0].boxes.conf
    return boxes, confidences
