from ultralytics import YOLO

# Load YOLOv8 model (nano, small, medium, large, or custom)
model = YOLO("yolov8n.pt")  # yolov8n.pt is CPU-friendly

# Train model
model.train(
    data="dataset.yaml",
    epochs=50,
    imgsz=320,
    batch=8,
    name="bangladesh_lp_model",
    device="cpu"  # change to "0" if you have GPU
)
