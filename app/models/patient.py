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

#trancript related function
def store_transcript(db, patient_id: str, transcript_text: str):
    from datetime import datetime
    today = datetime.today().strftime("%Y-%m-%d")
    visit_id = "V" + today.replace("-", "")
    db.clinicAi.update_one(
        {"patient_id": patient_id, "visits.visit_id": visit_id},
        {"$set": {"visits.$.transcript": transcript_text}}
    )

#audio related function
def store_soap_summary(db, patient_id: str, soap: dict):
    from datetime import datetime
    today = datetime.today().strftime("%Y-%m-%d")
    visit_id = "V" + today.replace("-", "")
    db.clinicAi.update_one(
        {"patient_id": patient_id, "visits.visit_id": visit_id},
        {"$set": {"visits.$.soap_summary": soap}}
    )

#function to get latest visit snapshot
def get_note_state(db, patient_id: str):
    visit = get_latest_visit_snapshot(db, patient_id)
    return {
        "transcript": visit.get("transcript", ""),
        "soap_summary": visit.get("soap_summary", {})
    }
