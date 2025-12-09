from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from plate_detector import detect_plate
import shutil

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/detect-plate")
async def detect_plate_api(file: UploadFile = File(...)):
    with open("temp.jpg", "wb") as f:
        shutil.copyfileobj(file.file, f)
    boxes, conf = detect_plate("temp.jpg")
    return {"boxes": boxes.tolist(), "confidences": conf.tolist()}
