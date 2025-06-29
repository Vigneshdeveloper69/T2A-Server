from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
import tempfile
import shutil
from gtts import gTTS
import speech_recognition as sr

app = FastAPI()

# Root endpoint to avoid 404 on base URL
@app.get("/")
async def root():
    return {"message": "T2A Server is running"}

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static folder for audio output
AUDIO_FOLDER = "static"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

app.mount("/static", StaticFiles(directory=AUDIO_FOLDER), name="static")

# 🗣️ Endpoint 1: Upload audio and convert to text
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

# 🔊 Endpoint 2: Convert text to audio using gTTS
@app.post("/api/tts")
async def text_to_speech(text: str = Form(...), lang: str = Form("en")):
    try:
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(AUDIO_FOLDER, filename)

        tts = gTTS(text=text, lang=lang)
        tts.save(filepath)

        return {"audio_url": f"https://t2a-server.onrender.com/static/{filename}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# 🎤 Optional Endpoint: Alternate name for speech-to-text
@app.post("/api/audio-to-text")
async def audio_to_text(file: UploadFile = File(...)):
    return await upload_audio(file)
