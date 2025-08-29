# app/services/intake_orchestrator.py
from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from uuid import uuid4
import json
import os
import re

from pymongo import ReturnDocument

from app.db import get_database
from app.models.patient import get_patient_by_name_mobile, insert_patient_record
from app.schemas.intake_schema import PatientInfo

# ---------- OpenAI client (new SDK) ----------
from openai import OpenAI

def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Lazily fail with a clear message only when needed
        raise RuntimeError("OPENAI_API_KEY not set. Set it or load via .env before running.")
    return OpenAI(api_key=api_key)


CLINIC_PREFIX = "CLINIC01"

# In-memory session store (resets on server restart)
_SESSIONS: Dict[str, Dict[str, Any]] = {}

# Hard rules
_TARGET_QUESTIONS = 10          # normal cap
_EXTRA_ALLOWED_MAX = 3          # allow up to 2-3 more if info incomplete
_HARD_CAP = _TARGET_QUESTIONS + _EXTRA_ALLOWED_MAX  # absolute max

_FALLBACK_QUESTIONS: List[str] = [
    "What brings you in today?",
    "How long have you had these symptoms?",
    "Where is the pain located, if any?",
    "Any fever, cough, or shortness of breath?",
    "Any known allergies?",
    "Are you taking any medications or supplements?",
    "Any prior similar episodes?",
    "Any recent travel or exposure to sick contacts?",
    "Any chronic conditions (e.g., diabetes, hypertension)?",
    "Is there anything else the doctor should know right now?",
]

# ---------- System prompt for the LLM ----------
_SYSTEM_PROMPT = """
You are a general physician AI assistant conducting an intake interview.
Rules:
1) Ask ONE question at a time (no multi-part questions).
2) Keep it short, simple, clinically relevant, and non-repetitive.
3) Default max is 10 questions total.
4) If after 10 questions the information is still insufficient to form a basic preliminary understanding,
   you may ask up to 2–3 extra questions (absolute max 13). Only do this if clearly necessary.
5) Use prior answers to avoid repeating the same idea with different words.
6) Output STRICT JSON only with keys:

{
  "next_question": "string or empty if done",
  "done": true,
  "needs_extra": false,
  "reason": "short note"
}

- Booleans must be true/false.
- Set done=true when you believe enough information has been gathered.
- If the count has reached 10 and more info is truly needed, set needs_extra=true.
""".strip()

def _extract_json(s: str) -> dict:
    """
    Try to parse model output as JSON, even if extra text is around.
    """
    s = s.strip()
    # If it's already valid JSON
    try:
        return json.loads(s)
    except Exception:
        pass

    # Look for a JSON object in the text
    m = re.search(r'\{.*\}', s, flags=re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    raise ValueError("Could not parse LLM output as JSON")

def _llm_next_question(
    patient_info: dict,
    qa_history: List[Tuple[str, str]],
    asked_count: int,
) -> dict:
    """
    Ask the LLM for the next single question (or signal 'done').
    Returns parsed JSON dict with: next_question, done, needs_extra, reason
    """
    client = _get_client()

    # Build a compact transcript
    transcript_lines = []
    for i, (q, a) in enumerate(qa_history, start=1):
        transcript_lines.append(f"Q{i}: {q}")
        transcript_lines.append(f"A{i}: {a if a is not None else ''}")
    transcript = "\n".join(transcript_lines) if transcript_lines else "(no prior Q/A)"

    user_block = (
        f"Patient: Name={patient_info.get('name')}, Age={patient_info.get('age')}, "
        f"Gender={patient_info.get('gender')}\n"
        f"Questions asked so far: {asked_count}\n"
        f"Target max: 10; Absolute max: 13 (only if necessary).\n"
        f"Transcript so far:\n{transcript}\n\n"
        "Return STRICT JSON only."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_block},
        ],
    )
    raw = resp.choices[0].message.content or ""
    data = _extract_json(raw)

    # Basic shape guard
    if "next_question" not in data or "done" not in data or "needs_extra" not in data:
        raise ValueError("LLM JSON missing required keys")

    # Normalize types
    data["next_question"] = (data.get("next_question") or "").strip()
    data["done"] = bool(data.get("done"))
    data["needs_extra"] = bool(data.get("needs_extra"))
    return data


