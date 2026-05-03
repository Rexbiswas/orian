from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import uvicorn
import io
import os
import speech_recognition as sr
from brain import brain
from emotion import personality
from neural_system import neural_sys
from llm_core import llm
from pydantic import BaseModel
from typing import Optional, List
import random

# --- NEURAL EMOTION LEXICON (400+ Nuanced States) ---
EMOTION_LEXICON = {
    "happy": ["JUBILANT", "ELATED", "CHEERFUL", "ECSTATIC", "RADIANT", "CONTENT", "BEAMING", "JOYFUL", "EXUBERANT", "VIBRANT"],
    "calm": ["SERENE", "CONTEMPLATIVE", "STOIC", "OBSERVANT", "TRANQUIL", "PACIFIC", "ZENITH", "HARMONIOUS", "STEADY", "COMPOSED"],
    "focused": ["ANALYTICAL", "DETERMINED", "INTRIGUED", "CALCULATING", "ABSORBED", "ATTENTIVE", "RESOLUTE", "COGNITIVE", "FOCUSED", "DECISIVE"],
    "surprised": ["ASTONISHED", "AMAZED", "STARTLED", "AWESTRUCK", "BEWILDERED", "ELECTRIFIED", "STUNNED", "CAPTIVATED", "SHOCKED", "DAZZLED"],
    "sad": ["MELANCHOLY", "SOMBER", "PENSIVE", "DISCONSOLATE", "FORLORN", "WISTFUL", "GLOOMY", "DEJECTED", "RESERVED", "QUIET"],
    "analyzing": ["SCANNING", "PROCESSING", "DECODING", "EVALUATING", "MAPPING", "INTERPRETING", "CALIBRATING", "SENSING", "PROBING", "LEARNING"]
}

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
def load_cascade(name):
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + name)
    if cascade.empty():
        print(f"[SenseEngine] WARNING: Failed to load {name}")
    return cascade

face_cascade = load_cascade('haarcascade_frontalface_default.xml')
eye_cascade = load_cascade('haarcascade_eye.xml')
smile_cascade = load_cascade('haarcascade_smile.xml')



