from datetime import datetime
import hashlib
from pymongo import ReturnDocument
from app.db import get_database
from app.models.patient import get_patient_by_name_mobile, insert_patient_record



def generate_patient_id(db, name: str, mobile: str) -> str:
    # Combine name and mobile to create a unique string
    raw_id = f"{name.strip().lower()}_{mobile.strip()}"
    # Use hashlib to create a SHA-256 hash of the string
    hash_object = hashlib.sha256(raw_id.encode())
    encrypted_id = hash_object.hexdigest()[:12]  # Use first 12 chars for brevity
    return encrypted_id

def create_patient_record(data: dict):
    db = get_database()
    existing = get_patient_by_name_mobile(db, data['name'], data['mobile'])
    
    if existing:
        return {"patient_id": existing['patient_id'], "message": "Patient already exists."}
    
    patient_id = generate_patient_id(db, data['name'], data['mobile'])

    new_patient = {
        "patient_id": patient_id,
        "patient_info": data,
        "visits": []
    }
    
    insert_patient_record(db, new_patient)
    return {"patient_id": patient_id, "message": "Patient created."}
