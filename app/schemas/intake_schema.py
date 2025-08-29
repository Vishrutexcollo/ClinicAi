from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel, EmailStr, Field


# ---------- Existing models (kept as-is) ----------

class PatientInfo(BaseModel):
    name: str = Field(..., example="John Doe")
    age: int = Field(..., gt=0, example=35)
    gender: str = Field(..., example="Male")
    mobile: str = Field(..., example="+919876543210")
    email: Optional[EmailStr] = None
    emergency_contact: Optional[str] = None


class IntakeQuestion(BaseModel):
    question_id: str
    question_text: str


class IntakeAnswer(BaseModel):
    patient_id: str
    visit_id: str
    question_id: str
    answer: str


class IntakeRequest(BaseModel):
    patient_id: str
    visit_id: str


class IntakeResponse(BaseModel):
    patient_id: str
    visit_id: str
    questions: List[IntakeQuestion]


# ---------- New models used by router/orchestrator ----------

class AnswerSubmission(BaseModel):
    """Body for answering the current question."""
    value: str


class Question(BaseModel):
    """Next-question payload used by the orchestrator."""
    id: str
    text: str
    index: int
    total: int


class SessionState(BaseModel):
    """Debug/inspect state for an intake session."""
    patient_id: str
    asked: int
    target_max: int
    extras_used: int
    questions: List[str]
    answers: Dict[str, Optional[str]]
    llm_disabled: bool
    created_at: datetime
