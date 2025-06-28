from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
import tempfile
import shutil
import pyttsx3
import speech_recognition as sr

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to store generated audio
AUDIO_FOLDER = "static"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Mount static folder to serve audio files
app.mount("/static", StaticFiles(directory=AUDIO_FOLDER), name="static")

# Endpoint 1: Convert uploaded audio to text
@app.post("/api/upload")
async def upload_audio(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_path = tmp.name
            shutil.copyfileobj(file.file, tmp)

        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)

        os.remove(tmp_path)
        return {"text": text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Endpoint 2: Convert text to speech
@app.post("/api/tts")
async def text_to_speech(text: str = Form(...), lang: str = Form("en")):
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")

        # Voice selection logic
        voice_map = {
            "en": "english",
            "ta": "tamil",
            "hi": "hindi"
        }

        target_voice = voice_map.get(lang.lower(), "english")
        for voice in voices:
            if target_voice in voice.name.lower():
                engine.setProperty("voice", voice.id)
                break

        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(AUDIO_FOLDER, filename)

        engine.save_to_file(text, filepath)
        engine.runAndWait()

        return {"audio_url": f"http://localhost:8000/static/{filename}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Endpoint 3: Optional - extra speech-to-text API
@app.post("/api/audio-to-text")
async def audio_to_text(file: UploadFile = File(...)):
    return await upload_audio(file)
