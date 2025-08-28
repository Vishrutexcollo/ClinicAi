from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class PatientInfo(BaseModel):
    name: str = Field(..., example="John Doe")
    age: int = Field(..., gt=0, example=35)
    gender: str = Field(..., example="Male")
    mobile: str = Field(..., example="+919876543210")
    email: Optional[EmailStr] = None
    emergency_contact: Optional[str] = None
