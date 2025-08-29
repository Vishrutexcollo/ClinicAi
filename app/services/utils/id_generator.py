from datetime import datetime
from uuid import uuid4

def new_patient_id(prefix: str = "CLINIC01") -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    return f"{prefix}-{today}-{str(uuid4())[:8].upper()}"

def new_visit_id(prefix: str = "V") -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    return f"{prefix}{today}"

# Backwards-compat aliases
def generate_patient_id(prefix: str = "CLINIC01") -> str:
    return new_patient_id(prefix)

def generate_visit_id(prefix: str = "V") -> str:
    return new_visit_id(prefix)


def generate_patient_id(db: Optional[object] = None, prefix: str = "CLINIC01") -> str:
    if db is None:
        return new_patient_id(prefix)
    today = datetime.utcnow().strftime("%Y%m%d")
    doc = db.patient_counter.find_one_and_update(
        {"_id": today},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    seq = str(doc["seq"]).zfill(4)
    return f"{prefix}-{today}-{seq}"

def generate_visit_id(db: Optional[object] = None, patient_id: Optional[str] = None) -> str:
    if db is None:
        return new_visit_id()
    today = datetime.utcnow().strftime("%Y%m%d")
    key = f"{patient_id}:{today}" if patient_id else f"VISIT_GLOBAL:{today}"
    doc = db.visit_counter.find_one_and_update(
        {"_id": key},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    seq = str(doc["seq"]).zfill(3 if patient_id else 4)
    if patient_id:
        return f"{patient_id}-V{today}-{seq}"
    return f"V{today}-{seq}"
