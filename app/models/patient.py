# app/models/patient.py
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

from app.schemas.intake_schema import PatientInfo
from app.services.utils.id_generator import generate_patient_id, generate_visit_id

def get_latest_visit_snapshot(db, patient_id: str):
    """
    Returns the last visit object (from visits array) for a patient.
    Used to fetch transcript, SOAP summary, etc.
    """
    patient = db.clinicAi.find_one(
        {"patient_id": patient_id},
        {"_id": 0, "visits": {"$slice": -1}}
    )
    if patient and "visits" in patient and patient["visits"]:
        return patient["visits"][0]
    return None

def get_patient_by_name_mobile(db, name: str, mobile: str):
    return db.clinicAi.find_one({
        "patient_info.name": name,
        "patient_info.mobile": mobile
    })

def insert_patient_record(db, patient_record: dict):
    db.clinicAi.insert_one(patient_record)

# transcript related function
def store_transcript(db, patient_id: str, transcript_text: str):
    from datetime import datetime
    today = datetime.today().strftime("%Y-%m-%d")
    visit_id = "V" + today.replace("-", "")
    db.clinicAi.update_one(
        {"patient_id": patient_id, "visits.visit_id": visit_id},
        {"$set": {"visits.$.transcript": transcript_text}}
    )

# audio related function
def store_soap_summary(db, patient_id: str, soap: dict):
    from datetime import datetime
    today = datetime.today().strftime("%Y-%m-%d")
    visit_id = "V" + today.replace("-", "")
    db.clinicAi.update_one(
        {"patient_id": patient_id, "visits.visit_id": visit_id},
        {"$set": {"visits.$.soap_summary": soap}}
    )

# function to get latest visit snapshot
def get_note_state(db, patient_id: str):
    visit = get_latest_visit_snapshot(db, patient_id)
    return {
        "transcript": visit.get("transcript", "") if visit else "",
        "soap_summary": visit.get("soap_summary", {}) if visit else {}
    }

# ---------- Added: one-shot create/reuse patient then create visit ----------
def create_or_reuse_patient_and_new_visit(
    db,
    info: PatientInfo
) -> Tuple[str, str, bool]:
    """
    Lookup by (name, mobile):
      - If found: reuse patient_id, update patient_info, create new visit
      - If not: create new patient document, then create first visit
    Returns: (patient_id, visit_id, is_new_patient)
    """
    existing = get_patient_by_name_mobile(db, info.name, info.mobile)
    is_new_patient = existing is None

    if is_new_patient:
        patient_id = generate_patient_id(db)
        doc = {
            "patient_id": patient_id,
            "patient_info": info.model_dump(),
            "visits": [],
            "created_at": datetime.utcnow(),
        }
        insert_patient_record(db, doc)
    else:
        patient_id = existing["patient_id"]
        # Keep patient info fresh with latest details
        db.clinicAi.update_one(
            {"patient_id": patient_id},
            {"$set": {"patient_info": info.model_dump()}}
        )

    visit_id = generate_visit_id(db, patient_id)
    visit_doc = {
        "visit_id": visit_id,
        "status": "intake-in-progress",
        "created_at": datetime.utcnow(),
        "intake_form": {
            "personal": info.model_dump(),
            "submitted_at": datetime.utcnow(),
        },
    }
    db.clinicAi.update_one(
        {"patient_id": patient_id},
        {"$push": {"visits": visit_doc}}
    )

    return patient_id, visit_id, is_new_patient
