from ultralytics import YOLO

# Load your trained YOLO model
model = YOLO("../runs/detect/bangladesh_lp_model/weights/best.pt")

def detect_plate(image_path):
    """
    Detect license plates in an image using YOLO.
    Returns bounding boxes and confidences.
    """
    results = model(image_path)
    if len(results) == 0:
        return [], []

    boxes = results[0].boxes.xyxy  # [[x1, y1, x2, y2], ...]
    confidences = results[0].boxes.conf  # [conf1, conf2, ...]

    return boxes, confidences
