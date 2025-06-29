from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
import tempfile
import shutil
from gtts import gTTS
import speech_recognition as sr
import logging

app = FastAPI()

# Enable logging
logging.basicConfig(level=logging.INFO)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static folder setup
AUDIO_FOLDER = "static"
os.makedirs(AUDIO_FOLDER, exist_ok=True)
app.mount("/static", StaticFiles(directory=AUDIO_FOLDER), name="static")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "T2A Server is running ✅"}

# 🎙️ Upload audio and convert to text
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
        logging.error(f"Error in /api/upload: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# 🔊 Convert text to speech and return URL
@app.post("/api/tts")
async def text_to_speech(request: Request, text: str = Form(...), lang: str = Form("en")):
    SUPPORTED_LANGUAGES = {"en", "ta", "hi"}  # Add more if needed

    try:
        if not text.strip():
            return JSONResponse(status_code=400, content={"error": "Text cannot be empty."})

        if lang not in SUPPORTED_LANGUAGES:
            return JSONResponse(status_code=400, content={"error": f"Unsupported language: {lang}"})

        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(AUDIO_FOLDER, filename)

        logging.info(f"Generating audio for: {text[:30]}... in {lang}")
        tts = gTTS(text=text, lang=lang)
        tts.save(filepath)

        base_url = str(request.base_url).rstrip("/")
        return {"audio_url": f"{base_url}/static/{filename}"}
    except Exception as e:
        logging.error(f"Error in /api/tts: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# Optional alias endpoint
@app.post("/api/audio-to-text")
async def audio_to_text(file: UploadFile = File(...)):
    return await upload_audio(file)
