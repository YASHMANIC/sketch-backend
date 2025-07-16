from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse, JSONResponse
import cv2
import numpy as np
import io
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

app = FastAPI()
# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sketch-frontend-1yxjixml2-yashmanics-projects.vercel.app/"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/process-image")
async def process_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Failed to decode image")

        print("Image Received:", file.filename)

        # Convert to grayscale and apply sketch effect
        grey_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        invert = cv2.bitwise_not(grey_img)
        blur = cv2.GaussianBlur(invert, (21, 21), 0)
        inverted_blur = cv2.bitwise_not(blur)
        sketch = cv2.divide(grey_img, inverted_blur, scale=220.0)

        # Encode image as PNG in memory
        _, img_encoded = cv2.imencode('.png', sketch)
        # Ensure directories exist
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("outputs", exist_ok=True)

        # Save original image
        safe_filename = file.filename or "uploaded_image"
        upload_path = os.path.join("uploads", safe_filename)
        with open(upload_path, "wb") as f:
            f.write(contents)

        # Save sketch image
        sketch_filename = os.path.splitext(safe_filename)[0] + "_sketch.png"
        output_path = os.path.join("outputs", sketch_filename)
        with open(output_path, "wb") as f:
            f.write(img_encoded.tobytes())
            
        return StreamingResponse(io.BytesIO(img_encoded.tobytes()), media_type="image/png")
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
