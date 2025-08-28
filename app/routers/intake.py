from fastapi import APIRouter
from app.schemas.intake_schema import PatientInfo
from app.services.intake_orchestrator import create_patient_record

router = APIRouter(prefix="/intake", tags=["Intake"])

@router.post("/register")
def submit_patient_info(info: PatientInfo):
    result = create_patient_record(info.dict())
    return result


