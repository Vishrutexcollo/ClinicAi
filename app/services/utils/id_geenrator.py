# app/services/utils/id_generator.py
from datetime import datetime
from uuid import uuid4

def new_patient_id(prefix: str = "CLINIC01") -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    return f"{prefix}-{today}-{str(uuid4())[:8].upper()}"

def new_visit_id(prefix: str = "V") -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    return f"{prefix}{today}"

