# Audio orchestrator logic here
import os
import sys
import requests
from app.models.patient import store_transcript
from app.db import get_database
db = get_database()
# Ensure the parent directory is in sys.path so 'app' can be imported
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import OPENAI_API_KEY


# OPENAI_API_KEY =os.getenv("OPENAI_API_KEY")

def transcribe_audio_from_url(patient_id, audio_url):
    print(" Step 1: Starting transcription for patient:", patient_id)
    
    try:
        print(" Step 2: Downloading audio from:", audio_url)
        audio_response = requests.get(audio_url, timeout=10)
        if audio_response.status_code != 200:
            print(" Audio download failed:", audio_response.status_code)
            return {"error": "Failed to download audio"}

        TEMP_FILE_PATH = "temp_audio.mp3"
        with open(TEMP_FILE_PATH, "wb") as f:
            f.write(audio_response.content)
        print(" Step 3: Audio downloaded and saved")

        print(" Step 4: Sending audio to OpenAI Whisper...")
        with open(TEMP_FILE_PATH, "rb") as audio_file:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            }
            files = {
                "file": audio_file,
                "model": (None, "whisper-1")
            }
            whisper_response = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files,
                timeout=60
            )

        if whisper_response.status_code != 200:
            print(" Whisper API error:", whisper_response.text)
            return {"error": "Transcription failed", "details": whisper_response.text}

        transcript = whisper_response.json()["text"]
        print(" Step 5: Transcription complete:", transcript)


        #save transcript in db
        store_transcript(db,patient_id,transcript)

        return {
            "patient_id": patient_id,
            "transcript": transcript,
            "message": "transcript saved successfully"
        }

    except Exception as e:
        print(" Exception occurred:", e)
        return {"error": "Unexpected error", "details": str(e)}
