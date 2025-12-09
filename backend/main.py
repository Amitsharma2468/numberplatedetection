# backend/main.py
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from plate_detector import detect_plate
import shutil
import os
import cv2
import easyocr

app = FastAPI()

# Allow all origins for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# EasyOCR reader for Bengali
reader = easyocr.Reader(['bn'])

# Minimal Bangla to Avro mapping (extend as needed)
BN_TO_AVRO = {
    'অ': 'a', 'আ': 'aa', 'ই': 'i', 'ঈ': 'ii', 'উ': 'u', 'ঊ': 'uu',
    'এ': 'e', 'ঐ': 'oi', 'ও': 'o', 'ঔ': 'ou',
    'ক': 'k', 'খ': 'kh', 'গ': 'g', 'ঘ': 'gh', 'ঙ': 'ng',
    'চ': 'c', 'ছ': 'ch', 'জ': 'j', 'ঝ': 'jh', 'ঞ': 'n',
    'ট': 'T', 'ঠ': 'Th', 'ড': 'D', 'ঢ': 'Dh', 'ণ': 'N',
    'ত': 't', 'থ': 'th', 'দ': 'd', 'ধ': 'dh', 'ন': 'n',
    'প': 'p', 'ফ': 'ph', 'ব': 'b', 'ভ': 'bh', 'ম': 'm',
    'য': 'y', 'র': 'r', 'ল': 'l', 'শ': 'sh', 'ষ': 'Sh',
    'স': 's', 'হ': 'h', 'ং': 'ng', 'ঃ': ':', 'ঁ': '~',
    'ড়': 'r', 'ঢ়': 'rh', 'য়': 'y',
    '।': '.', '০': '0', '১': '1', '২': '2', '৩': '3',
    '৪': '4', '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
}

def bangla_to_avro(text: str) -> str:
    """Convert Bangla text to Avro phonetic typing."""
    result = ""
    for c in text:
        result += BN_TO_AVRO.get(c, c)  # Keep unknown chars as-is
    return result

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/detect-plate")
async def detect_plate_api(file: UploadFile = File(...)):
    temp_path = "temp_input.jpg"
    output_path = "temp_output.jpg"

    # Save uploaded file
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        # Detect plates
        boxes, conf = detect_plate(temp_path)

        # Load image
        img = cv2.imread(temp_path)
        detected_texts = []
        detected_avro = []

        for box in boxes.tolist():
            x1, y1, x2, y2 = map(int, box)
            pad = 3
            x1 = max(0, x1 - pad)
            y1 = max(0, y1 - pad)
            x2 = min(img.shape[1], x2 + pad)
            y2 = min(img.shape[0], y2 + pad)

            # Crop plate region
            plate_img = img[y1:y2, x1:x2]
            plate_gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)

            # OCR with EasyOCR
            result = reader.readtext(plate_gray)
            plate_text = "".join([text[1] for text in result])
            detected_texts.append(plate_text)

            # Convert to Avro typing
            detected_avro.append(bangla_to_avro(plate_text))

            # Draw bounding box
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Save annotated image
        cv2.imwrite(output_path, img)

        return JSONResponse({
            "plates": detected_texts,            # Bangla text       # Avro typing
            "image_path": output_path            # Annotated image
        })

    finally:
        # Clean temp input
        if os.path.exists(temp_path):
            os.remove(temp_path)
