# app/routers/consultation.py
from datetime import datetime
from typing import Optional, Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db import get_database
from app.models.patient import get_note_state
from app.services import audio_orchestrator, soap_orchestrator

router = APIRouter(prefix="/consultation", tags=["Consultation"])

# ---------- Audio & SOAP (kept) ----------

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

# ---------- Consultation flow (mongomock-friendly) ----------

class ConsultationStart(BaseModel):
    patient_id: str
    visit_id: str

class NoteCreate(BaseModel):
    patient_id: str
    visit_id: str
    text: str = Field(..., min_length=1)

class ConsultationComplete(BaseModel):
    patient_id: str
    visit_id: str
    summary: Optional[str] = None

class ConsultationResponse(BaseModel):
    message: str

def _col(db):
    # Use your main collection here (change if needed)
    return db.clinicAi

def _get_patient(db, patient_id: str) -> Optional[Dict[str, Any]]:
    return _col(db).find_one({"patient_id": patient_id}, {"_id": 0})

def _ensure_patient(db, patient_id: str) -> Dict[str, Any]:
    doc = _get_patient(db, patient_id)
    if not doc:
        _col(db).insert_one({
            "patient_id": patient_id,
            "patient_info": {},
            "visits": [],
            "created_at": datetime.utcnow(),
        })
        doc = _get_patient(db, patient_id)
    return doc

def _find_visit(visits: List[Dict[str, Any]], visit_id: str) -> Optional[Dict[str, Any]]:
    return next((v for v in visits if v.get("visit_id") == visit_id), None)

def _ensure_visit(db, patient_id: str, visit_id: str) -> Dict[str, Any]:
    """
    Ensure a visit exists by loading the patient, appending if missing,
    and writing back the *entire* visits array (no positional operators).
    Returns the refreshed patient document.
    """
    patient = _ensure_patient(db, patient_id)
    visits = list(patient.get("visits", []))
    visit = _find_visit(visits, visit_id)
    if not visit:
        visit = {"visit_id": visit_id, "created_at": datetime.utcnow()}
        visits.append(visit)
        _col(db).update_one({"patient_id": patient_id}, {"$set": {"visits": visits}})
        patient = _get_patient(db, patient_id)  # refresh
    return patient

def _get_visit_or_404(db, patient_id: str, visit_id: str) -> Dict[str, Any]:
    patient = _get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    visit = _find_visit(patient.get("visits", []), visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    return {"patient": patient, "visit": visit}

def _mutate_visit(db, patient_id: str, visit_id: str, mutate_fn):
    """
    Load patient, mutate the matching visit in Python, then write back the whole visits array.
    This avoids positional projection/update (mongomock-safe).
    """
    patient = _ensure_patient(db, patient_id)
    visits = list(patient.get("visits", []))
    for i, v in enumerate(visits):
        if v.get("visit_id") == visit_id:
            visits[i] = mutate_fn(dict(v))  # copy before modify
            break
    else:
        # Create visit if missing
        visits.append(mutate_fn({"visit_id": visit_id, "created_at": datetime.utcnow()}))
    _col(db).update_one({"patient_id": patient_id}, {"$set": {"visits": visits}})

@router.post("/start", response_model=ConsultationResponse)
def start_consultation(payload: ConsultationStart):
    db = get_database()
    _ensure_visit(db, payload.patient_id, payload.visit_id)

    def _set_started(v):
        c = dict(v.get("consultation") or {})
        c.setdefault("notes", [])
        c["status"] = "in-progress"
        c["started_at"] = c.get("started_at") or datetime.utcnow()
        v["consultation"] = c
        return v

    _mutate_visit(db, payload.patient_id, payload.visit_id, _set_started)
    return ConsultationResponse(message="Consultation started")

@router.post("/note", response_model=ConsultationResponse)
def add_note(payload: NoteCreate):
    db = get_database()

    def _add(v):
        c = dict(v.get("consultation") or {})
        notes = list(c.get("notes") or [])
        notes.append({"text": payload.text, "created_at": datetime.utcnow()})
        c["notes"] = notes
        c["status"] = "in-progress"
        v["consultation"] = c
        return v

    _mutate_visit(db, payload.patient_id, payload.visit_id, _add)
    return ConsultationResponse(message="Note added")

@router.get("/{patient_id}/{visit_id}")
def get_consultation(patient_id: str, visit_id: str):
    db = get_database()
    data = _get_visit_or_404(db, patient_id, visit_id)
    visit = data["visit"]
    c = visit.get("consultation") or {}
    return {
        "patient_id": patient_id,
        "visit_id": visit_id,
        "consultation": {
            "status": c.get("status", "not-started"),
            "started_at": c.get("started_at"),
            "completed_at": c.get("completed_at"),
            "summary": c.get("summary"),
            "notes": c.get("notes", []),
        },
    }

@router.post("/complete", response_model=ConsultationResponse)
def complete_consultation(payload: ConsultationComplete):
    db = get_database()

    def _complete(v):
        c = dict(v.get("consultation") or {})
        c["status"] = "completed"
        c["completed_at"] = datetime.utcnow()
        if payload.summary:
            c["summary"] = payload.summary
        v["consultation"] = c
        return v

    _mutate_visit(db, payload.patient_id, payload.visit_id, _complete)
    return ConsultationResponse(message="Consultation completed")
