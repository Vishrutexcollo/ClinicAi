from fastapi import APIRouter
from app.schemas.intake_schema import PatientInfo
from app.services.intake_orchestrator import create_patient_record, start_intake_session, get_next_intake_question, submit_intake_answer, get_intake_state
from app.schemas.intake_schema import AnswerSubmission

router = APIRouter(prefix="/intake", tags=["Intake"])

@router.post("/patient-info")
def submit_patient_info(info: PatientInfo):
    record = create_patient_record(info)
    # Make response JSON-safe
    if isinstance(record, dict):
        record = dict(record)          # copy, just in case
        record.pop("_id", None)        # or: if "_id" in record: record["_id"] = str(record["_id"])
    return record



@router.post("/start")
def start_session(patient_id: str):
    """Start intake Q&A session for a given patient ID"""
    return start_intake_session(patient_id)

@router.get("/next-question")
def next_question(patient_id: str):
    """Get next AI-generated question for intake form"""
    return get_next_intake_question(patient_id)

@router.post("/submit-answer")
def submit_answer(data: AnswerSubmission):
    """Submit patient's answer to a specific question"""
    return submit_intake_answer(data)

@router.get("/state")
def fetch_state(patient_id: str):
    """Fetch current state of intake form (asked/answered questions)"""
    return get_intake_state(patient_id)