@app.post("/api/sense/process")
async def process_senses(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Debug Log
        # print(f"[SenseEngine] Processing frame: {len(contents)} bytes")
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image data")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Balanced Range Scanning (1.2 scaleFactor for performance, 5 neighbors for stability)
        faces = face_cascade.detectMultiScale(gray, 1.1, 3, minSize=(30, 30))
        print(f"[SenseEngine] Scanned Frame: {len(faces)} face(s) detected.")
        
        is_looking = False
        dominant_emotion = "neutral"
        face_center = {"x": 0.5, "y": 0.5}
        spatial_data = {"azimuth": 0, "distance": 1}

        if len(faces) > 0:
            # Sort by area to get the largest (closest) face
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            (x, y, w, h) = faces[0]
            face_center = {
                "x": float((x + w/2) / img.shape[1]),
                "y": float((y + h/2) / img.shape[0])
            }
            
            # Engagement Range: Set to 100% of the frame (0.0 to 1.0)
            if 0.0 <= face_center["x"] <= 1.0:
                is_looking = True

            # Crop face for emotion detection
            roi_gray = gray[y:y+h, x:x+w]
            
            # Facial Link Logic (Independent from Eye Contact)
            # Higher sensitivity (minNeighbors reduced) for increased distance range
            smiles = smile_cascade.detectMultiScale(roi_gray, 1.1, 10)
            eyes_detected = eye_cascade.detectMultiScale(roi_gray, 1.05, 3)
            
            base_state = "analyzing"
            if len(smiles) > 0:
                base_state = "happy"
            elif len(eyes_detected) == 0:
                base_state = "focused" 
            elif len(eyes_detected) > 2: 
                base_state = "surprised"
            elif len(eyes_detected) > 0 and len(smiles) == 0:
                # If eyes are visible but no smile, it's either calm or sad
                base_state = "calm" if h > w * 0.8 else "sad" # Heuristic for pensive/sad
            else:
                base_state = "calm"

            # 400+ Emotion Simulation: Map base state to 40+ nuanced words
            # Combining this with intensity [%] creates 400+ unique status messages
            nuance = random.choice(EMOTION_LEXICON.get(base_state, ["STABLE"]))
            intensity = int(np.random.randint(10, 99))
            final_emotion = f"{nuance} [{intensity}%]"

            # Spatial Audio
            spatial_data = {
                "azimuth": (face_center["x"] - 0.5) * 100,
                "distance": 1.0 - (w / img.shape[1]) # Size of face as distance proxy
            }

        return {
            "success": True,
            "senses": {
                "emotion": {
                    "dominant": final_emotion,
                    "base": base_state,
                    "scores": {"intensity": intensity}
                },
                "engagement": {
                    "is_looking": is_looking,
                    "status": "ESTABLISHED" if is_looking else "SCANNING",
                    "face_center": face_center
                },
                "spatial": spatial_data
            }
        }

    except Exception as e:
        return {"success": False, "message": str(e)}

# --- NEURAL COMMAND EXECUTOR ---

def execute_neural_command(text: str):
    """Processes commands and learns from them in real-time."""
    text = text.lower().strip()
    
    # 1. Corrective Feedback (Error Reflection)
    if "mistake" in text and "should" in text:
        try:
            parts = text.split("when i say")
            command_part = parts[1].split(", you should")[0].strip()
            correction_part = text.split("you should")[1].strip()
            brain.report_mistake(f"command_{command_part}", "User Correction", correction_part)
            return f"Neural correction acknowledged. I will now map '{command_part}' to '{correction_part}'. Evolution increased."
        except:
            return "Correction format unrecognized. Please use: 'When I say [X], you should [Y]'"

    # 2. Skill Integration (Neural Expansion)
    if "download" in text and "skill" in text:
        category = "coding"
        if "hacking" in text: category = "hacking_sim"
        elif "editing" in text: category = "editing"
        result = neural_sys.download_skill(category)
        return result

    # 3. Habitual Interaction (Pattern Learning)
    if "open" in text or "start" in text or "launch" in text:
        action = text.replace("orian", "").strip()
        neural_sys.record_action(action)
        app_name = action.replace("open ", "").replace("launch ", "").replace("start ", "").strip()
        success = brain.launch_app(app_name)
        if success:
            return f"Initializing {app_name}. Pattern recorded in neural core."
        else:
            return f"Action {app_name} queued, but executable not found. Teaching required?"

    # 4. Pattern Prediction
    if "predict" in text:
        prediction = neural_sys.predict_next_action()
        if prediction["prediction"]:
            return prediction["suggestion"]
        return "Not enough data for a confident prediction yet, master."

    return None

@app.post("/api/sense/voice")
async def process_voice(file: UploadFile = File(...)):
    """Processes audio with multi-tone sensitivity and executes neural commands."""
    try:
        contents = await file.read()
        
        # 1. Audio Normalization
        try:
            header_offset = 44
            audio_np = np.frombuffer(contents[header_offset:], dtype=np.int16).copy()
            if len(audio_np) > 0:
                peak = np.max(np.abs(audio_np))
                if peak > 0 and peak < 16384:
                    multiplier = 28000 / peak
                    audio_np = (audio_np * multiplier).clip(-32768, 32767).astype(np.int16)
                normalized_contents = contents[:header_offset] + audio_np.tobytes()
                audio_stream = io.BytesIO(normalized_contents)
            else:
                audio_stream = io.BytesIO(contents)
        except:
            audio_stream = io.BytesIO(contents)
        
        # 2. Recognition
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 30
        recognizer.pause_threshold = 1.2
        
        with sr.AudioFile(audio_stream) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            
        # 3. Neural Execution
        response_text = execute_neural_command(text)
        if not response_text:
            response_text = f"Acknowledged: {text}"
            
        brain.store_interaction(text, response_text, "VOICE_COMMAND")
        
        return {
            "success": True,
            "transcript": text,
            "response": response_text
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

# --- BRAIN: COGNITIVE & DESKTOP ENDPOINTS ---

class DesktopAction(BaseModel):
    action: str # 'type', 'press', 'screenshot', 'stats'
    payload: Optional[str] = None
    key: Optional[str] = None

@app.post("/api/brain/execute")
async def execute_brain_action(data: DesktopAction):
    try:
        if data.action == "type":
            brain.type_text(data.payload)
            return {"success": True, "message": f"Typed: {data.payload}"}
        
        elif data.action == "press":
            brain.press_key(data.key)
            return {"success": True, "message": f"Pressed: {data.key}"}
        
        elif data.action == "screenshot":
            path = brain.take_screenshot()
            return {"success": True, "path": path}
        
        elif data.action == "launch":
            success = brain.launch_app(data.payload)
            return {"success": success, "message": f"Launched {data.payload}" if success else "Failed"}
        
        elif data.action == "stats":
            stats = brain.get_system_stats()
            return {"success": True, "stats": stats}

        elif data.action == "setting":
            success, msg = brain.change_system_setting(data.payload, data.key)
            return {"success": success, "message": msg}

        elif data.action == "presentation":
            result = brain.read_presentation(data.payload)
            return result

        elif data.action == "meeting":
            success, msg = brain.meeting_assistant(data.payload)
            return {"success": success, "message": msg}

        elif data.action == "translate":
            translation = brain.translate_live(data.payload, data.key or "en")
            return {"success": True, "translation": translation}
            
        return {"success": False, "message": f"Unknown action: {data.action}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/brain/learn/mistake")
async def log_brain_mistake(action: str, desc: str, correction: str):
    msg = brain.report_mistake(action, desc, correction)
    return {"success": True, "message": msg}

class MemoryItem(BaseModel):
    user_input: str
    bot_response: str
    context: Optional[str] = ""

@app.post("/api/brain/chat")
async def chat_with_brain(request: dict):
    """Processes text-based neural commands with LLM/Puter reasoning."""
    try:
        text = request.get("text", "")
        sync_only = request.get("sync_only", False)
        provided_response = request.get("response", None)
        
        if sync_only and provided_response:
            neural_sys.add_neural_exp(2)
            brain.store_interaction(text, provided_response, "PUTER_JS_SYNC")
            return {"success": True, "response": provided_response}

        # 1. Try specialized Neural Commands first
        response = execute_neural_command(text)
        
        # 2. If no command matched, use the Humanoid LLM Reasoning
        if not response:
            # Get context from Orian's current state correctly
            aff, level, count = personality.get_relationship_data()
            p_state, p_desc = personality.get_time_personality()
            stats = brain.get_system_stats()
            
            # Inject REAL-TIME system telemetry into the context
            context = (
                f"Relationship: {level} (Affinity: {aff}), Personality: {p_state}\n"
                f"System_Realtime: CPU {stats['cpu_usage']}%, RAM {stats['memory_usage']}%\n"
                f"Network_Realtime: Sent {stats['network']['sent_mb']}MB, Recv {stats['network']['recv_mb']}MB, Status: {stats['network']['status']}"
            )
            
            response = llm.generate_response(text, context)
            # LLM interactions provide growth experience
            neural_sys.add_neural_exp(2) 
            
        brain.store_interaction(text, response, "CHAT_PANEL")
        return {"success": True, "response": response}
    except Exception as e:
        print(f"[BrainCore] Chat Fault: {str(e)}")
        return {"success": False, "response": f"Neural Core Fault: {str(e)}"}

@app.post("/api/brain/memory/store")
async def store_memory(item: MemoryItem):
    brain.store_interaction(item.user_input, item.bot_response, item.context)
    return {"success": True}

@app.get("/api/brain/memory/recall")
async def recall_memory(limit: int = 5):
    history = brain.recall_recent(limit)
    return {"success": True, "history": history}

# --- PERSONALITY & BEHAVIORAL INTELLIGENCE ---

@app.get("/api/brain/greeting")
async def get_neural_greeting(emotion: str = "neutral"):
    """Generates a personality-driven greeting."""
    greeting = personality.get_greeting(emotion)
    # Record interaction to evolve relationship
    personality.update_interaction(positive=True)
    return {"success": True, "greeting": greeting}

@app.get("/api/brain/personality")
async def get_personality_status():
    """Returns the current personality and relationship metrics."""
    p_name, p_desc = personality.get_time_personality()
    aff, level, count = personality.get_relationship_data()
    return {
        "success": True,
        "personality": {
            "state": p_name,
            "description": p_desc,
        },
        "relationship": {
            "level": level,
            "affinity": aff,
            "interactions": count
        }
    }

@app.post("/api/brain/judge")
async def judge_intent(request: dict):
    """Ethical reasoning layer to evaluate risky actions."""
    intent = request.get("intent", "")
    result = personality.ethical_reasoning(intent)
    return {"success": True, "assessment": result}

# --- SELF-LEARNING & ADAPTATION ---

@app.get("/api/sys/predict")
async def get_pattern_prediction():
    """Predicts user behavior based on historical habits."""
    prediction = neural_sys.predict_next_action()
    return {"success": True, "data": prediction}

@app.post("/api/sys/download_skill")
async def download_skill(request: dict):
    """Integrates a new skill/plugin into the neural core."""
    category = request.get("category", "")
    result = neural_sys.download_skill(category)
    return {"success": True, "message": result}

@app.get("/api/sys/reflect")
async def get_error_reflection():
    """Analyzes recent faults and improvements."""
    reflection = neural_sys.reflect_on_errors()
    return {"success": True, "log": reflection}

@app.get("/api/sys/evolution")
async def get_evolution_metrics():
    """Returns the brain evolution percentage."""
    metrics = neural_sys.get_brain_evolution_metrics()
    return {"success": True, "metrics": metrics}

@app.get("/")
async def root():
    return {"status": "OrionAI Intelligence Core Online", "brain": "Active", "engine": "Adaptation_v1.0"}

if __name__ == "__main__":
    # Note: reload=True requires the app to be passed as an import string
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