# ---------- Helpers ----------
def _generate_patient_id(db, name: str, mobile: str) -> str:
    today_str = datetime.now().strftime("%Y%m%d")
    counter = db.patient_counter.find_one_and_update(
        {"_id": today_str},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    seq = str(counter["seq"]).zfill(4)
    return f"{CLINIC_PREFIX}-{today_str}-{seq}"

def _get_patient_info_by_id(db, patient_id: str) -> Optional[dict]:
    doc = db.clinicAi.find_one({"patient_id": patient_id}, {"_id": 0, "patient_info": 1})
    return doc.get("patient_info") if doc else None

# ---------- API used by your router ----------

def create_patient_record(patient_info: PatientInfo) -> dict:
    """
    Creates (or returns) a patient record using name+mobile as dedupe.
    """
    db = get_database()
    existing = get_patient_by_name_mobile(db, patient_info.name, patient_info.mobile)
    if existing:
        return existing

    patient_id = _generate_patient_id(db, patient_info.name, patient_info.mobile)
    record = {
        "patient_id": patient_id,
        "patient_info": patient_info.model_dump(),  # Pydantic v2
        "visits": [],
        "created_at": datetime.utcnow(),
    }
    insert_patient_record(db, record)
    return record

def start_intake_session(patient_id: str) -> str:
    """
    Start a session. LLM will choose each next question on demand.
    """
    session_id = str(uuid4())
    _SESSIONS[session_id] = {
        "patient_id": patient_id,
        "q_index": 0,                # how many have been asked
        "answers": {},               # qid -> text
        "questions": [],             # list of asked questions (text)
        "target_max": _TARGET_QUESTIONS,
        "extras_used": 0,
        "created_at": datetime.utcnow(),
        "llm_disabled": False,       # if LLM errors, we fall back
    }
    return session_id

def get_next_intake_question(session_id: str) -> Optional[dict]:
    """
    Returns the next question dict: {id, text, index, total}
    If done, returns None.
    """
    s = _SESSIONS.get(session_id)
    if not s:
        return None

    asked = s["q_index"]
    total_cap = s["target_max"]

    # If we've already reached current cap, consider allowing extras:
    if asked >= total_cap and s["extras_used"] == 0 and asked >= _TARGET_QUESTIONS:
        # We'll let the LLM decide if extras are justified when we call it below
        pass
    elif asked >= total_cap:
        # Already at the (possibly extended) cap → we're done
        return None

    db = get_database()
    pi = _get_patient_info_by_id(db, s["patient_id"]) or {}

    # Build history as pairs (Q, A) for the LLM
    qa_history: List[Tuple[str, str]] = []
    for i, q_text in enumerate(s["questions"], start=1):
        qid = f"q{i}"
        qa_history.append((q_text, s["answers"].get(qid)))

    # Try LLM (unless disabled due to prior errors)
    next_q_text: Optional[str] = None
    allow_extra = False
    done = False
    if not s["llm_disabled"]:
        try:
            data = _llm_next_question(pi, qa_history, asked_count=asked)
            next_q_text = (data.get("next_question") or "").strip()
            done = bool(data.get("done"))
            allow_extra = bool(data.get("needs_extra"))
        except Exception:
            # Disable LLM for this session and fall back
            s["llm_disabled"] = True

    # Fallback logic
    if s["llm_disabled"]:
        if asked < len(_FALLBACK_QUESTIONS):
            next_q_text = _FALLBACK_QUESTIONS[asked]
            done = False
        else:
            done = True

    # Apply caps/extra rules
    if done:
        return None

    if asked >= _TARGET_QUESTIONS and allow_extra and s["extras_used"] < _EXTRA_ALLOWED_MAX:
        # grant one more slot up to hard cap
        s["extras_used"] += 1
        s["target_max"] = min(_HARD_CAP, _TARGET_QUESTIONS + s["extras_used"])
        total_cap = s["target_max"]  # update view

    # If no question produced (edge case), also finish
    if not next_q_text:
        return None

    # Register the question we are about to ask
    s["questions"].append(next_q_text)
    s["q_index"] += 1
    q_id = f"q{len(s['questions'])}"
    return {"id": q_id, "text": next_q_text, "index": len(s["questions"]), "total": total_cap}

def submit_intake_answer(session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Saves the current question's answer and advances.
    Payload: {"value": "...user answer..."}
    Returns: {completed: bool, next_question: Optional[dict]}
    """
    s = _SESSIONS.get(session_id)
    if not s:
        return {"error": "invalid_session"}

    current_idx = len(s["questions"])
    if current_idx == 0:
        # No question asked yet
        next_q = get_next_intake_question(session_id)
        return {"completed": next_q is None, "next_question": next_q}

    # Save answer to the last asked question
    q_id = f"q{current_idx}"
    s["answers"][q_id] = payload.get("value")

    # Ask next one
    next_q = get_next_intake_question(session_id)
    return {"completed": next_q is None, "next_question": next_q}

def get_intake_state(session_id: str) -> Optional[dict]:
    """
    Returns a snapshot of the session, including asked questions, answers, and caps.
    """
    s = _SESSIONS.get(session_id)
    if not s:
        return None
    # Redact nothing here; this is an internal summary endpoint.
    return {
        "patient_id": s["patient_id"],
        "asked": len(s["questions"]),
        "target_max": s["target_max"],
        "extras_used": s["extras_used"],
        "questions": s["questions"],
        "answers": s["answers"],
        "llm_disabled": s["llm_disabled"],
        "created_at": s["created_at"].isoformat(),
    }
