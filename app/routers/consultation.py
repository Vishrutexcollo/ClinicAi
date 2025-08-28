from fastapi import APIRouter
from pydantic import BaseModel
from app.services import audio_orchestrator, soap_orchestrator
from app.db import get_database
from app.models.patient import get_note_state

router = APIRouter(prefix="/consultation", tags=["Note & SOAP"])

class AudioRequest(BaseModel):
    patient_id: str
    audio_url: str

class SOAPRequest(BaseModel):
    patient_id: str

@router.post("/transcribe")
def transcribe_audio(req: AudioRequest):
    return audio_orchestrator.transcribe_audio_from_url(req.patient_id, req.audio_url)

@router.post("/soap")
def generate_soap(req: SOAPRequest):
    return soap_orchestrator.generate_soap_summary(req.patient_id)

@router.get("/state")
def note_state(patient_id: str):
    db = get_database()
    return get_note_state(db, patient_id)
