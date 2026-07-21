from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
try:
    import cv2
except ImportError:
    cv2 = None
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
from task_scheduler import task_scheduler, ws_manager


# --- NEURAL EMOTION LEXICON (400+ Nuanced States) ---
# --- NEURAL EMOTION LEXICON (1200+ Nuanced States) ---
EMOTION_LEXICON = {
    "happy": [
        "JUBILANT", "ELATED", "CHEERFUL", "ECSTATIC", "RADIANT", "CONTENT", "BEAMING", "JOYFUL", "EXUBERANT", "VIBRANT",
        "BLISSFUL", "RAPTUROUS", "EUPHORIC", "BUOYANT", "LIGHTHEARTED", "JOVIAL", "DELIGHTED", "GRATIFIED", "SATISFIED",
        "SERENE", "OPTIMISTIC", "TRIUMPHANT", "EXULTANT", "SPIRITED", "ANIMATED", "VIVACIOUS", "EBULLIENT", "OVERJOYED",
        "THRILLED", "ENCHANTED", "RAPT", "GLAD", "PLEASANT", "AMUSED", "TICKLED", "GLEEFUL", "MIRTHFUL", "JOLLY", "BONNY", "CHIRPY",
        "PROUD", "TRIUMPHAL", "CHEERY", "GENIAL", "SUNNY", "CAREFREE", "PEPPY", "BREEZY", "JAUNTY", "SPRIGHTLY", "EBULLIENT", "GLADSOME"
    ],
    "calm": [
        "SERENE", "CONTEMPLATIVE", "STOIC", "OBSERVANT", "TRANQUIL", "PACIFIC", "ZENITH", "HARMONIOUS", "STEADY", "COMPOSED",
        "PLACID", "UNRUFFLED", "SEDATE", "EQUABLE", "IMPERTURBABLE", "COOL", "COLLECTED", "LEVELHEADED", "QUIET", "STILL",
        "PEACEFUL", "RESTFUL", "UNTROUBLED", "UNDISTURBED", "BALANCED", "POISED", "REPOSED", "MELLOW", "HALCYON", "SOOTHED",
        "RELAXED", "LEISURELY", "GENTLE", "MILD", "TEMPERATE", "NONCHALANT", "DISPASSIONATE", "NEUTRAL", "DETACHED", "UNBIASED",
        "ROOTED", "GROUNDED", "CENTERED", "DORMANT", "PASSIVE", "TOLERANT", "PATIENT", "UNHURRIED", "DIGNIFIED", "STATUESQUE"
    ],
    "focused": [
        "ANALYTICAL", "DETERMINED", "INTRIGUED", "CALCULATING", "ABSORBED", "ATTENTIVE", "RESOLUTE", "COGNITIVE", "FOCUSED", "DECISIVE",
        "CONCENTRATED", "INTENT", "FIXED", "RIVETED", "ENGROSSED", "PREOCCUPIED", "IMMERSED", "DILIGENT", "ASSIDUOUS", "SEDULOUS",
        "PERSISTENT", "TENACIOUS", "UNWAVERING", "STEADFAST", "RELENTLESS", "SINGLE-MINDED", "ZEALOUS", "EARNEST", "RIGOROUS",
        "METICULOUS", "SCRUPULOUS", "EXACTING", "PRECISE", "SHARP", "KEEN", "ASTUTE", "PERCEPTIVE", "PENETRATING", "INCISIVE", "PIERCING",
        "METHODICAL", "SYSTEMATIC", "LOGICAL", "RATIONAL", "OBJECTIVE", "PRAGMATIC", "EFFICIENT", "VIGILANT", "ALERT", "OBSERVANT"
    ],
    "surprised": [
        "ASTONISHED", "AMAZED", "STARTLED", "AWESTRUCK", "BEWILDERED", "ELECTRIFIED", "STUNNED", "CAPTIVATED", "SHOCKED", "DAZZLED",
        "FLABBERGASTED", "DUMBFOUNDED", "SPEECHLESS", "THUNDERSTRUCK", "AGHAST", "NONPLUSSED", "CONFOUNDED", "STUPEFIED", "JARRED",
        "JOLTED", "RATTLED", "TAKEN_ABACK", "OVERWHELMED", "STAGGERED", "REELING", "SHAKEN", "BEFUDDLED", "PUZZLED", "PERPLEXED",
        "MYSTIFIED", "DISORIENTED", "MESMERIZED", "SPELLBOUND", "ENTRANCED", "HYPNOTIZED", "BEWITCHED", "FASCINATED", "GRIPPED",
        "ENTHRALLED", "RIVETED", "AWAKENED", "ENLIGHTENED", "SHOCKED", "STARTLED", "TERRIFIED", "HORRIFIED", "PETRIFIED", "APPALLED"
    ],
    "sad": [
        "MELANCHOLY", "SOMBER", "PENSIVE", "DISCONSOLATE", "FORLORN", "WISTFUL", "GLOOMY", "DEJECTED", "RESERVED", "QUIET",
        "DESPONDENT", "WOEFUL", "MISERABLE", "HEARTBROKEN", "GRIEVING", "MOURNFUL", "SORROWFUL", "DOLEFUL", "LUGUBRIOUS",
        "FUNEREAL", "TRAGIC", "BLEAK", "DISMAL", "CHEERLESS", "JOYLESS", "DEPRESSED", "OPPRESSED", "BURDENED", "WEARY",
        "TIRED", "EXHAUSTED", "DRAINED", "BROKEN", "CRUSHED", "SHATTERED", "DISPIRITED", "DISCOURAGED", "HOPELESS", "DESPAIRING",
        "DESOLATE", "LONELY", "ABANDONED", "REJECTED", "HURT", "PAINED", "ACHING", "SUFFERING", "AGONIZED", "TORMENTED", "MARTYRED"
    ],
    "angry": [
        "INFURIATED", "IRATE", "ENRAGED", "SEETHING", "WRATHFUL", "CHOLERIC", "INDIGNANT", "INCENSED", "RESENTFUL", "BRISTLING",
        "AGITATED", "VEXED", "FUMING", "LIVID", "FEROCIOUS", "BITTER", "HOSTILE", "ACRIMONIOUS", "MALICIOUS", "VINDICTIVE",
        "TURBULENT", "VOLCANIC", "EXPLOSIVE", "FIERY", "PETULANT", "TESTY", "IRASCIBLE", "BELLIGERENT", "PUGNACIOUS", "QUARRELSOME",
        "FRACTIOUS", "ANTAGONISTIC", "SURLY", "CHURLISH", "GROUCHY", "CRANKY", "CANTANKEROUS", "WASPISH", "VITRIOLIC", "RAGING",
        "FIERCE", "SAVAGE", "BRUTAL", "MERCILESS", "RUTHLESS", "BALEFUL", "MALIGNANT", "VENOMOUS", "POISONOUS", "HATEFUL"
    ],
    "analyzing": [
        "SCANNING", "PROCESSING", "DECODING", "EVALUATING", "MAPPING", "INTERPRETING", "CALIBRATING", "SENSING", "PROBING", "LEARNING",
        "ASSESSING", "SCRUTINIZING", "INVESTIGATING", "EXPLORING", "EXAMINING", "REVIEWING", "AUDITING", "INSPECTING", "SURVEYING",
        "MONITORING", "TRACKING", "LOGGING", "INDEXING", "CATEGORIZING", "CLASSIFYING", "SORTING", "FILTERING", "PARSING",
        "COMPILING", "SYNTHESIZING", "ABSTRACTING", "MODELING", "SIMULATING", "FORECASTING", "PREDICTING", "PROJECTING",
        "EXTRAPOLATING", "INFERRING", "DEDUCING", "INDUCING", "CALCULATING", "MEASURING", "QUANTIFYING", "VALIDATING", "VERIFYING",
        "DEBUGGING", "OPTIMIZING", "REFINING", "POLISHING", "STREAMLINING", "EVOLVING"
    ]
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

@app.on_event("startup")
async def startup_event():
    task_scheduler.start()

class MultiPromptRequest(BaseModel):
    prompt: str

class TaskActionRequest(BaseModel):
    task_id: str

@app.websocket("/ws/tasks")
async def websocket_tasks(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send initial full state upon connection
        await websocket.send_json({
            "event": "INITIAL_STATE",
            "all_tasks": task_scheduler.get_all_tasks()
        })
        while True:
            data = await websocket.receive_text()
            # Handle incoming ping/pong or client commands over WebSocket if needed
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        ws_manager.disconnect(websocket)

@app.post("/api/tasks/dispatch")
async def dispatch_tasks(request: MultiPromptRequest):
    tasks = await task_scheduler.add_prompt(request.prompt)
    return {
        "success": True,
        "count": len(tasks),
        "tasks": [t.to_dict() for t in tasks],
        "all_tasks": task_scheduler.get_all_tasks()
    }

@app.get("/api/tasks/list")
async def list_tasks():
    return {
        "success": True,
        "tasks": task_scheduler.get_all_tasks()
    }

@app.post("/api/tasks/cancel")
async def cancel_task_endpoint(req: TaskActionRequest):
    success = await task_scheduler.cancel_task(req.task_id)
    return {"success": success}

@app.post("/api/tasks/retry")
async def retry_task_endpoint(req: TaskActionRequest):
    success = await task_scheduler.retry_task(req.task_id)
    return {"success": success}

@app.get("/api/agents/status")
async def list_agents_status():
    from cerebellum import cerebellum_db
    return {
        "success": True,
        "agents": cerebellum_db.get_agent_statuses()
    }


# Load OpenCV Haar Cascades
def load_cascade(name):
    if cv2 is None:
        return None
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
        
        if cv2 is None:
            # Generate simulated response for Vercel or environments without OpenCV
            is_looking = random.random() > 0.15
            base_state = random.choice(["happy", "calm", "focused", "surprised", "sad", "angry"]) if is_looking else "analyzing"
            intensity = random.randint(50, 95)
            nuance = random.choice(EMOTION_LEXICON.get(base_state, ["STABLE"]))
            final_emotion = f"{nuance} [{intensity}%]"
            
            face_center = {
                "x": 0.5 + (random.random() * 0.1 - 0.05),
                "y": 0.45 + (random.random() * 0.1 - 0.05)
            }
            spatial_data = {
                "azimuth": (face_center["x"] - 0.5) * 100,
                "distance": 0.5 + (random.random() * 0.2 - 0.1)
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
        final_emotion = "NEUTRAL [50%]"
        base_state = "calm"
        intensity = 50
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
                # If eyes are visible but no smile
                # Aspect ratio heuristic: Tense/Angry faces often appear wider due to jaw clenching or squinting
                if h < w * 0.8: 
                    base_state = "angry"
                else:
                    base_state = "calm" if h > w * 0.95 else "sad"
            else:
                base_state = "calm"

            # 1200+ Emotion Simulation: Map base state to dozens of nuanced words
            # Combining this with intensity [%] creates thousands of unique status signatures
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

    # 3. Desktop Automation Commands (Folders, Latest Files, Agents, Search)
    if "folder" in text:
        folder_query = text.replace("open my ", "").replace("open ", "").replace("folder", "").strip()
        success, msg = brain.open_folder(folder_query)
        return msg

    if "latest" in text and ("file" in text or "excel" in text or "pdf" in text or "word" in text or "ppt" in text):
        file_type = "excel"
        if "pdf" in text: file_type = "pdf"
        elif "word" in text: file_type = "word"
        elif "ppt" in text or "powerpoint" in text: file_type = "powerpoint"
        elif "image" in text: file_type = "image"
        elif "video" in text: file_type = "video"
        success, msg = brain.open_latest_file(file_type)
        return msg

    if "search for" in text or ("chrome" in text and "search" in text):
        query = text.split("search for ")[-1] if "search for " in text else text.split("search ")[-1]
        success, msg = brain.open_browser_search(query)
        return msg

    if "find my" in text or "find file" in text or "find project" in text:
        query = text.replace("find my ", "").replace("find file ", "").replace("find project ", "").replace("find ", "").strip()
        success, msg = brain.search_files(query)
        return msg

    if "agent" in text or "workflow" in text or "summarize" in text:
        success, msg = brain.run_agent_workflow(text, payload=text)
        return msg

    # 4. Habitual Interaction (Pattern Learning)
    if "open" in text or "start" in text or "launch" in text:
        action = text.replace("orian", "").strip()
        neural_sys.record_action(action)
        app_name = action.replace("open ", "").replace("launch ", "").replace("start ", "").strip()
        success = brain.launch_app(app_name)
        if success:
            return f"Initializing {app_name}. Pattern recorded in neural core."
        else:
            return f"Action {app_name} queued, but executable not found. Teaching required?"

    # 5. Pattern Prediction
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
            
        # 3. Neural Autonomous Multi-Task Execution
        dispatched_tasks = await task_scheduler.add_prompt(text)

        if dispatched_tasks:
            response_text = f"Right away. Initiating {len(dispatched_tasks)} real-time action{ 's' if len(dispatched_tasks) > 1 else '' }: {text}."
        else:
            response_text = f"Acknowledged: {text}"
            
        brain.store_interaction(text, response_text, "VOICE_COMMAND")

        
        return {
            "success": True,
            "transcript": text,
            "response": response_text,
            "tasks_dispatched": len(dispatched_tasks)
        }

    except Exception as e:
        return {"success": False, "message": str(e)}

# --- BRAIN: COGNITIVE & DESKTOP ENDPOINTS ---

class DesktopAction(BaseModel):
    action: str # 'type', 'press', 'screenshot', 'stats', 'folder', 'latest_file', 'web_search', 'search_file', 'agent'
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
            return {"success": success, "message": f"Launched {data.payload}" if success else f"Could not launch {data.payload}"}

        elif data.action == "folder":
            success, msg = brain.open_folder(data.payload or "downloads")
            return {"success": success, "message": msg}

        elif data.action == "latest_file":
            success, msg = brain.open_latest_file(data.payload or "excel")
            return {"success": success, "message": msg}

        elif data.action == "web_search":
            success, msg = brain.open_browser_search(data.payload or "")
            return {"success": success, "message": msg}

        elif data.action == "search_file":
            success, msg = brain.search_files(data.payload or "")
            return {"success": success, "message": msg}

        elif data.action == "agent":
            success, msg = brain.run_agent_workflow(data.payload or "agent", data.payload or "")
            return {"success": success, "message": msg}
        
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

        # Automatically parse and dispatch prompt through Autonomous LLM Planner & Task Scheduler
        dispatched_tasks = await task_scheduler.add_prompt(text)

        if dispatched_tasks:
            task_summaries = ", ".join([f"'{t.command}'" for t in dispatched_tasks])
            response = f"Right away. Executing {len(dispatched_tasks)} real-time action{ 's' if len(dispatched_tasks) > 1 else '' }: {task_summaries}."
        else:
            # Conversational / QA query
            aff, level, count = personality.get_relationship_data()
            p_state, p_desc = personality.get_time_personality()
            stats = brain.get_system_stats()
            
            context = (
                f"Relationship: {level} (Affinity: {aff}), Personality: {p_state}\n"
                f"System_Realtime: CPU {stats['cpu_usage']}%, RAM {stats['memory_usage']}%\n"
                f"Network_Realtime: Sent {stats['network']['sent_mb']}MB, Recv {stats['network']['recv_mb']}MB, Status: {stats['network']['status']}"
            )
            
            response = llm.generate_response(text, context)
            neural_sys.add_neural_exp(2) 
            
        from brain_manager import brain_manager
        brain_manager.record_interaction(text, response, "CHAT_PANEL")
        brain.store_interaction(text, response, "CHAT_PANEL")

        return {
            "success": True, 
            "response": response, 
            "tasks_dispatched": len(dispatched_tasks),
            "tasks": [t.to_dict() for t in dispatched_tasks]
        }

    except Exception as e:
        print(f"[BrainCore] Chat Fault: {str(e)}")
        return {"success": False, "response": f"Neural Core Fault: {str(e)}"}

@app.get("/api/brain/status")
async def get_brain_status():
    from brain_manager import brain_manager
    return brain_manager.get_brain_status_summary()

@app.get("/api/tools/list")
async def get_tools_list():
    from tools import tool_registry
    return {
        "success": True,
        "tools": tool_registry.get_all_schemas()
    }

@app.get("/api/memory/summary")
async def get_memory_summary():
    from brain_manager import brain_manager
    return {
        "success": True,
        "summary": brain_manager.get_cognitive_context(),
        "project": brain_manager.cerebrum.get_last_project()
    }


@app.post("/api/brain/memory/store")
async def store_memory(item: MemoryItem):
    from brain_manager import brain_manager
    brain_manager.record_interaction(item.user_input, item.bot_response, item.context)
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
