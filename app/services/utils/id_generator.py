# app/services/utils/id_generator.py
from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from typing import Optional

try:
    # Optional import so this file still works if pymongo isn't present at import time
    from pymongo import ReturnDocument  # type: ignore
except Exception:  # pragma: no cover
    ReturnDocument = None  # type: ignore


def _today_str() -> str:
    return datetime.utcnow().strftime("%Y%m%d")


def generate_patient_id(db: Optional[object] = None, prefix: str = "CLINIC01") -> str:
    """
    If a MongoDB `db` is provided, use a per-day counter to make IDs like:
      CLINIC01-20250829-0001
    Otherwise, fall back to a UUID suffix.
    """
    date = _today_str()
    if db and ReturnDocument:
        try:
            counter = db.patient_counter.find_one_and_update(
                {"_id": date},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
            seq = str(counter["seq"]).zfill(4)
            return f"{prefix}-{date}-{seq}"
        except Exception:
            # fall through to UUID fallback if counter fails
            pass
    return f"{prefix}-{date}-{str(uuid4())[:8].upper()}"


def generate_visit_id(
    db: Optional[object] = None,
    patient_id: Optional[str] = None,
    prefix: str = "V",
) -> str:
    """
    If a MongoDB `db` and `patient_id` are provided, use a per-(patient,day) counter to make IDs like:
      V20250829-01, V20250829-02, ...
    Otherwise, fall back to a UUID suffix.
    """
    date = _today_str()
    if db and patient_id and ReturnDocument:
        try:
            key = f"{patient_id}:{date}"
            counter = db.visit_counter.find_one_and_update(
                {"_id": key},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
            seq = str(counter["seq"]).zfill(2)
            return f"{prefix}{date}-{seq}"
        except Exception:
            # fall through to UUID fallback if counter fails
            pass
    return f"{prefix}{date}-{str(uuid4())[:4].upper()}"


# ---- Legacy helpers kept for backward compatibility ----
def new_patient_id(prefix: str = "CLINIC01") -> str:
    return generate_patient_id(None, prefix)


def new_visit_id(prefix: str = "V") -> str:
    # Historical simple style without counter
    return f"{prefix}{_today_str()}"
