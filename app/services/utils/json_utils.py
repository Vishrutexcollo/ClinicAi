# app/services/utils/json_utils.py
import json

def safe_json(data) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception:
        return str(data)
