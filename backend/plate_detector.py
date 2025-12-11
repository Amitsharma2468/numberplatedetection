from ultralytics import YOLO
import cv2
import easyocr
import numpy as np
from collections import defaultdict
import os

# ----------------- LOAD MODELS -----------------
# YOLOv8 model trained on Bangladeshi license plates
model = YOLO("../runs/detect/bangladesh_lp_model/weights/best.pt")

# EasyOCR reader with Bengali + English
reader = easyocr.Reader(['bn', 'en'], gpu=False)

# ----------------- HELPER FUNCTIONS -----------------
def iou(boxA, boxB):
    """Compute Intersection over Union for two boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    inter_area = max(0, xB - xA) * max(0, yB - yA)
    if inter_area == 0:
        return 0
    boxA_area = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxB_area = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    return inter_area / float(boxA_area + boxB_area - inter_area)

def clean_text(text: str) -> str:
    """Keep only Bangla digits and English letters/numbers."""
    if not isinstance(text, str):
        return "" 
    allowed_chars = "০১২৩৪৫৬৭৮৯ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    return "".join(ch for ch in text if ch in allowed_chars)

def best_plate(plates, confidences=None):
    """Select the best plate from multiple detections using length and confidence, with min length filter."""
    if not plates:
        return None
    
    valid_plates = []
    valid_confidences = []
    MIN_PLATE_LENGTH = 6 # Require at least 6 cleaned characters for a valid read

    for i, p in enumerate(plates):
        if len(p) >= MIN_PLATE_LENGTH:
            valid_plates.append(p)
            if confidences and len(confidences) > i:
                 valid_confidences.append(confidences[i])

    if not valid_plates:
        # Fallback to the longest plate read, even if it's short, if no plate meets the minimum length
        return sorted(plates, key=lambda x: len(x), reverse=True)[0]
    
    if valid_confidences and len(valid_plates) == len(valid_confidences):
        # Score = length * confidence
        scores = [len(p) * c for p, c in zip(valid_plates, valid_confidences)]
        return valid_plates[np.argmax(scores)]
    else:
        # Fallback: select the longest text from the valid plates
        return sorted(valid_plates, key=lambda x: len(x), reverse=True)[0]

# ----------------- PLATE DETECTION -----------------
def detect_plate_video(input_video_path: str, output_video_path: str):
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print("Error opening video")
        return False, {}

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    try:
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (w, h))
    except Exception as e:
        print(f"Error creating video writer: {e}")
        cap.release()
        return False, {}


    next_car_id = 1
    tracked_cars = {} 
    car_plate_list = defaultdict(list)
    car_plate_conf = defaultdict(list) 

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # YOLO detection
        try:
            results = model(frame, conf=0.5, verbose=False) 
        except Exception as e:
            print("YOLO detection error:", e)
            continue

        for r in results:
            if r.boxes and r.boxes.xyxy.shape[0] > 0:
                for box in r.boxes.xyxy:
                    x1, y1, x2, y2 = map(int, box.tolist())
                    detected_box = [x1, y1, x2, y2]

                    # --------- ASSIGN CAR ID VIA IOU (STRICTEST THRESHOLD) ---------
                    assigned_id = None
                    for car_id, prev_box in tracked_cars.items():
                        # Increased to 0.6 for maximum stable tracking
                        if iou(prev_box, detected_box) > 0.6: 
                            assigned_id = car_id
                            tracked_cars[car_id] = detected_box 
                            break

                    if assigned_id is None:
                        assigned_id = next_car_id
                        tracked_cars[next_car_id] = detected_box
                        next_car_id += 1

                    # --------- ADVANCED PREPROCESS CROP FOR OCR ---------
                    y1_c = max(0, y1)
                    y2_c = min(h, y2)
                    x1_c = max(0, x1)
                    x2_c = min(w, x2)
                    
                    crop = frame[y1_c:y2_c, x1_c:x2_c]
                    
                    if crop.size == 0 or crop.shape[0] < 5 or crop.shape[1] < 5:
                        continue

                    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                    
                    # NEW STRATEGY: CLAHE + Adaptive Thresholding
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    clahe_applied = clahe.apply(gray)
                    
                    # Adaptive Thresholding for better character separation
                    thresh = cv2.adaptiveThreshold(
                        clahe_applied, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 4
                    )

                    # Safe resizing and blurring
                    max_dim = 200
                    scale = min(max_dim / max(thresh.shape), 2)
                    thresh = cv2.resize(thresh, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
                    thresh = cv2.medianBlur(thresh, 3)

                    # --------- OCR DETECTION (with enhanced selection) ---------
                    plate_text = ""
                    best_conf = 0.0
                    try:
                        ocr_result = reader.readtext(thresh, detail=1)
                    except Exception as e:
                        print("OCR error:", e)
                        ocr_result = []

                    if ocr_result:
                        best_score = -1
                        current_plate_text = ""
                        current_best_conf = 0.0
                        MIN_CLEAN_LENGTH = 4 

                        for _, text, conf in ocr_result:
                            clean_t = clean_text(text)
                            current_score = len(clean_t) * conf
                            
                            if current_score > best_score and len(clean_t) >= MIN_CLEAN_LENGTH:
                                best_score = current_score
                                current_plate_text = clean_t
                                current_best_conf = conf

                        plate_text = current_plate_text
                        best_conf = current_best_conf
                        
                        if plate_text:
                            car_plate_list[assigned_id].append(plate_text)
                            car_plate_conf[assigned_id].append(best_conf)
                            
                    # --------- DRAW ON FRAME ---------
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    text_to_display = f"Car {assigned_id}: {plate_text or '...'}"
                    cv2.putText(
                        frame, text_to_display, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
                    )

        out.write(frame)

    cap.release()
    out.release()

    # --------- FINAL BEST PLATE PER CAR (Uses MIN_PLATE_LENGTH filter) ---------
    final_output = {}
    for car_id in car_plate_list:
        final_output[car_id] = best_plate(
            car_plate_list[car_id], car_plate_conf.get(car_id)
        )

    final_output = {cid: plate for cid, plate in final_output.items() if plate}

    return True, final_output