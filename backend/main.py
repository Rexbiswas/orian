from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import uvicorn
import io
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load OpenCV Haar Cascades
# These are built-in and highly compatible with Python 3.14
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

@app.get("/")
async def root():
    return {"status": "OrionAI OpenCV Core Online", "engine": "HaarCascades_3.14"}

@app.post("/api/sense/process")
async def process_senses(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image data")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        is_looking = False
        dominant_emotion = "neutral"
        face_center = {"x": 0.5, "y": 0.5}
        spatial_data = {"azimuth": 0, "distance": 1}

        if len(faces) > 0:
            # We take the first face detected
            (x, y, w, h) = faces[0]
            face_center = {
                "x": float((x + w/2) / img.shape[1]),
                "y": float((y + h/2) / img.shape[0])
            }
            
            # Gaze/Engagement: If face is centered
            if 0.3 < face_center["x"] < 0.7:
                is_looking = True

            # Crop face for emotion detection
            roi_gray = gray[y:y+h, x:x+w]
            
            # Simple Emotion Logic based on Smile/Eye detection
            smiles = smile_cascade.detectMultiScale(roi_gray, 1.8, 20)
            eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 10)
            
            if len(smiles) > 0:
                dominant_emotion = "happy"
            elif len(eyes) < 2:
                dominant_emotion = "sad" # Approximation if eyes are squinted or closed
            else:
                dominant_emotion = "neutral"

            # Spatial Audio
            spatial_data = {
                "azimuth": (face_center["x"] - 0.5) * 100,
                "distance": 1.0 - (w / img.shape[1]) # Size of face as distance proxy
            }

        return {
            "success": True,
            "senses": {
                "emotion": {
                    "dominant": dominant_emotion,
                    "scores": {"neutral": 1.0}
                },
                "engagement": {
                    "is_looking": is_looking,
                    "face_center": face_center
                },
                "spatial": spatial_data
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
