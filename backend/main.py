import tempfile

import shutil

import os

import uuid

from fastapi import FastAPI, UploadFile, File

from fastapi.responses import JSONResponse, FileResponse

from fastapi.middleware.cors import CORSMiddleware

from starlette.background import BackgroundTask

from starlette.concurrency import run_in_threadpool

from plate_detector import detect_plate_video  # Your YOLO + OCR function



app = FastAPI()

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_methods=["*"],

    allow_headers=["*"]

)



# Store processed videos and car info in memory

processed_videos = {}   # session_id -> video_path

processed_cars = {}     # session_id -> [{"car_id":1,"plate":"AB123"}]





@app.post("/api/detect-plate-video")

async def detect_plate_video_api(file: UploadFile = File(...)):

    session_id = str(uuid.uuid4())



    # Save uploaded video temporarily

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input:

        input_path = temp_input.name

        shutil.copyfileobj(file.file, temp_input)

    await file.close()



    output_path = f"output_with_boxes_{session_id}.mp4"



    try:

        # Run detection in thread pool

        success, car_results = await run_in_threadpool(detect_plate_video, input_path, output_path)



        if not success or not os.path.exists(output_path):

            return JSONResponse(status_code=500, content={"error": "Video processing failed"})



        # Convert to list of dicts

        cars_output = [{"car_id": int(cid), "plate": plate} for cid, plate in car_results.items()]

        processed_videos[session_id] = output_path

        processed_cars[session_id] = cars_output



        return JSONResponse(

            status_code=200,

            content={

                "message": "Video processed successfully",

                "count": len(cars_output),

                "cars": cars_output,

                "session_id": session_id,

                "download_url": f"/download-video/{session_id}"

            }

        )

    finally:

        # Remove input video after processing

        try:

            os.remove(input_path)

        except Exception as e:

            print(f"Failed to remove input file: {e}")





@app.get("/download-video/{session_id}")

async def download_video(session_id: str):

    video_path = processed_videos.get(session_id)

    if not video_path or not os.path.exists(video_path):

        return JSONResponse(status_code=404, content={"error": "Processed video not found"})



    # Optional cleanup after download

    def cleanup(path, sid):

        try:

            os.remove(path)

        except Exception as e:

            print(f"Failed to delete output video: {e}")

        processed_videos.pop(sid, None)

        processed_cars.pop(sid, None)



    return FileResponse(

        path=video_path,

        media_type="video/mp4",

        filename="detected_plate_video.mp4",

        background=BackgroundTask(cleanup, video_path, session_id)

    )





# ----------------- NEW: Get video info -----------------

@app.get("/api/get-video-info/{session_id}")

async def get_video_info(session_id: str):

    cars_info = processed_cars.get(session_id)

    if cars_info is None:

        return JSONResponse(status_code=404, content={"error": "Session not found or expired"})



    return JSONResponse(

        status_code=200,

        content={

            "session_id": session_id,

            "cars": cars_info

        }

    )