# app/routers/intake.py
from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.db import get_database
from app.schemas.intake_schema import (
    PatientInfo,
    AnswerSubmission,
    IntakeStartRequest,
    IntakeStartResponse,
)
from app.services.intake_orchestrator import (
    create_patient_record,
    start_intake_session,
    get_next_intake_question,
    submit_intake_answer,
    get_intake_state,
)
from app.models.patient import (
    create_or_reuse_patient_and_new_visit,
)

router = APIRouter(prefix="/intake", tags=["Intake"])

# ----------------
@router.post("/patient-info")
def submit_patient_info(info: PatientInfo):
    record = create_patient_record(info)

    # Make response JSON-safe
    if isinstance(record, dict):
        record = dict(record)          # copy, just in case
        record.pop("_id", None)        # or: if "_id" in record: record["_id"] = str(record["_id"])

    return record


@router.post("/start-session")
def start_session(patient_id: str):
    """Start intake Q&A session for a given patient ID (returns session_id)."""
    return start_intake_session(patient_id)

@router.get("/next-question")
def next_question(session_id: str):
    """
    Get next AI-generated question for the given session.
    NOTE: expects session_id (not patient_id).
    """
    q = get_next_intake_question(session_id)
    if q is None:
        return {"next_question": None, "completed": True}
    return {"next_question": q, "completed": False}

@router.post("/submit-answer")
def submit_answer(session_id: str, data: AnswerSubmission):
    """Submit patient's answer and get the next question."""
    return submit_intake_answer(session_id, data.model_dump())

@router.get("/state")
def fetch_state(session_id: str):
    """Fetch current state of intake form (asked/answered questions)."""
    s = get_intake_state(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Invalid session_id")
    return s

# ---------- Added: unified route (create/reuse patient & create visit) ----------
@router.post("/register", response_model=IntakeStartResponse)
def register_and_create_visit(payload: IntakeStartRequest):
    """
    Submit personal details once -> returns patient_id + visit_id.
    - If (name, mobile) exists: reuse patient_id, create NEW visit_id.
    - Else: create new patient_id AND a new visit_id.
    In both cases, store the personal details as the visit's intake form.
    """
    db = get_database()
    patient_id, visit_id, is_new = create_or_reuse_patient_and_new_visit(db, payload)
    return IntakeStartResponse(
        patient_id=patient_id,
        visit_id=visit_id,
        is_new_patient=is_new,
    )
